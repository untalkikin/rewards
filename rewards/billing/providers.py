"""Mercado Pago subscription contract; intentionally has NO HTTP transport.

Reference: https://www.mercadopago.com.mx/developers/es/reference/online-payments/subscriptions/create-preapproval/post
Never trust a browser return URL as proof of payment. Before enabling payments,
implement signed webhooks plus authenticated provider reconciliation.
"""
class ProviderNotConnected(Exception):
    pass

class MercadoPagoProvider:
    connected = False

    def subscription_payload(self, solicitud, back_url):
        from urllib.parse import urlsplit
        if solicitud.precio is None or solicitud.precio <= 0:
            raise ValueError("Configura un precio positivo antes de conectar Mercado Pago.")
        url = urlsplit(back_url)
        if url.scheme != "https" or not url.netloc:
            raise ValueError("La URL de retorno debe usar HTTPS.")
        return {
            "reason": solicitud.plan.nombre,
            "external_reference": str(solicitud.pk),
            "payer_email": solicitud.email_pagador,
            "back_url": back_url,
            "status": "pending",
            "auto_recurring": {
                "frequency": solicitud.intervalo_meses,
                "frequency_type": "months",
                "transaction_amount": float(solicitud.precio),
                "currency_id": solicitud.moneda,
            },
        }

    def create_subscription(self, *args, **kwargs):
        raise ProviderNotConnected("Mercado Pago está preparado, pero no conectado.")
