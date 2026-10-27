from django.urls import path

from .views import ConfiguracionNegocioView

app_name = "stores"

urlpatterns = [
    path("negocio/configuracion/", ConfiguracionNegocioView.as_view(), name="configuracion"),
]
