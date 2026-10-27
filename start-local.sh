#!/usr/bin/env bash
# Equivalente a start-local.ps1, para Git Bash.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="$SCRIPT_DIR/env/Scripts/python.exe"

if [ ! -f "$PYTHON_BIN" ]; then
    echo "Crea el entorno env e instala requirements.txt primero." >&2
    exit 1
fi

export DJANGO_DEBUG=1
export DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Google Wallet (modo demostracion)
export GOOGLE_WALLET_ISSUER_ID=3388000000023223572
export GOOGLE_WALLET_SERVICE_ACCOUNT_FILE="C:/Users/henry/OneDrive/Security/WalletRewards/nexusrewards-ec63a4cb0655.json"

cd "$SCRIPT_DIR/rewards"

"$PYTHON_BIN" manage.py check

cat <<'EOF'

==================== Usuarios de prueba ====================
  Negocio: Cafeteria Central

  Dueno                 dueno    / Dueno123!
  Cajero (Sucursal Centro)  cajero1  / Cajero123!
  Cajero (Sucursal Norte)   cajero2  / Cajero123!
  Cajero (sin sucursal)     cajero3  / Cajero123!
  Cajero (perfil inactivo)  cajero4  / Cajero123!
  Superusuario (/admin/)    admin    / Admin123!

  Clientes (login en /mi-cuenta/login/ con negocio+telefono+PIN):
    Cliente Demo      tel 3001234567  PIN 1234   (1/5 sellos)
    Carlos Ruiz       tel 3005551234  PIN 1357   (5/5, listo para canjear)
    Lucia Fernandez   tel 3007778888  PIN 9999   (3/5, historial de compras)
    Andrea Gomez      tel 3009876543  PIN 2468   (0/5, recien creada)
==============================================================

EOF

"$PYTHON_BIN" manage.py runserver 127.0.0.1:8000
