from django import forms
from django.utils import timezone

from .models import (
    AlcanceRestriccion,
    ESTILO_FONDO_PERSONALIZADO,
    Promocion,
    RestriccionPromocion,
    TipoMecanica,
)


class PromocionForm(forms.ModelForm):
    """Alta de una promoción por parte del dueño: elige la mecánica
    (MONTO/VISITA) y, opcionalmente, un límite antiabuso de escaneos por
    día. save() arma tanto la Promocion como su RestriccionPromocion."""

    limitar_escaneos = forms.BooleanField(
        label="Limitar cuántas veces por día se le puede registrar puntos a un mismo cliente",
        required=False, initial=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    max_escaneos_dia = forms.IntegerField(
        label="Máximo de registros por día",
        min_value=1, initial=1, required=False,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    alcance = forms.ChoiceField(
        label="Ese límite se cuenta...",
        choices=AlcanceRestriccion.choices,
        initial=AlcanceRestriccion.SUCURSAL, required=False,
        widget=forms.RadioSelect,
    )

    class Meta:
        model = Promocion
        fields = [
            "nombre", "descripcion", "tipo_mecanica", "monto_base",
            "puntos_otorgados", "meta_puntos", "descripcion_premio", "activa",
            "estilo_fondo", "color_fondo", "sello_imagen",
        ]
        labels = {
            "puntos_otorgados": "Puntos por cada monto_base gastado (o puntos fijos por visita)",
            "meta_puntos": "Meta de puntos -o casillas, si es por visita- para el premio",
            "activa": "Dejar esta promoción activa de inmediato",
            "color_fondo": "Color personalizado",
            "sello_imagen": "Ícono de los sellos (opcional)",
        }
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control", "autofocus": True}),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "tipo_mecanica": forms.RadioSelect,
            "monto_base": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "puntos_otorgados": forms.NumberInput(attrs={"class": "form-control"}),
            "meta_puntos": forms.NumberInput(attrs={"class": "form-control"}),
            "descripcion_premio": forms.TextInput(attrs={"class": "form-control"}),
            "activa": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "estilo_fondo": forms.RadioSelect,
            "color_fondo": forms.TextInput(attrs={
                "class": "form-control form-control-color",
                "type": "color",
                "title": "Elige un color",
            }),
            "sello_imagen": forms.ClearableFileInput(attrs={
                "class": "form-control", "accept": "image/*",
            }),
        }

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("tipo_mecanica") == TipoMecanica.MONTO and not cleaned.get("monto_base"):
            self.add_error("monto_base", "Requerido para promociones por monto de compra.")
        if cleaned.get("estilo_fondo") == ESTILO_FONDO_PERSONALIZADO and not cleaned.get("color_fondo"):
            self.add_error("color_fondo", "Elige un color para la opción 'Color personalizado'.")
        return cleaned

    def save(self, *, store, commit=True):
        promocion = super().save(commit=False)
        promocion.store = store
        promocion.vigente_desde = timezone.now()
        if promocion.tipo_mecanica == TipoMecanica.VISITA:
            promocion.monto_base = None
        if not commit:
            return promocion

        if promocion.activa:
            Promocion.objects.filter(store=store, activa=True).update(activa=False)
        promocion.save()

        if self.cleaned_data.get("limitar_escaneos"):
            RestriccionPromocion.objects.update_or_create(
                promocion=promocion,
                defaults={
                    "max_escaneos_dia": self.cleaned_data.get("max_escaneos_dia") or 1,
                    "alcance": self.cleaned_data.get("alcance") or AlcanceRestriccion.SUCURSAL,
                },
            )
        else:
            RestriccionPromocion.objects.filter(promocion=promocion).delete()
        return promocion
