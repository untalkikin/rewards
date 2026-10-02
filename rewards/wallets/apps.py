from django.apps import AppConfig
class WalletsConfig(AppConfig):
    name = "wallets"
    default_auto_field = "django.db.models.BigAutoField"
    def ready(self):
        from . import signals
