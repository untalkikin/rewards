from django.contrib import admin
from .models import Compra


@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display = ("costumer", "sucursal", "cajero", "monto", "puntos_otorgados", "fecha")
    list_filter = ("sucursal", "fecha")
    search_fields = ("costumer__nombre", "referencia")
    readonly_fields = ("costumer", "sucursal", "cajero", "monto", "puntos_otorgados", "referencia", "fecha")

    def has_add_permission(self, request):
        return False
