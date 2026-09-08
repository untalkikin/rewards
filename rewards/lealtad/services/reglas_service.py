from ..models import ReglaPuntos


def regla_vigente(store):
    """Lectura simple (sin locking) para mostrar progreso/UI. La ruta que
    escribe puntos (compra_service, canje_service) hace su propia consulta
    con select_for_update para evitar condiciones de carrera."""
    if store is None:
        return None
    return (
        ReglaPuntos.objects.filter(store=store, activa=True)
        .order_by("-vigente_desde")
        .first()
    )
