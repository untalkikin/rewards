from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from stores.access import staff_store
from django.views import View

from cuentas.mixins import DuenoRequiredMixin
from lealtad.services.promociones_service import casillas_de, promocion_vigente
from stores.models import Store
from wallets.services.apple_service import AppleWalletProvider
from wallets.services.google_service import GoogleWalletProvider

from .forms import ClienteLoginForm, RegistrarClienteForm
from .models import Costumer
from .session_auth import get_current_costumer, login_costumer, logout_costumer

_apple_wallet = AppleWalletProvider()
_google_wallet = GoogleWalletProvider()


def _progreso(tarjeta, promocion):
    if not promocion or not promocion.meta_puntos:
        return 0
    return max(0, min(100, int(tarjeta.saldo * 100 / promocion.meta_puntos)))


def _store_banners():
    """Antes de iniciar sesión no hay forma de saber 'el negocio' del
    visitante (recién va a elegirlo en el selector) -- se manda el fondo de
    cada negocio para que el JS de login/registro lo cambie al vuelo según
    la opción elegida."""
    return {
        str(store.pk): store.login_banner.url if store.login_banner else ""
        for store in Store.objects.all()
    }


class RegistrarClienteView(DuenoRequiredMixin, View):
    """Alta de clientes por parte del dueño. Los cajeros no dan de alta
    clientes -- el modelo de negocio es autorregistro (ver ClienteRegistroView
    en MiCuentaView) o alta directa por el dueño."""

    template_name = "costumers/registrar.html"

    def get(self, request):
        return render(request, self.template_name, {"form": RegistrarClienteForm(store=staff_store(request))})

    def post(self, request):
        form = RegistrarClienteForm(request.POST, store=staff_store(request))
        if form.is_valid():
            costumer = form.save()
            messages.success(request, f"Cliente {costumer.nombre} registrado correctamente.")
            return redirect("costumers:registrado", codigo=costumer.card_code)
        return render(request, self.template_name, {"form": form})


class ClienteRegistradoView(DuenoRequiredMixin, View):
    """Pantalla de confirmación tras el alta: muestra el código/QR de la
    tarjeta para entregárselo al cliente, y el botón de wallet si ya hay
    credenciales configuradas."""

    template_name = "costumers/registrado.html"

    def get(self, request, codigo):
        costumer = get_object_or_404(Costumer, card_code=codigo, store=staff_store(request))
        return render(request, self.template_name, {
            "costumer": costumer,
            "tarjeta": costumer.tarjeta,
            "apple_wallet_disponible": _apple_wallet.is_configured(),
            "google_wallet_disponible": _google_wallet.is_configured(),
        })


class ClienteLoginView(View):
    """Login del cliente a su panel (mi-cuenta), con teléfono + PIN."""

    template_name = "costumers/login.html"

    def get(self, request):
        if get_current_costumer(request):
            return redirect("costumers:mi_cuenta")
        return render(request, self.template_name, {"form": ClienteLoginForm(), "store_banners": _store_banners()})

    def post(self, request):
        form = ClienteLoginForm(request.POST)
        if form.is_valid():
            telefono = form.cleaned_data["telefono"].strip()
            pin = form.cleaned_data["pin"]
            costumer = Costumer.objects.filter(telefono=telefono, store=form.cleaned_data["store"]).first()
            if costumer and costumer.tarjeta.activa and costumer.check_pin(pin):
                login_costumer(request, costumer)
                next_url = request.GET.get("next") or reverse("costumers:mi_cuenta")
                if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
                    next_url = reverse("costumers:mi_cuenta")
                return redirect(next_url)
            form.add_error(None, "Teléfono o PIN incorrectos.")
        return render(request, self.template_name, {"form": form, "store_banners": _store_banners()})


class ClienteLogoutView(View):
    def get(self, request):
        logout_costumer(request)
        return redirect("costumers:login")

    post = get


class MiCuentaView(View):
    """Home del cliente: sin sesión, la pantalla para crear su tarjeta
    (autorregistro); con sesión, su panel (saldo, historial, QR, wallet)."""

    def get(self, request):
        costumer = get_current_costumer(request)
        if costumer is None:
            return render(request, "costumers/registro.html", {
                "form": RegistrarClienteForm(), "store_banners": _store_banners(),
            })
        return self._panel(request, costumer)

    def post(self, request):
        costumer = get_current_costumer(request)
        if costumer is not None:
            return self._panel(request, costumer)

        form = RegistrarClienteForm(request.POST)
        if form.is_valid():
            costumer = form.save(descripcion="Cliente autorregistrado desde el login.")
            login_costumer(request, costumer)
            messages.success(request, f"¡Bienvenido, {costumer.nombre}! Tu tarjeta ya está lista.")
            return redirect("costumers:mi_cuenta")
        return render(request, "costumers/registro.html", {
            "form": form, "store_banners": _store_banners(),
        })

    def _panel(self, request, costumer):
        tarjeta = costumer.tarjeta
        promocion = promocion_vigente(costumer.store)
        context = {
            "negocio": costumer.store,
            "costumer": costumer,
            "tarjeta": tarjeta,
            "historial": tarjeta.movimientos.all()[:20],
            "promocion": promocion,
            "progreso": _progreso(tarjeta, promocion),
            "casillas": casillas_de(tarjeta, promocion),
            "apple_wallet_disponible": _apple_wallet.is_configured(),
            "google_wallet_disponible": _google_wallet.is_configured(),
        }
        return render(request, "costumers/mi_cuenta.html", context)
