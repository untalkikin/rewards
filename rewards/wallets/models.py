import secrets
from django.db import models

def pass_token():
    return secrets.token_urlsafe(32)

class WalletIdentity(models.Model):
    tarjeta = models.OneToOneField("lealtad.TarjetaLealtad", on_delete=models.CASCADE, related_name="wallet_identity")
    token = models.CharField(max_length=64, default=pass_token, editable=False)
    google_requested = models.BooleanField(default=False)

class AppleRegistration(models.Model):
    identity = models.ForeignKey(WalletIdentity, on_delete=models.CASCADE, related_name="devices")
    device_id = models.CharField(max_length=200)
    push_token = models.CharField(max_length=256)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["identity", "device_id"], name="apple_device_pass_unique")]

class WalletUpdate(models.Model):
    """Transactional outbox; retained IDs also serve as Apple update tags."""
    identity = models.ForeignKey(WalletIdentity, on_delete=models.CASCADE, related_name="updates")
    created = models.DateTimeField(auto_now_add=True)
    delivered = models.BooleanField(default=False)
    attempts = models.PositiveIntegerField(default=0)
    last_error = models.CharField(max_length=120, blank=True)
    class Meta:
        ordering = ["id"]
