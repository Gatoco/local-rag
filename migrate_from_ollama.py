#!/usr/bin/env python3
"""
Script de migración de Ollama a llama.cpp

Ayuda a usuarios existentes a migrar su configuración y descargar
un modelo GGUF equivalente al que usaban en Ollama.

Uso:
    python migrate_from_ollama.py
"""

import os
import shutil
from pathlib import Path

def check_ollama_models():
    """Verifica modelos instalados en Ollama."""
    print("\n" + "=" * 60)
    print("VERIFICANDO MODELOS DE OLLAMA".center(60))
    print("=" * 60)
    
    try:
        import subprocess
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("\nModelos encontrados en Ollama:")
            print(result.stdout)
            return True
        else:
            print("\n⚠ Ollama no está instalado o no hay modelos descargados.")
            return False
            
    except FileNotFoundError:
        print("\n⚠ Ollama no está instalado en este sistema.")
        return False
    except subprocess.TimeoutExpired:
        print("\n⚠ Timeout al consultar Ollama.")
        return False


def map_ollama_to_gguf(ollama_model: str) -> dict:
    """Mapea modelo de Ollama a equivalente GGUF."""
    mapping = {
        "mistral": {
            "name": "Mistral-7B-Instruct-v0.3",
            "gguf_url": "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.3-GGUF/resolve/main/mistral-7b-instruct-v0.3.Q4_K_M.gguf",
            "size": "4.4 GB",
            "vram": "6 GB"
        },
        "mistral-nemo": {
            "name": "Mistral-Nemo-12B",
            "gguf_url": "https://huggingface.co/Bartowski/Mistral-Nemo-12B-Instruct-GGUF/resolve/main/Mistral-Nemo-12B-Instruct-Q4_K_M.gguf",
            "size": "7.0 GB",
            "vram": "8 GB"
        },
        "llama2": {
            "name": "Llama-2-7B-Chat",
            "gguf_url": "https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf",
            "size": "4.4 GB",
            "vram": "6 GB"
        },
        "llama3": {
            "name": "Llama-3-8B-Instruct",
            "gguf_url": "https://huggingface.co/lmstudio-community/Meta-Llama-3-8B-Instruct-GGUF/resolve/main/Meta-Llama-3-8B-Instruct.Q4_K_M.gguf",
            "size": "4.9 GB",
            "vram": "6 GB"
        },
        "llama3.2": {
            "name": "Llama-3.2-3B-Instruct",
            "gguf_url": "https://huggingface.co/lmstudio-community/Llama-3.2-3B-Instruct-GGUF/resolve/main/llama-3.2-3b-instruct.Q4_K_M.gguf",
            "size": "2.0 GB",
            "vram": "4 GB"
        },
        "neural-chat": {
            "name": "Neural-Chat-7B-v3-1",
            "gguf_url": "https://huggingface.co/TheBloke/neural-chat-7B-v3-1-GGUF/resolve/main/neural-chat-7b-v3-1.Q4_K_M.gguf",
            "size": "4.4 GB",
            "vram": "6 GB"
        },
        "phi": {
            "name": "Phi-3-mini-4k-instruct",
            "gguf_url": "https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct.Q4_K_M.gguf",
            "size": "2.3 GB",
            "vram": "4 GB"
        },
        "gemma": {
            "name": "Gemma-7B-Instruct",
            "gguf_url": "https://huggingface.co/bartowski/gemma-7b-it-GGUF/resolve/main/gemma-7b-it-Q4_K_M.gguf",
            "size": "4.9 GB",
            "vram": "6 GB"
        },
        "gemma2": {
            "name": "Gemma-2-9B-Instruct",
            "gguf_url": "https://huggingface.co/bartowski/gemma-2-9b-it-GGUF/resolve/main/gemma-2-9b-it-Q4_K_M.gguf",
            "size": "5.5 GB",
            "vram": "8 GB"
        },
    }
    
    return mapping.get(ollama_model, None)


def backup_old_config():
    """Crea backup de configuración antigua."""
    print("\n" + "=" * 60)
    print("CREANDO BACKUP DE CONFIGURACIÓN".center(60))
    print("=" * 60)
    
    if os.path.exists(".env"):
        backup_path = ".env.ollama.backup"
        shutil.copy(".env", backup_path)
        print(f"\n✓ Backup creado: {backup_path}")
    else:
        print("\n⚠ No existe .env actual.")
    
    if os.path.exists("requirements.txt"):
        backup_path = "requirements.txt.ollama.backup"
        shutil.copy("requirements.txt", backup_path)
        print(f"✓ Backup creado: {backup_path}")


