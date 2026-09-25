from django.conf import settings
from django.db import models
from bases.models import ModelClass
from costumers.models import Costumer
from locations.models import Sucursal
from stores.models import Store


class TipoMecanica(models.TextChoices):
    MONTO = "MONTO", "Por monto de compra"
    VISITA = "VISITA", "Por visita (sello/casilla)"


class AlcanceRestriccion(models.TextChoices):
    SUCURSAL = "SUCURSAL", "Por sucursal"
    NEGOCIO = "NEGOCIO", "Por negocio (todas las sucursales)"


class Promocion(ModelClass):
    """Configura la mecánica de acumulación de puntos y la meta para el
    premio. Versionable por fecha de vigencia para no romper el histórico
    ya calculado con una promoción anterior.

    tipo_mecanica decide cómo se calculan los puntos de cada evento
    (services.mecanicas resuelve la estrategia correspondiente):
    - MONTO: unidades = monto // monto_base; puntos = unidades * puntos_otorgados.
    - VISITA: cada escaneo otorga puntos_otorgados puntos fijos (monto_base
      no aplica). meta_puntos representa entonces la cantidad de "casillas"
      de la tarjeta de sellos.
    """

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="promociones",
    )
    tipo_mecanica = models.CharField(
        max_length=10,
        choices=TipoMecanica.choices,
        default=TipoMecanica.MONTO,
    )
    monto_base = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        help_text="Solo para tipo MONTO: monto gastado que otorga 'puntos_otorgados' puntos, ej. 10.00",
    )
    puntos_otorgados = models.PositiveIntegerField(
        help_text="Puntos por cada 'monto_base' gastado (MONTO), o puntos fijos por escaneo (VISITA).",
    )
    meta_puntos = models.PositiveIntegerField(
        help_text="Puntos (o casillas, si es VISITA) necesarios para alcanzar el premio.",
    )
    descripcion_premio = models.CharField(max_length=255)

    vigente_desde = models.DateTimeField()
    vigente_hasta = models.DateTimeField(null=True, blank=True)
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Promoción"
        verbose_name_plural = "Promociones"
        ordering = ["-vigente_desde"]

    def __str__(self):
        return f"{self.nombre} - {self.store.name}"


class RestriccionPromocion(models.Model):
    """Límite antiabuso de una promoción: cuántos escaneos por día se
    aceptan para una misma tarjeta, y si ese límite se cuenta por
    sucursal (cada una lleva su propio conteo) o por negocio (comparten
    el conteo todas las sucursales del Store)."""

    promocion = models.OneToOneField(
        Promocion,
        on_delete=models.CASCADE,
        related_name="restriccion",
    )
    max_escaneos_dia = models.PositiveSmallIntegerField(default=1)
    alcance = models.CharField(
        max_length=10,
        choices=AlcanceRestriccion.choices,
        default=AlcanceRestriccion.SUCURSAL,
    )

    class Meta:
        verbose_name = "Restricción de promoción"
        verbose_name_plural = "Restricciones de promoción"

    def __str__(self):
        return f"Máx. {self.max_escaneos_dia}/día ({self.get_alcance_display()}) - {self.promocion.nombre}"


ESTILOS_FONDO = {
    "atardecer": {"label": "Atardecer", "css": "linear-gradient(135deg, #ff9966, #ff5e62)", "solido": "#ff5e62"},
    "oceano": {"label": "Océano", "css": "linear-gradient(135deg, #2193b0, #6dd5ed)", "solido": "#2193b0"},
    "bosque": {"label": "Bosque", "css": "linear-gradient(135deg, #11998e, #38ef7d)", "solido": "#11998e"},
    "noche": {"label": "Noche", "css": "linear-gradient(135deg, #232526, #414345)", "solido": "#232526"},
    "dorado": {"label": "Dorado", "css": "linear-gradient(135deg, #f7971e, #ffd200)", "solido": "#f7971e"},
}

ESTILO_FONDO_PERSONALIZADO = "personalizado"

ESTILO_FONDO_CHOICES = (
    [("", "Color de marca del negocio")]
    + [(clave, valor["label"]) for clave, valor in ESTILOS_FONDO.items()]
    + [(ESTILO_FONDO_PERSONALIZADO, "Color personalizado")]
)


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

    estilo_fondo = models.CharField(
        max_length=20, blank=True, choices=ESTILO_FONDO_CHOICES,
        help_text="Fondo prediseñado de la tarjeta. 'Color personalizado' usa color_fondo.",
    )
    color_fondo = models.CharField(
        max_length=7, blank=True,
        help_text="Color hex para la opción 'Color personalizado', ej. #405189.",
    )
    sello_imagen = models.ImageField(
        upload_to="tarjetas/sellos/", blank=True, null=True,
        help_text="Ícono propio para cada sello/visita de la tarjeta (opcional). Sin uno, se usa una estrella por default.",
    )

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

    @property
    def fondo_css(self):
        """Valor para el CSS `background` de la tarjeta -- puede ser un
        degradado. Vacío = usar el color de marca del negocio."""
        if self.estilo_fondo == ESTILO_FONDO_PERSONALIZADO:
            return self.color_fondo
        estilo = ESTILOS_FONDO.get(self.estilo_fondo)
        return estilo["css"] if estilo else ""

    @property
    def fondo_solido(self):
        """Equivalente en un solo color plano, para superficies que no
        soportan degradados (ej. el `backgroundColor` de un pase de Apple
        Wallet). Vacío = usar el color de marca del negocio."""
        if self.estilo_fondo == ESTILO_FONDO_PERSONALIZADO:
            return self.color_fondo
        estilo = ESTILOS_FONDO.get(self.estilo_fondo)
        return estilo["solido"] if estilo else ""

    def __str__(self):
        return f"Tarjeta de {self.costumer} ({self.codigo})"


class Visita(models.Model):
    """Evento de acumulación por escaneo (mecánica VISITA): igual que
    Compra, pero sin monto -- el escaneo por sí solo otorga los puntos
    fijos de la promoción vigente."""

    tarjeta = models.ForeignKey(
        TarjetaLealtad,
        on_delete=models.PROTECT,
        related_name="visitas",
    )
    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.PROTECT,
        related_name="visitas",
    )
    cajero = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="visitas_registradas",
    )
    puntos_otorgados = models.PositiveIntegerField()
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Visita"
        verbose_name_plural = "Visitas"
        ordering = ["-fecha"]

    def __str__(self):
        return f"Visita {self.fecha:%Y-%m-%d} - {self.tarjeta.codigo}"


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
    visita = models.ForeignKey(
        Visita,
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
