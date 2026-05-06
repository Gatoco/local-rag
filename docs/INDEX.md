# Índice de Documentación - Sistema RAG Local

**Primera vez? Comienza aquí:**

## Para Arrancar Rápido
- 📖 **[QUICKSTART.md](QUICKSTART.md)** ← Comienza aquí para dejar funcionando en 5 minutos
  - Requisitos del sistema
  - 3 pasos para ejecutar
  - Resolución de problemas básicos

## Para Entender la Arquitectura
- 📖 **[README.md](README.md)** ← Guía técnica completa
  - Stack tecnológico detallado
  - Explicación del flujo RAG (ingesta → embeddings → recuperación → generación)
  - Buenas prácticas de rendimiento
  - Configuración avanzada

## Para Resolver Problemas
- 📖 **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** ← Soluciones a errores comunes
  - Error de Python 3.14 (detalles)
  - Ollama no disponible
  - Memoria insuficiente
  - ChromaDB no persiste
  - Customización del prompt

## Para Ver Lo Implementado
- 📖 **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** ← Resumen técnico
  - Cambios realizados
  - Stack validado
  - Tests pasando
  - Próximos pasos opcionales

---

## Guía de Lectura por Rol

### Yo solo quiero que funcione
```
1. QUICKSTART.md (5 min)
2. Ejecutar: python main.py
3. Si hay error → TROUBLESHOOTING.md
```

### Quiero personalizar la app
```
1. README.md (entender stack)
2. .env (cambiar configuración)
3. QUICKSTART.md (arrancar con cambios)
4. src/ (explorar código)
```

### Quiero entender todo en profundidad
```
1. README.md (arquitectura completa)
2. IMPLEMENTATION_SUMMARY.md (cambios técnicos)
3. docs/stack.md (stack detallado)
4. src/ (código fuente)
5. TROUBLESHOOTING.md (casos edge)
```

### Tengo un problema/error
```
1. TROUBLESHOOTING.md (soluciones indexadas)
2. .env (verificar configuración)
3. logs/ (si hay logs)
4. main.py stdout (mensajes de error)
```

---

## Archivos Clave

### Configuración
- `.env` - Variables de entorno (valores por defecto)
- `.env.example` - Plantilla comentada de configuración

### Documentación
- `README.md` - Guía técnica completa
- `QUICKSTART.md` - Inicio rápido
- `TROUBLESHOOTING.md` - Solución de problemas
- `IMPLEMENTATION_SUMMARY.md` - Resumen de lo implementado

### Código (Arquitectura Hexagonal)
- `main.py` - Punto de entrada
- `src/domain/` - Modelos (Document, Query, Answer)
- `src/application/` - Lógica RAG (RAGService)
- `src/infrastructure/adapters/` - Implementaciones concretas
- `src/infrastructure/entrypoints/` - CLI interactiva

### Tests
- `tests/unit/` - Tests unitarios (27/27 pasando)
- `tests/integration/` - Tests de integración RAG

### Dependencias
- `requirements.txt` - Paquetes Python (versionados)

---

## Comandos Útiles

```bash
# Activar entorno
source .venv/bin/activate

# Ejecutar app
python main.py

# Ejecutar tests
pytest tests/unit -q

# Ver qué documentos están indexados
ls -la chroma_db/

# Limpiar base de datos (para reingesta completa)
rm -rf chroma_db/

# Descargar nuevo modelo LLM
ollama pull neural-chat
```

---

## Soporte Rápido

| Problema | Solución |
|----------|----------|
| App no arranca | [QUICKSTART.md](QUICKSTART.md) → "Requisitos del Sistema" |
| "TypeError: 'function' object is not subscriptable" | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) → "Error: TypeError" |
| "Conexión rechazada a Ollama" | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) → "Error: Conexión rechazada" |
| Primera ejecución lenta | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) → "Primera ejecución lenta" |
| Respuestas genéricas | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) → "Respuestas genéricas" |
| Quiero cambiar modelo | [.env](.env) → OLLAMA_MODEL |

---

## Stack Validado

✓ Python 3.12  
✓ Ollama + mistral-nemo  
✓ ChromaDB 1.5.5  
✓ LangChain 0.3.28  
✓ Hugging Face Embeddings  
✓ 27 tests unitarios pasando  

**Estado: OPERATIVO Y TESTEADO**

---

Última actualización: 21 de marzo 2026
