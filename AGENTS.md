# AGENTS.md — Local-RAG Development Standards

> Standards for AI-assisted and human development of the Local-RAG project.
> Migrated from the agent workspace standards (2026-08-18).

## Testing

### Requirements
- **Minimum coverage**: 80% for new code (enforced in CI with `--cov-fail-under=80`)
- **Unit tests**: for every public function/method
- **Integration tests**: for complete flows (API, RAG)

### Running tests
```bash
# Unit tests
pytest tests/unit/ -v --cov=src --cov-report=term-missing

# Integration tests
pytest tests/integration/ -v

# Benchmarks
pytest tests/benchmarks/ -v

# All tests
pytest tests/ -v --cov=src
```

### Pre-commit checklist
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Coverage did not drop below 80%
- [ ] Ruff lint passes: `ruff check src/`
- [ ] No new mypy warnings: `mypy src/`

## Linting and Formatting

```bash
# Ruff (linter + formatter)
ruff check src/ tests/
ruff format src/ tests/

# Config lives in pyproject.toml:
# - line-length: 99
# - target-version: py312
# - select: E, F, W, I, N, UP, B, C4
```

## Type Checking

```bash
# mypy
mypy src/ --ignore-missing-imports

# Config in pyproject.toml
# python_version: 3.12
# warn_return_any: true
```

## Git

### Branch naming
- `agent/<type>-<description>` for agent work
- `fix/<description>` for bug fixes
- `feature/<description>` for features
- `refactor/<description>` for refactors

### Commits
- Clear, descriptive message
- First line: summary (max 72 chars)
- Second line: empty
- Third line+: details if needed

### Workflow
1. Create branch from main: `git checkout -b agent/fix-xxx`
2. Make changes
3. Run tests
4. Commit with descriptive message
5. Push: `git push -u origin agent/fix-xxx`
6. Create PR or wait for approval to merge

## Dependencies

### Adding a dependency
1. Add to `pyproject.toml` under `[dependencies]`
2. Run `uv sync` or `pip install -e .`
3. Regenerate requirements.txt: `uv export --no-hashes --format requirements-txt > requirements.txt`
4. Commit with message: `deps: add <package>`

### Removing a dependency
1. Remove from `pyproject.toml`
2. Run `uv sync`
3. Regenerate requirements.txt
4. Commit with message: `deps: remove <package>`

## Code Review Checklist

- [ ] Readable, documented code
- [ ] No overly long functions/methods (>100 lines)
- [ ] Clear variable names
- [ ] Tests for new code
- [ ] No hardcoded values (use constants/config)
- [ ] Appropriate error handling
- [ ] Appropriate logging
- [ ] Type hints on public functions

## Logging

Use the configured logging system:
```python
from src.infrastructure.utils.logging_config import get_logger
logger = get_logger(__name__)

logger.info("message")
logger.debug("detail")
logger.error("error", exc_info=True)
```

Do NOT use `print()` in production code — only `logger`.

## Security

- Never hardcode credentials — use environment variables
- Never print sensitive data
- Validate user inputs
- Secrets never in code or git history

## Docker

### Build
```bash
docker build -t local-rag .
docker compose up -d
```

### Multi-stage
The Dockerfile uses 2 stages:
- `builder`: compiles with build-essential, gcc
- `runtime`: clean final image without compilation tools

The `.dockerignore` excludes: tests/, agent/, memory/, backups/, .venv/, __pycache__/
