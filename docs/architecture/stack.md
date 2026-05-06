# Stack Tecnológico - Sistema RAG Local

## Descripción General

Este proyecto implementa un sistema de **Generación Aumentada por Recuperación (RAG)** completamente local, utilizando una arquitectura hexagonal. El stack está diseñado para funcionar sin dependencias de servicios externos en la nube, permitiendo máxima privacidad y control.

---

## Componentes del Stack

### 1. **Ollama**
**Categoría:** Large Language Model (LLM) Local  
**Propósito:** Ejecutar modelos de lenguaje grandes de manera local.

- Permite ejecutar LLMs (como Llama 2, Mistral, etc.) directamente en el servidor sin enviar datos a servicios externos.
- Proporciona una API REST simple para interactuar con los modelos.
- Ideal para privacidad y latencia baja.

**En el proyecto:** `OllamaLLMAdapter` se comunica con Ollama para generar respuestas contextualizadas.

---

### 2. **ChromaDB**
**Categoría:** Vector Database  
**Propósito:** Almacenar y buscar documentos mediante búsqueda vectorial (similitud semántica).

- Base de datos vectorial optimizada para embeddings de alta dimensión.
- Soporta búsqueda por similitud coseno rápida y eficiente.
- Puede persistir datos en disco para reutilización.
- Ligera y fácil de integrar, sin necesidad de servidor separado.

**En el proyecto:** `ChromaDBAdapter` maneja el almacenamiento de documentos procesados y la búsqueda de documentos relevantes según una consulta de usuario.

---

### 3. **HuggingFace / Sentence Transformers**
**Categoría:** Text Embedding Models  
**Propósito:** Convertir texto a representaciones vectoriales (embeddings).

- Proporciona modelos pre-entrenados de transformers que generan embeddings semánticamente significativos.
- El modelo `sentence-transformers/all-MiniLM-L6-v2` es ligero, rápido y preciso para búsqueda de similitud.
- Permite identificar documentos relevantes comparando la similitud semántica de la consulta con los documentos almacenados.

**En el proyecto:** `HFEmbeddingAdapter` genera embeddings para:
- Documentos ingested (para almacenamiento en ChromaDB)
- Consultas del usuario (para búsqueda de documentos similares)

---

### 4. **LangChain**
**Categoría:** Framework de Aplicaciones de IA  
**Propósito:** Simplificar la carga, división y procesamiento de documentos.

- Proporciona utilidades para cargar documentos de múltiples formatos (PDF, TXT, CSV, etc.).
- Incluye capacidades de división de documentos en chunks para procesamiento eficiente.
- Facilita la integración entre componentes de IA (LLMs, embeddings, vectorstores).

**En el proyecto:** `LangChainLoaderAdapter` se encarga de:
- Cargar documentos desde rutas de archivo.
- Dividir documentos grandes en chunks manejables.

---

### 5. **Arquitectura Hexagonal (Ports & Adapters)**
**Categoría:** Patrón Arquitectónico  
**Propósito:** Desacoplar la lógica de negocio de detalles técnicos de implementación.

Permite que el proyecto sea flexible, testeable y fácil de mantener.

**Capas:**
- **Domain (Dominio):** Lógica pura, independiente de tecnologías externas. Define puertos (interfaces).
- **Application (Aplicación):** Servicios que orquestan el flujo de negocio.
- **Infrastructure (Infraestructura):** Adaptadores concretos que implementan los puertos (ChromaDB, Ollama, etc.).

**Ventajas:**
- Cambiar de Ollama a OpenAI sin modificar la lógica de negocio.
- Cambiar de ChromaDB a Pinecone o Weaviate sin afectar la aplicación.
- Facilita testing con mocks.

---

## Flujo de Integración

```
Usuario (CLI)
    ↓
CLIAdapter (Entrada)
    ↓
RAGService (Orquestación - Dominio de Aplicación)
    ├─→ DocumentLoaderAdapter (LangChain) → Carga documentos
    ├─→ EmbeddingAdapter (HuggingFace) → Genera embeddings
    ├─→ DocumentStoreAdapter (ChromaDB) → Almacena y busca
    └─→ LLMAdapter (Ollama) → Genera respuestas
    ↓
CLIAdapter (Salida)
    ↓
Usuario (Respuesta con contexto)
```

---

## Dependencias Principales

| Framework/Librería | Versión | Rol |
|---|---|---|
| **LangChain** | ≥0.1.0 | Carga y procesamiento de documentos |
| **ChromaDB** | ≥0.3.0 | Base de datos vectorial |
| **Ollama** | (Externo) | Modelo de lenguaje local |
| **HuggingFace/Transformers** | ≥4.30.0 | Modelos de embeddings |
| **Sentence Transformers** | ≥2.2.0 | Embeddings semánticos |
| **Python** | ≥3.9 | Runtime |

---

## Ventajas de Este Stack

✅ **Privacidad Total:** Todo funciona localmente. Los datos nunca salen del servidor.  
✅ **Sin costos de API:** No depende de servicios en la nube caros.  
✅ **Bajo latency:** Ejecución local sin roundtrips de red.  
✅ **Flexible:** Fácil cambiar componentes gracias a la arquitectura hexagonal.  
✅ **Escalable:** ChromaDB y LangChain manejan gran volumen de documentos.  
✅ **Mantenible:** Código desacoplado, testeable, con responsabilidades claras.

---

## Posibles Extensiones

- **Alternativa a Ollama:** OpenAI API, Anthropic Claude, Hugging Face Inference API.
- **Alternativa a ChromaDB:** Pinecone, Weaviate, Milvus, elasticsearch.
- **Alternativa a HuggingFace:** OpenAI Embeddings, Cohere.
- **Cacheo:** Redis para cachear embeddings y respuestas frecuentes.
- **Monitoreo:** Logging avanzado, métricas de relevancia, análisis de consultas.
