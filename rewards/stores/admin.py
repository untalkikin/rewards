from django.contrib import admin
from .models import Store


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ("name", "rfc", "email", "creado_en")
    search_fields = ("name", "rfc")
