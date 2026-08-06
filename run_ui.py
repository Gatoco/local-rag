#!/usr/bin/env python3
"""
Script para ejecutar la UI Web del sistema RAG con Streamlit.

Uso:
    python run_ui.py

O directamente:
    streamlit run ui/app.py
"""

import os
import sys
import subprocess
from pathlib import Path

from dotenv import load_dotenv
from colorama import Fore, Style, init

# Cargar variables de entorno
load_dotenv()

# Inicializar colores
init(autoreset=True)


def check_streamlit_installed() -> bool:
    """Verifica si Streamlit está instalado."""
    try:
        import streamlit
        return True
    except ImportError:
        return False


def install_streamlit():
    """Instala Streamlit si no está instalado."""
    print(f"{Fore.YELLOW}Instalando Streamlit...{Style.RESET_ALL}")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit", "-q"])
    print(f"{Fore.GREEN}✓ Streamlit instalado{Style.RESET_ALL}")


def main():
    """Punto de entrada principal."""
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*60}")
    print("UI WEB - SISTEMA RAG LOCAL".center(60))
    print(f"{'='*60}{Style.RESET_ALL}\n")

    # Verificar Streamlit
    if not check_streamlit_installed():
        print(f"{Fore.YELLOW}⚠ Streamlit no está instalado{Style.RESET_ALL}")
        install = input("¿Deseas instalarlo ahora? (s/n): ").lower().strip()
        
        if install == 's':
            install_streamlit()
        else:
            print(f"\n{Fore.RED}❌ Streamlit es requerido para la UI Web{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}💡 Instala manualmente: pip install streamlit{Style.RESET_ALL}")
            sys.exit(1)

    # Verificar API
    api_url = os.getenv("API_URL", "http://localhost:8000")
    print(f"{Fore.YELLOW}[*] Verificando conexión con API...{Style.RESET_ALL}")
    
    try:
        import requests
        response = requests.get(f"{api_url}/api/v1/health", timeout=5)
        if response.status_code == 200:
            print(f"{Fore.GREEN}    ✓ API disponible en {api_url}{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}    ⚠ API respondió con estado {response.status_code}{Style.RESET_ALL}")
    except requests.exceptions.RequestException:
        print(f"{Fore.RED}    ✗ API no disponible en {api_url}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}    💡 Ejecuta 'python run_api.py' en otra terminal{Style.RESET_ALL}")
        print(f"\n{Fore.YELLOW}    La UI se iniciará pero algunas funciones no estarán disponibles.{Style.RESET_ALL}")

    # Información de la UI
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*60}")
    print("INICIANDO UI WEB".center(60))
    print(f"{'='*60}{Style.RESET_ALL}\n")

    print(f"{Fore.GREEN}🌐 URL: http://localhost:8501")
    print(f"{Fore.GREEN}📱 La UI se abrirá automáticamente en tu navegador")
    print(f"\n{Fore.YELLOW}Presiona Ctrl+C para detener{Style.RESET_ALL}\n")

    # Ejecutar Streamlit
    try:
        ui_path = Path(__file__).parent / "ui" / "app.py"
        
        if not ui_path.exists():
            print(f"{Fore.RED}❌ Error: UI app no encontrada en {ui_path}{Style.RESET_ALL}")
            sys.exit(1)

        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            str(ui_path),
            "--server.address", "localhost",
            "--server.port", "8501",
            "--server.headless", "false",
            "--browser.gatherUsageStats", "false",
        ])
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}UI Web detenida por el usuario{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}❌ Error al ejecutar UI Web: {e}{Style.RESET_ALL}")
        sys.exit(1)


if __name__ == "__main__":
    main()
