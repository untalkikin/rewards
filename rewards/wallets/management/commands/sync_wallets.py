from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import F
from wallets.models import WalletUpdate
from wallets.services.sync import deliver

class Command(BaseCommand):
    help = "Consulta la cola de Wallet. Requiere --send y WALLET_SYNC_ENABLED=1 para enviar."
    def add_arguments(self, parser):
        parser.add_argument("--send", action="store_true")
        parser.add_argument("--limit", type=int, default=100)
    def handle(self, *args, **options):
        if options["limit"] < 1:
            raise CommandError("--limit debe ser positivo.")
        pending = WalletUpdate.objects.filter(delivered=False)
        if not options["send"]:
            self.stdout.write(f"Actualizaciones pendientes: {pending.count()}. Sin conexiones externas.")
            return
        if not settings.WALLET_SYNC_ENABLED:
            raise CommandError("WALLET_SYNC_ENABLED está deshabilitado.")
        failures = 0
        for update in pending.select_related("identity__tarjeta__costumer__store")[:options["limit"]]:
            try:
                deliver(update)
            except Exception as exc:
                failures += 1
                # Do not persist response bodies, tokens or credentials.
                pending.filter(pk=update.pk).update(attempts=F("attempts") + 1, last_error=type(exc).__name__)
            else:
                pending.filter(pk=update.pk).update(delivered=True, attempts=F("attempts") + 1, last_error="")
        if failures:
            raise CommandError(f"{failures} actualizaciones fallaron; se conservan para reintento.")
        self.stdout.write("Cola procesada.")
