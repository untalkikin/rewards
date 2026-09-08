from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class PaseResult:
    """Resultado uniforme para que la vista no necesite saber qué
    proveedor respondió: o es un archivo para descargar, o es una URL
    a la que redirigir."""

    kind: str  # "file" | "redirect"
    content: Optional[bytes] = None
    content_type: Optional[str] = None
    filename: Optional[str] = None
    url: Optional[str] = None


class WalletProvider(ABC):
    """Interfaz común para los proveedores de wallet (Apple, Google).
    Cada proveedor decide si está configurado a partir de sus propias
    credenciales (variables de entorno / archivos); si no lo está, la
    vista debe mostrar un aviso en vez de romper."""

    @abstractmethod
    def is_configured(self) -> bool:
        ...

    @abstractmethod
    def generar_pase(self, tarjeta, request) -> PaseResult:
        ...
