from django.contrib import admin
from .models import Plan, Suscripcion, SolicitudSuscripcion, Pago
@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("nombre", "precio", "moneda", "intervalo_meses", "activo")
@admin.register(Suscripcion)
class SuscripcionAdmin(admin.ModelAdmin):
    list_display = ("store", "plan", "estado", "vigente_hasta")
    readonly_fields = ("proveedor_id",)
@admin.register(SolicitudSuscripcion, Pago)
class ReadOnlyBillingAdmin(admin.ModelAdmin):
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
