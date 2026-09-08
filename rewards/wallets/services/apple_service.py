import io

from django.conf import settings
from django.urls import reverse

from py_pkpass.models import Barcode, BarcodeFormat, Pass, StoreCard

from .base import PaseResult, WalletProvider


class AppleWalletProvider(WalletProvider):
    """Genera un pase tipo 'store card' (.pkpass) con el saldo y el QR de
    la tarjeta. La actualización automática vía APNs queda para una fase
    futura; por ahora el pase se (re)genera bajo demanda en cada descarga."""

    def is_configured(self) -> bool:
        return bool(
            settings.APPLE_WALLET_TEAM_ID
            and settings.APPLE_WALLET_PASS_TYPE_ID
            and settings.APPLE_WALLET_CERTIFICATE_PATH
            and settings.APPLE_WALLET_KEY_PATH
            and settings.APPLE_WALLET_WWDR_PATH
        )

    def generar_pase(self, tarjeta, request) -> PaseResult:
        from lealtad.services.reglas_service import regla_vigente
        from stores.models import Store

        negocio = Store.objects.first()
        regla = regla_vigente(negocio)
        nombre_negocio = negocio.name if negocio else "Rewards"

        card = StoreCard()
        card.addPrimaryField("balance", str(tarjeta.saldo), "Puntos")
        if regla:
            card.addSecondaryField("meta", str(regla.meta_puntos), "Meta")
            card.addSecondaryField("premio", regla.descripcion_premio, "Premio")
        card.addAuxiliaryField("cliente", tarjeta.costumer.nombre, "Cliente")

        passfile = Pass(
            card,
            passTypeIdentifier=settings.APPLE_WALLET_PASS_TYPE_ID,
            organizationName=nombre_negocio,
            teamIdentifier=settings.APPLE_WALLET_TEAM_ID,
        )
        passfile.serialNumber = tarjeta.codigo
        passfile.description = f"Tarjeta de lealtad - {nombre_negocio}"
        if negocio and negocio.color_primario:
            passfile.backgroundColor = _hex_to_rgb_css(negocio.color_primario)

        url = request.build_absolute_uri(
            reverse("lealtad:tarjeta_detail", args=[tarjeta.codigo])
        )
        passfile.barcode = Barcode(message=url, format=BarcodeFormat.QR)

        for filename, data in _iconos(negocio).items():
            passfile.addFile(filename, io.BytesIO(data))

        buf = io.BytesIO()
        passfile.create(
            settings.APPLE_WALLET_CERTIFICATE_PATH,
            settings.APPLE_WALLET_KEY_PATH,
            settings.APPLE_WALLET_WWDR_PATH,
            settings.APPLE_WALLET_KEY_PASSWORD,
            buf,
        )
        return PaseResult(
            kind="file",
            content=buf.getvalue(),
            content_type="application/vnd.apple.pkpass",
            filename=f"{tarjeta.codigo}.pkpass",
        )


def _iconos(negocio):
    """icon.png (29x29) e icon@2x.png (58x58) son obligatorios: sin ellos
    Apple considera el .pkpass inválido. Se generan desde el logo del
    negocio, o un cuadrado del color de marca si no hay logo."""
    from PIL import Image

    color = _hex_to_rgb(negocio.color_primario) if negocio and negocio.color_primario else (64, 81, 137)

    iconos = {}
    for name, size in (("icon.png", 29), ("icon@2x.png", 58)):
        if negocio and negocio.logo:
            img = Image.open(negocio.logo.path).convert("RGBA").resize((size, size))
        else:
            img = Image.new("RGBA", (size, size), color + (255,))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        iconos[name] = buf.getvalue()
    return iconos


def _hex_to_rgb(value):
    value = value.lstrip("#")
    if len(value) != 6:
        return (64, 81, 137)
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def _hex_to_rgb_css(value):
    r, g, b = _hex_to_rgb(value)
    return f"rgb({r}, {g}, {b})"
