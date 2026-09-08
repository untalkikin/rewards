from django.urls import path

from .views import BuscarClienteView, CanjeConfirmView, ClienteCajeroView

app_name = "compras"

urlpatterns = [
    path("cajero/", BuscarClienteView.as_view(), name="buscar_cliente"),
    path("cajero/cliente/<str:codigo>/", ClienteCajeroView.as_view(), name="cliente_detail"),
    path("cajero/cliente/<str:codigo>/canje/", CanjeConfirmView.as_view(), name="canje_confirm"),
]
