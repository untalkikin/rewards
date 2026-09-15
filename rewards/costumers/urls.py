from django.urls import path

from .views import (
    ClienteLoginView,
    ClienteLogoutView,
    ClienteRegistradoView,
    MiCuentaView,
    RegistrarClienteView,
)

app_name = "costumers"

urlpatterns = [
    path("clientes/nuevo/", RegistrarClienteView.as_view(), name="registrar"),
    path("clientes/nuevo/<str:codigo>/exito/", ClienteRegistradoView.as_view(), name="registrado"),
    path("mi-cuenta/login/", ClienteLoginView.as_view(), name="login"),
    path("mi-cuenta/logout/", ClienteLogoutView.as_view(), name="logout"),
    path("mi-cuenta/", MiCuentaView.as_view(), name="mi_cuenta"),
]
