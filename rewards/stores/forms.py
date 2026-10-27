from django import forms

from .models import Store


class StoreBrandingForm(forms.ModelForm):
    """El dueño personaliza la marca de su negocio: logo, favicon, colores
    y el fondo de las pantallas de acceso de sus clientes (login/registro)."""

    class Meta:
        model = Store
        fields = ["logo", "favicon", "login_banner", "color_primario", "color_secundario"]
        widgets = {
            "logo": forms.ClearableFileInput(attrs={"class": "form-control", "accept": "image/*"}),
            "favicon": forms.ClearableFileInput(attrs={"class": "form-control", "accept": "image/*"}),
            "login_banner": forms.ClearableFileInput(attrs={"class": "form-control", "accept": "image/*"}),
            "color_primario": forms.TextInput(attrs={
                "class": "form-control form-control-color", "type": "color",
            }),
            "color_secundario": forms.TextInput(attrs={
                "class": "form-control form-control-color", "type": "color",
            }),
        }
