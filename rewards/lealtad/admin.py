from django.contrib import admin
from .models import Canje, MovimientoPuntos, Promocion, RestriccionPromocion, TarjetaLealtad, Visita


class RestriccionPromocionInline(admin.StackedInline):
    model = RestriccionPromocion
    extra = 0
    max_num = 1


@admin.register(Promocion)
class PromocionAdmin(admin.ModelAdmin):
    list_display = (
        "nombre", "store", "tipo_mecanica", "puntos_otorgados",
        "meta_puntos", "vigente_desde", "vigente_hasta", "activa",
    )
    list_filter = ("store", "tipo_mecanica", "activa")
    inlines = [RestriccionPromocionInline]


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


@admin.register(Visita)
class VisitaAdmin(admin.ModelAdmin):
    list_display = ("tarjeta", "sucursal", "cajero", "puntos_otorgados", "fecha")
    list_filter = ("sucursal", "fecha")
    readonly_fields = ("tarjeta", "sucursal", "cajero", "puntos_otorgados", "fecha")

    def has_add_permission(self, request):
        return False


@admin.register(Canje)
class CanjeAdmin(admin.ModelAdmin):
    list_display = ("tarjeta", "sucursal", "cajero", "puntos_consumidos", "premio", "fecha")
    list_filter = ("sucursal", "fecha")
    readonly_fields = ("tarjeta", "sucursal", "cajero", "puntos_consumidos", "premio", "fecha")

    def has_add_permission(self, request):
        return False
