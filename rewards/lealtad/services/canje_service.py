from django.db import transaction

from ..models import Canje, MovimientoPuntos, ReglaPuntos, TipoMovimiento


class SinReglaPuntosVigente(Exception):
    """No hay una ReglaPuntos activa para el negocio de la sucursal."""


class SaldoInsuficiente(Exception):
    """El saldo de la tarjeta no alcanza la meta de la regla vigente."""


@transaction.atomic
def efectuar_canje(*, tarjeta, sucursal, cajero):
    regla = (
        ReglaPuntos.objects.select_for_update()
        .filter(store=sucursal.store, activa=True)
        .order_by("-vigente_desde")
        .first()
    )
    if regla is None:
        raise SinReglaPuntosVigente(
            "El negocio no tiene una regla de puntos activa configurada."
        )

    saldo = tarjeta.saldo
    if saldo < regla.meta_puntos:
        raise SaldoInsuficiente(
            f"El cliente tiene {saldo} puntos; se necesitan {regla.meta_puntos}."
        )

    # Reset a cero: se consume TODO el saldo actual, no solo la meta.
    canje = Canje.objects.create(
        tarjeta=tarjeta,
        sucursal=sucursal,
        cajero=cajero,
        puntos_consumidos=saldo,
        premio=regla.descripcion_premio,
    )
    MovimientoPuntos.objects.create(
        tarjeta=tarjeta,
        tipo=TipoMovimiento.CANJE,
        puntos=-saldo,
        canje=canje,
    )
    return canje
