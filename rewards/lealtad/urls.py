from django.urls import path

from .views import (
    PromocionActivarView,
    PromocionCreateView,
    PromocionListView,
    TarjetaDetailView,
    tarjeta_apple_wallet_view,
    tarjeta_google_wallet_view,
    tarjeta_qr_view,
)

app_name = "lealtad"

urlpatterns = [
    path("tarjeta/<str:codigo>/", TarjetaDetailView.as_view(), name="tarjeta_detail"),
    path("tarjeta/<str:codigo>/qr.png", tarjeta_qr_view, name="tarjeta_qr"),
    path("tarjeta/<str:codigo>/apple.pkpass", tarjeta_apple_wallet_view, name="tarjeta_apple"),
    path("tarjeta/<str:codigo>/google", tarjeta_google_wallet_view, name="tarjeta_google"),
    path("promociones/", PromocionListView.as_view(), name="promocion_list"),
    path("promociones/nueva/", PromocionCreateView.as_view(), name="promocion_create"),
    path("promociones/<int:pk>/activar/", PromocionActivarView.as_view(), name="promocion_activar"),
]
