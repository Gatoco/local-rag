"""
Validación robusta de dependencias para el sistema RAG.

Verifica:
- Paquetes Python instalados
- Versiones mínimas requeridas
- Dependencias del sistema (compiladores, librerías)
- Modelos GGUF disponibles
"""

import importlib
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class DependencyError(Exception):
    """Excepción para errores de dependencias."""

    pass


class DependencyValidator:
    """Valida dependencias Python y del sistema."""

    REQUIRED_PACKAGES = {
        "llama_cpp": {"min_version": "0.2.90", "name": "llama-cpp-python"},
        "langchain": {"min_version": "0.3.0", "name": "langchain"},
        "langchain_core": {"min_version": "0.3.0", "name": "langchain-core"},
        "chromadb": {"min_version": "0.5.0", "name": "chromadb"},
        "sentence_transformers": {"min_version": "2.2.0", "name": "sentence-transformers"},
    }

    OPTIONAL_PACKAGES = {
        "pypdf": {"name": "pypdf", "feature": "procesamiento PDF"},
        "docx": {"name": "python-docx", "feature": "procesamiento DOCX"},
        "requests": {"name": "requests", "feature": "descarga de modelos"},
    }

    def __init__(self):
        self.missing_deps: list[str] = []
        self.version_errors: list[tuple[str, str, str]] = []
        self.warnings: list[str] = []

    def validate_python_version(
        self, min_version: tuple[int, int] = (3, 12), max_version: tuple[int, int] = (3, 13)
    ) -> bool:
        """Valida versión de Python."""
        current = sys.version_info[:2]

        if current < min_version:
            self.warnings.append(
                f"Python {min_version[0]}.{min_version[1]}+ recomendado. "
                f"Tienes {current[0]}.{current[1]}"
            )
            return False

        if current >= max_version:
            self.warnings.append(
                f"Python {max_version[0]}.{max_version[1]} puede tener incompatibilidades. "
                f"Tienes {current[0]}.{current[1]}"
            )

        logger.info(f"Python version: {current[0]}.{current[1]}")
        return True

    def validate_package(self, package: str, min_version: str | None = None) -> bool:
        """Valida un paquete individual."""
        try:
            module = importlib.import_module(package)

            if min_version:
                version = getattr(module, "__version__", "unknown")
                if version != "unknown" and not self._version_gte(version, min_version):
                    self.version_errors.append((package, version, min_version))
                    return False

            logger.debug(f"✓ {package} OK")
            return True

        except ImportError:
            self.missing_deps.append(package)
            logger.debug(f"✗ {package} MISSING")
            return False

    def _version_gte(self, version: str, min_version: str) -> bool:
        """Compara versiones semánticas."""
        try:
            v_parts = [int(x) for x in version.split(".")[:3]]
            m_parts = [int(x) for x in min_version.split(".")[:3]]
            return v_parts >= m_parts
        except (ValueError, AttributeError):
            return True  # Si no se puede parsear, asumir OK

    def validate_all(self, strict: bool = False) -> bool:
        """
        Valida todas las dependencias.

        Args:
            strict: Si True, falla por dependencias opcionales

        Returns:
            True si todas las dependencias críticas están OK
        """
        logger.info("Validando dependencias...")

        # Validar Python
        self.validate_python_version()

        # Validar paquetes requeridos
        for package, info in self.REQUIRED_PACKAGES.items():
            self.validate_package(package, info["min_version"])

        # Validar opcionales
        for package, info in self.OPTIONAL_PACKAGES.items():
            if not self.validate_package(package):
                if strict:
                    self.warnings.append(
                        f"Opcional recomendado: {info['name']} ({info['feature']})"
                    )

        # Reportar resultados
        return self._report_results()

    def _report_results(self) -> bool:
        """Reporta resultados de validación."""
        if self.missing_deps:
            logger.error(f"Dependencias faltantes: {', '.join(self.missing_deps)}")
            logger.error("Instala con: pip install -r requirements.txt")
            return False

        if self.version_errors:
            for pkg, ver, min_ver in self.version_errors:
                logger.error(f"{pkg} {ver} < {min_ver} (versión insuficiente)")
            return False

        if self.warnings:
            for warning in self.warnings:
                logger.warning(warning)

        logger.info("✓ Todas las dependencias validadas")
        return True

    def get_install_command(self) -> str:
        """Genera comando de instalación para dependencias faltantes."""
        if not self.missing_deps:
            return "pip install -r requirements.txt"

        missing_names = []
        for dep in self.missing_deps:
            for pkg, info in {**self.REQUIRED_PACKAGES, **self.OPTIONAL_PACKAGES}.items():
                if pkg == dep or info["name"] == dep:
                    missing_names.append(info["name"])
                    break

        return f"pip install {' '.join(missing_names)}"


def validate_gguf_model(model_path: str) -> dict[str, Any]:
    """
    Valida un modelo GGUF.

    Args:
        model_path: Ruta al modelo

    Returns:
        Dict con información del modelo y validación
    """
    path = Path(model_path)
    result = {
        "exists": path.exists(),
        "is_file": path.is_file() if path.exists() else False,
        "size_mb": path.stat().st_size / (1024 * 1024) if path.exists() else 0,
        "valid_size": False,
        "valid_header": False,
    }

    if not result["exists"]:
        return result

    # Validar tamaño mínimo (100 MB)
    result["valid_size"] = result["size_mb"] >= 100

    # Validar header GGUF (magic number: 0x46554747 = "GGUF")
    try:
        with open(path, "rb") as f:
            magic = f.read(4)
            result["valid_header"] = magic == b"GGUF"  # Little endian
    except Exception as e:
        logger.error(f"Error leyendo header: {e}")

    return result


def check_system_requirements() -> dict[str, bool]:
    """Verifica requisitos del sistema."""
    results = {
        "gcc_available": False,
        "cmake_available": False,
        "sufficient_ram": False,
    }

    # Verificar compiladores
    try:
        subprocess.run(["gcc", "--version"], capture_output=True, timeout=5)
        results["gcc_available"] = True
    except (subprocess.SubprocessError, FileNotFoundError):
        pass

    try:
        subprocess.run(["cmake", "--version"], capture_output=True, timeout=5)
        results["cmake_available"] = True
    except (subprocess.SubprocessError, FileNotFoundError):
        pass

    # Verificar RAM (mínimo 4 GB)
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    mem_kb = int(line.split()[1])
                    mem_gb = mem_kb / (1024 * 1024)
                    results["sufficient_ram"] = mem_gb >= 4
                    break
    except Exception:
        results["sufficient_ram"] = True  # Asumir OK si no se puede verificar

    return results


def main():
    """Ejecuta validación completa."""
    import logging

    logging.basicConfig(level=logging.INFO)

    validator = DependencyValidator()
    success = validator.validate_all()

    if not success:
        print(f"\nError: {validator.get_install_command()}")
        sys.exit(1)

    # Validar modelo si existe .env
    import os

    from dotenv import load_dotenv

    load_dotenv()
    model_path = os.getenv("LLAMA_CPP_MODEL_PATH")

    if model_path:
        print(f"\nValidando modelo: {model_path}")
        model_info = validate_gguf_model(model_path)

        if model_info["exists"]:
            print(f"  Tamaño: {model_info['size_mb']:.1f} MB")
            print(f"  Header GGUF: {'✓' if model_info['valid_header'] else '✗'}")
        else:
            print("  ✗ Modelo no encontrado")

    print("\n✓ Validación completada")


if __name__ == "__main__":
    main()
