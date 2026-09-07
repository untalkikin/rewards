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