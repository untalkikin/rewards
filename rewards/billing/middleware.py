from django.conf import settings
from django.shortcuts import redirect
from django.http import HttpResponseForbidden
from .models import Suscripcion

class SubscriptionMiddleware:
    """Optional enforcement for staff; disabled while the instance is prepared."""
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request):
        if settings.BILLING_ENFORCE_SUBSCRIPTION and request.user.is_authenticated and not request.user.is_superuser:
            perfil = getattr(request.user, "perfil", None)
            exempt = request.path.startswith(("/suscripcion/", "/login/", "/logout/", "/cuenta/", "/static/"))
            if perfil and perfil.store_id and not exempt:
                subscription = Suscripcion.objects.filter(store_id=perfil.store_id).first()
                if not subscription or not subscription.permite_acceso:
                    if perfil.rol == "DUENO":
                        return redirect("billing:panel")
                    return HttpResponseForbidden("El dueño debe revisar la suscripción del negocio.")
        return self.get_response(request)
