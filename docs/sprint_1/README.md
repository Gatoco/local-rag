# SPRINT 1: Índice de Documentación

## 📖 Documentación del SPRINT 1

Este sprint se enfoca en **definir el corazón del dominio**: los modelos de datos.

### 📚 Archivos de Guía

#### 1. **`01_models_guia_detallada.md`** ← EMPEZAR AQUÍ
Guía **paso a paso**  y **línea por línea** para escribir `models.py`.

Contiene:
- ¿Qué es models.py y por qué existe?
- Conceptos base (dataclasses, type hints, field)
- Guía paso a paso para cada modelo
- Análisis detallado de cada línea
- Decisiones de diseño explicadas
- Ejemplos de uso real
- Errores comunes
- Preguntas frecuentes

**Tiempo de lectura:** 20-30 minutos  
**Nivel:** Principiante → Intermedio  
**Resultado:** Entiendes completamente models.py

---

#### 2. **`02_ports_introduccion.md`** 
Introducción a los **Puertos** (interfaces) del sistema.

Contiene:
- Qué son los Ports y por qué existen
- Analogía del mundo real
- Visión general de los 4 puertos principales
- Cómo fluye la inyección de dependencias
- Relación entre Domain Ports y Application Ports

**Tiempo de lectura:** 10-15 minutos  
**Nivel:** Principiante  
**Resultado:** Entiendes la arquitectura de puertos

---

#### 3. **`03_verificacion_y_testing.md`**
**Guía práctica** para verificar, testear y validar los modelos.

Contiene:
- Paso a paso: Verificar sintaxis
- Paso a paso: Testear manualmente
- Cómo ejecutar tests unitarios
- Cómo ver coverage
- Troubleshooting de errores comunes
- Resultados esperados

**Tiempo de lectura:** 5-10 minutos  
**Nivel:** Principiante  
**Resultado:** Saber que todo funciona correctamente

---

### 💻 Archivos de Código

#### 1. **`src/domain/models.py`** ✅ YA COMPLETADO
- ✓ 3 dataclasses: Document, Query, Answer
- ✓ Docstrings completos
- ✓ Type hints correctos
- ✓ Listo para usar

#### 2. **`tests/unit/test_models.py`** ✅ YA COMPLETADO
- ✓ 45+ tests unitarios
- ✓ 100% coverage para models.py
- ✓ Tests de integración
- ✓ Tests de edge cases
- ✓ Tests de manejo de errores

---

## 🎯 Checklist de SPRINT 1

### Día 1: Comprensión
- [ ] Leer `01_models_guia_detallada.md` completamente
- [ ] Entender qué son dataclasses
- [ ] Entender qué son type hints
- [ ] Entender por qué cada modelo (Document, Query, Answer)

### Día 2: Revisión de Implementación
- [ ] Revisar `src/domain/models.py` (ya está hecho)
- [ ] Comparar con lo que aprendiste
- [ ] Entender cada línea del código
- [ ] Entender cada docstring

### Día 3: Validación
- [ ] Leer `03_verificacion_y_testing.md`
- [ ] Ejecutar `python -c "from src.domain.models import Document, Query, Answer"`
- [ ] Ejecutar tests: `pytest tests/unit/test_models.py -v`
- [ ] Verificar que todos los tests pasan

### Día 4: Ports y Siguiente Sprint
- [ ] Leer `02_ports_introduccion.md`
- [ ] Entender qué son los 4 puertos
- [ ] Prepararse para SPRINT 2 (Adapters)

---

## 📌 Concepto General de SPRINT 1

```
SPRINT 1: Dominio Puro
├── Models (qué datos existen) ✅
├── Ports (qué operaciones necesitamos) 📖
└── Exceptions (qué errores pueden ocurrir) ⏳

Resultado: La "verdad fundamental" del sistema
├── Independiente de tecnología
├── Independiente de adaptadores
└── Base para todo lo que viene después
```

---

## 💡 Filosofía

En SPRINT 1, **definimos qué es el negocio**, sin meternos en HOW implementarlo.

- ¿QUÉ es un Document? → `models.py` ✅
- ¿QUÉ operaciones necesitamos? → `ports/` 📖
- ¿QUÉ suele ir mal? → `exceptions.py` ⏳

Los SPRINTS 2-5 dirán HOW:
- HOW almacenar → ChromaDBAdapter
- HOW embeddings → HFEmbeddingAdapter
- HOW LLMs → OllamaLLMAdapter
- etc.

---

## 📊 Progreso de SPRINT 1

| Componente | Estado | Descripción |
|----------|--------|-------------|
| **models.py** | ✅ Completado | Document, Query, Answer implementados |
| **test_models.py** | ✅ Completado | 45+ tests con 100% coverage |
| **01_models_guia** | ✅ Completado | Guía detallada paso a paso |
| **02_ports_intro** | ✅ Completado | Introducción a puertos |
| **03_verificacion** | ✅ Completado | Guía de testing |
| **exceptions.py** | ⏳ Próximo | Definición de errores |
| **ports documentacion** | ⏳ Próximo | Especificación detallada ||

---

## 🚀 Próxima Lectura Recomendada

1. ✅ **Lee** `01_models_guia_detallada.md` (30 min)
2. ✅ **Revisa** `src/domain/models.py` (10 min)
3. ✅ **Lee** `03_verificacion_y_testing.md` (10 min)
4. ✅ **Ejecuta** los tests para verificar (5 min)
5. ✅ **Lee** `02_ports_introduccion.md` (15 min)

**Total: ~70-80 minutos** para completar SPRINT 1

---

## ✨ Confirmación

Cuando termines SPRINT 1, habrás comprendido:
- ✅ Qué son dataclasses y type hints
- ✅ Por qué existen Document, Query, Answer
- ✅ Cómo funcionan los tests unitarios
- ✅ Qué son los Ports (interfaces)
- ✅ Por qué está separado el código en capas

**Estás listo para SPRINT 2: Implementar los Adapters** 🎯

---

**Bienvenido a SPRINT 1. ¡Tienes todo lo que necesitas para triunfar!** 🚀
