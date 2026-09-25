from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View

from cuentas.mixins import StaffRequiredMixin
from lealtad.models import ESTILOS_FONDO
from lealtad.services.promociones_service import casillas_de, promocion_vigente
from stores.models import Store
from wallets.services.apple_service import AppleWalletProvider
from wallets.services.google_service import GoogleWalletProvider

from .forms import ClienteLoginForm, PersonalizarTarjetaForm, RegistrarClienteForm
from .models import Costumer
from .session_auth import ClienteRequiredMixin, get_current_costumer, login_costumer, logout_costumer

_apple_wallet = AppleWalletProvider()
_google_wallet = GoogleWalletProvider()


def _progreso(tarjeta, promocion):
    if not promocion or not promocion.meta_puntos:
        return 0
    return max(0, min(100, int(tarjeta.saldo * 100 / promocion.meta_puntos)))


class RegistrarClienteView(StaffRequiredMixin, View):
    """Alta de clientes por parte de un cajero o dueño."""

    template_name = "costumers/registrar.html"

    def get(self, request):
        return render(request, self.template_name, {"form": RegistrarClienteForm()})

    def post(self, request):
        form = RegistrarClienteForm(request.POST)
        if form.is_valid():
            costumer = form.save()
            messages.success(request, f"Cliente {costumer.nombre} registrado correctamente.")
            return redirect("costumers:registrado", codigo=costumer.card_code)
        return render(request, self.template_name, {"form": form})


class ClienteRegistradoView(StaffRequiredMixin, View):
    """Pantalla de confirmación tras el alta: muestra el código/QR de la
    tarjeta para entregárselo al cliente."""

    template_name = "costumers/registrado.html"

    def get(self, request, codigo):
        costumer = get_object_or_404(Costumer, card_code=codigo)
        return render(request, self.template_name, {
            "costumer": costumer,
            "tarjeta": costumer.tarjeta,
        })


class ClienteLoginView(View):
    """Login del cliente a su panel (mi-cuenta), con teléfono + PIN."""

    template_name = "costumers/login.html"

    def get(self, request):
        if get_current_costumer(request):
            return redirect("costumers:mi_cuenta")
        return render(request, self.template_name, {"form": ClienteLoginForm()})

    def post(self, request):
        form = ClienteLoginForm(request.POST)
        if form.is_valid():
            telefono = form.cleaned_data["telefono"].strip()
            pin = form.cleaned_data["pin"]
            costumer = Costumer.objects.filter(telefono=telefono).first()
            if costumer and costumer.check_pin(pin):
                login_costumer(request, costumer)
                next_url = request.GET.get("next") or reverse("costumers:mi_cuenta")
                return redirect(next_url)
            form.add_error(None, "Teléfono o PIN incorrectos.")
        return render(request, self.template_name, {"form": form})


class ClienteLogoutView(View):
    def get(self, request):
        logout_costumer(request)
        return redirect("costumers:login")

    post = get


class MiCuentaView(ClienteRequiredMixin, View):
    """Panel del cliente autenticado: su saldo, historial y su QR."""

    template_name = "costumers/mi_cuenta.html"

    def get(self, request):
        costumer = request.costumer
        tarjeta = costumer.tarjeta
        promocion = promocion_vigente(Store.objects.first())
        context = {
            "costumer": costumer,
            "tarjeta": tarjeta,
            "historial": tarjeta.movimientos.all()[:20],
            "promocion": promocion,
            "progreso": _progreso(tarjeta, promocion),
            "casillas": casillas_de(tarjeta, promocion),
            "apple_wallet_disponible": _apple_wallet.is_configured(),
            "google_wallet_disponible": _google_wallet.is_configured(),
        }
        return render(request, self.template_name, context)


class PersonalizarTarjetaView(ClienteRequiredMixin, View):
    """El cliente elige el fondo de su tarjeta: un estilo prediseñado, un
    color personalizado, o volver al color de marca del negocio."""

    template_name = "costumers/personalizar.html"

    def get(self, request):
        form = PersonalizarTarjetaForm(instance=request.costumer.tarjeta)
        return self._render(request, form)

    def post(self, request):
        tarjeta = request.costumer.tarjeta
        form = PersonalizarTarjetaForm(request.POST, request.FILES, instance=tarjeta)
        if form.is_valid():
            form.save()
            messages.success(request, "Tu tarjeta se personalizó correctamente.")
            return redirect("costumers:mi_cuenta")
        return self._render(request, form)

    def _render(self, request, form):
        tarjeta = request.costumer.tarjeta
        promocion = promocion_vigente(Store.objects.first())
        return render(request, self.template_name, {
            "form": form,
            "tarjeta": tarjeta,
            "estilos_fondo": ESTILOS_FONDO,
            "promocion": promocion,
            "casillas": casillas_de(tarjeta, promocion),
        })
