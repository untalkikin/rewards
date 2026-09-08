from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from costumers.models import Costumer
from cuentas.mixins import CajeroRequiredMixin
from lealtad.services.canje_service import (
    SaldoInsuficiente,
    SinReglaPuntosVigente,
    efectuar_canje,
)
from lealtad.services.reglas_service import regla_vigente

from .forms import BuscarClienteForm, RegistrarCompraForm
from .services.compra_service import registrar_compra
from .services.compra_service import SinReglaPuntosVigente as SinReglaCompra


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
        context["form"] = RegistrarCompraForm()
        return render(request, self.template_name, context)

    def post(self, request, codigo):
        costumer = get_object_or_404(Costumer, card_code=codigo)
        form = RegistrarCompraForm(request.POST)
        perfil = request.user.perfil

        if not perfil.sucursal:
            form.add_error(None, "Tu usuario de cajero no tiene una sucursal asignada.")
        elif form.is_valid():
            try:
                registrar_compra(
                    costumer=costumer,
                    sucursal=perfil.sucursal,
                    cajero=request.user,
                    monto=form.cleaned_data["monto"],
                    referencia=form.cleaned_data["referencia"],
                )
                messages.success(request, "Compra registrada. Saldo actualizado.")
                return redirect("compras:cliente_detail", codigo=codigo)
            except SinReglaCompra as exc:
                form.add_error(None, str(exc))

        context = self._context(costumer, perfil)
        context["form"] = form
        return render(request, self.template_name, context)

    def _context(self, costumer, perfil):
        tarjeta = costumer.tarjeta
        regla = regla_vigente(perfil.sucursal.store) if perfil.sucursal else None
        puede_canjear = bool(regla and tarjeta.saldo >= regla.meta_puntos)
        return {
            "costumer": costumer,
            "tarjeta": tarjeta,
            "historial": tarjeta.movimientos.all()[:10],
            "regla": regla,
            "puede_canjear": puede_canjear,
        }


class CanjeConfirmView(CajeroRequiredMixin, View):
    template_name = "compras/canje_confirm.html"

    def get(self, request, codigo):
        costumer = get_object_or_404(Costumer, card_code=codigo)
        tarjeta = costumer.tarjeta
        perfil = request.user.perfil
        regla = regla_vigente(perfil.sucursal.store) if perfil.sucursal else None
        return render(request, self.template_name, {
            "costumer": costumer,
            "tarjeta": tarjeta,
            "regla": regla,
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
            except (SinReglaPuntosVigente, SaldoInsuficiente) as exc:
                messages.error(request, str(exc))

        return redirect("compras:cliente_detail", codigo=codigo)
