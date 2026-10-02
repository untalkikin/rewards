from django.db.models.signals import post_save
from django.dispatch import receiver
from lealtad.models import MovimientoPuntos, TarjetaLealtad, Promocion
from .models import WalletIdentity, WalletUpdate

def enqueue_card(tarjeta_id):
    identity = WalletIdentity.objects.filter(tarjeta_id=tarjeta_id).first()
    if identity:
        WalletUpdate.objects.create(identity=identity)

def enqueue_store(store):
    WalletUpdate.objects.bulk_create([WalletUpdate(identity=i) for i in WalletIdentity.objects.filter(tarjeta__costumer__store=store)])

@receiver(post_save, sender=MovimientoPuntos)
def points_changed(sender, instance, created, **kwargs):
    if created:
        enqueue_card(instance.tarjeta_id)

@receiver(post_save, sender=TarjetaLealtad)
def card_changed(sender, instance, created, **kwargs):
    if not created:
        enqueue_card(instance.pk)

@receiver(post_save, sender=Promocion)
def promotion_changed(sender, instance, **kwargs):
    enqueue_store(instance.store)
