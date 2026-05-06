# Sistema RAG Local (llama.cpp + ChromaDB + Hugging Face + LangChain)

Implementación de un sistema RAG totalmente local, optimizado para privacidad, control de datos y modularidad. La arquitectura sigue Ports & Adapters (hexagonal), por lo que puedes cambiar componentes de infraestructura sin romper la lógica de negocio.

## Objetivo técnico

Construir un pipeline RAG local de extremo a extremo:

1. Ingesta y preprocesamiento de documentos.
2. Fragmentación (chunking) para recuperación semántica estable.
3. Generación de embeddings locales con modelos de Hugging Face.
4. Almacenamiento y búsqueda vectorial en ChromaDB persistente.
5. Generación final con LLM local usando **llama.cpp** (sin proceso externo).

## Stack usado

- **llama.cpp** para inferencia local del LLM (embebido, sin servidor externo).
- ChromaDB como vector store persistente.
- Hugging Face Sentence Transformers para embeddings.
- LangChain como capa de orquestación RAG.

## Requisitos previos

- **Python 3.12** (OBLIGATORIO - especificado en `.python-version` y `pyproject.toml`)
  - ❌ Python 3.14: Incompatible con Pydantic v2
  - ⚠️ Python 3.11: No soportado (EOL octubre 2027)
  - ✅ Python 3.12: Versión estable recomendada

- **Modelo GGUF descargado** (formato cuantizado para llama.cpp)

## Modelos GGUF Recomendados