def update_env_file(ollama_model: str, gguf_info: dict):
    """Actualiza archivo .env con nueva configuración."""
    print("\n" + "=" * 60)
    print("ACTUALIZANDO .env".center(60))
    print("=" * 60)
    
    env_content = f"""# ========================================
# CONFIGURACIÓN DE LLM (LLAMA.CPP)
# ========================================
# Modelo GGUF equivalente a Ollama: {ollama_model}
# {gguf_info['name']}
LLAMA_CPP_MODEL_PATH=./models/{ollama_model.replace('.', '-')}.Q4_K_M.gguf

# Capas en GPU (0=CPU, >0=GPU layers)
N_GPU_LAYERS=0

# Ventana de contexto (tokens)
N_CTX=4096

# ========================================
# CONFIGURACIÓN DE EMBEDDINGS (HUGGING FACE)
# ========================================
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# ========================================
# CONFIGURACIÓN DE PERSISTENCIA (CHROMADB)
# ========================================
CHROMA_DB_PATH=./chroma_db

# ========================================
# CONFIGURACIÓN DE INGESTA
# ========================================
DOCS_PATH=./docs_to_ingest
CHUNK_SIZE=1000
CHUNK_OVERLAP=150

# ========================================
# CONFIGURACIÓN DE RECUPERACIÓN RAG
# ========================================
TOP_K_DOCUMENTS=4
"""
    
    with open(".env", "w") as f:
        f.write(env_content)
    
    print(f"\n✓ .env actualizado con:")
    print(f"  Modelo: {gguf_info['name']}")
    print(f"  Tamaño: {gguf_info['size']}")
    print(f"  VRAM recomendada: {gguf_info['vram']}")


def main():
    print("\n" + "=" * 60)
    print("MIGRACIÓN DE OLLAMA A LLAMA.CPP".center(60))
    print("=" * 60)
    
    # Paso 1: Verificar modelos de Ollama
    has_ollama = check_ollama_models()
    
    if has_ollama:
        print("\n¿Qué modelo de Ollama usabas principalmente?")
        print("Opciones comunes: mistral, mistral-nemo, llama3, llama3.2, phi, gemma")
        ollama_model = input("\nNombre del modelo: ").lower().strip()
    else:
        print("\nUsando modelo por defecto: mistral")
        ollama_model = "mistral"
    
    # Paso 2: Buscar equivalente GGUF
    gguf_info = map_ollama_to_gguf(ollama_model)
    
    if not gguf_info:
        print(f"\n⚠ No hay mapeo automático para '{ollama_model}'")
        print("Usando Mistral-7B como recomendación por defecto.")
        gguf_info = map_ollama_to_gguf("mistral")
        ollama_model = "mistral"
    
    print(f"\n✓ Modelo equivalente GGUF encontrado:")
    print(f"  Ollama: {ollama_model}")
    print(f"  GGUF: {gguf_info['name']}")
    print(f"  Tamaño: {gguf_info['size']}")
    print(f"  VRAM: {gguf_info['vram']}")
    
    # Paso 3: Backup
    backup_old_config()
    
    # Paso 4: Actualizar .env
    update_env_file(ollama_model, gguf_info)
    
    # Paso 5: Instrucciones de descarga
    print("\n" + "=" * 60)
    print("SIGUIENTES PASOS".center(60))
    print("=" * 60)
    
    model_filename = f"{ollama_model.replace('.', '-')}.Q4_K_M.gguf"
    
    print(f"""
1. Descarga el modelo GGUF:

   python download_model.py
   
   O manualmente:
   
   mkdir -p ./models
   wget -O ./models/{model_filename} \\
     {gguf_info['gguf_url']}

2. Verifica .env:
   
   cat .env | grep LLAMA_CPP_MODEL_PATH

3. Instala nuevas dependencias:

   pip install -r requirements.txt

4. Ejecuta el sistema:

   python main.py

¡Listo! Ya no necesitas ejecutar 'ollama serve'.
""")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
