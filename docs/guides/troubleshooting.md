# Troubleshooting - Sistema RAG Local

## Error: "TypeError: 'function' object is not subscriptable"

### Causa
Python 3.14 cambió la forma en que maneja la subscripción de tipos (`dict[str, Any]` vs `Dict[str, Any]`). Pydantic v2 y LangChain 0.3.x aún no son totalmente compatibles con estos cambios.

### Solución: Cambiar a Python 3.12

```bash
# 1. Verificar versión instalada
python --version

# 2. Si tienes acceso a python3.12 en el sistema:
which python3.12

# 3. Si no está instalado, instálalo con tu gestor de paquetes:

# Linux (Debian/Ubuntu):
sudo apt install python3.12 python3.12-venv

# Linux (Fedora/RHEL):
sudo dnf install python3.12 python3.12-venv

# macOS (Homebrew):
brew install python@3.12

# 4. Recrea el entorno virtual con Python 3.12:
rm -rf .venv
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

---

## Error: "Conexión rechazada a Ollama (localhost:11434)"

### Causa
Ollama no está ejecutándose o no está en http://localhost:11434.

### Solución

```bash
# 1. En una terminal separada, inicia Ollama:
ollama serve

# 2. En otra terminal, verifica que funciona:
curl http://localhost:11434/api/tags

# 3. Si no tienes modelos descargados, descarga uno:
ollama pull mistral-nemo

# 4. Luego ejecuta la app en una tercera terminal:
. .venv/bin/activate
python main.py
```

### Si Ollama está en otra máquina
Edita `.env`:
```env
OLLAMA_BASE_URL=http://IP_REMOTA:11434
```

---

## Error: "Modelo no encontrado en Ollama"

### Causa
El modelo especificado no está descargado en Ollama.

### Solución

```bash
# Listar modelos disponibles localmente:
ollama list

# Descargar un modelo (ejemplos):
ollama pull mistral-nemo    # 9B, recomendado para CPU
ollama pull mistral         # 7B, más ligero
ollama pull neural-chat     # 7B, optimizado para chat
ollama pull llama2          # 7B, alternativa clásica

# Después edita .env:
OLLAMA_MODEL=mistral-nemo  # O el modelo que descargaste
```

---

## Error: "No space left on device" al descargar embeddings/modelos

### Causa
No hay espacio en disco para descargar modelos de IA (~500 MB para embeddings + tamaño del modelo LLM).

### Solución

```bash
# Limpia la caché de HuggingFace
rm -rf ~/.cache/huggingface

# O Ollama
rm -rf ~/.ollama

# O desactiva descarga automática y especifica ruta personalizada
export HF_HOME=/ruta/con/mas/espacio
```

---

## La primera ejecución es muy lenta

### Causa normal
- Primera descarga de embeddings: ~500 MB (2-5 minutos)
- Primera compilación de índices Chroma
- Inicialización de LLM

### Solución
Es normal. Ejecutar ` iaciones, se cachea todo:las posteriores serán rápidas (~30 seg).

```bash
# Para acelerar futuros arranques, considera precarga:
python -c "from langchain_huggingface import HuggingFaceEmbeddings; HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2').embed_query('test')"
```

---

## Error: "Memoria insuficiente" o "CUDA out of memory"

### Solución

```env
# Usa CPU explícitamente en HF embeddings (editamos el adaptador):
# En src/infrastructure/adapters/hf_embedding_adapter.py:
#  self.model = HuggingFaceEmbeddings(
#      model_name=model_name,
#      model_kwargs={'device': 'cpu'},  # Esto ya está por defecto
#      encode_kwargs={'normalize_embeddings': True}
#  )

# Para Ollama, ajusta parámetros en .env:
# Si tienes <4GB RAM: reduce TOP_K_DOCUMENTS=2
TOP_K_DOCUMENTS=2

# También puedes limitar contexto del modelo:
# Edita main.py y añade a OllamaLLMAdapter:
# options={'num_ctx': 2048}  # En lugar del default 4096
```

---

## Error: "Pydantic validation error"

Esto puede ocurrir si hay versión incompatible de Pydantic.

```bash
# Fuerza reinstalación de dependencias LangChain compatibles:
python -m pip install --force-reinstall -r requirements.txt

# O más agresivo:
python -m pip uninstall -y langchain langchain-core langchain-community pydantic
python -m pip install -r requirements.txt
```

---

## La consulta RAG devuelve respuestas genéricas

### Posible causa
Los documentos ingeridos no son relevantes a la consulta, o se necesita más documentos en la ingesta.

### Solución

```bash
# 1. Verifica que la ingesta completó correctamente:
rag> ingest-dir ./docs_to_ingest
# Debe mostrar "Directorio indexado correctamente: N fragmentos"

# 2. Aumenta TOP_K para ver más contexto:
# Edita .env:
TOP_K_DOCUMENTS=8

# 3. Aumenta CHUNK_SIZE para contextos más amplios:
CHUNK_SIZE=1500
CHUNK_OVERLAP=250

# 4. Reinicia la app
python main.py
```

---

## Chrome/ChromaDB no persiste entre ejecuciones

### Verificar

```bash
# Asegúrate de que la ruta existe:
ls -la ./chroma_db/

# Debe existir y contener archivos .db
```

### Si no persiste

```bash
# Resetea la base de datos:
rm -rf ./chroma_db/

# Reinicia la app para que recree:
python main.py
```

---

## ¿Cómo personalizar el prompt RAG?

Edita [src/application/services/rag_service.py](src/application/services/rag_service.py) línea ~30:

```python
self.prompt_template = ChatPromptTemplate.from_template("""
Eres un Asistente Técnico especializado en [TU_TEMA].
Tu misión es responder usando ÚNICAMENTE el contexto proporcionado.

CONTEXTO:
{context}

PREGUNTA:
{input}

RESPUESTA (técnica, clara, en español):
""")
```

---

## Preguntas frecuentes adicionales

**P: ¿Puedo cambiar el modelo LLM sin reiniciar?**
R: No, la app lo carga al arrancar. Cambia `OLLAMA_MODEL` en `.env` y reinicia.

**P: ¿Puedo usar GPU?**
R: Sí, si tienes CUDA instalado. Ollama la usa automáticamente. No aplica para embeddings HF (usa CPU por defecto).

**P: ¿Cómo limpio la base de datos de documentos?**
R: `rm -rf ./chroma_db/` y reinicia la app.

**P: ¿Puedo usar otros modelos de embeddings?**
R: Sí, cambia `EMBEDDING_MODEL` en `.env` a cualquier modelo de HF (ej: `sentence-transformers/all-mpnet-base-v2`).

---

**Última actualización: 21 de marzo 2026**
