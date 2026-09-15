from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from bases.models import ModelClass

import secrets
import uuid


def get_code():
    """
    Identificador permanente de la tarjeta de lealtad del cliente.
    """
    return secrets.token_urlsafe(24)


class Costumer(ModelClass):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    telefono = models.CharField(
        max_length=30,
        unique=True
    )

    email = models.EmailField(
        unique=True
    )

    card_code = models.CharField(
        max_length=64,
        unique=True,
        default=get_code
    )

    pin = models.CharField(
        max_length=128,
        blank=True,
        help_text="PIN hasheado para el login del cliente (card_code + PIN). Nunca se guarda en texto plano.",
    )

    def set_pin(self, raw_pin):
        self.pin = make_password(raw_pin)

    def check_pin(self, raw_pin):
        if not self.pin:
            return False
        return check_password(raw_pin, self.pin)

    def tiene_pin(self):
        return bool(self.pin)