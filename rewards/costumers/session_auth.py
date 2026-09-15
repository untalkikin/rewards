"""Autenticación del cliente por sesión (card_code + PIN), independiente
del sistema de auth de Django (que es para el personal: cajero/dueño).
El cliente no tiene User ni password; solo su Costumer con un PIN hasheado.
"""

from django.shortcuts import redirect
from django.urls import reverse

from .models import Costumer

SESSION_KEY = "costumer_id"


def login_costumer(request, costumer):
    request.session[SESSION_KEY] = str(costumer.pk)


def logout_costumer(request):
    request.session.pop(SESSION_KEY, None)


def get_current_costumer(request):
    costumer_id = request.session.get(SESSION_KEY)
    if not costumer_id:
        return None
    return Costumer.objects.filter(pk=costumer_id).first()


class ClienteRequiredMixin:
    """Restringe la vista a un Costumer con sesión iniciada (mi-cuenta).
    No usa request.user (eso es del personal) sino request.costumer."""

    def dispatch(self, request, *args, **kwargs):
        costumer = get_current_costumer(request)
        if costumer is None:
            login_url = reverse("costumers:login")
            return redirect(f"{login_url}?next={request.path}")
        request.costumer = costumer
        return super().dispatch(request, *args, **kwargs)
