from django.urls import path

from .views import CambiarPasswordView

app_name = "cuentas"

urlpatterns = [
    path("cuenta/cambiar-password/", CambiarPasswordView.as_view(), name="cambiar_password"),
]
