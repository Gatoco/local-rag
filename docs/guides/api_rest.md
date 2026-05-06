# API REST - Sistema RAG Local

Documentación de la API REST para el sistema RAG local con llama.cpp.

---

## 🚀 Inicio Rápido

### 1. Iniciar el servidor API

```bash
# Forma recomendada: usar script dedicado
python run_api.py

# Opciones personalizadas
python run_api.py --host 0.0.0.0 --port 8000
python run_api.py --reload  # Desarrollo (auto-recarga)

# Variables de entorno
API_HOST=0.0.0.0 API_PORT=8000 python run_api.py
```

### 2. Verificar que está funcionando

```bash
curl http://localhost:8000/api/v1/health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "model": "mistral-7b-instruct-v0.3.Q4_K_M.gguf",
  "documents_count": 4843
}
```

### 3. Documentación interactiva

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json

---

## 📡 Endpoints

### Health & Métricas

#### `GET /api/v1/health`

Verifica el estado del sistema.

**Response:** `HealthResponse`

```bash
curl http://localhost:8000/api/v1/health
```

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "model": "mistral-7b-instruct-v0.3.Q4_K_M.gguf",
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
  "documents_count": 4843,
  "timestamp": "2026-03-25T10:30:45.123456"
}
```

---

#### `GET /api/v1/metrics`

Obtiene métricas del sistema.

**Response:** `MetricsResponse`

```bash
curl http://localhost:8000/api/v1/metrics
```

```json
{
  "total_queries": 150,
  "total_documents": 4843,
  "avg_latency_ms": 2345.67,
  "cache_hit_rate": 0.0,
  "uptime_seconds": 3600.5
}
```

---

### Consultas (Query)

#### `POST /api/v1/query`

Ejecuta una consulta RAG.

**Request:** `QueryRequest`
```json
{
  "question": "¿Qué es el cálculo diferencial?",
  "top_k": 4,
  "max_tokens": 512,
  "stream": false
}
```

**Response:** `QueryResponse`

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Qué es el cálculo diferencial?",
    "top_k": 4,
    "max_tokens": 512
  }'
```

```json
{
  "answer": "El cálculo diferencial estudia las tasas de cambio instantáneo de funciones...",
  "sources": [
    {
      "content": "El cálculo diferencial estudia las tasas de cambio...",
      "metadata": {"source": "matematicas.pdf", "page": 1},
      "id": "chunk_001",
      "score": 0.85
    }
  ],
  "question": "¿Qué es el cálculo diferencial?",
  "timestamp": "2026-03-25T10:30:45.123456",
  "latency_ms": 2345.67,
  "model": "mistral-7b-instruct-v0.3.Q4_K_M.gguf"
}
```

---

#### `POST /api/v1/query/stream`

Ejecuta una consulta con streaming de tokens (Server-Sent Events).

**Request:** `QueryRequest`

```bash
curl -X POST http://localhost:8000/api/v1/query/stream \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Qué es Python?",
    "stream": true
  }'
```

**Response:** Stream de tokens en formato SSE

```
data: El

data: 

data: cálculo

data: 

data: diferencial

data: ...

```

---

### Ingestión (Ingestion)

#### `POST /api/v1/ingest/file`

Ingiere un archivo individual al índice vectorial.

**Request:** `IngestFileRequest`
```json
{
  "file_path": "./docs_to_ingest/matematicas.pdf",
  "force": false
}
```

**Response:** `IngestResponse`

```bash
curl -X POST http://localhost:8000/api/v1/ingest/file \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "./docs_to_ingest/matematicas.pdf"
  }'
```

```json
{
  "status": "success",
  "message": "Documento ingerido correctamente",
  "file_path": "./docs_to_ingest/matematicas.pdf",
  "chunks_count": 125,
  "timestamp": "2026-03-25T10:30:45.123456"
}
```

---

#### `POST /api/v1/ingest/directory`

Ingiere todos los documentos de un directorio.

**Request:** `IngestDirectoryRequest`
```json
{
  "dir_path": "./docs_to_ingest",
  "recursive": true,
  "force": false
}
```

**Response:** `IngestResponse`

```bash
curl -X POST http://localhost:8000/api/v1/ingest/directory \
  -H "Content-Type: application/json" \
  -d '{
    "dir_path": "./docs_to_ingest",
    "recursive": true
  }'
```

```json
{
  "status": "success",
  "message": "Directorio ingerido correctamente",
  "dir_path": "./docs_to_ingest",
  "chunks_count": 4843,
  "timestamp": "2026-03-25T10:30:45.123456"
}
```

---

### Gestión de Documentos

#### `GET /api/v1/documents`

Lista documentos indexados (paginado).

**Query Params:**
- `limit` (int, default=20): Máximo de documentos
- `offset` (int, default=0): Offset para paginación

**Response:** `ListDocumentsResponse`

```bash
curl "http://localhost:8000/api/v1/documents?limit=20&offset=0"
```

```json
{
  "total": 4843,
  "documents": [
    {"id": "chunk_001", "source": "matematicas.pdf", "page": 1},
    {"id": "chunk_002", "source": "matematicas.pdf", "page": 2}
  ],
  "limit": 20,
  "offset": 0
}
```

---

#### `DELETE /api/v1/documents`

Elimina un documento del índice.

