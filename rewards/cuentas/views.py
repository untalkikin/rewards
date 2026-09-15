from django.contrib import messages
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy

from .forms import CambiarPasswordForm


class CambiarPasswordView(PasswordChangeView):
    """Cambio de contraseña del usuario de staff (cajero/dueño) logueado.
    PasswordChangeView ya exige login y llama a update_session_auth_hash,
    así que la sesión actual no se cierra al cambiar la contraseña."""

    form_class = CambiarPasswordForm
    template_name = "cuentas/cambiar_password.html"
    success_url = reverse_lazy("core:dashboard")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Tu contraseña se actualizó correctamente.")
        return response
