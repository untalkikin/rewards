"""Specification: cada Restriccion valida de forma independiente si un
evento puede otorgar puntos. restricciones_de() arma la lista de
restricciones activas para una promoción (hoy solo hay un tipo, pero el
service que las aplica no sabe ni le importa cuántas ni cuáles son)."""

from abc import ABC, abstractmethod

from django.db.models import Q
from django.utils import timezone

from ..models import AlcanceRestriccion, TipoMovimiento
from .exceptions import RestriccionNoCumplida


class Restriccion(ABC):
    @abstractmethod
    def validar(self, *, costumer, sucursal):
        """Lanza RestriccionNoCumplida si el evento no puede registrarse."""


class RestriccionMaxEscaneosDia(Restriccion):
    def __init__(self, maximo, alcance):
        self.maximo = maximo
        self.alcance = alcance

    def validar(self, *, costumer, sucursal):
        from ..models import MovimientoPuntos

        hoy = timezone.localdate()
        qs = MovimientoPuntos.objects.filter(
            tarjeta=costumer.tarjeta,
            tipo=TipoMovimiento.ACUMULACION,
            fecha__date=hoy,
        )
        if self.alcance == AlcanceRestriccion.SUCURSAL:
            qs = qs.filter(Q(compra__sucursal=sucursal) | Q(visita__sucursal=sucursal))

        if qs.count() >= self.maximo:
            alcance_txt = "en esta sucursal" if self.alcance == AlcanceRestriccion.SUCURSAL else "en el negocio"
            raise RestriccionNoCumplida(
                f"Este cliente ya alcanzó el máximo de {self.maximo} registro(s) por día {alcance_txt}."
            )


def restricciones_de(promocion) -> list[Restriccion]:
    config = getattr(promocion, "restriccion", None)
    if config is None:
        return []
    return [RestriccionMaxEscaneosDia(maximo=config.max_escaneos_dia, alcance=config.alcance)]
