from functools import wraps
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from urllib.parse import urlencode
from .models import TarjetaLealtad
from costumers.session_auth import get_current_costumer
from stores.access import staff_store

def tarjeta_autorizada(request, codigo):
    customer = get_current_costumer(request)
    if customer:
        return get_object_or_404(TarjetaLealtad, costumer=customer, costumer__card_code=codigo, activa=True)
    if request.user.is_authenticated:
        return get_object_or_404(TarjetaLealtad, costumer__store=staff_store(request), costumer__card_code=codigo, activa=True)
    return None

def card_access(view):
    @wraps(view)
    def wrapped(request, codigo, *args, **kwargs):
        if tarjeta_autorizada(request, codigo) is None:
            return redirect(reverse("costumers:login") + "?" + urlencode({"next": request.get_full_path()}))
        response = view(request, codigo, *args, **kwargs)
        response["Cache-Control"] = "private, no-store"
        return response
    return wrapped
