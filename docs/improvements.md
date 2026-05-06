# Plan de Mejoras del Proyecto

## ✅ Completado

### 1. CI/CD Pipeline ✅
- Pipeline en `.github/workflows/ci.yml`
- Tests con coverage
- Ruff lint + mypy typecheck
- Docker build

---

## Prioridad: Crítica (Pendiente)

### 2. Testing - Aumentar Coverage

**Problema:** Coverage insuficiente. Muchos adapters tienen smoke tests skippeados.

**Acciones:**
- [ ] Agregar tests para `SemanticCache`
- [ ] Agregar tests de seguridad (JWT, rate limiting)
- [ ] Coverage real: ejecutar `pytest tests/ --cov=src --cov-report=html`

---

## Prioridad: Alta

### 3. Seguridad - Secretos y Credenciales ✅

**Estado:** Completado

**Cambios:**
- Secretos obligatorios via env vars (JWT_SECRET_KEY, ADMIN_PASSWORD, USER_PASSWORD)
- Rate limiting con Redis (RedisRateLimiter)
- Usuarios persistidos en SQLite

---

### 4. Rate Limiting Distribuido ✅

**Estado:** Completado

**Cambios:**
- `RedisRateLimiter` implementado usando Redis
- Sliding window algorithm
- Headers X-RateLimit-* incluidos en respuestas

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