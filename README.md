# Sistema RAG Local

Un sistema completo de **Generación Aumentada por Recuperación (RAG)** basado en arquitectura hexagonal, que funciona completamente local sin dependencias en servicios en la nube.

## 🚀 Características

- ✅ **100% Local**: Sin envío de datos a servicios externos
- ✅ **Arquitectura Hexagonal**: Código desacoplado y mantenible
- ✅ **LLMs Locales**: Integración con Ollama (Llama 2, Mistral, etc.)
- ✅ **Vector Database**: ChromaDB para búsqueda semántica eficiente
- ✅ **Embeddings Inteligentes**: HuggingFace Sentence Transformers
- ✅ **Múltiples Formatos**: Soporta CSV, PDF, DOCX, XLSX, TXT
- ✅ **CLI Interactiva**: Interfaz amigable de línea de comandos

## 📋 Requisitos Previos

- **Python 3.9+**
- **Ollama** instalado y ejecutándose localmente (descarga desde [ollama.ai](https://ollama.ai))
- **Git**

## 🔧 Instalación

### 1. Clonar el Repositorio

```bash
git clone <tu-repo>
cd local-rag
```

### 2. Crear Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# o
.venv\Scripts\activate  # Windows
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Descargar Modelo Ollama (Opcional)

Si aún no tienes Ollama instalado:

```bash
ollama pull llama2
# o
ollama pull mistral
```

## 📖 Uso Rápido

### Iniciar la Aplicación

```bash
python main.py
```

### Comandos Disponibles

```
ingest <ruta_archivo>  - Cargar documentos
  Ejemplo: ingest data/raw/sample.csv

query <pregunta>       - Hacer una pregunta
  Ejemplo: query ¿Cuál es el impacto financiero?

help                   - Mostrar ayuda

exit                   - Salir
```

## 📁 Estructura del Proyecto

```
local-rag/
├── src/
│   ├── domain/                      # Core del negocio (sin dependencias externas)
│   │   ├── models.py               # Document, Query, Answer
│   │   ├── ports/                  # Interfaces (contratos)
│   │   └── exceptions.py
│   ├── application/                # Lógica de aplicación
│   │   ├── services/               # RAGService (orquestación)
│   │   └── ports/                  # Puerto de entrada
│   └── infrastructure/             # Implementaciones concretas
│       ├── adapters/               # ChromaDB, Ollama, HF Embeddings, LangChain
│       └── entrypoints/            # CLI
├── data/
│   ├── raw/                        # Documentos originales
│   └── processed/                  # Documentos procesados
├── docs/                           # Documentación
├── tests/
│   ├── unit/                       # Tests unitarios
│   └── integration/                # Tests de integración
├── logs/                           # Archivos de log
├── main.py                         # Punto de entrada
├── requirements.txt                # Dependencias Python
└── README.md                       # Este archivo
```

## 🏗️ Arquitectura

El proyecto implementa **Arquitectura Hexagonal (Ports & Adapters)**:

```
┌─────────────────────────────────────┐
│         CLI Adapter (Entrada)       │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│     RAGService (Orquestación)       │
└─────────────────┬───────────────────┘
                  │
        ┌─────────┼─────────┬─────────┐
        │         │         │         │
   ┌────▼──┐ ┌───▼──┐ ┌───▼──┐ ┌───▼──┐
   │ChromaDB  HF Embed  Ollama  LangChain
   └────────┘ └───────┘ └──────┘ └───────┘
```

**Ventajas:**
- Cambiar de infraestructura sin tocar la lógica de negocio
- Fácil testing con mocks
- Código escalable y mantenible

## 📚 Documentación Detallada

- [Stack Tecnológico](docs/stack.md) - Explicación de cada framework
- [Plan de Desarrollo](docs/DEVELOPMENT_PLAN.md) - Sprints y roadmap completo

## 🧪 Testing

Ejecutar tests:

```bash
pytest tests/
```

Con coverage:

```bash
pytest --cov=src tests/
```

## 🔍 Flujo RAG

1. **Ingestión**: Documentos → Cargador → Dividir en chunks → Generar embeddings → ChromaDB
2. **Consulta**: Query → Embedding → Búsqueda en ChromaDB → Contexto → LLM → Respuesta

## ⚙️ Configuración

Variables de entorno (crear `.env`):

```
# Modelo LLM
OLLAMA_MODEL=llama2
OLLAMA_BASE_URL=http://localhost:11434

# Embeddings
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# ChromaDB
CHROMA_DB_PATH=./chroma_db

# Búsqueda
TOP_K_DOCUMENTS=4
```

## 🚨 Troubleshooting

### Error: "Conexión a Ollama rechazada"

```bash
# Verificar que Ollama está ejecutándose
ollama serve
```

### Error: "No suitable CUDA-capable device found"

Asegúrate de que tienes CUDA si quieres aceleración GPU. Sin GPU funciona pero más lentamente.

### Error: "módulo no encontrado"

```bash
# Reactivar el venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 📊 Performance

- **Embeddings**: ~50ms por documento (GPU) / ~200ms (CPU)
- **Búsqueda**: ~10ms en 1000 documentos
- **Generación**: Depende del modelo LLM (Llama2: ~5-10 palabras/seg en CPU)

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

MIT License - Ver `LICENSE` para detalles

## 💡 Próximos Pasos

- [ ] API REST con FastAPI
- [ ] Soporte multi-usuario
- [ ] Dashboard de analytics
- [ ] Fine-tuning de embeddings
- [ ] Caché con Redis
- [ ] Exportación de respuestas (PDF, Word)

## 📞 Soporte

Para questions o issues, abre un GitHub Issue.

---

**Construido con ❤️ usando LangChain + ChromaDB + Ollama**
