from django import forms
from .models import Plan
class SolicitudForm(forms.Form):
    plan = forms.ModelChoiceField(queryset=Plan.objects.filter(activo=True), widget=forms.Select(attrs={"class": "form-select"}))
    email_pagador = forms.EmailField(label="Correo para la suscripción", widget=forms.EmailInput(attrs={"class": "form-control"}))
