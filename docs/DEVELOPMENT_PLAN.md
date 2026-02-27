# Plan de Desarrollo - Sistema RAG Local

## 1. Justificación del Enfoque

### ¿Por qué esta arquitectura?
La **arquitectura hexagonal** se eligió por varias razones estratégicas:

**1.1 Desacoplamiento de Capas**
- El dominio (lógica de negocio) está completamente separado de la infraestructura.
- Cambiar de Ollama a OpenAI o de ChromaDB a Pinecone NO requiere tocar la lógica central.
- Facilita testing: Podemos crear mocks de los adaptadores sin necesidad de servicios reales.

**1.2 Flexibilidad Tecnológica**
- Si en el futuro quieres cambiar el LLM, solo cambia el adaptador.
- Si necesitas otra base de datos vectorial, solo crea un nuevo adaptador.
- La aplicación permanece intacta.

**1.3 Escalabilidad**
- Cada componente tiene una responsabilidad clara.
- Facilita agregar nuevas funcionalidades sin romper existentes.
- Permite trabajo en paralelo: diferentes desarrolladores en diferentes adapters.

**1.4 Testabilidad**
- Cada componente es testeable independientemente.
- Los mocks reemplazan fácilmente a los adapters reales.
- Garantiza confiabilidad en producción.

---

## 2. Orden de Desarrollo Recomendado

### ¿Por qué esto es el orden correcto?

**Principio:** Desarrollar de "adentro hacia afuera", desde lo que NO depende de nada, hasta lo que depende de todo.

```
PASO 1: Domain (Core - Sin dependencias externas)
        ↓
PASO 2: Ports (Interfaces - Contratos entre capas)
        ↓
PASO 3: Adapters (Implementaciones concretas)
        ↓
PASO 4: Application Service (Orquestación)
        ↓
PASO 5: Entrypoint CLI (Interfaz de usuario)
```

---

## 3. Sprints Detallados

### SPRINT 0: Configuración y Setup (1-2 días)
**Objetivo:** Preparar el ambiente de desarrollo.

**Justificación:** Sin un environment limpio y bien configurado, los sprints posteriores sufren retrasos. Es inversión inicial que se recupera.

**Tareas:**

1. **Setup del Virtual Environment**
   - Crear `.venv` con Python 3.9+
   - Instalar dependencias base: `pip install langchain chromadb sentence-transformers`
   - Crear `requirements.txt` documentado
   - **Por qué:** Reproducibilidad, evitar conflictos de versiones.

2. **Verificación de Dependencias**
   - Comprobar que ChromaDB se instala correctamente
   - Verificar que HuggingFace Transformers funciona
   - Probar conexión a Ollama (si está instalado localmente)
   - **Por qué:** Detectar problemas temprano ahorra horas de debugging después.

3. **Estructura Final del Proyecto**
   - Organizar carpetas (data/raw, data/processed, logs, tests)
   - Crear `.gitignore` con `__pycache__`, `.venv`, `*.pyc`, archivos sensibles
   - Inicializar repo git si no existe
   - **Por qué:** Claridad desde el inicio, facilita colaboración.

4. **Documentación Base**
   - Este documento (DEVELOPMENT_PLAN.md) ✓
   - README.md con instrucciones de setup
   - **Por qué:** Onboarding más rápido para nuevos desarrolladores.

**Entregables:**
- Environment activado y funcional
- `requirements.txt` actualizado
- Estructura de carpetas lista

---

### SPRINT 1: Dominio y Puertos (2-3 días)
**Objetivo:** Definir la estructura fundamental del sistema.

**Justificación:** El dominio y los puertos son el "contrato" que el resto del código debe cumplir. Si están bien definidos, todo lo demás fluye naturalmente.

**Tareas:**

