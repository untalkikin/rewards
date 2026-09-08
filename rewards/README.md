# Rewards

> Nota: este README se completa en la Fase 6 (cómo correr, datos semilla, roles de
> prueba, flujo de demo). Por ahora documenta lo que pide explícitamente la Fase 5:
> las credenciales de Apple/Google Wallet.

## Wallets (Apple / Google)

Ambas integraciones son **opcionales**: si faltan las variables de entorno
correspondientes, los botones de "Añadir a Apple Wallet" / "Guardar en Google
Wallet" simplemente no aparecen en la tarjeta del cliente (`/tarjeta/<codigo>/`),
y sus endpoints devuelven un aviso (HTTP 501) en vez de romper la app.

### Apple Wallet

Requiere una cuenta de **Apple Developer** con un **Pass Type ID** creado en
developer.apple.com, y sus certificados exportados a formato PEM.

| Variable | Qué es | Dónde conseguirla |
|---|---|---|
| `APPLE_WALLET_TEAM_ID` | Team ID de la cuenta de developer | Membership → Team ID en developer.apple.com |
| `APPLE_WALLET_PASS_TYPE_ID` | Identificador del Pass Type (ej. `pass.com.tunegocio.rewards`) | Certificates, Identifiers & Profiles → Identifiers → Pass Type IDs |
| `APPLE_WALLET_CERTIFICATE_PATH` | Ruta al certificado del pase, en PEM | Se genera un `.cer` desde el Pass Type ID y se convierte a PEM (`openssl x509 -inform DER -in cert.cer -out cert.pem`) |
| `APPLE_WALLET_KEY_PATH` | Ruta a la llave privada del certificado, en PEM | Se exporta el `.p12` desde Keychain Access y se convierte (`openssl pkcs12 -in cert.p12 -out key.pem -nocerts`) |
| `APPLE_WALLET_KEY_PASSWORD` | Password de la llave privada (si se le puso una al exportar) | La que hayas definido al exportar el `.p12` |
| `APPLE_WALLET_WWDR_PATH` | Ruta al certificado intermedio Apple WWDR, en PEM | developer.apple.com/certificationauthority (convertir igual que el certificado del pase) |

El pase se regenera bajo demanda en cada descarga (`GET /tarjeta/<codigo>/apple.pkpass`).
La actualización automática de puntos vía APNs (push silencioso al pase ya instalado)
queda para una fase futura.

### Google Wallet

Requiere una **cuenta de servicio de Google Cloud** con acceso a la Google Wallet API,
y el **Issuer ID** del programa de lealtad.

| Variable | Qué es | Dónde conseguirla |
|---|---|---|
| `GOOGLE_WALLET_ISSUER_ID` | ID del emisor del programa de lealtad | Google Wallet Business Console (pay.google.com/business/console) |
| `GOOGLE_WALLET_SERVICE_ACCOUNT_FILE` | Ruta al JSON de la cuenta de servicio | Google Cloud Console → IAM → Cuentas de servicio → crear llave JSON. Esa cuenta de servicio debe estar vinculada como usuario en el Wallet Business Console. |
| `GOOGLE_WALLET_CLASS_SUFFIX` | Opcional (default `rewards_loyalty_class`) | Sufijo con el que se arma el `classId` como `<issuer_id>.<sufijo>` |

El botón redirige a `pay.google.com/gp/v/save/<jwt>`, con la clase y el objeto de
lealtad embebidos en el propio JWT firmado (no requiere pre-crear la clase por la
REST API antes del primer uso).

### Dónde poner las variables

Cualquier mecanismo estándar de variables de entorno del sistema operativo o del
proceso que corre Django (por ejemplo, exportarlas antes de `manage.py runserver`,
o en la configuración del servicio en producción). El proyecto no usa un paquete
tipo `django-environ`/`.env` todavía; si lo prefieres, se puede agregar en la Fase 6.
