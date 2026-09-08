from .models import Store


def negocio(request):
    """Inyecta la configuración de marca del Negocio (Store) en todos los
    templates, para que Velzon muestre logo/favicon/nombre/colores sin
    tocar el layout base. Al ser un despliegue por negocio, toma el primero
    (o único) registro existente."""
    return {"negocio": Store.objects.first()}
