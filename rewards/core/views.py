from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.utils import timezone
from django.views.generic import TemplateView

from compras.models import Compra
from costumers.models import Costumer
from cuentas.mixins import DuenoRequiredMixin
from cuentas.models import Rol
from lealtad.models import Canje, MovimientoPuntos, TipoMovimiento, Visita
from locations.models import Sucursal
from stores.models import Store

DIAS_GRAFICA = 14


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "core/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        perfil = getattr(self.request.user, "perfil", None)
        context["perfil"] = perfil
        if perfil and perfil.rol == Rol.DUENO and perfil.activo:
            context.update(self._dueno_context())
        return context

    def _dueno_context(self):
        store = Store.objects.first()
        compras_qs = Compra.objects.filter(sucursal__store=store)
        visitas_qs = Visita.objects.filter(sucursal__store=store)
        canjes_qs = Canje.objects.filter(sucursal__store=store)

        puntos_compras = compras_qs.aggregate(t=Sum("puntos_otorgados"))["t"] or 0
        puntos_visitas = visitas_qs.aggregate(t=Sum("puntos_otorgados"))["t"] or 0

        totales = {
            "ingresos": compras_qs.aggregate(t=Sum("monto"))["t"] or 0,
            "puntos_otorgados": puntos_compras + puntos_visitas,
            "puntos_canjeados": canjes_qs.aggregate(t=Sum("puntos_consumidos"))["t"] or 0,
            "total_clientes": Costumer.objects.count(),
        }

        dias = [
            timezone.localdate() - timedelta(days=i)
            for i in range(DIAS_GRAFICA - 1, -1, -1)
        ]
        movimientos_qs = MovimientoPuntos.objects.filter(
            tipo=TipoMovimiento.ACUMULACION,
            tarjeta__costumer__isnull=False,
        )
        serie = []
        for dia in dias:
            pts = movimientos_qs.filter(fecha__date=dia).aggregate(t=Sum("puntos"))["t"] or 0
            serie.append(pts)

        actividad = list(
            MovimientoPuntos.objects.select_related(
                "tarjeta__costumer",
                "compra__sucursal", "compra__cajero",
                "visita__sucursal", "visita__cajero",
                "canje__sucursal", "canje__cajero",
            ).order_by("-fecha")[:50]
        )

        return {
            "totales": totales,
            "chart_labels": [dia.strftime("%d %b") for dia in dias],
            "chart_data": serie,
            "actividad": actividad,
        }


class ReportesView(DuenoRequiredMixin, TemplateView):
    """Reportes de compras y puntos otorgados/canjeados por sucursal,
    filtrables por periodo (?desde=YYYY-MM-DD&hasta=YYYY-MM-DD)."""

    template_name = "core/reportes.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        desde = self.request.GET.get("desde") or ""
        hasta = self.request.GET.get("hasta") or ""

        compras_qs = Compra.objects.all()
        canjes_qs = Canje.objects.all()
        if desde:
            compras_qs = compras_qs.filter(fecha__date__gte=desde)
            canjes_qs = canjes_qs.filter(fecha__date__gte=desde)
        if hasta:
            compras_qs = compras_qs.filter(fecha__date__lte=hasta)
            canjes_qs = canjes_qs.filter(fecha__date__lte=hasta)

        filas = []
        for sucursal in Sucursal.objects.select_related("store"):
            compras_sucursal = compras_qs.filter(sucursal=sucursal)
            canjes_sucursal = canjes_qs.filter(sucursal=sucursal)
            filas.append({
                "sucursal": sucursal,
                "num_compras": compras_sucursal.count(),
                "monto_total": compras_sucursal.aggregate(t=Sum("monto"))["t"] or 0,
                "puntos_otorgados": compras_sucursal.aggregate(t=Sum("puntos_otorgados"))["t"] or 0,
                "num_canjes": canjes_sucursal.count(),
                "puntos_canjeados": canjes_sucursal.aggregate(t=Sum("puntos_consumidos"))["t"] or 0,
            })

        context["filas"] = filas
        context["desde"] = desde
        context["hasta"] = hasta
        context["totales"] = {
            "num_compras": sum(f["num_compras"] for f in filas),
            "monto_total": sum(f["monto_total"] for f in filas),
            "puntos_otorgados": sum(f["puntos_otorgados"] for f in filas),
            "num_canjes": sum(f["num_canjes"] for f in filas),
            "puntos_canjeados": sum(f["puntos_canjeados"] for f in filas),
        }
        return context
