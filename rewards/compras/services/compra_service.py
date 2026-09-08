from django.db import transaction

from lealtad.models import MovimientoPuntos, ReglaPuntos, TipoMovimiento

from ..models import Compra


class SinReglaPuntosVigente(Exception):
    """No hay una ReglaPuntos activa para el negocio de la sucursal."""


@transaction.atomic
def registrar_compra(*, costumer, sucursal, cajero, monto, referencia=""):
    tarjeta = costumer.tarjeta

    regla = (
        ReglaPuntos.objects.select_for_update()
        .filter(store=sucursal.store, activa=True)
        .order_by("-vigente_desde")
        .first()
    )
    if regla is None or not regla.monto_base:
        raise SinReglaPuntosVigente(
            "El negocio no tiene una regla de puntos activa configurada."
        )

    unidades = int(monto // regla.monto_base)
    puntos = unidades * regla.puntos_otorgados

    compra = Compra.objects.create(
        costumer=costumer,
        sucursal=sucursal,
        cajero=cajero,
        monto=monto,
        puntos_otorgados=puntos,
        referencia=referencia,
    )
    MovimientoPuntos.objects.create(
        tarjeta=tarjeta,
        tipo=TipoMovimiento.ACUMULACION,
        puntos=puntos,
        compra=compra,
    )
    return compra
