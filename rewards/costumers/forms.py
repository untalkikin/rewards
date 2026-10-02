from django import forms

from .models import Costumer
from stores.models import Store

_PIN_WIDGET_ATTRS = {
    "class": "form-control",
    "inputmode": "numeric",
    "pattern": "[0-9]*",
    "autocomplete": "off",
}


class RegistrarClienteForm(forms.ModelForm):
    """Alta de un cliente por parte de un cajero o dueño. Además de los
    datos del cliente, define el PIN con el que después podrá entrar a
    su panel (mi-cuenta) junto con su teléfono y negocio."""

    store = forms.ModelChoiceField(queryset=Store.objects.all(), label="Negocio", widget=forms.Select(attrs={"class": "form-select"}))

    pin = forms.CharField(
        label="PIN (4 a 6 dígitos)",
        min_length=4,
        max_length=6,
        widget=forms.PasswordInput(attrs=_PIN_WIDGET_ATTRS),
    )
    pin_confirmacion = forms.CharField(
        label="Confirmar PIN",
        min_length=4,
        max_length=6,
        widget=forms.PasswordInput(attrs=_PIN_WIDGET_ATTRS),
    )

    class Meta:
        model = Costumer
        fields = ["store", "nombre", "telefono", "email"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control", "autofocus": True}),
            "telefono": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }
        error_messages = {
            "telefono": {"unique": "Ya existe una tarjeta registrada con este teléfono."},
            "email": {"unique": "Ya existe una tarjeta registrada con este correo."},
        }

    def __init__(self, *args, store=None, **kwargs):
        super().__init__(*args, **kwargs)
        if store is not None:
            self.fields["store"].queryset = Store.objects.filter(pk=store.pk)
            self.fields["store"].initial = store
            self.fields["store"].disabled = True

    def clean_pin(self):
        pin = self.cleaned_data["pin"]
        if not pin.isdigit():
            raise forms.ValidationError("El PIN debe contener solo números.")
        return pin

    def clean(self):
        cleaned = super().clean()
        pin = cleaned.get("pin")
        confirmacion = cleaned.get("pin_confirmacion")
        if pin and confirmacion and pin != confirmacion:
            self.add_error("pin_confirmacion", "Los PIN no coinciden.")
        return cleaned

    def save(self, commit=True, descripcion="Cliente registrado desde el panel de staff."):
        costumer = super().save(commit=False)
        costumer.descripcion = descripcion
        costumer.set_pin(self.cleaned_data["pin"])
        if commit:
            costumer.save()
        return costumer


class ClienteLoginForm(forms.Form):
    telefono = forms.CharField(
        label="Teléfono",
        max_length=30,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "autofocus": True,
            "inputmode": "tel",
            "placeholder": "Tu número de teléfono",
        }),
    )
    store = forms.ModelChoiceField(queryset=Store.objects.all(), label="Negocio", widget=forms.Select(attrs={"class": "form-select"}))

    pin = forms.CharField(
        label="PIN",
        max_length=6,
        widget=forms.PasswordInput(attrs=_PIN_WIDGET_ATTRS),
    )