| Modelo | Tamaño | VRAM | Calidad | Download |
|--------|--------|------|---------|----------|
| Mistral-7B-Instruct-v0.3 | 4.4 GB | 6 GB | ⭐⭐⭐⭐ | [Q4_K_M](https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.3-GGUF/resolve/main/mistral-7b-instruct-v0.3.Q4_K_M.gguf) |
| Llama-3.2-3B-Instruct | 2.0 GB | 4 GB | ⭐⭐⭐ | [Q4_K_M](https://huggingface.co/lmstudio-community/Llama-3.2-3B-Instruct-GGUF) |
| Phi-3-mini-4k-instruct | 2.3 GB | 4 GB | ⭐⭐⭐⭐ | [Q4_K_M](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf) |

### Descargar modelo (ejemplo con Mistral-7B)

```bash
# Crear directorio de modelos
mkdir -p ./models

# Descargar Mistral-7B cuantizado (4.4 GB)
wget -O ./models/mistral-7b-instruct-v0.3.Q4_K_M.gguf \
  https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.3-GGUF/resolve/main/mistral-7b-instruct-v0.3.Q4_K_M.gguf
```

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Nota:** `llama-cpp-python` puede tardar unos minutos en compilar la primera vez.

## Configuración

Crea un archivo `.env` en la raíz del proyecto:

```env
# LLM local con llama.cpp (modelo GGUF)
LLAMA_CPP_MODEL_PATH=./models/mistral-7b-instruct-v0.3.Q4_K_M.gguf

# Capas en GPU (0=CPU, >0=GPU layers)
N_GPU_LAYERS=0

# Ventana de contexto (tokens)
N_CTX=4096

# Embeddings locales
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Persistencia vectorial
CHROMA_DB_PATH=./chroma_db

# Ruta de ingesta inicial (opcional)
DOCS_PATH=./docs_to_ingest

# Recuperación
TOP_K_DOCUMENTS=4

# Chunking
CHUNK_SIZE=1000
CHUNK_OVERLAP=150
```

## Arranque de la aplicación

### Opción 1: CLI Interactiva (Mejorada)

```bash
python main.py
```

**Novedades:**
- 🎨 Emojis para feedback visual
- 📝 Respuestas con word-wrap automático
- 🆕 Comandos: `count`, `clear`
- ❌ Mensajes de error descriptivos

### Opción 2: API REST

```bash
# Iniciar servidor API
python run_api.py

# Servidor corriendo en http://localhost:8000
# Documentación interactiva: http://localhost:8000/docs
```

Ver [docs/API_REST.md](docs/API_REST.md) para documentación completa de la API.

### Opción 3: UI Web (NUEVO)

```bash
# Iniciar UI Web con Streamlit
python run_ui.py

# UI corriendo en http://localhost:8501
# Se abre automáticamente en tu navegador
```

**Características:**
- 💬 Chat interactivo con historial
- 📁 Ingesta de documentos (drag & drop)
- 📈 Dashboard con métricas en tiempo real
- ⚙️ Configuración desde sidebar

Ver [docs/UI_WEB.md](docs/UI_WEB.md) para guía completa.

## CLI interactiva

Comandos disponibles:

```text
ingest-file <ruta>   : ingesta un archivo .pdf/.txt/.docx
ingest-dir <ruta>    : ingesta recursiva de un directorio
query <pregunta>     : ejecuta consulta RAG
help                 : ayuda
exit                 : salir
```

Ejemplos:

```text
rag> ingest-dir ./docs_to_ingest
rag> query Explica el teorema fundamental del calculo segun mis documentos
rag> query Resume los conceptos clave de algebra lineal en 5 puntos
```

## Flujo técnico detallado

### 1. Ingesta y preprocesamiento

- `LangChainLoaderAdapter` detecta formato y carga contenido.
- Soporta `.pdf`, `.txt`, `.docx`.
- Recorre directorios de forma recursiva con `os.walk`.

### 2. Chunking

- `RecursiveCharacterTextSplitter` divide texto en fragmentos solapados.
- `CHUNK_SIZE` y `CHUNK_OVERLAP` controlan granularidad y continuidad de contexto.

### 3. Embeddings locales

- `HFEmbeddingAdapter` usa `HuggingFaceEmbeddings`.
- Los embeddings se normalizan (`normalize_embeddings=True`) para mejorar similitud coseno.

### 4. Persistencia y recuperación semántica

- `ChromaDBAdapter` guarda embeddings en disco (`CHROMA_DB_PATH`).
- `RAGService` configura `retriever` con `top_k` configurable.

### 5. Generación aumentada (con llama.cpp)

- `LlamaCppLLMAdapter` ejecuta el modelo GGUF directamente en el proceso Python.
- **Sin servidor HTTP externo** - todo ocurre en memoria.
- El prompt fuerza respuestas en español, técnicas y sin alucinaciones fuera de contexto.

## Estructura relevante del proyecto

```text
src/
  application/services/rag_service.py
  application/ports/rag_port.py
  domain/ports/*.py
  infrastructure/adapters/
    chromadb_adapter.py
    hf_embedding_adapter.py
    langchain_loader_adapter.py
    llama_cpp_llm_adapter.py    # ← NUEVO: reemplaza Ollama
    chat_llama_cpp.py           # ← Wrapper LangChain
  infrastructure/entrypoints/cli_adapter.py
main.py
```

## Buenas prácticas de rendimiento local

- Usa modelos GGUF cuantizados en Q4_K_M para equilibrio calidad/rendimiento.
- Ajusta `N_GPU_LAYERS` si tienes GPU NVIDIA/AMD (ej: 35 para parcial en GPU).
- Ajusta `TOP_K_DOCUMENTS`: si es muy alto, aumenta costo de tokens y latencia.
- Ajusta chunking según tipo de documento: documentos técnicos suelen requerir overlap mayor.
- Mantén Chroma persistente para evitar reindexar en cada ejecución.
- Para trabajo offline estricto, descarga modelos GGUF antes de desconectar red.

## Troubleshooting

### Error: "Modelo GGUF no encontrado"

```bash
# Descarga un modelo:
mkdir -p ./models
wget -O ./models/mistral-7b-instruct-v0.3.Q4_K_M.gguf \
  https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.3-GGUF/resolve/main/mistral-7b-instruct-v0.3.Q4_K_M.gguf
```

### Error: "llama-cpp-python no está instalado"

```bash
# Reinstala dependencias:
pip install -r requirements.txt

# O instala directamente:
pip install llama-cpp-python
```

### Error por dependencias de LangChain

```bash
pip install -r requirements.txt --upgrade
```

### Primera ejecución lenta (compilación)

La primera instalación de `llama-cpp-python` puede compilar desde fuente (2-5 minutos).
Es normal. Ejecuciones posteriores son instantáneas.

## Tests

```bash
pytest tests/unit
pytest tests/integration  # Requiere modelo GGUF disponible
```

Nota: El test de integración se salta automáticamente si no hay modelo GGUF disponible.

## Comparación: Ollama vs llama.cpp directo

| Característica | Ollama | llama.cpp (este proyecto) |
|----------------|--------|---------------------------|
| Proceso externo | Sí (`ollama serve`) | No (embebido en Python) |
| Overhead HTTP | Sí (~10-15%) | No |
| Rendimiento CPU | Bueno | Óptimo (+20-40% más rápido) |
| Uso de RAM | +500MB | Base |
| Gestión de modelos | Automática | Manual (descarga GGUF) |
| Facilidad de uso | Muy alta | Media |
| Control de parámetros | Limitado | Total |

## Migración desde Ollama

Si ya tenías el proyecto con Ollama:

1. Descarga un modelo GGUF equivalente al que usabas en Ollama
2. Actualiza `.env` con `LLAMA_CPP_MODEL_PATH=./models/tu-modelo.gguf`
3. Ejecuta `pip install -r requirements.txt` (instala llama-cpp-python)
4. No necesitas ejecutar `ollama serve`

## Referencias

- [llama.cpp GitHub](https://github.com/ggerganov/llama.cpp)
- [TheBloke GGUF Models](https://huggingface.co/TheBloke)
- [llama-cpp-python Docs](https://llama-cpp-python.readthedocs.io/)
