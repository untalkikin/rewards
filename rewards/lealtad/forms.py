from datetime import datetime, time

from django import forms
from django.db import transaction
from stores.models import Store
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

    vigente_desde = forms.DateField(
        label="Fecha de inicio",
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    vigente_hasta = forms.DateField(
        label="Fecha de fin (vacío = sin vencimiento)",
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
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

    @staticmethod
    def initial_de(promocion):
        """Arma el `initial=` para editar: las fechas y la restricción no
        son campos del modelo que ModelForm precargue solo, son extra."""
        tz = timezone.get_current_timezone()
        initial = {
            "vigente_desde": timezone.localtime(promocion.vigente_desde, tz).date(),
            "vigente_hasta": (
                timezone.localtime(promocion.vigente_hasta, tz).date()
                if promocion.vigente_hasta else None
            ),
        }
        restriccion = getattr(promocion, "restriccion", None)
        initial["limitar_escaneos"] = bool(restriccion)
        if restriccion:
            initial["max_escaneos_dia"] = restriccion.max_escaneos_dia
            initial["alcance"] = restriccion.alcance
        return initial

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("tipo_mecanica") == TipoMecanica.MONTO and not cleaned.get("monto_base"):
            self.add_error("monto_base", "Requerido para promociones por monto de compra.")
        if cleaned.get("estilo_fondo") == ESTILO_FONDO_PERSONALIZADO and not cleaned.get("color_fondo"):
            self.add_error("color_fondo", "Elige un color para la opción 'Color personalizado'.")
        for field in ("puntos_otorgados", "meta_puntos"):
            if cleaned.get(field) is not None and cleaned[field] <= 0:
                self.add_error(field, "Debe ser mayor que cero.")
        if cleaned.get("monto_base") is not None and cleaned["monto_base"] <= 0:
            self.add_error("monto_base", "Debe ser mayor que cero.")
        desde, hasta = cleaned.get("vigente_desde"), cleaned.get("vigente_hasta")
        if desde and hasta and hasta < desde:
            self.add_error("vigente_hasta", "Debe ser igual o posterior a la fecha de inicio.")
        return cleaned

    @transaction.atomic
    def save(self, *, store, commit=True):
        Store.objects.select_for_update().get(pk=store.pk)
        promocion = super().save(commit=False)
        promocion.store = store
        tz = timezone.get_current_timezone()
        promocion.vigente_desde = timezone.make_aware(
            datetime.combine(self.cleaned_data["vigente_desde"], time.min), tz,
        )
        hasta = self.cleaned_data.get("vigente_hasta")
        promocion.vigente_hasta = (
            timezone.make_aware(datetime.combine(hasta, time.max), tz) if hasta else None
        )
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
