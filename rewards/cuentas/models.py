from django.conf import settings
from django.db import models

from locations.models import Sucursal


class Rol(models.TextChoices):
    DUENO = "DUENO", "Dueño"
    CAJERO = "CAJERO", "Cajero"


class Perfil(models.Model):
    """Extiende AUTH_USER_MODEL con el rol dentro del negocio. Un cajero
    queda ligado a la sucursal donde opera; un dueño no requiere sucursal."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil",
    )
    rol = models.CharField(max_length=10, choices=Rol.choices)
    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.PROTECT,
        related_name="cajeros",
        null=True,
        blank=True,
        help_text="Requerido solo para cajeros.",
    )
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_username()} ({self.get_rol_display()})"
