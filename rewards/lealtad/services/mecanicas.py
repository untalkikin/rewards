"""Strategy: cada tipo de promoción (TipoMecanica) sabe calcular sus
propios puntos y si necesita un monto de compra. obtener_mecanica actúa
de Factory para no tener 'if tipo == ...' desperdigados por el código."""

from abc import ABC, abstractmethod

from ..models import TipoMecanica


class MecanicaAcumulacion(ABC):
    @abstractmethod
    def requiere_monto(self) -> bool:
        ...

    @abstractmethod
    def calcular_puntos(self, promocion, *, monto=None) -> int:
        ...


class MecanicaPorMonto(MecanicaAcumulacion):
    """1 unidad de 'monto_base' gastada = 'puntos_otorgados' puntos."""

    def requiere_monto(self):
        return True

    def calcular_puntos(self, promocion, *, monto=None):
        if not monto or not promocion.monto_base:
            return 0
        unidades = int(monto // promocion.monto_base)
        return unidades * promocion.puntos_otorgados


class MecanicaPorVisita(MecanicaAcumulacion):
    """Cada escaneo otorga puntos_otorgados puntos fijos (normalmente 1
    'sello'), sin importar ningún monto."""

    def requiere_monto(self):
        return False

    def calcular_puntos(self, promocion, *, monto=None):
        return promocion.puntos_otorgados


_MECANICAS = {
    TipoMecanica.MONTO: MecanicaPorMonto,
    TipoMecanica.VISITA: MecanicaPorVisita,
}


def obtener_mecanica(tipo_mecanica) -> MecanicaAcumulacion:
    clase = _MECANICAS.get(tipo_mecanica)
    if clase is None:
        raise ValueError(f"Mecánica de acumulación desconocida: {tipo_mecanica}")
    return clase()
