import json
import secrets
from django.conf import settings
from django.db.models import Max
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_GET
from .models import WalletIdentity, AppleRegistration, WalletUpdate
from .services.apple_service import AppleWalletProvider

def authorized_identity(request, pass_type, serial):
    if pass_type != settings.APPLE_WALLET_PASS_TYPE_ID:
        return None
    identity = WalletIdentity.objects.select_related("tarjeta__costumer__store").filter(tarjeta__costumer__card_code=serial).first()
    auth = request.headers.get("Authorization", "")
    if not identity or not secrets.compare_digest(auth, "ApplePass " + identity.token):
        return None
    return identity

@csrf_exempt
@require_http_methods(["POST", "DELETE"])
def registration(request, device, pass_type, serial):
    identity = authorized_identity(request, pass_type, serial)
    if identity is None:
        return HttpResponse(status=401)
    if len(device) > 200:
        return HttpResponse(status=400)
    if request.method == "DELETE":
        AppleRegistration.objects.filter(identity=identity, device_id=device).delete()
        return HttpResponse(status=200)
    try:
        data = json.loads(request.body)
        token = data["pushToken"]
        if not isinstance(token, str) or not 1 <= len(token) <= 256:
            raise ValueError()
    except (ValueError, KeyError, TypeError):
        return HttpResponse(status=400)
    _, created = AppleRegistration.objects.update_or_create(identity=identity, device_id=device, defaults={"push_token": token})
    if created:
        WalletUpdate.objects.create(identity=identity)
    return HttpResponse(status=201 if created else 200)

@require_GET
def serials(request, device, pass_type):
    # Apple protocol does not include an Authorization header for this endpoint.
    if pass_type != settings.APPLE_WALLET_PASS_TYPE_ID:
        return HttpResponse(status=404)
    try:
        since = int(request.GET.get("passesUpdatedSince", "0"))
        if since < 0:
            raise ValueError()
    except ValueError:
        return HttpResponse(status=400)
    updates = WalletUpdate.objects.filter(identity__devices__device_id=device, pk__gt=since)
    last = updates.aggregate(last=Max("pk"))["last"]
    if last is None:
        return HttpResponse(status=204)
    codes = list(updates.values_list("identity__tarjeta__costumer__card_code", flat=True).distinct())
    return JsonResponse({"serialNumbers": codes, "lastUpdated": str(last)})

@require_GET
def latest_pass(request, pass_type, serial):
    identity = authorized_identity(request, pass_type, serial)
    if identity is None:
        return HttpResponse(status=401)
    provider = AppleWalletProvider()
    if not provider.is_configured():
        return HttpResponse(status=503)
    result = provider.generar_pase(identity.tarjeta, request)
    response = HttpResponse(result.content, content_type=result.content_type)
    response["Cache-Control"] = "no-store"
    return response
