"""Punto de entrada único para acumular puntos, sea por compra o por
visita. Es el 'Template Method' del flujo: los pasos son siempre los
mismos (traer la promoción vigente, validar restricciones, calcular
puntos, registrar el evento, escribir el ledger) y solo el cálculo de
puntos y el tipo de evento creado varían según la mecánica (Strategy)."""

from django.db import transaction

from ..models import MovimientoPuntos, Promocion, TipoMovimiento, Visita
from .exceptions import SinPromocionVigente
from .mecanicas import obtener_mecanica
from .restricciones import restricciones_de


@transaction.atomic
def registrar_evento(*, costumer, sucursal, cajero, monto=None, referencia=""):
    promocion = (
        Promocion.objects.select_for_update()
        .select_related("restriccion")
        .filter(store=sucursal.store, activa=True)
        .order_by("-vigente_desde")
        .first()
    )
    if promocion is None:
        raise SinPromocionVigente(
            "El negocio no tiene una promoción activa configurada."
        )

    for restriccion in restricciones_de(promocion):
        restriccion.validar(costumer=costumer, sucursal=sucursal)

    mecanica = obtener_mecanica(promocion.tipo_mecanica)
    puntos = mecanica.calcular_puntos(promocion, monto=monto)
    tarjeta = costumer.tarjeta

    if mecanica.requiere_monto():
        from compras.models import Compra

        evento = Compra.objects.create(
            costumer=costumer, sucursal=sucursal, cajero=cajero,
            monto=monto, puntos_otorgados=puntos, referencia=referencia,
        )
        movimiento_kwargs = {"compra": evento}
    else:
        evento = Visita.objects.create(
            tarjeta=tarjeta, sucursal=sucursal, cajero=cajero,
            puntos_otorgados=puntos,
        )
        movimiento_kwargs = {"visita": evento}

    MovimientoPuntos.objects.create(
        tarjeta=tarjeta, tipo=TipoMovimiento.ACUMULACION, puntos=puntos,
        **movimiento_kwargs,
    )
    return evento
