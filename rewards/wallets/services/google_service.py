import json
import time

import jwt
from django.conf import settings
from django.urls import reverse

from .base import PaseResult, WalletProvider


class GoogleWalletProvider(WalletProvider):
    """Genera el JWT firmado para el botón 'Save to Google Wallet' de una
    clase loyalty. La clase y el objeto van embebidos en el propio JWT
    (no requiere una llamada previa a la REST API de Google Wallet)."""

    SAVE_URL = "https://pay.google.com/gp/v/save/{token}"

    def is_configured(self) -> bool:
        return bool(
            settings.GOOGLE_WALLET_ISSUER_ID
            and settings.GOOGLE_WALLET_SERVICE_ACCOUNT_FILE
        )

    def generar_pase(self, tarjeta, request) -> PaseResult:
        from lealtad.services.reglas_service import regla_vigente
        from stores.models import Store

        negocio = Store.objects.first()
        regla = regla_vigente(negocio)
        nombre_negocio = negocio.name if negocio else "Rewards"

        client_email, private_key = _credenciales()
        class_id = _class_id()
        object_id = _object_id(tarjeta)

        loyalty_class = {
            "id": class_id,
            "issuerName": nombre_negocio,
            "programName": nombre_negocio,
            "reviewStatus": "UNDER_REVIEW",
        }

        label_puntos = "Puntos"
        if regla and regla.meta_puntos:
            label_puntos = f"Puntos (meta {regla.meta_puntos})"

        loyalty_object = {
            "id": object_id,
            "classId": class_id,
            "state": "ACTIVE",
            "accountId": tarjeta.codigo,
            "accountName": tarjeta.costumer.nombre,
            "loyaltyPoints": {
                "label": label_puntos,
                "balance": {"string": str(tarjeta.saldo)},
            },
            "barcode": {
                "type": "QR_CODE",
                "value": request.build_absolute_uri(
                    reverse("lealtad:tarjeta_detail", args=[tarjeta.codigo])
                ),
            },
        }

        payload = {
            "iss": client_email,
            "aud": "google",
            "typ": "savetowallet",
            "iat": int(time.time()),
            "origins": [],
            "payload": {
                "loyaltyClasses": [loyalty_class],
                "loyaltyObjects": [loyalty_object],
            },
        }
        token = jwt.encode(payload, private_key, algorithm="RS256")
        return PaseResult(kind="redirect", url=self.SAVE_URL.format(token=token))


def _credenciales():
    with open(settings.GOOGLE_WALLET_SERVICE_ACCOUNT_FILE) as fh:
        data = json.load(fh)
    return data["client_email"], data["private_key"]


def _class_id():
    return f"{settings.GOOGLE_WALLET_ISSUER_ID}.{settings.GOOGLE_WALLET_CLASS_SUFFIX}"


def _object_id(tarjeta):
    return f"{settings.GOOGLE_WALLET_ISSUER_ID}.{tarjeta.codigo}"
