from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from .models import Rol


class CajeroRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Restringe la vista a usuarios con Perfil rol=CAJERO y activo."""

    def test_func(self):
        perfil = getattr(self.request.user, "perfil", None)
        return bool(perfil and perfil.rol == Rol.CAJERO and perfil.activo)


class DuenoRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Restringe la vista a usuarios con Perfil rol=DUENO y activo."""

    def test_func(self):
        perfil = getattr(self.request.user, "perfil", None)
        return bool(perfil and perfil.rol == Rol.DUENO and perfil.activo)
