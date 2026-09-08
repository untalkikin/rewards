import io

import qrcode


def generar_qr_png(data: str) -> bytes:
    """Genera el PNG del QR de una tarjeta. El QR solo identifica a la
    tarjeta (codifica la URL pública de la tarjeta); no suma ni canjea
    puntos por sí mismo."""
    img = qrcode.make(data)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()
