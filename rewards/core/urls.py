from django.urls import path
from .views import DashboardView, ReportesView

app_name = "core"

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("reportes/", ReportesView.as_view(), name="reportes"),
]
