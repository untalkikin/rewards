from ..models import Promocion, TipoMecanica


def promocion_vigente(store):
    """Lectura simple (sin locking) para mostrar progreso/UI. La ruta que
    escribe puntos (acumulacion_service, canje_service) hace su propia
    consulta con select_for_update para evitar condiciones de carrera."""
    if store is None:
        return None
    return (
        Promocion.objects.select_related("restriccion")
        .filter(store=store, activa=True)
        .order_by("-vigente_desde")
        .first()
    )


def casillas_de(tarjeta, promocion):
    """Lista de booleans para pintar la clásica tarjeta de sellos (mecánica
    VISITA): True = casilla llena, False = vacía. Vacía si la promoción es
    de tipo MONTO (esa usa la barra de progreso numérica en su lugar)."""
    if not promocion or promocion.tipo_mecanica != TipoMecanica.VISITA or not promocion.meta_puntos:
        return []
    llenas = min(tarjeta.saldo, promocion.meta_puntos)
    return [True] * llenas + [False] * (promocion.meta_puntos - llenas)
