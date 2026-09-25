from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, ListView

from cuentas.mixins import DuenoRequiredMixin
from stores.models import Store
from wallets.services.apple_service import AppleWalletProvider
from wallets.services.google_service import GoogleWalletProvider

from .forms import PromocionForm
from .models import Promocion, TarjetaLealtad
from .services.promociones_service import casillas_de, promocion_vigente
from .services.qr_service import generar_qr_png

_apple_wallet = AppleWalletProvider()
_google_wallet = GoogleWalletProvider()


class TarjetaDetailView(DetailView):
    """Panel del cliente: público (sin login), accesible solo con el código
    único e inmutable de la tarjeta -- el mismo que va codificado en el QR."""

    model = TarjetaLealtad
    template_name = "lealtad/tarjeta_detail.html"
    context_object_name = "tarjeta"

    def get_object(self, queryset=None):
        return get_object_or_404(
            TarjetaLealtad.objects.select_related("costumer"),
            costumer__card_code=self.kwargs["codigo"],
            activa=True,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tarjeta = self.object
        # Despliegue de un solo negocio: se toma la promoción vigente del único Store.
        promocion = promocion_vigente(Store.objects.first())
        context["historial"] = tarjeta.movimientos.all()[:20]
        context["promocion"] = promocion
        context["progreso"] = _progreso(tarjeta, promocion)
        context["casillas"] = casillas_de(tarjeta, promocion)
        context["apple_wallet_disponible"] = _apple_wallet.is_configured()
        context["google_wallet_disponible"] = _google_wallet.is_configured()
        return context


def _progreso(tarjeta, promocion):
    if not promocion or not promocion.meta_puntos:
        return 0
    return max(0, min(100, int(tarjeta.saldo * 100 / promocion.meta_puntos)))


def tarjeta_qr_view(request, codigo):
    tarjeta = get_object_or_404(TarjetaLealtad, costumer__card_code=codigo)
    url = request.build_absolute_uri(
        reverse("lealtad:tarjeta_detail", args=[codigo])
    )
    png = generar_qr_png(url)
    return HttpResponse(png, content_type="image/png")


def _tarjeta_activa(codigo):
    return get_object_or_404(TarjetaLealtad, costumer__card_code=codigo, activa=True)


def tarjeta_apple_wallet_view(request, codigo):
    tarjeta = _tarjeta_activa(codigo)
    if not _apple_wallet.is_configured():
        return HttpResponse(
            "Apple Wallet todavía no está configurado para este negocio.",
            status=501,
            content_type="text/plain; charset=utf-8",
        )
    resultado = _apple_wallet.generar_pase(tarjeta, request)
    response = HttpResponse(resultado.content, content_type=resultado.content_type)
    response["Content-Disposition"] = f'attachment; filename="{resultado.filename}"'
    return response


def tarjeta_google_wallet_view(request, codigo):
    tarjeta = _tarjeta_activa(codigo)
    if not _google_wallet.is_configured():
        return HttpResponse(
            "Google Wallet todavía no está configurado para este negocio.",
            status=501,
            content_type="text/plain; charset=utf-8",
        )
    resultado = _google_wallet.generar_pase(tarjeta, request)
    return redirect(resultado.url)


class PromocionListView(DuenoRequiredMixin, ListView):
    """Panel del dueño: promociones del negocio, con cuál está activa."""

    model = Promocion
    template_name = "lealtad/promocion_list.html"
    context_object_name = "promociones"

    def get_queryset(self):
        return (
            Promocion.objects.filter(store=Store.objects.first())
            .select_related("restriccion")
            .order_by("-activa", "-vigente_desde")
        )


class PromocionCreateView(DuenoRequiredMixin, View):
    """Alta de una promoción: el dueño elige la mecánica (por monto de
    compra o por visita) y, si quiere, un límite antiabuso de escaneos."""

    template_name = "lealtad/promocion_form.html"

    def get(self, request):
        return render(request, self.template_name, {"form": PromocionForm()})

    def post(self, request):
        form = PromocionForm(request.POST)
        if form.is_valid():
            form.save(store=Store.objects.first())
            messages.success(request, "Promoción creada correctamente.")
            return redirect("lealtad:promocion_list")
        return render(request, self.template_name, {"form": form})


class PromocionActivarView(DuenoRequiredMixin, View):
    """Activa una promoción y desactiva cualquier otra del mismo negocio
    (solo una promoción puede estar vigente a la vez)."""

    def post(self, request, pk):
        promocion = get_object_or_404(Promocion, pk=pk)
        Promocion.objects.filter(store=promocion.store, activa=True).update(activa=False)
        promocion.activa = True
        promocion.save(update_fields=["activa"])
        messages.success(request, f"'{promocion.nombre}' ahora es la promoción activa.")
        return redirect("lealtad:promocion_list")
