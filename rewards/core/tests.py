from datetime import timedelta
from decimal import Decimal
from io import StringIO
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.core.management import call_command, CommandError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from stores.models import Store
from locations.models import Sucursal
from cuentas.models import Perfil, Rol
from costumers.models import Costumer
from costumers.forms import RegistrarClienteForm
from lealtad.models import Promocion, TipoMecanica, MovimientoPuntos, Canje, RestriccionPromocion
from lealtad.services.acumulacion_service import registrar_evento
from lealtad.services.canje_service import efectuar_canje
from lealtad.services.promociones_service import promocion_vigente
from lealtad.services.exceptions import SinPromocionVigente, RestriccionNoCumplida, SaldoInsuficiente
from billing.models import Plan, Suscripcion, SolicitudSuscripcion, Pago
from billing.providers import MercadoPagoProvider, ProviderNotConnected
from wallets.models import WalletIdentity, WalletUpdate, AppleRegistration

class RewardsFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.store = Store.objects.create(name="Negocio A")
        cls.other = Store.objects.create(name="Negocio B")
        cls.branch = Sucursal.objects.create(store=cls.store, nombre="Sucursal A")
        cls.other_branch = Sucursal.objects.create(store=cls.other, nombre="Sucursal B")
        cls.owner = get_user_model().objects.create_user("dueno", email="owner@example.test", password="owner-pass")
        Perfil.objects.create(user=cls.owner, rol=Rol.DUENO, store=cls.store)
        cls.cashier = get_user_model().objects.create_user("cajero", password="cashier-pass")
        Perfil.objects.create(user=cls.cashier, rol=Rol.CAJERO, store=cls.store, sucursal=cls.branch)
        cls.customer = Costumer.objects.create(store=cls.store, nombre="Cliente A", telefono="111", email="a@example.test")
        cls.customer.set_pin("1234"); cls.customer.save()
        cls.other_customer = Costumer.objects.create(store=cls.other, nombre="Cliente B", telefono="111", email="a@example.test")
        cls.other_customer.set_pin("5678"); cls.other_customer.save()
        cls.promo = Promocion.objects.create(store=cls.store, nombre="Visitas", tipo_mecanica=TipoMecanica.VISITA,
            puntos_otorgados=2, meta_puntos=3, descripcion_premio="Café", vigente_desde=timezone.now()-timedelta(days=1))

    def customer_login(self):
        return self.client.post(reverse("costumers:login"), {"store": self.store.pk, "telefono": "111", "pin": "1234"})

    def earn(self):
        return registrar_evento(costumer=self.customer, sucursal=self.branch, cajero=self.cashier)

    def test_purchase_visits_and_redemption_ledger(self):
        self.earn(); self.earn()
        self.assertEqual(self.customer.tarjeta.saldo, 4)
        canje = efectuar_canje(tarjeta=self.customer.tarjeta, sucursal=self.branch, cajero=self.cashier)
        self.assertEqual(canje.puntos_consumidos, 4)
        self.assertEqual(self.customer.tarjeta.saldo, 0)
        self.assertEqual(self.customer.tarjeta.movimientos.count(), 3)
        with self.assertRaises(SaldoInsuficiente):
            efectuar_canje(tarjeta=self.customer.tarjeta, sucursal=self.branch, cajero=self.cashier)
        self.promo.tipo_mecanica = TipoMecanica.MONTO; self.promo.monto_base = Decimal("100")
        self.promo.save()
        event = registrar_evento(costumer=self.customer, sucursal=self.branch, cajero=self.cashier, monto=Decimal("250"))
        self.assertEqual(event.puntos_otorgados, 4)

    def test_expired_and_future_promotions_cannot_earn_or_redeem(self):
        self.earn(); self.earn()
        self.promo.vigente_hasta = timezone.now()-timedelta(seconds=1); self.promo.save()
        self.assertIsNone(promocion_vigente(self.store))
        with self.assertRaises(SinPromocionVigente): self.earn()
        with self.assertRaises(SinPromocionVigente):
            efectuar_canje(tarjeta=self.customer.tarjeta, sucursal=self.branch, cajero=self.cashier)
        self.promo.vigente_hasta = None; self.promo.vigente_desde = timezone.now()+timedelta(days=1); self.promo.save()
        self.assertIsNone(promocion_vigente(self.store))
        with self.assertRaises(SinPromocionVigente): self.earn()
        self.assertEqual(Canje.objects.count(), 0)

    def test_daily_limit_rolls_back(self):
        RestriccionPromocion.objects.create(promocion=self.promo, max_escaneos_dia=1)
        self.earn()
        with self.assertRaises(RestriccionNoCumplida): self.earn()
        self.assertEqual(self.customer.tarjeta.saldo, 2)

    def test_service_rejects_cross_tenant_and_inactive_cards(self):
        with self.assertRaises(PermissionDenied):
            registrar_evento(costumer=self.other_customer, sucursal=self.branch, cajero=self.cashier)
        self.customer.tarjeta.activa=False; self.customer.tarjeta.save()
        with self.assertRaises(PermissionDenied): self.earn()
        self.assertEqual(MovimientoPuntos.objects.count(), 0)

    def test_anonymous_card_qr_wallet_require_login(self):
        for route in ("tarjeta_detail", "tarjeta_qr", "tarjeta_apple", "tarjeta_google"):
            response = self.client.get(reverse("lealtad:"+route, args=[self.customer.card_code]))
            self.assertEqual(response.status_code, 302)
            self.assertIn("/mi-cuenta/login/", response.url)

    def test_customer_only_own_card(self):
        self.assertEqual(self.customer_login().status_code, 302)
        self.assertEqual(self.client.get(reverse("lealtad:tarjeta_detail", args=[self.customer.card_code])).status_code, 200)
        self.assertEqual(self.client.get(reverse("lealtad:tarjeta_qr", args=[self.customer.card_code])).status_code, 200)
        self.assertEqual(self.client.get(reverse("lealtad:tarjeta_detail", args=[self.other_customer.card_code])).status_code, 404)
        self.assertEqual(self.client.get(reverse("costumers:mi_cuenta")).status_code, 200)

    def test_login_business_scope_and_safe_return(self):
        response = self.client.post(reverse("costumers:login")+"?next=https://evil.invalid", {"store": self.other.pk, "telefono":"111", "pin":"1234"})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("costumer_id", self.client.session)
        response = self.client.post(reverse("costumers:login")+"?next=https://evil.invalid", {"store":self.store.pk, "telefono":"111", "pin":"1234"})
        self.assertEqual(response.url, reverse("costumers:mi_cuenta"))

    def test_registration_customer_and_staff_scope(self):
        data = {"store": self.other.pk, "nombre":"Nueva", "telefono":"222", "email":"new@example.test", "pin":"1234", "pin_confirmacion":"1234"}
        form = RegistrarClienteForm(data, store=self.store)
        self.assertTrue(form.is_valid(), form.errors)
        customer = form.save()
        self.assertEqual(customer.store, self.store)
        self.assertTrue(customer.check_pin("1234"))
        self.assertEqual(customer.tarjeta.saldo, 0)
        self.assertFalse(RegistrarClienteForm({**data, "store":self.store.pk}).is_valid())

    def test_cashier_and_owner_cannot_access_other_business(self):
        self.client.force_login(self.cashier)
        self.assertEqual(self.client.get(reverse("compras:cliente_detail", args=[self.other_customer.card_code])).status_code,404)
        self.assertEqual(self.client.get(reverse("billing:panel")).status_code,403)
        other_promo = Promocion.objects.create(store=self.other, nombre="Ajena", puntos_otorgados=1, meta_puntos=1, descripcion_premio="X", vigente_desde=timezone.now())
        self.client.force_login(self.owner)
        self.assertEqual(self.client.post(reverse("lealtad:promocion_activar", args=[other_promo.pk])).status_code,404)
        self.assertEqual(self.client.get('/admin/').status_code,302)

    def test_reports_include_visits_and_filter_by_date_and_business(self):
        self.earn()
        self.client.force_login(self.owner)
        response = self.client.get(reverse("core:reportes"))
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.context['totales']['puntos_otorgados'],2)
        self.assertEqual(len(response.context['filas']),1)
        self.assertEqual(response.context['filas'][0]['num_visitas'],1)
        response = self.client.get(reverse("core:reportes"), {"desde":(timezone.localdate()+timedelta(days=1)).isoformat()})
        self.assertEqual(response.context['totales']['puntos_otorgados'],0)
        response = self.client.get(reverse("core:reportes"), {"desde":"bad"})
        self.assertTrue(response.context['periodo'].errors)
        response = self.client.get(reverse("core:dashboard"))
        self.assertEqual(response.context['totales']['total_clientes'],1)

    def test_billing_saves_intent_once_without_activating_or_network(self):
        self.client.force_login(self.owner)
        plan = Plan.objects.create(nombre="Prueba", precio=Decimal("199.00"))
        with patch('socket.socket.connect', side_effect=AssertionError("Unexpected network")):
            self.assertEqual(self.client.get(reverse("billing:panel")).status_code,200)
            for _ in range(2):
                self.assertEqual(self.client.post(reverse("billing:panel"), {"plan":plan.pk,"email_pagador":"owner@example.test"}).status_code,302)
            self.assertEqual(self.client.get(reverse("billing:panel")).status_code,200)
        self.assertEqual(SolicitudSuscripcion.objects.count(),1)
        self.assertEqual(Pago.objects.count(),0)
        subscription = Suscripcion.objects.get(store=self.store)
        self.assertEqual(subscription.estado, "PREPARACION")
        self.assertFalse(subscription.permite_acceso)
        self.assertIsNone(subscription.plan_id)
        provider = MercadoPagoProvider()
        intent=subscription.solicitudes.get()
        self.assertEqual(provider.subscription_payload(intent,"https://example.test/suscripcion/")["auto_recurring"]["transaction_amount"],199.0)
        with self.assertRaises(ProviderNotConnected): provider.create_subscription(intent)
        self.assertEqual(self.client.post(reverse("billing:webhook"), data='{"status":"approved"}', content_type="application/json").status_code,503)
        self.assertEqual(Pago.objects.count(),0)

    def test_billing_never_overwrites_active_subscription(self):
        plan = Plan.objects.create(nombre="Actual", precio=100)
        subscription = Suscripcion.objects.create(store=self.store,plan=plan,estado="ACTIVA",vigente_hasta=timezone.now()+timedelta(days=30))
        new_plan = Plan.objects.create(nombre="Cambio", precio=200)
        self.client.force_login(self.owner)
        self.client.post(reverse("billing:panel"), {"plan":new_plan.pk,"email_pagador":"owner@example.test"})
        subscription.refresh_from_db()
        self.assertEqual(subscription.plan_id,plan.pk)
        self.assertTrue(subscription.permite_acceso)

    @override_settings(BILLING_ENFORCE_SUBSCRIPTION=True)
    def test_subscription_access_gate_optional(self):
        self.client.force_login(self.owner)
        response=self.client.get(reverse("core:dashboard"))
        self.assertEqual(response.url,reverse("billing:panel"))
        self.assertEqual(self.client.get(reverse("billing:panel")).status_code,200)
        self.client.force_login(self.cashier)
        self.assertEqual(self.client.get(reverse("compras:buscar_cliente")).status_code,403)

    def test_wallet_update_outbox_and_offline_command(self):
        identity=WalletIdentity.objects.create(tarjeta=self.customer.tarjeta)
        self.earn()
        self.assertEqual(identity.updates.count(),1)
        with patch('socket.socket.connect', side_effect=AssertionError("Unexpected network")):
            call_command("sync_wallets", stdout=StringIO())
            with self.assertRaises(CommandError): call_command("sync_wallets",send=True,stdout=StringIO())
        self.assertFalse(identity.updates.get().delivered)

    @override_settings(WALLET_SYNC_ENABLED=True)
    def test_wallet_retry_then_success(self):
        identity=WalletIdentity.objects.create(tarjeta=self.customer.tarjeta)
        self.earn()
        with patch('wallets.management.commands.sync_wallets.deliver',side_effect=RuntimeError("secret not saved")):
            with self.assertRaises(CommandError): call_command("sync_wallets",send=True,stdout=StringIO())
        update=identity.updates.get()
        self.assertEqual(update.last_error,"RuntimeError")
        with patch('wallets.management.commands.sync_wallets.deliver'):
            call_command("sync_wallets",send=True,stdout=StringIO())
        update.refresh_from_db()
        self.assertTrue(update.delivered)
        self.assertEqual(update.attempts,2)

    @override_settings(APPLE_WALLET_PASS_TYPE_ID="pass.test")
    def test_apple_device_auth_and_update_tags(self):
        identity=WalletIdentity.objects.create(tarjeta=self.customer.tarjeta)
        path=f"/wallets/apple/v1/devices/device-a/registrations/pass.test/{self.customer.card_code}"
        self.assertEqual(self.client.post(path,data='{"pushToken":"push"}',content_type="application/json").status_code,401)
        headers={"HTTP_AUTHORIZATION":"ApplePass "+identity.token}
        self.assertEqual(self.client.post(path,data='{"pushToken":"push"}',content_type="application/json",**headers).status_code,201)
        response=self.client.get('/wallets/apple/v1/devices/device-a/registrations/pass.test')
        self.assertEqual(response.json()['serialNumbers'],[self.customer.card_code])
        tag=response.json()['lastUpdated']
        self.assertEqual(self.client.get('/wallets/apple/v1/devices/device-a/registrations/pass.test',{'passesUpdatedSince':tag}).status_code,204)
        self.earn()
        self.assertEqual(self.client.get('/wallets/apple/v1/devices/device-a/registrations/pass.test',{'passesUpdatedSince':tag}).status_code,200)
        self.assertEqual(self.client.get('/wallets/apple/v1/devices/other-device/registrations/pass.test').status_code,204)
        self.assertEqual(self.client.delete(path,**headers).status_code,200)
        self.assertEqual(AppleRegistration.objects.count(),0)

    def test_billing_data_is_private_between_businesses(self):
        plan = Plan.objects.create(nombre="Privado", precio=100)
        other_subscription = Suscripcion.objects.create(store=self.other, plan=plan)
        Pago.objects.create(suscripcion=other_subscription, proveedor_id="private-payment", importe=100, moneda="MXN", estado="approved", fecha=timezone.now())
        self.client.force_login(self.owner)
        response = self.client.get(reverse("billing:panel"))
        self.assertEqual(list(response.context["pagos"]), [])
        self.assertEqual(list(response.context["solicitudes"]), [])

    def test_post_requires_csrf_and_does_not_trust_request_store(self):
        from django.test import Client
        strict = Client(enforce_csrf_checks=True)
        strict.force_login(self.owner)
        plan = Plan.objects.create(nombre="CSRF", precio=100)
        response = strict.post(reverse("billing:panel"), {"plan":plan.pk,"email_pagador":"owner@example.test"})
        self.assertEqual(response.status_code,403)
        self.client.force_login(self.owner)
        self.client.post(reverse("billing:panel"), {"plan":plan.pk,"email_pagador":"owner@example.test", "store":self.other.pk})
        self.assertTrue(Suscripcion.objects.filter(store=self.store).exists())
        self.assertFalse(Suscripcion.objects.filter(store=self.other).exists())

    def test_wallet_queue_rolls_back_with_points(self):
        from django.db import transaction
        identity = WalletIdentity.objects.create(tarjeta=self.customer.tarjeta)
        try:
            with transaction.atomic():
                self.earn()
                raise ValueError("rollback")
        except ValueError:
            pass
        self.assertEqual(identity.updates.count(),0)
        self.assertEqual(self.customer.tarjeta.saldo,0)

    @override_settings(GOOGLE_WALLET_ISSUER_ID="issuer", GOOGLE_WALLET_CLASS_SUFFIX="rewards")
    def test_google_pass_uses_customer_business_and_no_network(self):
        from wallets.services.google_service import GoogleWalletProvider
        from django.test import RequestFactory
        request = RequestFactory().get("/", HTTP_HOST="localhost")
        with patch("wallets.services.google_service._credenciales", return_value=("issuer@example.test","fake-key")), patch("wallets.services.google_service.jwt.encode", return_value="signed") as encode, patch("socket.socket.connect", side_effect=AssertionError("Unexpected network")):
            result = GoogleWalletProvider().generar_pase(self.other_customer.tarjeta, request)
        payload = encode.call_args.args[0]
        self.assertEqual(payload["payload"]["loyaltyClasses"][0]["issuerName"],self.other.name)
        self.assertTrue(result.url.endswith("signed"))
        self.assertTrue(WalletIdentity.objects.get(tarjeta=self.other_customer.tarjeta).google_requested)
