from django.db import models
import uuid
# Create your models here.
class Store(models.Model):
        """La cuenta comercial que paga la suscripción (una tienda, cadena,
    franquicia, etc.). Puede tener una o varias sucursales."""

    # UUID en vez de autoincremental: evita filtrar el volumen de negocio
    # (cuántos comercios existen) por el simple hecho de exponer un id en
    # la API, y facilita generar el id en el cliente si algún día hace
    # falta (alta offline, importaciones, etc.).
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    rfc = models.CharField(max_length=13, blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name