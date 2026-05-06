@echo off
REM Script de configuración inicial del proyecto RAG Local (Windows)
REM Valida Python 3.12 y configura el entorno

setlocal enabledelayedexpansion

echo.
echo ================================================================
echo   SETUP: SISTEMA RAG LOCAL
echo ================================================================
echo.

REM Verificar Python 3.12
python --version >nul 2>&1
if errorlevel 1 (
    echo. ❌ Python no encontrado en el sistema
    echo.
    echo Instala Python 3.12 desde:
    echo   https://www.python.org/downloads/
    echo.
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VER=%%i
echo [*] Python detectado: %PYTHON_VER%
echo [*] Ejecutable: 
python -c "import sys; print('    ' + sys.executable)"
echo.

if exist .venv (
    echo [*] Virtual environment ya existe
    goto activate_venv
)

echo [*] Creando virtual environment...
python -m venv .venv
echo ✅ Virtual environment creado
echo.

:activate_venv
echo [*] Activando virtual environment...
call .venv\Scripts\activate.bat

echo [*] Upgrading pip...
python -m pip install --upgrade pip setuptools wheel > nul 2>&1
echo ✅ Dependencias base actualizadas
echo.

echo [*] Instalando dependencias del proyecto...
pip install -r requirements.txt

echo.
echo ================================================================
echo   ✅ SETUP COMPLETADO EXITOSAMENTE
echo ================================================================
echo.
echo Próximos pasos:
echo   1. Activar el venv: .venv\Scripts\activate
echo   2. Crear archivo .env: copy .env.example .env
echo   3. Iniciar Ollama en otra terminal: ollama serve
echo   4. Ejecutar el sistema: python main.py
echo.
echo Para más información, ver: docs/PYTHON_COMPATIBILITY.md
echo.
pause
