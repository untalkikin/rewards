import uuid
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone

class Plan(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(1)])
    moneda = models.CharField(max_length=3, default="MXN", choices=[("MXN", "MXN")])
    intervalo_meses = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1)])
    activo = models.BooleanField(default=True)
    def __str__(self):
        return self.nombre

class Suscripcion(models.Model):
    class Estado(models.TextChoices):
        PREPARACION = "PREPARACION", "En preparación"
        PRUEBA = "PRUEBA", "Periodo de prueba"
        ACTIVA = "ACTIVA", "Activa"
        VENCIDA = "VENCIDA", "Vencida"
        CANCELADA = "CANCELADA", "Cancelada"
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    store = models.OneToOneField("stores.Store", on_delete=models.PROTECT, related_name="suscripcion")
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, null=True, blank=True)
    estado = models.CharField(max_length=15, choices=Estado.choices, default=Estado.PREPARACION)
    vigente_hasta = models.DateTimeField(null=True, blank=True)
    proveedor_id = models.CharField(max_length=150, blank=True)
    actualizado = models.DateTimeField(auto_now=True)
    @property
    def permite_acceso(self):
        return self.estado in (self.Estado.ACTIVA, self.Estado.PRUEBA) and self.vigente_hasta is not None and self.vigente_hasta > timezone.now()

class SolicitudSuscripcion(models.Model):
    """A local intent is never evidence of payment or active subscription."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    suscripcion = models.ForeignKey(Suscripcion, on_delete=models.PROTECT, related_name="solicitudes")
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    precio = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    moneda = models.CharField(max_length=3)
    intervalo_meses = models.PositiveSmallIntegerField()
    email_pagador = models.EmailField()
    creado_por = models.ForeignKey("auth.User", on_delete=models.PROTECT)
    creada = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=30, default="PREPARADA", editable=False)
    class Meta:
        ordering = ["-creada"]

class Pago(models.Model):
    suscripcion = models.ForeignKey(Suscripcion, on_delete=models.PROTECT, related_name="pagos")
    proveedor_id = models.CharField(max_length=150, unique=True)
    importe = models.DecimalField(max_digits=10, decimal_places=2)
    moneda = models.CharField(max_length=3, default="MXN")
    estado = models.CharField(max_length=30)
    fecha = models.DateTimeField()
    class Meta:
        ordering = ["-fecha"]
