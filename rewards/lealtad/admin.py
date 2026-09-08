from django.contrib import admin
from .models import Canje, MovimientoPuntos, ReglaPuntos, TarjetaLealtad


@admin.register(ReglaPuntos)
class ReglaPuntosAdmin(admin.ModelAdmin):
    list_display = (
        "nombre", "store", "monto_base", "puntos_otorgados",
        "meta_puntos", "vigente_desde", "vigente_hasta", "activa",
    )
    list_filter = ("store", "activa")


class MovimientoPuntosInline(admin.TabularInline):
    model = MovimientoPuntos
    extra = 0
    readonly_fields = ("tipo", "puntos", "fecha")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(TarjetaLealtad)
class TarjetaLealtadAdmin(admin.ModelAdmin):
    list_display = ("costumer", "codigo", "saldo", "activa", "fecha_alta")
    search_fields = ("costumer__nombre", "costumer__card_code")
    inlines = [MovimientoPuntosInline]


@admin.register(MovimientoPuntos)
class MovimientoPuntosAdmin(admin.ModelAdmin):
    list_display = ("tarjeta", "tipo", "puntos", "fecha")
    list_filter = ("tipo",)


@admin.register(Canje)
class CanjeAdmin(admin.ModelAdmin):
    list_display = ("tarjeta", "sucursal", "cajero", "puntos_consumidos", "premio", "fecha")
    list_filter = ("sucursal", "fecha")
    readonly_fields = ("tarjeta", "sucursal", "cajero", "puntos_consumidos", "premio", "fecha")

    def has_add_permission(self, request):
        return False
