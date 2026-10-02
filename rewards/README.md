# Rewards — lealtad y suscripciones SaaS

Aplicación Django 5.2 para varios negocios, cada uno con clientes, personal,
sucursales, promociones, tarjetas privadas y reportes separados.

## Arranque local

Desde la raíz del repositorio, en PowerShell:

```powershell
.\env\Scripts\Activate.ps1
cd rewards
$env:DJANGO_DEBUG = "1"
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

Para instalar en una máquina nueva, crea un entorno Python 3.12 y ejecuta
`python -m pip install -r requirements.txt` dentro de esta carpeta.
`.env.example` documenta las variables: no se carga automáticamente.
Se incluye `start-local.ps1` en la raíz para iniciar el entorno local existente.

## Roles y datos existentes

- El administrador de la plataforma (superusuario) usa `/admin/` para dar de
  alta negocios, sucursales, usuarios, perfiles y planes. El admin global queda
  reservado a superusuarios para evitar accesos entre negocios.
- Cada perfil requiere un `store`; un cajero requiere además una sucursal del
  mismo negocio. Los dueños entran por `/login/` y usan su panel.
- El cliente selecciona negocio y accede con teléfono/PIN en `/mi-cuenta/login/`.
  El mismo teléfono o correo puede existir en distintos negocios.
- El código QR identifica una tarjeta; no concede acceso a su saldo/historial.
  Tarjeta, QR y descargas de Wallet requieren sesión autorizada.
- La migración conserva registros y asigna datos antiguos automáticamente solo
  cuando existe un único negocio. Si hay varios y la titularidad es ambigua,
  se detiene con un error para que el operador asigne los `store_id` correctos.

## Lealtad y reportes

La promoción debe estar activa y dentro de `[vigente_desde, vigente_hasta)`.
Las compras acumulan por múltiplos de monto_base; las visitas otorgan puntos
fijos. Los límites diarios y reportes usan DJANGO_TIME_ZONE (por defecto
America/Mexico_City). Los reportes suman compras y visitas y validan fechas.
Los canjes conservan la regla original: consumen todo el saldo, no solo la meta.
Las operaciones usan transacciones y el saldo deriva de movimientos históricos.

## Suscripción y Mercado Pago: preparación sin conexión

El dueño dispone de **Suscripción y pagos** en `/suscripcion/`:

- Consulta estado, plan actual, vigencia, solicitudes e historial de pagos.
- Guarda una solicitud local con precio y periodicidad congelados.
- No se solicitan tarjetas, no se envía información a Mercado Pago y no se cobra.
- Una solicitud no activa, cambia ni cancela una suscripción vigente.
- Se incluye el plan inicial "Rewards SaaS", sin precio: el operador define su
  tarifa en el admin. No se inventan precios comerciales.

`billing.providers.MercadoPagoProvider.subscription_payload()` prepara el contrato
de creación de una suscripción mensual mediante `/preapproval`.
`create_subscription()` falla explícitamente: no tiene transporte HTTP.
Incluso con credenciales definidas, los cobros permanecen desconectados.
`POST /suscripcion/webhook/` responde 503 y no acepta pagos ni activa cuentas.

Para una integración real futura faltan la conexión autorizada al proveedor,
validación de firmas de webhooks, consulta autenticada del recurso, conciliación
idempotente de pagos, cancelaciones y pruebas en sandbox. Nunca activar una
suscripción a partir de parámetros de retorno del navegador.
Referencia: https://www.mercadopago.com.mx/developers/es/reference/online-payments/subscriptions/create-preapproval/post

`BILLING_ENFORCE_SUBSCRIPTION=0` permite preparar la instancia sin bloquear a los
usuarios existentes. Al habilitarlo, el personal necesita una suscripción ACTIVA
o PRUEBA con fecha vigente; el dueño conserva acceso a su panel de suscripción.
El administrador puede asignar periodos de prueba locales, sin registrarlos como pagos.

## Wallets: emisión y actualización preparadas, deshabilitadas

Apple requiere APPLE_WALLET_TEAM_ID, APPLE_WALLET_PASS_TYPE_ID,
APPLE_WALLET_CERTIFICATE_PATH, APPLE_WALLET_KEY_PATH, APPLE_WALLET_WWDR_PATH
y, si corresponde, APPLE_WALLET_KEY_PASSWORD. Los archivos son certificados PEM.
Google requiere GOOGLE_WALLET_ISSUER_ID y GOOGLE_WALLET_SERVICE_ACCOUNT_FILE;
GOOGLE_WALLET_CLASS_SUFFIX es opcional.

Las credenciales no están incluidas. Los botones de emisión permanecen ocultos
cuando faltan variables. Su presencia no prueba que las credenciales sean válidas.

La actualización se prepara con:

- Cola transaccional persistente para cambios de puntos, estado de tarjeta y promoción.
- Registro y baja de dispositivos Apple, listado incremental de pases y descarga
  autenticada por un token secreto distinto del código QR.
- Transporte APNs mediante HTTP/2 y actualización de saldo/estado/color de Google
  Wallet mediante OAuth y PATCH. Los fallos se conservan para reintento.

`WALLET_SERVICE_URL` debe ser la URL HTTPS pública que termina en `/wallets/apple/`.
Al configurarla, los nuevos pases Apple incluyen webServiceURL y authenticationToken.
Los pases antiguos deben descargarse otra vez para registrar el dispositivo.

```powershell
python manage.py sync_wallets
```

El comando anterior solo muestra pendientes y no usa la red. Para enviar en un
despliegue futuro se requieren credenciales, `WALLET_SYNC_ENABLED=1` y el argumento
`--send`. Ejecutar con un solo trabajador periódico. No se instala ni se programa
ningún trabajador por defecto. APNs requiere `httpx[http2]` de requirements.txt.
Los endpoints Apple usan el protocolo oficial; el listado por device ID no lleva
Authorization según ese protocolo, pero no devuelve saldos ni datos de clientes.
Referencias:
https://developer.apple.com/documentation/walletpasses/adding-a-web-service-to-update-passes
https://developers.google.com/wallet/retail/loyalty-cards/use-cases/updates

## Configuración y pruebas

Fuera de desarrollo, DJANGO_DEBUG es falso y DJANGO_SECRET_KEY es obligatorio.
Configura DJANGO_ALLOWED_HOSTS, DJANGO_CSRF_TRUSTED_ORIGINS y HTTPS. Las cookies
seguras, redirección HTTPS y HSTS se activan en producción. La configuración de
proxy/TLS debe adaptarse al despliegue. SQLite se mantiene para la instancia local;
antes de producción concurrente, configura una base con bloqueos de fila y valida
allí las operaciones simultáneas (SQLite no implementa select_for_update).

```powershell
python manage.py test --settings=rewards.test_settings
python manage.py makemigrations --check --dry-run
python manage.py check
```

Las pruebas usan una base en memoria e integraciones simuladas. No validan cuentas,
certificados, pases instalados ni cobros reales. No se han conectado proveedores.
