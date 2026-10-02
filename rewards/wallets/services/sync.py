"""External transports run ONLY when explicitly enabled and sync_wallets --send is used."""
import json
import ssl
import time
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen
from django.conf import settings
import jwt

def sync_google(identity):
    from .google_service import _credenciales, _object_id
    email, key = _credenciales()
    now = int(time.time())
    assertion = jwt.encode({"iss": email, "scope": "https://www.googleapis.com/auth/wallet_object.issuer",
        "aud": "https://oauth2.googleapis.com/token", "iat": now, "exp": now + 3600}, key, algorithm="RS256")
    body = urlencode({"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer", "assertion": assertion}).encode()
    with urlopen(Request("https://oauth2.googleapis.com/token", data=body), timeout=20) as response:
        access_token = json.load(response)["access_token"]
    tarjeta = identity.tarjeta
    from lealtad.services.promociones_service import promocion_vigente
    promotion = promocion_vigente(tarjeta.costumer.store)
    label = f"Puntos (meta {promotion.meta_puntos})" if promotion else "Puntos"
    color = (promotion.fondo_solido if promotion else "") or tarjeta.costumer.store.color_primario
    data = {"loyaltyPoints": {"label": label, "balance": {"string": str(tarjeta.saldo)}}, "state": "ACTIVE" if tarjeta.activa else "INACTIVE", "hexBackgroundColor": color}
    request = Request("https://walletobjects.googleapis.com/walletobjects/v1/loyaltyObject/" + quote(_object_id(tarjeta), safe=""),
        data=json.dumps(data).encode(), method="PATCH", headers={"Authorization": "Bearer " + access_token, "Content-Type": "application/json"})
    with urlopen(request, timeout=20) as response:
        response.read()

def sync_apple(identity):
    import httpx
    context = ssl.create_default_context()
    context.load_cert_chain(settings.APPLE_WALLET_CERTIFICATE_PATH, settings.APPLE_WALLET_KEY_PATH,
                            password=settings.APPLE_WALLET_KEY_PASSWORD or None)
    with httpx.Client(http2=True, verify=context, timeout=20) as client:
        for device in identity.devices.all():
            response = client.post("https://api.push.apple.com/3/device/" + quote(device.push_token, safe=""),
                json={}, headers={"apns-topic": settings.APPLE_WALLET_PASS_TYPE_ID, "apns-priority": "5", "apns-push-type": "background"})
            if response.status_code == 410:
                device.delete()
            else:
                response.raise_for_status()

def deliver(update):
    if not settings.WALLET_SYNC_ENABLED:
        raise RuntimeError("La sincronización externa está deshabilitada.")
    identity = update.identity
    if identity.google_requested:
        sync_google(identity)
    if identity.devices.exists():
        sync_apple(identity)
