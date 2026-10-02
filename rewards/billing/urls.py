from django.urls import path
from .views import SuscripcionView, webhook
app_name = "billing"
urlpatterns = [path("", SuscripcionView.as_view(), name="panel"), path("webhook/", webhook, name="webhook")]
