#!/bin/bash
# Script de configuración inicial del proyecto RAG Local
# Valida Python 3.12 y configura el entorno

set -e

echo ""
echo "================================================================"
echo "  SETUP: SISTEMA RAG LOCAL".center(66)
echo "================================================================"
echo ""

# Detectar Python 3.12
if command -v python3.12 &> /dev/null; then
    PYTHON_CMD="python3.12"
elif command -v python3 &> /dev/null; then
    PYTHON_VERSION=$($([[ -x /usr/bin/python3 ]] && /usr/bin/python3 --version 2>&1 | grep -oP '\d+\.\d+') || echo "0.0")
    if [[ "$PYTHON_VERSION" == "3.12"* ]]; then
        PYTHON_CMD="python3"
    else
        echo "❌ No se encontró Python 3.12"
        echo ""
        echo "Instalación requerida:"
        echo "  - Ubuntu/Debian: sudo apt-get install python3.12 python3.12-venv"
        echo "  - macOS: brew install python@3.12"
        echo "  - Windows: https://www.python.org/downloads/"
        echo ""
        exit 1
    fi
else
    echo "❌ Python no encontrado en el sistema"
    exit 1
fi

echo "[*] Python detectado: $($PYTHON_CMD --version)"
echo "[*] Ejecutable: $($PYTHON_CMD -c 'import sys; print(sys.executable)')"
echo ""

# Crear virtual environment
if [ ! -d ".venv" ]; then
    echo "[*] Creando virtual environment..."
    $PYTHON_CMD -m venv .venv
    echo "✅ Virtual environment creado"
else
    echo "[*] Virtual environment ya existe"
fi

echo ""
echo "[*] Activando virtual environment..."
source .venv/bin/activate

echo "[*] Upgrading pip..."
pip install --upgrade pip setuptools wheel > /dev/null 2>&1
echo "✅ Dependencias base actualizadas"

echo ""
echo "[*] Instalando dependencias del proyecto..."
pip install -r requirements.txt

echo ""
echo "================================================================"
echo "  ✅ SETUP COMPLETADO EXITOSAMENTE".center(66)
echo "================================================================"
echo ""
echo "Próximos pasos:"
echo "  1. Activar el venv: source .venv/bin/activate"
echo "  2. Crear archivo .env: cp .env.example .env"
echo "  3. Iniciar Ollama en otra terminal: ollama serve"
echo "  4. Ejecutar el sistema: python main.py"
echo ""
echo "Para más información, ver: docs/PYTHON_COMPATIBILITY.md"
echo ""
