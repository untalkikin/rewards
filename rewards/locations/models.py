from django.db import models
from bases.models import ModelClass
from stores.models import Store


class Sucursal(ModelClass):
    """Punto físico de un Store (Negocio) donde cajeros registran compras
    y canjes. ModelClass aporta nombre/descripcion/auditoría."""

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="sucursales",
    )
    direccion = models.CharField(max_length=255, blank=True)
    telefono = models.CharField(max_length=30, blank=True)
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Sucursal"
        verbose_name_plural = "Sucursales"

    def __str__(self):
        return f"{self.nombre} ({self.store.name})"
