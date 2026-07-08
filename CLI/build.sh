#!/usr/bin/env bash
set -euo pipefail

# Construye el ejecutable de la CLI para Linux/macOS con PyInstaller.
# Requisitos: Python 3.10+, pip

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "[1/4] Creando entorno virtual..."
python3 -m venv .venv
source .venv/bin/activate

echo "[2/4] Instalando dependencias..."
python -m pip install --upgrade pip --quiet
python -m pip install "typer[all]" httpx rich pyinstaller --quiet

echo "[3/4] Compilando ejecutable..."
pyinstaller cli.spec --clean --noconfirm

echo "[4/4] Listo!"
echo
echo " El ejecutable esta en: dist/bio-cli"
echo
echo " Pruebalo con:"
echo "   ./dist/bio-cli --help"
echo "   ./dist/bio-cli auth login"
echo "   ./dist/bio-cli projects list"
