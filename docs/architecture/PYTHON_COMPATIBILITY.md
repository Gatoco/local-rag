# Python 3.12: Requisito de Compatibilidad

## Tl;dr

- ✅ **Python 3.12** - REQUERIDO
- ❌ **Python 3.14** - NO COMPATIBLE (no instalar)
- ⚠️ **Python 3.11 o anteriores** - NO SOPORTADO

Archivos que especifican esto:
- `.python-version` → Herramientas como pyenv, asdf, nvm
- `pyproject.toml` → Herramienta de compilación (especifica `requires-python = ">=3.12,<3.13"`)
- `requirements.txt` → Documentación clara en el encabezado

---

## ¿Por qué Python 3.12 es obligatorio?

### El Problema: Python 3.14 + Pydantic v2

Cuando se intenta ejecutar el proyecto en Python 3.14, se obtiene este error:

```
TypeError: 'function' object is not subscriptable
```

**Causa:** Pydantic v2 (requerido por langchain-core) depende de `typing.get_args()` con generics. En Python 3.14, la API de typing ha cambiado significativamente, y ciertas funciones no pueden ser subscripted (indexadas) como en versiones anteriores.

Esto afecta las validaciones de esquema en LangChain cuando intenta procesar modelos de datos complejos.

### Por qué no Python 3.13?

Python 3.13 tiene cambios en la API de tipos que introducen warnings de deprecación en Pydantic 2.x. Aunque técnicamente funciona, genera ruido en la salida y puede fallar en futuras menores.

### La Solución: Python 3.12

Python 3.12 es la versión **estable más reciente** que:
- ✅ Tiene APIs de typing completamente estables
- ✅ Es totalmente compatible con Pydantic v2
- ✅ Tiene soporte hasta octubre 2028
- ✅ Se ejecuta en prácticamente todos los sistemas

---

## Cómo Verificar tu Versión Instalada

```bash
python --version
python3 --version
python3.12 --version
```

Expected output:
```
Python 3.12.X  ← ✅ Correcto
```

---

## Cómo Instalar Python 3.12

### macOS (Homebrew)
```bash
brew install python@3.12
```

### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install python3.12 python3.12-venv python3.12-dev
```

### Windows (Chocolatey)
```bash
choco install python312
```

### Arch Linux
```bash
sudo pacman -S python
```

### Usar pyenv (Recomendado para múltiples versiones)
```bash
# Instalar pyenv
curl https://pyenv.run | bash

# Instalar Python 3.12
pyenv install 3.12.0

# Activar en este proyecto
cd /ruta/al/proyecto
pyenv local 3.12.0
```

---

## Configuración de Entorno

Una vez instalado Python 3.12:

```bash
# 1. Crear virtual environment con Python 3.12
python3.12 -m venv .venv

# 2. Activar
source .venv/bin/activate  # Linux/macOS
# o en Windows:
# .venv\Scripts\activate

# 3. Verificar que se activó 3.12
python --version  # Debe mostrar 3.12.X

# 4. Instalar dependencias
pip install -r requirements.txt
```

---

## Verificación Automática

El script `check_python.py` valida automáticamente la versión:

```bash
python check_python.py
```

Output si está correcto:
```
✅ Python 3.12 detectado - CORRECTO
✅ SISTEMA LISTO PARA INSTALAR DEPENDENCIAS
```

Output si está incorrecto:
```
❌ Python 3.14 detectado - NO COMPATIBLE
❌ FALLA: VERSIÓN DE PYTHON NO COMPATIBLE
```

---

## Roadmap de Soporte Python

| Versión | Estado | Fin de Vida | Soportado |
|---------|--------|-------------|-----------|
| 3.10    | EOL    | Oct 2026   | ❌ No     |
| 3.11    | Deprecated | Oct 2027 | ⚠️ No     |
| **3.12**| **Estable** | **Oct 2028** | **✅ SÍ** |
| 3.13    | Optimizado | Oct 2029 | ⚠️ Quizás |
| 3.14    | En desarrollo | 2030 | ❌ No    |

---

## Cambios Documentados en Este Archivo

- `.python-version` → Especifica `3.12.0` para pyenv/asdf
- `pyproject.toml` → Especifica `requires-python = ">=3.12,<3.13"`
- `.tool-versions` → Soporte para asdf
- `requirements.txt` → Comentario explicativo en el encabezado
- `README.md` → Requisitos claros con ✅/❌/⚠️
- `check_python.py` → Script de validación automática

---

## Preguntas Frecuentes

**P: ¿Puedo usar Python 3.13?**  
R: Técnicamente sí, pero no es recomendado. Hay warnings de deprecación que pueden causar problemas futuros.

**P: ¿Qué pasa si instalo Python 3.14 accidentalmente?**  
R: El proyecto fallará en la inicialización con `TypeError: 'function' object is not subscriptable`. Desinstala Python 3.14 y vuelve a 3.12.

**P: ¿El proyecto se migará a Python 3.13+ en el futuro?**  
R: Cuando Pydantic v3 esté estable (probablemente en 2026), podremos migrar. Por ahora, 3.12 es la solución estable.

**P: ¿Y si mi sistema solo tiene Python 3.14?**  
R: Usa pyenv o conda para instalar múltiples versiones de Python en paralelo.

---

Última actualización: 25 de marzo de 2026  
Estado: ✅ Requisitos de Python documentados y formalizados
