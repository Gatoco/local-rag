# Guía de Uso: Sistema RAG Local con Documentos de Matemáticas

## 📚 Estado Actual

Tu sistema RAG ahora tiene **4843 fragmentos de documentos de matemáticas** indexados y listos para consultar.

### Documentos Cargados
✅ `Calculus.pdf` - Conceptos fundamentales de cálculo  
✅ `Laplace_Table.pdf` - Tablas y referencias de transformadas de Laplace  
✅ `calculo_diferencial_integral_func_una_var.pdf` - Cálculo diferencial e integral

---

## 🚀 Cómo Usar el Sistema

### 1. **Iniciar la Interfaz Interactiva**

```bash
python main.py
```

Verás algo como:
```
=== SISTEMA RAG LOCAL ===
✓ Embeddings listo (all-MiniLM-L6-v2 loaded)
✓ LLM listo (mistral-nemo initialized)
✓ ChromaDB listo (Chroma initialized)
[+] SISTEMA RAG OPERATIVO
```

### 2. **Comandos Disponibles**

#### `query <tu pregunta>`
Realiza una consulta RAG. El sistema buscará información en los documentos cargados.

**Ejemplos:**
```
> query ¿Cuáles son los conceptos fundamentales del cálculo diferencial?
> query Explica el concepto de derivada
> query ¿Qué es la integral indefinida?
> query Resumir la información sobre límites
```

**La respuesta incluye:**
- Explicación basada en los documentos
- Indicación de los documentos fuente utilizados

---

#### `ingest-file <ruta/archivo.pdf>`
Añade un nuevo documento individual al sistema.

**Ejemplo:**
```
> ingest-file ./docs_to_ingest/otro_documento.pdf
```

---

#### `ingest-dir <ruta/directorio>`
Añade todos los documentos de un directorio.

**Ejemplo:**
```
> ingest-dir ./docs_to_ingest/mas_matematicas
```

---

#### `help`
Muestra todos los comandos disponibles.

```
> help
```

---

#### `exit`
Sale del programa.

```
> exit
```

---

## 📊 Ejemplos de Consultas Efectivas

### Para obtener mejores respuestas, sé específico:

**❌ Vago:**
```
> query matemáticas
```

**✅ Específico:**
```
> query ¿Cuál es la definición formal de la derivada de una función?
```

**❌ Demasiado largo:**
```
> query ¿Puedes explicarme todo sobre cálculo, derivadas, integrales, límites y series?
```

**✅ Bien enfocado:**
```
> query Explica la relación entre derivadas e integrales
```

---

## 🔧 Configuración

El sistema usa estos parámetros (en `.env`):

```env
# Modelo del LLM
OLLAMA_MODEL=mistral-nemo

# Modelo de embeddings
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Tamaño de fragmentos de texto
CHUNK_SIZE=1000

# Número de documentos a recuperar
TOP_K_DOCUMENTS=4

# URL de Ollama
OLLAMA_BASE_URL=http://localhost:11434
```

Para cambiar algún parámetro, edita el archivo `.env` y reinicia `python main.py`.

---

## 💾 Datos Persistentes

- **Base de datos de vectores:** `./chroma_db/` 
  - Almacena los embeddings de todos los documentos
  - Puedes eliminar esta carpeta para limpiar la base de datos y empezar de cero

- **Índices:** Persistidos automáticamente
  - Cuando añadas documentos con `ingest-file` o `ingest-dir`, se guardan permanentemente

---

## 🐛 Troubleshooting

### "Error: Ollama no está disponible"
**Solución:** Inicia Ollama en otra terminal:
```bash
ollama serve
```

### "Error durante ingesta del documento"
- Verifica que el archivo PDF no esté corrupto
- Intenta con otro archivo PDF para descartar problemas del formato

### La respuesta no es relevante
- El LLM solo responde basándose en los documentos cargados
- Si la información no está en los PDFs, no podrá responder
- Añade más documentos relevantes con `ingest-dir`

---

## 📈 Próximas Acciones Sugeridas

1. **Prueba consultas diversas** sobre los temas en los PDFs
2. **Añade más documentos** si tienes otros materiales de matemáticas
3. **Ejecuta pruebas de integración:**
   ```bash
   python -m pytest tests/integration/
   ```

---

## 📝 Notas Técnicas

- **Modelo LLM local:** mistral-nemo (12.2B parámetros, cuantizado Q4_0)
- **Embeddings:** all-MiniLM-L6-v2 (384 dimensiones, ~22MB)
- **Vector store:** ChromaDB (base de datos vectorial abierta)
- **Framework:** LangChain 0.3.28 (compatible con Python 3.12)

---

¡Tu sistema RAG está completamente operativo! 🎉

Para preguntas adicionales, consulta los archivos en la carpeta `docs/`.