1. **Completar Domain Models** (`src/domain/models.py`)
   
   ```python
   @dataclass
   class Document:
       page_content: str
       metadata: Dict[str, Any] = field(default_factory=dict)
       id: Optional[str] = None
   
   @dataclass
   class Query:
       text: str
   
   @dataclass
   class Answer:
       text: str
       source_documents: List[Document] = field(default_factory=list)
   ```
   
   **Por qué estos modelos:**
   - `Document`: Abstracción de cualquier contenido textual con metadatos.
   - `Query`: Simplifica la interfaz de consulta.
   - `Answer`: Garantiza que cada respuesta incluye fuentes (trazabilidad).

2. **Revisar y Documentar Ports**
   
   Ya existen:
   - `DocumentStorePort` → Interfaz para almacenamiento vectorial
   - `EmbeddingPort` → Interfaz para generación de embeddings
   - `LLMPort` → Interfaz para LLMs
   - `DocumentLoaderPort` → Interfaz para carga de documentos
   
   **Tarea:** Documentar cada método con ejemplos de uso.
   **Por qué:** El resto del equipo entenderá QUÉ es obligatorio implementar sin necesidad de explicar verbalmente.

3. **Crear Port de Excepciones Personalizadas**
   
   ```python
   # src/domain/exceptions.py
   class RAGException(Exception):
       """Excepción base del sistema RAG"""
       pass
   
   class DocumentNotFoundError(RAGException):
       """Documento no encontrado en la base de datos"""
       pass
   
   class EmbeddingError(RAGException):
       """Error en la generación de embeddings"""
       pass
   ```
   
   **Por qué:** Manejo de errores consistente, permite que la aplicación responda inteligentemente a fallos.

**Entregables:**
- `models.py` completo y documentado
- Todos los puertos con docstrings detallados
- `exceptions.py` con casos de error cubiertos

---

### SPRINT 2: Adaptadores - Primera Onda (3-4 días)
**Objetivo:** Implementar adaptadores sin lógica compleja. Empezar por lo más simple.

**Justificación:** Los adaptadores son el "pegamento" entre el dominio y las tecnologías reales. Implementarlos permite testing de capas internas.

**Orden de Implementación (de menor a mayor complejidad):**

1. **HFEmbeddingAdapter** (Menor complejidad)
   
   ```python
   from sentence_transformers import SentenceTransformer
   
   class HFEmbeddingAdapter(EmbeddingPort):
       def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
           self.model = SentenceTransformer(model_name)
       
       def embed_documents(self, texts: List[str]) -> List[List[float]]:
           return self.model.encode(texts, convert_to_tensor=False).tolist()
       
       def embed_query(self, text: str) -> List[float]:
           return self.model.encode([text], convert_to_tensor=False)[0].tolist()
   ```
   
   **Por qué primero:** Es una simple envoltura de un modelo de HF. Sin estado, sin conexiones.

2. **DocumentLoaderAdapter** (Baja complejidad)
   
   ```python
   from langchain.document_loaders import CSVLoader, PDFPlumberLoader
   from langchain.text_splitter import RecursiveCharacterTextSplitter
   
   class LangChainLoaderAdapter(DocumentLoaderPort):
       def load_documents(self, file_path: str) -> List[Document]:
           # Detectar tipo de archivo y cargar
           # Convertir a nuestro modelo Document
           pass
       
       def split_documents(self, documents: List[Document], chunk_size: int = 512) -> List[Document]:
           # Dividir en chunks con overlap
           pass
   ```
   
   **Por qué segundo:** Depende de HFEmbeddingAdapter conceptualmente, pero no en código real.

3. **OllamaLLMAdapter** (Baja complejidad - si Ollama está disponible)
   
   ```python
   import ollama
   
   class OllamaLLMAdapter(LLMPort):
       def __init__(self, model_name: str = "llama2"):
           self.model_name = model_name
           # Verificar disponibilidad
       
       def generate_answer(self, prompt: str) -> str:
           response = ollama.generate(model=self.model_name, prompt=prompt)
           return response['response']
   ```
   
   **Por qué tercero:** Depende de que Ollama esté corriendo localmente.

