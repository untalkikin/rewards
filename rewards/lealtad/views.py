from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import DetailView

from stores.models import Store
from wallets.services.apple_service import AppleWalletProvider
from wallets.services.google_service import GoogleWalletProvider

from .models import TarjetaLealtad
from .services.qr_service import generar_qr_png
from .services.reglas_service import regla_vigente

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
        # Despliegue de un solo negocio: se toma la regla vigente del único Store.
        regla = regla_vigente(Store.objects.first())
        context["historial"] = tarjeta.movimientos.all()[:20]
        context["regla"] = regla
        context["progreso"] = _progreso(tarjeta, regla)
        context["apple_wallet_disponible"] = _apple_wallet.is_configured()
        context["google_wallet_disponible"] = _google_wallet.is_configured()
        return context


def _progreso(tarjeta, regla):
    if not regla or not regla.meta_puntos:
        return 0
    return max(0, min(100, int(tarjeta.saldo * 100 / regla.meta_puntos)))


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
