from django.contrib import messages
from django.shortcuts import redirect, render
from django.views import View

from cuentas.mixins import DuenoRequiredMixin

from .access import staff_store
from .forms import StoreBrandingForm


class ConfiguracionNegocioView(DuenoRequiredMixin, View):
    """El dueño edita el logo, favicon, colores y el fondo de las
    pantallas de acceso de sus clientes (login/registro)."""

    template_name = "stores/configuracion.html"

    def get(self, request):
        form = StoreBrandingForm(instance=staff_store(request))
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        store = staff_store(request)
        form = StoreBrandingForm(request.POST, request.FILES, instance=store)
        if form.is_valid():
            form.save()
            messages.success(request, "La configuración del negocio se actualizó correctamente.")
            return redirect("stores:configuracion")
        return render(request, self.template_name, {"form": form})
