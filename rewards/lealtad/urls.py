from django.urls import path

from .views import (
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
]
