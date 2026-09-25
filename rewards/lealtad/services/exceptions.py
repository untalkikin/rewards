class SinPromocionVigente(Exception):
    """No hay una Promocion activa para el negocio de la sucursal."""


class RestriccionNoCumplida(Exception):
    """El evento viola una restricción antiabuso de la promoción (ej. ya
    se alcanzó el máximo de escaneos del día)."""


class SaldoInsuficiente(Exception):
    """El saldo de la tarjeta no alcanza la meta de la promoción vigente."""
