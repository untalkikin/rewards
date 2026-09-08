from decimal import Decimal

from django import forms


class BuscarClienteForm(forms.Form):
    codigo = forms.CharField(
        label="Código de tarjeta / QR",
        max_length=64,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "autofocus": True,
            "placeholder": "Escanea o escribe el código",
        }),
    )


class RegistrarCompraForm(forms.Form):
    monto = forms.DecimalField(
        label="Monto de la compra",
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.01"),
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
    )
    referencia = forms.CharField(
        label="Referencia / ticket (opcional)",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
