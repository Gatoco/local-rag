# Guía de Inicio Rápido - Sistema RAG Local (llama.cpp)

## 1. Requisitos del Sistema

- **Python 3.12+** (OBLIGATORIO)
  - ✅ Python 3.12: Compatible
  - ❌ Python 3.14: NO compatible (Pydantic v2 incompatibility)
  - ❌ Python 3.11 o anteriores: No soportado

- **~2GB de RAM libre** (para embeddings + LLM en memoria)
- **~5GB de disco** (para modelo GGUF + embeddings)

## 2. Instalación

### Paso 1: Verificar Python

```bash
python --version  # Debe mostrar 3.12.X
```

### Paso 2: Crear entorno virtual

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# En Windows: .venv\Scripts\activate
```

### Paso 3: Instalar dependencias

```bash
pip install -r requirements.txt
```

**Nota:** `llama-cpp-python` puede tardar 2-5 minutos en compilar la primera vez.

## 3. Descargar modelo GGUF

Este proyecto usa **llama.cpp** en lugar de Ollama. Necesitas descargar un modelo en formato GGUF.

### Opción recomendada: Mistral-7B (4.4 GB)

```bash
# Crear directorio
mkdir -p ./models

# Descargar Mistral-7B cuantizado
wget -O ./models/mistral-7b-instruct-v0.3.Q4_K_M.gguf \
  https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.3-GGUF/resolve/main/mistral-7b-instruct-v0.3.Q4_K_M.gguf
```

### Alternativas (si tienes menos RAM)

```bash
# Llama-3.2-3B (2 GB) - más rápido, menos preciso
wget -O ./models/llama-3.2-3b-instruct.Q4_K_M.gguf \
  https://huggingface.co/lmstudio-community/Llama-3.2-3B-Instruct-GGUF/resolve/main/llama-3.2-3b-instruct.Q4_K_M.gguf

# Phi-3-mini (2.3 GB) - excelente equilibrio
wget -O ./models/phi-3-mini-4k-instruct.Q4_K_M.gguf \
  https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct.Q4_K_M.gguf
```

## 4. Configurar .env

Copia el archivo de ejemplo:

```bash
cp .env.example .env
```

Verifica que `LLAMA_CPP_MODEL_PATH` apunte a tu modelo:

```env
LLAMA_CPP_MODEL_PATH=./models/mistral-7b-instruct-v0.3.Q4_K_M.gguf
```

## 5. Ejecutar la aplicación

```bash
python main.py
```

Verás algo como:

```
=== SISTEMA RAG LOCAL (llama.cpp) ===
[*] Cargando motores de IA locales...
    → Cargando embeddings (primera ejecución: ~1 min)...
    ✓ Embeddings listo.
    → Inicializando LLM llama.cpp mistral-7b-instruct-v0.3.Q4_K_M.gguf (CPU)...
    ✓ LLM listo.
    → Inicializando base de datos vectorial (Chroma)...
    ✓ ChromaDB listo.
[+] SISTEMA RAG OPERATIVO. Modelo: mistral-7b-instruct-v0.3.Q4_K_M.gguf

[*] No hay documentos en ./docs_to_ingest.
    Puedes cargarlos con: ingest-dir <ruta>

--- CLI RAG INTERACTIVA ---

Comandos disponibles:
  ingest-file <ruta>   : Ingesta un archivo soportado (.pdf, .txt, .docx)
  ingest-dir <ruta>    : Ingesta todos los documentos válidos de un directorio
  query <pregunta>     : Ejecuta una consulta RAG
  help                 : Muestra esta ayuda
  exit                 : Cierra la aplicación

rag> _
```

## 6. Uso básico

### Cargar documentos

```
rag> ingest-dir ./docs_to_ingest
[*] Ingestando directorio: ./docs_to_ingest
[+] Directorio indexado correctamente: 125 fragmentos totales.
```

### Hacer una consulta

```
rag> query ¿Cuál es el impacto de la transformación digital en las empresas?

Respuesta:
[Respuesta generada por IA basada en tus documentos...]

Fuentes:
- documento1.pdf
- documento2.pdf
```

### Ver ayuda

```
rag> help
```

## 7. Resolución de problemas

### Error: "Modelo GGUF no encontrado"

```bash
# Descarga un modelo (ver paso 3):
mkdir -p ./models
wget -O ./models/mistral-7b-instruct-v0.3.Q4_K_M.gguf \
  https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.3-GGUF/resolve/main/mistral-7b-instruct-v0.3.Q4_K_M.gguf
```

### Error: "No module named 'llama_cpp'"

```bash
# Reinstala llama-cpp-python:
pip install llama-cpp-python --force-reinstall --no-cache-dir
```

### Error: "TypeError: 'function' object is not subscriptable"

Estás usando Python 3.14. Cambia a Python 3.12:

```bash
# Recrea el venv con Python 3.12
rm -rf .venv
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### Primera ejecución lenta

Es normal. En la primera ejecución:
- Se descargan embeddings (~400 MB): 2-5 minutos
- Se crea la base de datos Chroma
- **llama.cpp puede compilar la primera vez**: 2-5 minutos adicionales

Ejecuciones posteriores son mucho más rápidas.

### Compilación de llama-cpp-python falla

```bash
# Instala dependencias de compilación:

# Ubuntu/Debian:
sudo apt-get install build-essential cmake

# macOS (con Xcode):
xcode-select --install

# Luego reinstala:
pip install llama-cpp-python --force-reinstall
```

## 8. Personalización

Edita el archivo `.env` para cambiar:

```env
# Cambiar modelo GGUF
LLAMA_CPP_MODEL_PATH=./models/llama-3.2-3b-instruct.Q4_K_M.gguf

# Usar GPU (si tienes NVIDIA/AMD)
N_GPU_LAYERS=35

# Aumentar contexto (si el modelo lo soporta)
N_CTX=8192

# Aumentar documentos recuperados (más contexto, más lento)
TOP_K_DOCUMENTS=8

# Ajustar tamaño de fragmentos
CHUNK_SIZE=1500
CHUNK_OVERLAP=200
```

Luego reinicia la aplicación para aplicar cambios.

## 9. Ejemplos de consultas

Con documentos de matemáticas:
```
rag> query Explica el Teorema Fundamental del Cálculo en español
rag> query ¿Cuáles son las propiedades principales de las derivadas?
rag> query Resume integrales definidas en 5 puntos clave
```

Con documentos técnicos:
```
rag> query ¿Cuál es la arquitectura del sistema de recomendación?
rag> query Explica el flujo de datos en la pipeline de procesamiento
```

## 10. Próximos pasos

1. Lee [README.md](README.md) para entender la arquitectura completa
2. Explora [src/](src/) para ver cómo interceptar/personalizar el flujo RAG
3. Carga tus propios documentos en `docs_to_ingest/`
4. Considera usar GPU ajustando `N_GPU_LAYERS` en `.env`

---

**Construido con ❤️ usando llama.cpp + ChromaDB + LangChain**

**Ventaja clave:** Sin proceso externo - todo ocurre en un solo proceso Python.
