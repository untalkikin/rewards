from django.core.exceptions import ValidationError
from django.db import models
import uuid


def validar_tamano_imagen(archivo):
    limite_mb = 5
    if archivo.size > limite_mb * 1024 * 1024:
        raise ValidationError(f"La imagen no puede pesar más de {limite_mb}MB.")


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
    login_banner = models.ImageField(
        upload_to="negocio/login_banner/", blank=True, null=True,
        validators=[validar_tamano_imagen],
        help_text="Fondo de las pantallas de acceso de tus clientes (login/registro). Horizontal, máx. 5MB; se recorta para cubrir el espacio disponible.",
    )
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

    class Meta:
        # Orden estable en los selectores de negocio y en el administrador.
        ordering = ["creado_en"]

    def __str__(self):
        return self.name
