from django.contrib import admin
from .models import Costumer


@admin.register(Costumer)
class CostumerAdmin(admin.ModelAdmin):
    list_display = ("nombre", "telefono", "email", "card_code")
    search_fields = ("nombre", "telefono", "email", "card_code")
    readonly_fields = ("card_code",)
