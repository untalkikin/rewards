from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from cuentas.mixins import DuenoRequiredMixin
from stores.access import staff_store
from stores.models import Store
from .forms import SolicitudForm
from .models import Plan, Suscripcion, SolicitudSuscripcion

class SuscripcionView(DuenoRequiredMixin, View):
    def context(self, request, form=None):
        subscription = Suscripcion.objects.filter(store=staff_store(request)).first()
        return {"suscripcion": subscription, "planes": Plan.objects.filter(activo=True),
                "form": form if form is not None else SolicitudForm(initial={"email_pagador": request.user.email}),
                "solicitudes": subscription.solicitudes.select_related("plan")[:10] if subscription else [],
                "pagos": subscription.pagos.all()[:20] if subscription else []}

    def get(self, request):
        return render(request, "billing/suscripcion.html", self.context(request))

    @transaction.atomic
    def post(self, request):
        store = staff_store(request)
        Store.objects.select_for_update().get(pk=store.pk)
        form = SolicitudForm(request.POST)
        if form.is_valid():
            subscription, _ = Suscripcion.objects.get_or_create(store=store)
            plan = form.cleaned_data["plan"]
            # Avoid duplicate local intents on refresh/repeated submission.
            previous = subscription.solicitudes.first()
            email = form.cleaned_data["email_pagador"]
            if not (previous and previous.plan_id == plan.pk and previous.email_pagador == email
                    and previous.precio == plan.precio and previous.moneda == plan.moneda
                    and previous.intervalo_meses == plan.intervalo_meses):
                SolicitudSuscripcion.objects.create(suscripcion=subscription, plan=plan,
                    precio=plan.precio, moneda=plan.moneda, intervalo_meses=plan.intervalo_meses,
                    email_pagador=email, creado_por=request.user)
            messages.success(request, "Solicitud guardada. No se realizó ningún cobro; tu suscripción no ha cambiado.")
            return redirect("billing:panel")
        return render(request, "billing/suscripcion.html", self.context(request, form))

@csrf_exempt
@require_POST
def webhook(request):
    # Fail closed even if someone sets credentials or submits a fake paid event.
    response = JsonResponse({"detail": "Integración no conectada."}, status=503)
    response["Cache-Control"] = "no-store"
    return response
