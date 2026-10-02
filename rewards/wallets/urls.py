from django.urls import path
from . import views
app_name = "wallets"
urlpatterns = [
    path("v1/devices/<str:device>/registrations/<str:pass_type>/<str:serial>", views.registration),
    path("v1/devices/<str:device>/registrations/<str:pass_type>", views.serials),
    path("v1/passes/<str:pass_type>/<str:serial>", views.latest_pass),
]