**Testing en esta fase:**
```python
# tests/unit/test_hf_embedding_adapter.py
def test_embed_documents():
    adapter = HFEmbeddingAdapter()
    embeddings = adapter.embed_documents(["Hola mundo", "Adiós mundo"])
    assert len(embeddings) == 2
    assert len(embeddings[0]) == 384  # Dimensión de all-MiniLM-L6-v2

def test_embed_query():
    adapter = HFEmbeddingAdapter()
    embedding = adapter.embed_query("¿Qué es la IA?")
    assert isinstance(embedding, list)
    assert len(embedding) == 384
```

**Entregables:**
- `HFEmbeddingAdapter` implementado y testeado ✓
- `LangChainLoaderAdapter` implementado y testeado ✓
- `OllamaLLMAdapter` implementado y testeado ✓
- Suite de tests unitarios para cada adapter

---

### SPRINT 3: Adaptadores - Segunda Onda (3-4 días)
**Objetivo:** Implementar el adaptador más complejo: ChromaDB.

**Justificación:** ChromaDBAdapter es complejo porque:
- Requiere estado persistente (base de datos en disco).
- Depende de EmbeddingPort para generar embeddings.
- Es el "corazón" del almacenamiento de documentos.

1. **ChromaDBAdapter**
   
   ```python
   import chromadb
   
   class ChromaDBAdapter(DocumentStorePort):
       def __init__(self, embedding_model: EmbeddingPort, persist_dir: str = "./chroma_db"):
           self.embedding_model = embedding_model
           self.persist_dir = persist_dir
           self.client = chromadb.Client(
               chromadb.config.Settings(
                   chroma_db_impl="duckdb+parquet",
                   persist_directory=persist_dir,
                   anonymized_telemetry=False
               )
           )
           self.collection = None
       
       def add_documents(self, documents: List[Document]) -> List[str]:
           # 1. Generar embeddings para cada documento
           # 2. Preparar metadatos
           # 3. Agregar a ChromaDB con ID
           # 4. Persistir
           # 5. Retornar IDs
           pass
       
       def search_documents(self, query_embedding: List[float], k: int = 4) -> List[Document]:
           # 1. Buscar en ChromaDB con similitud
           # 2. Recuperar documentos
           # 3. Convertir a nuestro modelo
           # 4. Retornar
           pass
       
       def delete_document(self, document_id: str):
           # 1. Eliminar de ChromaDB
           # 2. Persistir
           pass
   ```
   
   **Por qué aquí:** Ahora tenemos HFEmbeddingAdapter listo para inyectar.

**Testing:**
```python
def test_add_and_search_documents():
    embedding_adapter = HFEmbeddingAdapter()
    store_adapter = ChromaDBAdapter(embedding_adapter, persist_dir=":memory:")
    
    docs = [
        Document(page_content="Python es un lenguaje de programación"),
        Document(page_content="JavaScript se ejecuta en navegadores"),
    ]
    
    ids = store_adapter.add_documents(docs)
    assert len(ids) == 2
    
    # Buscar documentos similares a "lenguajes de programación"
    query_embedding = embedding_adapter.embed_query("lenguajes de programación")
    results = store_adapter.search_documents(query_embedding, k=1)
    
    assert len(results) == 1
    assert "Python" in results[0].page_content
```

**Entregables:**
- ChromaDBAdapter completamente implementado ✓
- Tests de integración con HFEmbeddingAdapter ✓
- Persistencia de datos verificada

---

### SPRINT 4: Aplicación - RAGService (2-3 días)
**Objetivo:** Implementar la orquestación central.

**Justificación:** Ahora que tenemos todos los adapters, el RAGService es lo que los "coreografía".

