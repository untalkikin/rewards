from django.contrib import admin
from .models import Sucursal


@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = ("nombre", "store", "activa", "telefono")
    list_filter = ("store", "activa")
    search_fields = ("nombre", "direccion")
