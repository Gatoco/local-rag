# Estándares de Código - Local-RAG

## Testing

### Requisitos
- **Coverage mínimo**: 80% para código nuevo
- **Tests unitarios**: Para cada función/método público
- **Tests de integración**: Para flujos completos

### Ejecución de Tests
```bash
cd /home/iwakura/Documentos/github-projects/local-rag
source .venv/bin/activate

# Unit tests
pytest tests/unit/ -v --cov=src --cov-report=term-missing

# Integration tests
pytest tests/integration/ -v

# Benchmarks
pytest tests/benchmarks/ -v

# Todos los tests
pytest -v --cov=src
```

### Checklist antes de commit
- [ ] Todos los unit tests pasan
- [ ] Todos los integration tests pasan
- [ ] Coverage no bajó del 80%
- [ ] Ruff lint pasa
- [ ] No hay warnings nuevos

## Linting y Formatting

```bash
# Ruff (linter)
ruff check src/ tests/

# Formato automático
ruff format src/ tests/
```

## Git

### Branch Naming
- `agent/<tipo>-<descripción>` para trabajo del agente
- `fix/<descripción>` para bug fixes
- `feature/<descripción>` para features
- `refactor/<descripción>` para refactors

### Commits
- Mensaje claro y descriptivo
- Primera línea: resumen (máx 72 chars)
- Segunda línea: vacía
- Tercera línea+: detalles si necesario

### Flujo de trabajo
1. Crear branch desde main: `git checkout -b agent/fix-xxx`
2. Hacer cambios
3. Ejecutar tests
4. Commit con mensaje descriptivo
5. Push: `git push -u origin agent/fix-xxx`
6. Crear PR o esperar approval para merge

## Dependencias

### Agregar dependencia
1. Añadir a `pyproject.toml` en `[dependencies]`
2. Ejecutar `uv sync` o `pip install -e .`
3. Verificar que tests sigan pasando
4. Commit con mensaje: "deps: add <package>"

### Eliminar dependencia
1. Remover de `pyproject.toml`
2. Ejecutar `uv sync`
3. Verificar que tests sigan pasando
4. Commit con mensaje: "deps: remove <package>"

## Code Review Checklist

- [ ] Código legible ydocumentado
- [ ] No hay funciones/métodos demasiado largos (>100 líneas)
- [ ] Nombres de variables claros
- [ ] Tests para código nuevo
- [ ] Sin hardcoded values (usar constantes/config)
- [ ] Manejo de errores apropiado
- [ ] Logging apropiado

## Logging

Usa el sistema de logging configurado:
```python
from src.infrastructure.utils.logging_config import get_logger
logger = get_logger(__name__)

logger.info("mensaje")
logger.debug("detalle")
logger.error("error", exc_info=True)
```

## Seguridad

- No hardcodears credenciales
- Usar variables de entorno
- No hacer print de datos sensibles
- Validar inputs de usuario