**Request:** `DeleteDocumentRequest`
```json
{
  "document_id": "chunk_001"
}
```

**Response:** `DeleteResponse`

```bash
curl -X DELETE http://localhost:8000/api/v1/documents \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "chunk_001"
  }'
```

```json
{
  "status": "success",
  "message": "Documento eliminado correctamente",
  "document_id": "chunk_001"
}
```

---

## 🔌 Ejemplos de Uso

### Python (requests)

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Health check
response = requests.get(f"{BASE_URL}/health")
print(response.json())

# Consulta simple
response = requests.post(
    f"{BASE_URL}/query",
    json={"question": "¿Qué es RAG?", "top_k": 4}
)
result = response.json()
print(f"Respuesta: {result['answer']}")
print(f"Fuentes: {len(result['sources'])}")

# Ingestar archivo
response = requests.post(
    f"{BASE_URL}/ingest/file",
    json={"file_path": "./docs/matematicas.pdf"}
)
print(f"Ingestado: {response.json()['status']}")
```

### Python (streaming)

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

response = requests.post(
    f"{BASE_URL}/query/stream",
    json={"question": "¿Qué es Python?", "stream": true},
    stream=True
)

for line in response.iter_lines():
    if line:
        # Formato SSE: "data: <token>"
        token = line.decode('utf-8').replace('data: ', '')
        print(token, end='', flush=True)
```

### JavaScript (fetch)

```javascript
const BASE_URL = 'http://localhost:8000/api/v1';

// Consulta simple
async function query(question) {
  const response = await fetch(`${BASE_URL}/query`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({question, top_k: 4})
  });
  
  const result = await response.json();
  console.log('Respuesta:', result.answer);
  console.log('Fuentes:', result.sources);
  return result;
}

// Streaming
async function queryStream(question) {
  const response = await fetch(`${BASE_URL}/query/stream`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({question, stream: true})
  });
  
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  
  while (true) {
    const {value, done} = await reader.read();
    if (done) break;
    
    const chunk = decoder.decode(value);
    // Procesar tokens SSE
    chunk.split('\n').forEach(line => {
      if (line.startsWith('data: ')) {
        const token = line.replace('data: ', '');
        console.log(token);
      }
    });
  }
}

// Uso
query('¿Qué es el cálculo diferencial?');
```

### cURL

```bash
# Health
curl http://localhost:8000/api/v1/health

# Query
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Qué es RAG?"}'

# Query con streaming
curl -X POST http://localhost:8000/api/v1/query/stream \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Qué es Python?"}'

# Ingestar archivo
curl -X POST http://localhost:8000/api/v1/ingest/file \
  -H "Content-Type: application/json" \
  -d '{"file_path": "./docs/test.pdf"}'

# Métricas
curl http://localhost:8000/api/v1/metrics
```

---

## ⚠️ Manejo de Errores

### Errores HTTP

| Código | Significado | Ejemplo |
|--------|-------------|---------|
| 200 | Éxito | Consulta completada |
| 404 | No encontrado | Archivo/directorio no existe |
| 422 | Error de validación | Pregunta vacía, top_k inválido |
| 500 | Error interno | Error en LLM, ChromaDB, etc. |

### Response de Error

```json
{
  "detail": "Error executing query: LLM generation failed"
}
```

### Ejemplo en Python

```python
import requests
from requests.exceptions import HTTPError

try:
    response = requests.post(
        f"{BASE_URL}/query",
        json={"question": ""}  # Inválido
    )
    response.raise_for_status()
except HTTPError as e:
    if e.response.status_code == 422:
        print("Error de validación:", e.response.json())
    elif e.response.status_code == 500:
        print("Error interno:", e.response.json())
```

---

## 🔧 Configuración

### Variables de Entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `API_HOST` | `0.0.0.0` | Host para el servidor |
| `API_PORT` | `8000` | Puerto para el servidor |
| `LLAMA_CPP_MODEL_PATH` | `./models/...` | Ruta al modelo GGUF |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Modelo de embeddings |
| `TOP_K_DOCUMENTS` | `4` | Documentos a recuperar |
| `N_CTX` | `4096` | Contexto máximo (tokens) |
| `N_GPU_LAYERS` | `0` | Capas en GPU (0=CPU) |

### CORS

La API soporta CORS. Para configurar orígenes permitidos, edita `fastapi_adapter.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://tudominio.com"],  # Cambiar según necesidades
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📊 Rendimiento

### Latencia Típica

| Operación | Latencia |
|-----------|----------|
| Health check | < 10ms |
| Query (sin streaming) | 2-5s |
| Query (streaming, primer token) | 500-1000ms |
| Ingest archivo (100 páginas) | 5-10s |

### Optimización

- **Streaming:** Usa `/query/stream` para mejor UX en respuestas largas
- **top_k:** Reduce `top_k` para menor latencia (menos contexto)
- **GPU:** Configura `N_GPU_LAYERS=35` si tienes GPU NVIDIA

---

## 🧪 Tests

```bash
# Ejecutar tests de API
pytest tests/integration/test_api.py -v

# Cobertura
pytest tests/integration/test_api.py --cov=src.infrastructure.entrypoints
```

---

## 📚 Recursos

- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **OpenAPI Spec:** https://www.openapis.org/
- **Server-Sent Events:** https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events

---

**Versión:** 1.0.0  
**Última actualización:** 25 de marzo 2026