1. **RAGService - Implementación Completa**
   
   ```python
   class RAGService(RagPort):
       def __init__(
           self,
           document_store: DocumentStorePort,
           embedding_model: EmbeddingPort,
           llm_model: LLMPort,
           document_loader: DocumentLoaderPort
       ):
           self.document_store = document_store
           self.embedding_model = embedding_model
           self.llm_model = llm_model
           self.document_loader = document_loader
       
       def ingest_documents(self, file_paths: List[str]) -> List[str]:
           """
           Flujo:
           1. Cargar documentos desde archivos
           2. Dividir en chunks
           3. Crear embeddings para cada chunk
           4. Almacenar en ChromaDB
           5. Retornar IDs para tracking
           """
           all_ids = []
           for file_path in file_paths:
               raw_docs = self.document_loader.load_documents(file_path)
               chunked_docs = self.document_loader.split_documents(raw_docs)
               ids = self.document_store.add_documents(chunked_docs)
               all_ids.extend(ids)
           return all_ids
       
       def query(self, question: str) -> Answer:
           """
           Flujo RAG clásico:
           1. Crear embedding de la pregunta
           2. Buscar top-k documentos similares
           3. Construir prompt con contexto
           4. Generar respuesta con LLM
           5. Retornar respuesta + fuentes
           """
           # Paso 1: Embed la pregunta
           query_embedding = self.embedding_model.embed_query(question)
           
           # Paso 2: Buscar documentos relevantes
           relevant_docs = self.document_store.search_documents(query_embedding, k=4)
           
           # Paso 3: Construir prompt
           context = "\n".join([f"- {doc.page_content}" for doc in relevant_docs])
           prompt = f"""
           Contexto relevante:
           {context}
           
           Pregunta: {question}
           
           Responde basándote en el contexto proporcionado.
           """
           
           # Paso 4: Generar respuesta
           answer_text = self.llm_model.generate_answer(prompt)
           
           # Paso 5: Retornar con trazabilidad
           return Answer(text=answer_text, source_documents=relevant_docs)
   ```
   
   **Por qué así:**
   - Separa claramente el flujo de ingesta vs consulta.
   - Cada paso es independiente y testeable.
   - Fácil agregar logging, métricas, caché en cada paso.

**Testing de Integración:**
```python
def test_end_to_end_rag_flow():
    # Setup mocks
    embedding_adapter = HFEmbeddingAdapter()
    store_adapter = ChromaDBAdapter(embedding_adapter, persist_dir=":memory:")
    loader_adapter = LangChainLoaderAdapter()
    llm_adapter = OllamaLLMAdapter()  # o mock
    
    service = RAGService(store_adapter, embedding_adapter, llm_adapter, loader_adapter)
    
    # Ingestar documentos
    ids = service.ingest_documents(["data/raw/sample.csv"])
    assert len(ids) > 0
    
    # Hacer consulta
    answer = service.query("¿Cuál es el impacto financiero?")
    assert len(answer.text) > 0
    assert len(answer.source_documents) > 0
```

**Entregables:**
- RAGService completamente implementado ✓
- Métodos `ingest_documents` y `query` funcionales ✓
- Tests de integración de punta a punta ✓

---

### SPRINT 5: Interfaz de Usuario - CLI (2 días)
**Objetivo:** Hacer el sistema accesible a través de línea de comandos.

**Justificación:** La CLI es el "rostro" de la aplicación. Debe ser intuitiva y clara.

