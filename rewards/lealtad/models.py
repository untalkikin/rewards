from django.conf import settings
from django.db import models
from bases.models import ModelClass
from costumers.models import Costumer
from locations.models import Sucursal
from stores.models import Store


class ReglaPuntos(ModelClass):
    """Configura cuántos puntos se otorgan por cada monto gastado y la meta
    para el premio. Versionable por fecha de vigencia para no romper el
    histórico de compras ya calculadas con una regla anterior."""

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="reglas_puntos",
    )
    monto_base = models.DecimalField(
        max_digits=10, decimal_places=2,
        help_text="Monto gastado que otorga 'puntos_otorgados' puntos, ej. 10.00",
    )
    puntos_otorgados = models.PositiveIntegerField(
        help_text="Puntos otorgados por cada 'monto_base' gastado.",
    )
    meta_puntos = models.PositiveIntegerField(
        help_text="Puntos necesarios para alcanzar el premio.",
    )
    descripcion_premio = models.CharField(max_length=255)

    vigente_desde = models.DateTimeField()
    vigente_hasta = models.DateTimeField(null=True, blank=True)
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Regla de puntos"
        verbose_name_plural = "Reglas de puntos"
        ordering = ["-vigente_desde"]

    def __str__(self):
        return f"{self.nombre} - {self.store.name}"


class TarjetaLealtad(models.Model):
    """1-1 con Costumer. El código del QR es el `card_code` que ya existe
    en Costumer (no se duplica). El saldo NUNCA se guarda aquí: se deriva
    sumando los `MovimientoPuntos` del ledger."""

    costumer = models.OneToOneField(
        Costumer,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="tarjeta",
    )
    activa = models.BooleanField(default=True)
    fecha_alta = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Tarjeta de lealtad"
        verbose_name_plural = "Tarjetas de lealtad"

    @property
    def codigo(self):
        return self.costumer.card_code

    @property
    def saldo(self):
        total = self.movimientos.aggregate(total=models.Sum("puntos"))["total"]
        return total or 0

    def __str__(self):
        return f"Tarjeta de {self.costumer} ({self.codigo})"


class Canje(models.Model):
    """Evento de canje: separado de la acumulación. Por defecto resetea el
    saldo de la tarjeta a cero (se consume TODO el saldo actual, no solo la
    meta), sin borrar el histórico -- el MovimientoPuntos negativo asociado
    deja registro permanente."""

    tarjeta = models.ForeignKey(
        TarjetaLealtad,
        on_delete=models.PROTECT,
        related_name="canjes",
    )
    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.PROTECT,
        related_name="canjes",
    )
    cajero = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="canjes_registrados",
    )
    puntos_consumidos = models.PositiveIntegerField()
    premio = models.CharField(max_length=255)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Canje"
        verbose_name_plural = "Canjes"
        ordering = ["-fecha"]

    def __str__(self):
        return f"Canje {self.puntos_consumidos} pts - {self.tarjeta.codigo}"


class TipoMovimiento(models.TextChoices):
    ACUMULACION = "ACUMULACION", "Acumulación"
    CANJE = "CANJE", "Canje"
    AJUSTE = "AJUSTE", "Ajuste"


class MovimientoPuntos(models.Model):
    """Ledger inmutable: la fuente de verdad del saldo de una tarjeta.
    Nunca se edita ni se borra; solo se agregan movimientos nuevos."""

    tarjeta = models.ForeignKey(
        TarjetaLealtad,
        on_delete=models.CASCADE,
        related_name="movimientos",
    )
    tipo = models.CharField(max_length=15, choices=TipoMovimiento.choices)
    puntos = models.IntegerField(
        help_text="Positivo en acumulación/ajuste positivo, negativo en canje.",
    )
    compra = models.ForeignKey(
        "compras.Compra",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="movimientos",
    )
    canje = models.ForeignKey(
        Canje,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="movimientos",
    )
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Movimiento de puntos"
        verbose_name_plural = "Movimientos de puntos"
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.tipo} {self.puntos:+d} - {self.tarjeta.codigo}"
