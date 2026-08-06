# Contributing to Local RAG

Thank you for your interest in contributing to Local RAG!

This document provides guidelines and instructions for contributing to this project.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone. We do not tolerate harassment, discrimination, or inappropriate behavior.

## Getting Started

### Prerequisites

- Python 3.12 or higher
- Git
- A code editor (VS Code, PyCharm, etc.)
- (Optional) Docker for containerized development

### Development Setup

1. **Fork the repository** on GitHub

2. **Clone your fork locally:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/local-rag.git
   cd local-rag
   ```

3. **Add the upstream remote:**
   ```bash
   git remote add upstream https://github.com/iwakura/local-rag.git
   ```

4. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   # or
   .venv\Scripts\activate  # Windows
   ```

5. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -e ".[dev]"  # Install with dev dependencies
   ```

6. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/issue-you-are-fixing
   ```

## Development Workflow

### 1. Making Changes

- Follow the coding standards defined in `agent_context/STANDARDS.md`
- Write clean, well-documented code
- Use type hints where possible
- Keep functions focused and reasonably sized (< 100 lines)

### 2. Testing

All new code should include appropriate tests:

```bash
# Run unit tests
pytest tests/unit/ -v --cov=src --cov-report=term-missing

# Run integration tests
pytest tests/integration/ -v

# Run all tests
pytest tests/ -v --cov=src
```

**Requirements:**
- Maintain at least 80% code coverage
- All existing tests must pass
- Add tests for new functionality

### 3. Linting and Type Checking

Before committing, ensure your code passes all checks:

```bash
# Ruff linter
ruff check src/ tests/

# Ruff formatter
ruff format src/ tests/

# Type checking
mypy src/ --ignore-missing-imports
```

### 4. Committing

Follow these commit message guidelines:

```
type(scope): short description (max 72 chars)

Optional detailed explanation if needed.
Wrap at 72 characters.
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code refactoring
- `docs`: Documentation changes
- `test`: Adding/updating tests
- `chore`: Maintenance tasks
- `deps`: Dependency changes

**Example:**
```
feat(repl): add tab completion for commands

Implemented readline-based tab completion for REPL commands.
Includes completion for file paths in the index command.
```

### 5. Branch Naming Convention

- `feature/<description>` - New features
- `fix/<description>` - Bug fixes
- `refactor/<description>` - Code refactoring
- `docs/<description>` - Documentation updates
- `test/<description>` - Test improvements
- `agent/<type>-<description>` - Agent-related changes

## Project Architecture

Local RAG uses a **Hexagonal (Ports & Adapters)** architecture:

```
src/
├── domain/              # Core business models (no external dependencies)
│   ├── models.py        # Document, Query, Answer
│   └── ports/           # Abstract interfaces (contracts)
├── application/         # Application services
│   ├── ports/           # Application-level interfaces
│   └── services/        # RAGService orchestration
└── infrastructure/      # External adapters implementation
    ├── adapters/        # ChromaDB, LLM adapters, etc.
    ├── entrypoints/     # API, CLI, REPL interfaces
    ├── security/        # JWT, rate limiting
    └── cache/           # Semantic caching
```

**Key Principles:**
- Domain layer has no external dependencies
- Infrastructure depends on Domain (not the other way around)
- Use dependency injection for flexibility
- Ports define contracts, adapters implement them

## Pull Request Process

### Before Submitting

1. **Sync with upstream:**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run all checks:**
   ```bash
   pytest tests/ -v --cov=src
   ruff check src/ tests/
   mypy src/ --ignore-missing-imports
   ```

3. **Ensure coverage:**
   - New code should not reduce overall coverage below 80%
   - Critical paths should have higher coverage

### Submitting

1. Push your branch:
   ```bash
   git push origin feature/your-feature-name
   ```

2. Open a Pull Request against `main`

3. Fill out the PR template:
   - Description of changes
   - Related issue number (if applicable)
   - Testing performed
   - Screenshots (for UI changes)

### PR Review Process

- PRs require review before merging
- Address any feedback promptly
- Keep PRs focused and reasonably sized
- Multiple small PRs are preferred over one large PR

## Documentation

When adding new features, update relevant documentation:

- `README.md` - Overview and usage
- `docs/` - Detailed documentation
- Docstrings - For public APIs and complex functions
- Type hints - For all public methods

## Reporting Issues

When reporting bugs, include:

- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Relevant logs or error messages
- Code snippet that demonstrates the issue

## Questions?

Feel free to:
- Open a discussion on GitHub
- Check existing issues and discussions
- Contact the maintainers

## License

By contributing to Local RAG, you agree that your contributions will be licensed under the MIT License.