1. **CLIAdapter - Implementación Completa**
   
   ```python
   class CLIAdapter:
       def __init__(self, rag_service: RagPort):
           self.rag_service = rag_service
       
       def run(self):
           print("=" * 50)
           print("📚 Sistema RAG Local")
           print("=" * 50)
           print("\nComandos disponibles:")
           print("  ingest <file_paths>  - Cargar documentos")
           print("  query <question>     - Hacer una pregunta")
           print("  help                 - Mostrar esta ayuda")
           print("  exit                 - Salir\n")
           
           while True:
               try:
                   user_input = input("rag> ").strip()
                   
                   if not user_input:
                       continue
                   
                   parts = user_input.split(None, 1)
                   command = parts[0].lower()
                   args = parts[1] if len(parts) > 1 else ""
                   
                   if command == "ingest":
                       self._handle_ingest(args)
                   elif command == "query":
                       self._handle_query(args)
                   elif command == "help":
                       self._show_help()
                   elif command == "exit":
                       print("¡Hasta luego!")
                       break
                   else:
                       print(f"Comando desconocido: {command}")
               
               except KeyboardInterrupt:
                   print("\n¡Hasta luego!")
                   break
               except Exception as e:
                   print(f"Error: {e}")
       
       def _handle_ingest(self, file_paths_str: str):
           if not file_paths_str:
               print("Uso: ingest <ruta_archivo>")
               return
           
           file_paths = file_paths_str.split()
           print(f"Ingesting {len(file_paths)} archivo(s)...")
           
           try:
               ids = self.rag_service.ingest_documents(file_paths)
               print(f"✓ {len(ids)} documentos ingested exitosamente.")
           except Exception as e:
               print(f"✗ Error durante ingestión: {e}")
       
       def _handle_query(self, question: str):
           if not question:
               print("Uso: query <pregunta>")
               return
           
           print(f"\n🔍 Buscando: {question}\n")
           
           try:
               answer = self.rag_service.query(question)
               print(f"📝 Respuesta:\n{answer.text}\n")
               
               if answer.source_documents:
                   print("📚 Fuentes:")
                   for doc in answer.source_documents:
                       print(f"  - {doc.page_content[:100]}...")
               print()
           except Exception as e:
               print(f"✗ Error durante consulta: {e}\n")
   ```
   
   **Por qué así:**
   - Loop interactivo continuo.
   - Manejo de errores amigable.
   - Feedback visual claro.
   - Fácil de extender con más comandos.

2. **main.py - Orquestación Final**
   
   ```python
   def main():
       # 1. Inicializar adapters
       embedding_adapter = HFEmbeddingAdapter(model_name="sentence-transformers/all-MiniLM-L6-v2")
       store_adapter = ChromaDBAdapter(embedding_adapter, persist_directory="./chroma_db")
       llm_adapter = OllamaLLMAdapter(model_name="llama2")
       loader_adapter = LangChainLoaderAdapter()
       
       # 2. Inicializar servicio
       rag_service = RAGService(store_adapter, embedding_adapter, llm_adapter, loader_adapter)
       
       # 3. Inicializar CLI
       cli = CLIAdapter(rag_service)
       
       # 4. Ejecutar
       cli.run()
   
   if __name__ == "__main__":
       main()
   ```

**Entregables:**
- CLIAdapter completamente implementado ✓
- main.py con all wire-up ✓
- Sistema funcional end-to-end ✓

---

### SPRINT 6: Testing, Documentación y Optimización (2-3 días)
**Objetivo:** Asegurar calidad, documentar y optimizar.

**Justificación:** Sin tests y documentación, nadie más puede mantener el código. Sin optimización, fallará en producción.

1. **Testing**
   - Crear `tests/unit/` con tests para cada adapter.
   - Crear `tests/integration/` con tests de flujos completos.
   - Ejecutar con coverage: `pytest --cov=src tests/`
   - Objetivo: >80% code coverage.

2. **Documentación**
   - Docstrings en español para cada clase/método.
   - README.md actualizado con instrucciones de instalación.
   - Guía de uso en docs/.
   - Diagrama de arquitectura.

3. **Optimización**
   - Cachear embeddings para consultas frecuentes.
   - Batch processing para ingestión de muchos documentos.
   - Logging en detalle para debugging.

**Entregables:**
- Suite de tests completa ✓
- >80% code coverage ✓
- Documentación actualizada ✓
- Sistema optimizado ✓

---

## 4. Cronograma Visual

```
Semana 1:
├── SPRINT 0: Setup (Día 1-2)
│   └── Environment listo ✓
│
├── SPRINT 1: Domain & Ports (Día 2-3)
│   └── Modelos y contratos definidos ✓
│
└── SPRINT 2: Adapters - Primera Onda (Día 3-5)
    └── HF Embedding, LangChain Loader, Ollama LLM ✓

Semana 2:
├── SPRINT 3: Adapters - Segunda Onda (Día 1-3)
│   └── ChromaDB Adapter ✓
│
├── SPRINT 4: RAGService (Día 3-4)
│   └── Orquestación funcional ✓
│
└── SPRINT 5: CLI (Día 4-5)
    └── Sistema interactivo ✓

Semana 3:
└── SPRINT 6: Testing & Docs (Día 1-2)
    └── Calidad y mantenibilidad ✓
```

