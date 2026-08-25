from django.db import models
from bases.models import ModelClass
import secrets
import uuid
# Create your models here.


def get_code():
    """Identificador permanente de la tarjeta de lealtad del cliente (lo
    que se codifica en el QR de Apple/Google Wallet). A diferencia de
    Cupon.codigo, este NO rota: identifica al cliente, no autoriza un
    canje puntual por sí solo (eso lo decide canjes.services.confirmar_cupon
    al momento del escaneo)."""
    return secrets.token_urlsafe(24)

class Costumer(ModelClass):
    telefono = models.CharField(max_length=30, unique=True)
    email = models.EmailField(unique=True)
    card_code = models.CharField(
        max_length=64, unique=True, default=get_code
    )