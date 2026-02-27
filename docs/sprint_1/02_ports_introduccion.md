# SPRINT 1: Introducción a los PORTS (Interfaces)

## 📖 ¿Qué son los PORTS?

Los **Ports** son **interfaces** (contratos) que definen **QUÉ operaciones el sistema necesita**, sin especificar **CÓMO hacerlas**.

### Analogía del Mundo Real

Imagina un restaurante:
- **Port**: "Necesitamos un PROVEEDOR DE INGREDIENTES"
- **Adapter**: Un proveedor específico (Mercado XYZ, Huerto Local, etc)

El restaurante (aplicación) no necesita saber DÓNDE vienen los ingredientes, solo que alguien los proporciona según el contrato.

```
┌─────────────────────────────────┐
│   RAGService (Aplicación)       │
│                                 │
│  "Necesito un DocumentStore"    │
│  "Necesito un EmbeddingModel"   │
│  "Necesito un LLM"              │
│  "Necesito un DocumentLoader"   │
└────────────┬────────────────────┘
             │
    ┌────────┴────────┬────────────┬────────────┐
    │                 │            │            │
    ▼                 ▼            ▼            ▼
┌─────────────┐ ┌──────────┐ ┌────────┐ ┌──────────┐
│ChromaDB     │ │HF        │ │Ollama  │ │LangChain │
│Adapter      │ │Embedding │ │LLM     │ │Loader    │
│             │ │Adapter   │ │Adapter │ │Adapter   │
│Implementa   │ │          │ │        │ │          │
│DocumentStore│ │Implementa│ │Implementa│Implementa│
│Port         │ │Embedding │ │LLMPort  │DocumentLo│
│             │ │Port      │ │        │ │aderPort │
└─────────────┘ └──────────┘ └────────┘ └──────────┘
```

---

## 📋 Los 4 Puertos del Dominio

En nuestro sistema RAG, hay 4 puertos principales:

### 1. **DocumentStorePort** - Almacenamiento de Documentos

**Ubicación:** `src/domain/ports/document_store_port.py`

**¿Qué hace?** Abstrae la Base de Datos Vectorial.

**Métodos esperados:**
```python
class DocumentStorePort(ABC):
    def add_documents(self, documents: List[Document]) -> List[str]:
        """Agrega documentos y retorna sus IDs"""
        pass
    
    def search_documents(self, query_embedding: List[float], k: int = 4) -> List[Document]:
        """Busca documentos similares a un embedding"""
        pass
    
    def delete_document(self, document_id: str):
        """Elimina un documento por ID"""
        pass
```

**¿Por qué existe?** Para que RAGService pueda almacenar y buscar sin saber si estamos usando ChromaDB, Pinecone, o cualquier otra BD.

**Adapter que lo implementa:** `ChromaDBAdapter` (SPRINT 3)

---

### 2. **EmbeddingPort** - Generador de Embeddings

**Ubicación:** `src/domain/ports/embedding_port.py`

**¿Qué hace?** Convierte texto en vectores de números.

**Métodos esperados:**
```python
class EmbeddingPort(ABC):
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Genera embeddings para múltiples textos"""
        pass
    
    def embed_query(self, text: str) -> List[float]:
        """Genera embedding para una query"""
        pass
```

**¿Por qué existe?** Para que RAGService busque documentos sin saber si usamos HF, OpenAI, Cohere, etc.

**Adapter que lo implementa:** `HFEmbeddingAdapter` (SPRINT 2)

---

### 3. **LLMPort** - Generador de Respuestas

**Ubicación:** `src/domain/ports/llm_port.py`

**¿Qué hace?** Genera texto basado en un prompt.

**Métodos esperados:**
```python
class LLMPort(ABC):
    def generate_answer(self, prompt: str) -> str:
        """Genera una respuesta basada en un prompt"""
        pass
```

**¿Por qué existe?** Para que RAGService genere respuestas sin saber si usamos Ollama, OpenAI, Anthropic, etc.

**Adapter que lo implementa:** `OllamaLLMAdapter` (SPRINT 2)

---

### 4. **DocumentLoaderPort** - Cargador de Documentos

**Ubicación:** `src/domain/ports/document_loader_port.py`

**¿Qué hace?** Carga documentos de archivos y los divide en chunks.

**Métodos esperados:**
```python
class DocumentLoaderPort(ABC):
    def load_documents(self, file_path: str) -> List[Document]:
        """Carga documentos de un archivo"""
        pass
    
    def split_documents(self, documents: List[Document], chunk_size: int = 512) -> List[Document]:
        """Divide documentos en chunks"""
        pass
```

**¿Por qué existe?** Para que RAGService cargue documentos sin saber si son CSV, PDF, TXT, etc.

**Adapter que lo implementa:** `LangChainLoaderAdapter` (SPRINT 2)

---

## 🔄 Flujo de Entrada vs Salida

Los puertos se dividen en dos categorías:

### **Puertos de ENTRADA** (A otras capas)
Localizados en `src/application/ports/`

**RagPort** (`src/application/ports/rag_port.py`)
```python
class RagPort(ABC):
    """Interface que expone RAGService a superior (CLI)"""
    
    def ingest_documents(self, file_paths: List[str]) -> List[str]:
        pass
    
    def query(self, question: str) -> Answer:
        pass
```

### **Puertos de SALIDA** (A capas externas)
Localizados en `src/domain/ports/`

- `DocumentStorePort` → ChromaDB, Pinecone, Weaviate, etc.
- `EmbeddingPort` → HF, OpenAI, Cohere, etc.
- `LLMPort` → Ollama, OpenAI, Anthropic, etc.
- `DocumentLoaderPort` → LangChain, PyPDF, Custom, etc.

---

## 📚 Próximas Guías en SPRINT 1

1. ✅ **01_models_guia_detallada.md** - Ya completada
2. 🔄 **02_ports_explicacion.md** - Estás aquí (overview)
3. ⏳ **03_ports_detallado.md** - Especificación completa de cada port
4. ⏳ **04_excepciones.md** - Manejo de errores
5. ⏳ **05_testing_models.md** - Tests unitarios

---

**Después de entender Models y Ports, estarás listo para SPRINT 2: Implementar los Adapters.** ✨
