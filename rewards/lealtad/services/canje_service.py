from django.db import transaction
from .promociones_service import promociones_vigentes
from .access import validar_operacion
from ..models import TarjetaLealtad

from ..models import Canje, MovimientoPuntos, Promocion, TipoMovimiento
from .exceptions import SaldoInsuficiente, SinPromocionVigente

__all__ = ["SinPromocionVigente", "SaldoInsuficiente", "efectuar_canje"]


@transaction.atomic
def efectuar_canje(*, tarjeta, sucursal, cajero):
    tarjeta = TarjetaLealtad.objects.select_for_update().select_related("costumer").get(pk=tarjeta.pk)
    validar_operacion(tarjeta, sucursal, cajero)
    promocion = (
        promociones_vigentes(sucursal.store).select_for_update()
        .order_by("-vigente_desde")
        .first()
    )
    if promocion is None:
        raise SinPromocionVigente(
            "El negocio no tiene una promoción activa configurada."
        )

    saldo = tarjeta.saldo
    if saldo < promocion.meta_puntos:
        raise SaldoInsuficiente(
            f"El cliente tiene {saldo} puntos; se necesitan {promocion.meta_puntos}."
        )

    # Reset a cero: se consume TODO el saldo actual, no solo la meta.
    canje = Canje.objects.create(
        tarjeta=tarjeta,
        sucursal=sucursal,
        cajero=cajero,
        puntos_consumidos=saldo,
        premio=promocion.descripcion_premio,
    )
    MovimientoPuntos.objects.create(
        tarjeta=tarjeta,
        tipo=TipoMovimiento.CANJE,
        puntos=-saldo,
        canje=canje,
    )
    return canje
