# Nuevas dependencias

Agregadas en la Fase 1 a `requirements.txt`:

| Paquete | Versión | Para qué |
|---|---|---|
| `django-userforeignkey` | 0.4.0 | Ya estaba importado en `bases/models.py` (campos `creado_por`/`actualizado_por` de `ModelClass`) pero no estaba instalado ni registrado. Se instaló y se agregó su middleware (`UserForeignKeyMiddleware`) en `settings.py` para que esos campos se autopueblen con el usuario de la request. |
| `Pillow` | 12.3.0 | Requerido por Django para `ImageField` (logo/favicon del Negocio en `stores.Store`). |
| `qrcode` | 8.0 | Generación del PNG del QR de la tarjeta de lealtad (`TarjetaLealtad`), a usarse en la Fase 2. Se instala desde ahora para no reabrir `requirements.txt` en cada fase. |

Agregadas en la Fase 5 (integración de wallets):

| Paquete | Versión | Para qué |
|---|---|---|
| `py-pkpass` | 1.0.2 | Genera el archivo `.pkpass` (Apple Wallet) firmado con PKCS#7. Es el fork de `GlitchOo` (github.com/GlitchOo/py-pkpass), la variante mantenida en 2025 de la vieja librería `devartis/passbook`/`wallet`: usa la librería `cryptography` moderna en vez de `M2Crypto` (que ya no compila fácil en Python recientes) y tiene soporte activo para Python 3.8–3.12. Se evaluaron `applepassgenerator` y el `wallet` original de devartis, ambos con menos actividad reciente. |
| `cryptography` | 50.0.1 | Dependencia de `py-pkpass` para firmar el manifiesto del pase (PKCS#7/DER) y leer los certificados PEM. Se pinea explícitamente por ser código de firma/criptografía. |
| `PyJWT` | 2.13.0 | Firma el JWT del botón "Save to Google Wallet" (RS256, con la llave privada de la cuenta de servicio de Google Cloud). Es el estándar de facto para JWT en Python y el que usa la propia documentación de Google Wallet API. |

## Notas

- **Wallets con feature flag real:** ambos proveedores (`wallets/services/apple_service.py`, `wallets/services/google_service.py`) se autodesactivan si faltan sus credenciales — ver variables de entorno en `settings.py` (`APPLE_WALLET_*`, `GOOGLE_WALLET_*`) y el README. Sin credenciales, los botones no aparecen en la tarjeta del cliente y los endpoints devuelven un aviso (HTTP 501) en vez de un error 500.
- La app `wallets` **no está en `INSTALLED_APPS`**: no tiene modelos ni migraciones propias, es solo una librería de servicios (`wallets/services/`) que consumen las vistas de `lealtad`. No hace falta registrarla como app de Django.

- El entorno tenía instalados globalmente `djangorestframework`, `djangorestframework-simplejwt`, `django-cors-headers` y `django-environ`, pero **ninguno está referenciado en el código del proyecto** (no aparecen en `INSTALLED_APPS` ni se importan). No se agregaron a `requirements.txt` porque no se están usando; si planeas exponer una API REST más adelante, avísame y los incorporo con su configuración correspondiente.
- No se generó `requirements.txt` antes de esta fase — no existía en el repo.
