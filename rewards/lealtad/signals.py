from django.db.models.signals import post_save
from django.dispatch import receiver

from costumers.models import Costumer

from .models import TarjetaLealtad


@receiver(post_save, sender=Costumer)
def crear_tarjeta_lealtad(sender, instance, created, **kwargs):
    if created:
        TarjetaLealtad.objects.get_or_create(costumer=instance)
