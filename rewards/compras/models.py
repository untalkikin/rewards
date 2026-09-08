from django.conf import settings
from django.db import models

from costumers.models import Costumer
from locations.models import Sucursal


class Compra(models.Model):
    """Registro inmutable de una compra. Los puntos que otorgó ya quedan
    fijos aquí con la ReglaPuntos vigente al momento; no se recalculan
    después aunque la regla cambie."""

    costumer = models.ForeignKey(
        Costumer, on_delete=models.PROTECT, related_name="compras",
    )
    sucursal = models.ForeignKey(
        Sucursal, on_delete=models.PROTECT, related_name="compras",
    )
    cajero = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="compras_registradas",
    )
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    puntos_otorgados = models.PositiveIntegerField()
    referencia = models.CharField(max_length=100, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Compra"
        verbose_name_plural = "Compras"
        ordering = ["-fecha"]

    def __str__(self):
        return f"Compra ${self.monto} - {self.costumer} ({self.sucursal})"
