from django.db import models
import uuid


class Store(models.Model):
    """La cuenta comercial que paga la suscripción (una tienda, cadena,
    franquicia, etc.). Puede tener una o varias sucursales."""

    # UUID en vez de autoincremental: evita filtrar el volumen de negocio
    # (cuántos comercios existen) por el simple hecho de exponer un id en
    # la API, y facilita generar el id en el cliente si algún día hace
    # falta (alta offline, importaciones, etc.).
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    rfc = models.CharField(max_length=13, blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    # --- Marca / branding (panel del Dueño) ---
    logo = models.ImageField(upload_to="negocio/logo/", blank=True, null=True)
    favicon = models.ImageField(upload_to="negocio/favicon/", blank=True, null=True)
    color_primario = models.CharField(
        max_length=7, blank=True, default="#405189",
        help_text="Color hexadecimal, ej. #405189"
    )
    color_secundario = models.CharField(
        max_length=7, blank=True, default="#f3f6f9",
        help_text="Color hexadecimal, ej. #f3f6f9"
    )

    # --- Datos de contacto ---
    telefono = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    direccion = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name
