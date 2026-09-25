from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from costumers.models import Costumer
from cuentas.mixins import CajeroRequiredMixin
from lealtad.models import TipoMecanica
from lealtad.services.acumulacion_service import registrar_evento
from lealtad.services.canje_service import SaldoInsuficiente, efectuar_canje
from lealtad.services.exceptions import RestriccionNoCumplida, SinPromocionVigente
from lealtad.services.promociones_service import casillas_de, promocion_vigente

from .forms import BuscarClienteForm, RegistrarCompraForm


class BuscarClienteView(CajeroRequiredMixin, View):
    template_name = "compras/buscar_cliente.html"

    def get(self, request):
        return render(request, self.template_name, {"form": BuscarClienteForm()})

    def post(self, request):
        form = BuscarClienteForm(request.POST)
        if form.is_valid():
            codigo = form.cleaned_data["codigo"].strip()
            if Costumer.objects.filter(card_code=codigo).exists():
                return redirect("compras:cliente_detail", codigo=codigo)
            form.add_error("codigo", "No se encontró ningún cliente con ese código.")
        return render(request, self.template_name, {"form": form})


class ClienteCajeroView(CajeroRequiredMixin, View):
    template_name = "compras/cliente_detail.html"

    def get(self, request, codigo):
        costumer = get_object_or_404(Costumer, card_code=codigo)
        context = self._context(costumer, request.user.perfil)
        if context["promocion"] and context["promocion"].tipo_mecanica == TipoMecanica.MONTO:
            context["form"] = RegistrarCompraForm()
        return render(request, self.template_name, context)

    def post(self, request, codigo):
        costumer = get_object_or_404(Costumer, card_code=codigo)
        perfil = request.user.perfil

        if not perfil.sucursal:
            messages.error(request, "Tu usuario de cajero no tiene una sucursal asignada.")
            return redirect("compras:cliente_detail", codigo=codigo)

        promocion = promocion_vigente(perfil.sucursal.store)

        if promocion and promocion.tipo_mecanica == TipoMecanica.VISITA:
            try:
                registrar_evento(costumer=costumer, sucursal=perfil.sucursal, cajero=request.user)
                messages.success(request, "Visita registrada. Saldo actualizado.")
            except (SinPromocionVigente, RestriccionNoCumplida) as exc:
                messages.error(request, str(exc))
            return redirect("compras:cliente_detail", codigo=codigo)

        form = RegistrarCompraForm(request.POST)
        if form.is_valid():
            try:
                registrar_evento(
                    costumer=costumer,
                    sucursal=perfil.sucursal,
                    cajero=request.user,
                    monto=form.cleaned_data["monto"],
                    referencia=form.cleaned_data["referencia"],
                )
                messages.success(request, "Compra registrada. Saldo actualizado.")
                return redirect("compras:cliente_detail", codigo=codigo)
            except (SinPromocionVigente, RestriccionNoCumplida) as exc:
                form.add_error(None, str(exc))

        context = self._context(costumer, perfil)
        context["form"] = form
        return render(request, self.template_name, context)

    def _context(self, costumer, perfil):
        tarjeta = costumer.tarjeta
        promocion = promocion_vigente(perfil.sucursal.store) if perfil.sucursal else None
        puede_canjear = bool(promocion and tarjeta.saldo >= promocion.meta_puntos)
        return {
            "costumer": costumer,
            "tarjeta": tarjeta,
            "historial": tarjeta.movimientos.all()[:10],
            "promocion": promocion,
            "puede_canjear": puede_canjear,
            "casillas": casillas_de(tarjeta, promocion),
        }


class CanjeConfirmView(CajeroRequiredMixin, View):
    template_name = "compras/canje_confirm.html"

    def get(self, request, codigo):
        costumer = get_object_or_404(Costumer, card_code=codigo)
        tarjeta = costumer.tarjeta
        perfil = request.user.perfil
        promocion = promocion_vigente(perfil.sucursal.store) if perfil.sucursal else None
        return render(request, self.template_name, {
            "costumer": costumer,
            "tarjeta": tarjeta,
            "promocion": promocion,
        })

    def post(self, request, codigo):
        costumer = get_object_or_404(Costumer, card_code=codigo)
        tarjeta = costumer.tarjeta
        perfil = request.user.perfil

        if not perfil.sucursal:
            messages.error(request, "Tu usuario de cajero no tiene una sucursal asignada.")
        else:
            try:
                canje = efectuar_canje(
                    tarjeta=tarjeta, sucursal=perfil.sucursal, cajero=request.user,
                )
                messages.success(
                    request,
                    f"Canje registrado: {canje.premio}. El saldo se reinició a 0.",
                )
            except (SinPromocionVigente, SaldoInsuficiente) as exc:
                messages.error(request, str(exc))

        return redirect("compras:cliente_detail", codigo=codigo)
