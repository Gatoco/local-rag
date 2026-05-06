# Plan de Mejoras del Proyecto

## Prioridad: Crítica

### 1. CI/CD Pipeline

**Problema:** No existe pipeline de automatización para tests, linting o despliegue.

**Solución propuesta:**

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Run tests
        run: pytest tests/ -v --cov=src
      - name: Run linting
        run: ruff check src/
```

**Archivos a crear:**
- `.github/workflows/ci.yml`
- `.github/workflows/lint.yml`

---

### 2. Testing - Aumentar Coverage

**Problema:** Coverage insuficiente. Muchos adapters tienen smoke tests skippeados.

**Acciones:**
- [ ] Activar tests en `tests/integration/test_rag_service.py`
- [ ] Agregar tests para `SemanticCache`
- [ ] Agregar tests para `ChromaDBAdapter`
- [ ] Agregar tests de seguridad (JWT, rate limiting)
- [ ] Configurar coverage report con `coverage.toml`

**Comando para verificar coverage:**
```bash
pytest tests/ --cov=src --cov-report=html --cov-report=term
```

---

## Prioridad: Alta

### 3. Seguridad - Secretos y Credenciales

**Problema:** Secretos con valores por defecto débiles.

**Cambios en `src/infrastructure/security/auth.py`:**
```python
# ANTES (inseguro)
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "tu-secret-key-cambia-en-produccion")

# DESPUÉS (validación obligatoria)
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY or SECRET_KEY == "tu-secret-key-cambia-en-produccion":
    raise ValueError("JWT_SECRET_KEY must be set to a secure value in production")
```

**Cambios en `docker-compose.yml`:**
```yaml
# ANTES (inseguro)
ADMIN_PASSWORD=${ADMIN_PASSWORD:-admin123}

# DESPUÉS (sin default, obligatorio)
ADMIN_PASSWORD=${ADMIN_PASSWORD:?ADMIN_PASSWORD is required}
```

**Acciones:**
- [ ] Eliminar defaults débiles en docker-compose.yml
- [ ] Validar SECRET_KEY en auth.py
- [ ] Agregar validación de password strength

---

### 4. Escalabilidad - Rate Limiter Distribuido

**Problema:** Rate limiter in-memory no funciona con múltiples instancias.

**Solución propuesta:**
```python
# Usar Redis para rate limiting distribuido
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.contrib.redis import RedisRateLimiter

limiter = RedisRateLimiter(
    redis_url="redis://localhost:6379",
    default_limits=["100/day", "50/hour"]
)
```

**Acciones:**
- [ ] Implementar `DistributedRateLimiter` usando Redis
- [ ] Actualizar middleware de rate limiting
- [ ] Integrar con docker-compose.yml (ya tiene Redis configurado)

---

### 5. Caché Semántico - Integración y Mejora

**Problema:**
- Caché no está integrada en la API principal
- Usa hash SHA256 en lugar de semantic similarity

**Acciones:**
- [ ] Integrar `RAGServiceWithCache` en `run_api.py`
- [ ] Considerar usar embeddings para similarity en cache
- [ ] Agregar endpoint para invalidar caché

---

## Prioridad: Media

### 6. Documentación de API

**Problema:** Falta documentación interactiva de la API.

**Solución:** Agregar OpenAPI/Swagger

```python
# En run_api.py
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI()

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(...)
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

**Acciones:**
- [ ] Generar openapi.json
- [ ] Agregar Swagger UI a /docs
- [ ] Documentar todos los endpoints con examples

---

### 7. Type Hints Incompletos

**Problema:** No todas las funciones tienen type hints.

**Acciones:**
- [ ] Agregar type hints a `main.py`
- [ ] Agregar type hints a adaptadores
- [ ] Ejecutar `mypy src/` para verificar

---

### 8. Logging Estructurado

**Problema:** Inconsistencia en formato de logs.

**Acciones:**
- [ ] Estandarizar formato JSON para producción
- [ ] Agregar correlation IDs para trazas
- [ ] Configurar diferentes niveles por entorno

---

## Prioridad: Baja

### 9. ChromaDB Optimización

**Problema:** ChromaDB puede no ser óptimo para millones de documentos.

**Alternativas a considerar:**
- Qdrant (mejor performance para vector search)
- Milvus (mejor para scale-out)
- pgvector (si ya usas PostgreSQL)

**Acciones:**
- [ ] Agregar opción de configuración para vector store
- [ ] Crear adapter para Qdrant

---

### 10. Base de Datos de Usuarios

**Problema:** Usuarios hardcoded en memoria.

**Solución:** Implementar persistencia con SQLite o PostgreSQL

```python
# Ejemplo con SQLite
from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    username = Column(String, primary_key=True)
    password_hash = Column(String)
    created_at = Column(DateTime)

# Uso
engine = create_engine("sqlite:///users.db")
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)
```

**Acciones:**
- [ ] Crear modelo User con SQLAlchemy
- [ ] Implementar UserRepository
- [ ] Migrar de usuarios en memoria a persistidos

---

## Resumen de Acciones

| Prioridad | Acción | Esfuerzo |
|-----------|--------|----------|
| Crítica | Agregar CI/CD | Bajo |
| Crítica | Mejorar coverage tests | Medio |
| Alta | Corregir secretos débiles | Bajo |
| Alta | Rate limiter distribuido | Medio |
| Alta | Integrar caché | Medio |
| Media | Documentación API (OpenAPI) | Bajo |
| Media | Type hints completos | Alto |
| Media | Logging estructurado | Medio |
| Baja | Optimizar ChromaDB | Alto |
| Baja | Persistir usuarios | Medio |

---

## Checklist de Implementación

### Fase 1: Seguridad y CI (esfuerzo bajo, impacto alto)
- [ ] Configurar GitHub Actions básico
- [ ] Corregir SECRET_KEY y passwords por defecto
- [ ] Agregar pytest-cov

### Fase 2: Testing y Calidad
- [ ] Activar tests skippeados
- [ ] Agregar tests faltantes
- [ ] Configurar mypy y ruff

### Fase 3: Escalabilidad
- [ ] Integrar Redis para rate limiting
- [ ] Integrar caché en API
- [ ] Considerar Qdrant para vectors

### Fase 4: Polish
- [ ] OpenAPI docs
- [ ] Type hints completos
- [ ] Logging JSON estructurado