# Python 3.12 - Documentación de Compatibilidad

## Archivos que especifican Python 3.12

Este proyecto ha sido formalizado para **requerir Python 3.12** en todos los puntos de configuración:

### 📋 Archivos de Configuración

| Archivo | Tipo | Propósito |
|---------|------|----------|
| `.python-version` | ✅ Nuevo | Para `pyenv`, `asdf` y herramientas de versión |
| `pyproject.toml` | ✅ Nuevo | Especificación formal de compilación (PEP 517/518) |
| `.tool-versions` | ✅ Nuevo | Soporta `asdf` (unix) |
| `requirements.txt` | ✅ Actualizado | Comentarios clarificadores sobre Python 3.12 |
| `README.md` | ✅ Actualizado | Requisitos con ✅/❌/⚠️ clarificadores |
| `QUICKSTART.md` | ✅ Actualizado | Scripts de setup y pasos de instalación |

### 🔧 Scripts de Configuración

| Archivo | Plataforma | Acción |
|---------|-----------|--------|
| `setup.sh` | ✅ Linux/macOS | Script ejecutable que valida Python 3.12 e instala |
| `setup.bat` | ✅ Windows | Script batch que valida Python 3.12 e instala |
| `check_python.py` | ✅ Multiplataforma | Valida versión de Python y da instrucciones detalladas |

### 📚 Documentación

| Archivo | Contenido |
|---------|----------|
| `docs/PYTHON_COMPATIBILITY.md` | ✅ Nuevo - Guía técnica completa sobre por qué Python 3.12 |
| `GUIA_USO_RAG.md` | Existente - Menciona requisito Python 3.12 |

---

## Cómo se Especifica Python 3.12

### 1. **pyproject.toml** (Oficial PEP 508)
```toml
requires-python = ">=3.12,<3.13"
```
Esto dice que SOLO Python 3.12.x es soportado.

### 2. **.python-version** (pyenv/asdf)
```
3.12.0
```
Herramientas de manejo de versiones usan esto automáticamente.

### 3. **.tool-versions** (asdf)
```
python 3.12.0
```
Para usuarios de `asdf`.

### 4. **requirements.txt** (pip)
```
# System Requirements: Python 3.12+
# ⚠️ IMPORTANTE: Este proyecto REQUIERE Python 3.12
# ❌ NO compatible con Python 3.14 (Pydantic v2 incompatibility)
```

### 5. **setup.sh** / **setup.bat** (Automatizado)
Estos scripts:
- Detectan la versión de Python
- Crean venv con esa versión
- Instalan dependencias
- Validan que sea 3.12

---

## Historial: Por qué se Hizo esto

### Problema Inicial
Usuario utilizó Python 3.14 (beta), resultó en:
```
TypeError: 'function' object is not subscriptable
```

Causa: Incompatibilidad de Pydantic v2 con cambios en `typing` de Python 3.14.

### Solución Anterior
Recrearon el venv con Python 3.12 manualmente.

### Solución Actual
Se formalizó Python 3.12 como **requisito absoluto** en:
- ✅ Configuración de compilación (`pyproject.toml`)
- ✅ Herramientas de versión (`.python-version`, `.tool-versions`)
- ✅ Scripts de setup (automatizados)
- ✅ Documentación clara con ❌ para 3.14
- ✅ Verificación automática (`check_python.py`)

---

## Verificación Rápida

```bash
# Dentro del proyecto activado
. .venv/bin/activate
python --version  # Debe mostrar 3.12.X

# O sin activar
python check_python.py  # Valida automáticamente
```

✅ = Sistema listo
❌ = Falla clara con instrucciones de instalación

---

## Futuro (Post-Pydantic v3)

Cuando Pydantic v3 esté estable (probablemente 2026):
- Podremos migrar a Python 3.13+
- Estos archivos se actualizarán
- El proyecto será más "future-proof"

Por ahora: **Python 3.12 es la solución estable**.

---

**Última actualización:** 25 de marzo de 2026  
**Estado:** ✅ Python 3.12 formalizado en todos los puntos de configuración
