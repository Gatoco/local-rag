# SPRINT 1: Verificación y Testing de Models

## ✅ Checklist de Implementación

Después de escribir `models.py`, completa estos pasos:

### Paso 1: Verificar que el archivo existe y es válido

```bash
cd /home/iwakura/Documentos/github-proyects/local-rag

# Activar venv
source .venv/bin/activate

# Verificar que el archivo existe
ls -la src/domain/models.py

# Verificar que es válido (imports, sintaxis)
python -c "from src.domain.models import Document, Query, Answer; print('✓ Imports OK')"
```

**Salida esperada:**
```
✓ Imports OK
```

---

### Paso 2: Probar manualmente los modelos

```bash
source .venv/bin/activate

python << 'EOF'
from src.domain.models import Document, Query, Answer

# Test 1: Crear un Document
doc = Document(
    page_content="Python es un lenguaje de programación",
    metadata={"fuente": "wikipedia"},
    id="doc_001"
)
print("✓ Document creado:", doc.page_content[:30] + "...")

# Test 2: Crear una Query
query = Query(text="¿Qué es Python?")
print("✓ Query creada:", query.text)

# Test 3: Crear una Answer con documentos fuente
answer = Answer(
    text="Python es un lenguaje...",
    source_documents=[doc]
)
print("✓ Answer creada con", len(answer.source_documents), "documento(s)")

print("\n✅ Todos los modelos funcionan correctamente")
EOF
```

**Salida esperada:**
```
✓ Document creado: Python es un lenguaje...
✓ Query creada: ¿Qué es Python?
✓ Answer creada con 1 documento(s)

✅ Todos los modelos funcionan correctamente
```

---

### Paso 3: Ejecutar los Tests Unitarios

```bash
source .venv/bin/activate

# Ejecutar todos los tests de models
pytest tests/unit/test_models.py -v

# O verlos en forma resumida
pytest tests/unit/test_models.py
```

**Salida esperada (~40-50 tests):**
```
tests/unit/test_models.py::TestDocument::test_document_creation_minimal PASSED
tests/unit/test_models.py::TestDocument::test_document_creation_with_metadata PASSED
tests/unit/test_models.py::TestDocument::test_document_creation_with_id PASSED
... (más tests)

====== 45 passed in 0.34s ======
```

---

### Paso 4: Ejecutar tests con Coverage

```bash
source .venv/bin/activate

# Ver qué porcentaje del código está testeado
pytest tests/unit/test_models.py --cov=src.domain.models --cov-report=term

# O generar reporte HTML (más bonito)
pytest tests/unit/test_models.py --cov=src.domain.models --cov-report=html
# Luego abrir: htmlcov/index.html en el navegador
```

**Salida esperada:**
```
src/domain/models.py    89      0    100%
==== 45 passed ====
Coverage: 100%
```

---

### Paso 5: Ejecutar todos los tests (si los hay)

```bash
source .venv/bin/activate

# Todos los tests
pytest tests/ -v

# Con coverage
pytest tests/ --cov=src --cov-report=term
```

---

## 🐛 Troubleshooting

### Error: `ModuleNotFoundError: No module named 'src'`

**Solución:** Asegúrate de ejecutar el comando desde la raíz del proyecto:
```bash
cd /home/iwakura/Documentos/github-proyects/local-rag
python -c "from src.domain.models import Document"
```

### Error: `No module named 'pytest'`

**Solución:** Instala pytest (ya debería estar en requirements.txt):
```bash
source .venv/bin/activate
pip install pytest pytest-cov
```

### Error: `dataclasses` no encontrado

**Solución:** `dataclasses` es parte de stdlib desde Python 3.7. Verifica tu versión:
```bash
python --version  # Debe ser 3.9+
```

---

## 📊 Resultados Finales Esperados

Después de completar SPRINT 1, deberías tener:

✅ **`src/domain/models.py`**
- 3 modelos: Document, Query, Answer
- Cada uno con docstring completo
- Type hints correctos
- Funcional y testeado

✅ **`tests/unit/test_models.py`**
- 45+ tests
- Coverage 100% en models.py
- Todos los tests pasando

✅ **Documentación**
- Guía completa en `docs/sprint_1/`
- Explicación línea por línea
- Ejemplos de uso
- Errores comunes

✅ **Entendimiento**
- Sabes QUÉ son dataclasses
- Entiendes type hints
- Comprendes por qué cada modelo existe

---

## 🚀 Próximo Sprint

Después de SPRINT 1, estarás listo para:

**SPRINT 2: Implementar los Adapters**
- HFEmbeddingAdapter
- LangChainLoaderAdapter
- OllamaLLMAdapter

---

## ✨ Felicidades

Si completaste esto, **entiendes el corazón del sistema RAG.** 

Los modelos son los cimientos. Todo lo demás se construye sobre ellos.

**¡Adelante al SPRINT 2!** 🎯
