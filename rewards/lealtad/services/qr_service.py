import io

import qrcode
from qrcode.constants import ERROR_CORRECT_M


def generar_qr_png(data: str) -> bytes:
    """Genera el PNG del QR de una tarjeta. El QR solo identifica a la
    tarjeta (codifica la URL pública de la tarjeta); no suma ni canjea
    puntos por sí mismo. box_size más grande = módulos más nítidos y
    fáciles de leer por una cámara, incluso escalado en pantalla."""
    qr = qrcode.QRCode(error_correction=ERROR_CORRECT_M, box_size=12, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image()
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()