**Tiempo Total Estimado:** 10-12 días de desarrollo dedicado.

---

## 5. Decisiones Arquitéctonicas Clave

### 5.1 ¿Por qué no un monolito?

**Alternativa Rechazada:** Código todo en un archivo (`rag.py`).

**Por qué no:** 
- No testeable.
- No escalable.
- Cambios tecnológicos = reescribir todo.
- Imposible colaboración.

**Nuestra Solución:** Arquitectura hexagonal = cada pieza independiente.

---

### 5.2 ¿Por qué DocumentLoaderPort?

**Alternativa:** Cargar documentos directamente en main.py.

**Por qué ImportPorts:**
- Abstrae la complejidad de LangChain.
- Si cambias de loader (LangChain → PyPDF → Custom), no changes the app.
- Testeable sin necesidad de archivos reales.

---

### 5.3 ¿Por qué EmbeddingPort separado?

**Alternativa:** Embeddings dentro de DocumentStorePort.

**Por qué separados:**
- El dominio y la app necesitan embeddings para búsqueda, no solo almacenamiento.
- RAGService.query() llama directamente a EmbeddingPort para la query.
- Permite usar el mismo modelo de embeddings en múltiples lugares.

---

### 5.4 ¿Por qué guardar fuentes en Answer?

**Alternativa:** Retornar solo el texto de la respuesta.

**Por qué incluir fuentes:**
- Trazabilidad: el usuario sabe en qué se basó la respuesta.
- Auditoría: puedes rastrear si los documentos cambiaron.
- Confianza: las respuestas con fuentes son más creíbles.

---

## 6. Checklist de Desarrollo

Usa esto para rastrear progreso:

```
SPRINT 0: Setup
☐ .venv creado y activado
☐ requirements.txt completo
☐ .gitignore en lugar
☐ Carpetas data/{raw,processed} creadas
☐ README.md base escrito

SPRINT 1: Domain & Ports
☐ models.py finalizado con docstrings
☐ Todos los Ports documentados
☐ exceptions.py creado
☐ Ejemplos de uso en docstrings

SPRINT 2: Adapters onda 1
☐ HFEmbeddingAdapter implementado
☐ HFEmbeddingAdapter testeado
☐ LangChainLoaderAdapter implementado
☐ LangChainLoaderAdapter testeado
☐ OllamaLLMAdapter implementado
☐ OllamaLLMAdapter testeado

SPRINT 3: Adapters onda 2
☐ ChromaDBAdapter implementado
☐ add_documents() funcional
☐ search_documents() funcional
☐ delete_document() funcional
☐ Tests de integración pasando

SPRINT 4: RAGService
☐ ingest_documents() completo
☐ query() completo
☐ Tests e2e pasando
☐ Logging agregado

SPRINT 5: CLI
☐ CLIAdapter completamente implementado
☐ main.py orchestration funcional
☐ Todos los comandos testeados manualmente

SPRINT 6: Polish
☐ Coverage >80%
☐ Documentación completa
☐ Performance optimizado
☐ Listo para producción
```

---

## 7. Próximos Pasos Opcionales (Post-MVP)

Después de completar los 6 sprints, considera:

1. **API REST:** Exponer el RAG a través de FastAPI.
2. **Caché de Embeddings:** Redis para mejorar performance.
3. **Multi-usuario:** Soporte para múltiples colecciones de documentos.
4. **Analytics:** Dashboard de consultas más comunes.
5. **Fine-tuning:** Entrenar embeddings con datos específicos del dominio.
6. **Exportar Respuestas:** PDF, Word con historial.

---

## Resumen

**El flujo es:** Setup → Domain → Puertos → Adapters → Servicio → CLI → Testing → Documentación.

**Cada sprint genera deliverables tangibles y testeables.**

**Al final: Un sistema RAG completamente funcional, escalable y mantenible.**

Estás construyendo infraestructura para IA sobre fundaciones sólidas. 🚀
