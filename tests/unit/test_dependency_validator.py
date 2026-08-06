"""
Tests para DependencyValidator y validación de modelo GGUF.

Run: pytest tests/unit/test_dependency_validator.py -v
"""

import sys
from unittest.mock import patch

import pytest

from src.infrastructure.utils.dependency_validator import (
    DependencyError,
    DependencyValidator,
    validate_gguf_model,
)


class TestDependencyValidatorInit:
    def test_init_empty(self):
        v = DependencyValidator()
        assert v.missing_deps == []
        assert v.version_errors == []
        assert v.warnings == []

    def test_required_packages_defined(self):
        assert "langchain" in DependencyValidator.REQUIRED_PACKAGES
        assert "chromadb" in DependencyValidator.REQUIRED_PACKAGES
        assert "llama_cpp" in DependencyValidator.REQUIRED_PACKAGES

    def test_optional_packages_defined(self):
        assert "pypdf" in DependencyValidator.OPTIONAL_PACKAGES


class TestValidatePackage:
    def test_installed_package(self):
        v = DependencyValidator()
        with patch("importlib.import_module") as mock_import:
            mock_module = type("M", (), {"__version__": "1.0.0"})()
            mock_import.return_value = mock_module
            assert v.validate_package("fake_pkg") is True

    def test_missing_package(self):
        v = DependencyValidator()
        with patch("importlib.import_module", side_effect=ImportError):
            assert v.validate_package("nope_pkg") is False
            assert "nope_pkg" in v.missing_deps

    def test_version_too_old(self):
        v = DependencyValidator()
        with patch("importlib.import_module") as mock_import:
            mock_module = type("M", (), {"__version__": "0.1.0"})()
            mock_import.return_value = mock_module
            assert v.validate_package("pkg", min_version="1.0.0") is False
            assert len(v.version_errors) == 1
            assert v.version_errors[0][0] == "pkg"

    def test_version_sufficient(self):
        v = DependencyValidator()
        with patch("importlib.import_module") as mock_import:
            mock_module = type("M", (), {"__version__": "2.5.0"})()
            mock_import.return_value = mock_module
            assert v.validate_package("pkg", min_version="1.0.0") is True

    def test_unknown_version_assumed_ok(self):
        v = DependencyValidator()
        with patch("importlib.import_module") as mock_import:
            mock_module = type("M", (), {"__version__": "unknown"})()
            mock_import.return_value = mock_module
            assert v.validate_package("pkg", min_version="1.0.0") is True


class TestVersionCompare:
    def test_gte_simple(self):
        v = DependencyValidator()
        assert v._version_gte("1.2.3", "1.2.0") is True
        assert v._version_gte("1.2.3", "1.2.3") is True
        assert v._version_gte("1.2.3", "1.2.4") is False

    def test_gte_handles_short_versions(self):
        v = DependencyValidator()
        assert v._version_gte("1.2", "1.0.0") is True

    def test_gte_unparseable_returns_true(self):
        v = DependencyValidator()
        assert v._version_gte("weird", "1.0.0") is True


class TestGetInstallCommand:
    def test_no_missing_returns_pip_install_requirements(self):
        v = DependencyValidator()
        cmd = v.get_install_command()
        assert "pip install" in cmd
        assert "requirements.txt" in cmd

    def test_with_missing_returns_specific_packages(self):
        v = DependencyValidator()
        v.missing_deps = ["langchain"]
        cmd = v.get_install_command()
        assert "langchain" in cmd


class TestReportResults:
    def test_all_ok(self):
        v = DependencyValidator()
        assert v._report_results() is True

    def test_missing_deps_fails(self):
        v = DependencyValidator()
        v.missing_deps = ["critical_pkg"]
        assert v._report_results() is False

    def test_version_errors_fails(self):
        v = DependencyValidator()
        v.version_errors = [("pkg", "0.1", "1.0")]
        assert v._report_results() is False


class TestValidateGGUFModel:
    def test_nonexistent_model(self, tmp_path):
        result = validate_gguf_model(str(tmp_path / "nofile.gguf"))
        assert result["exists"] is False
        assert result["is_file"] is False
        assert result["valid_size"] is False
        assert result["valid_header"] is False

    def test_small_file_invalid_size(self, tmp_path):
        f = tmp_path / "small.gguf"
        f.write_bytes(b"GGUF" + b"x" * 100)
        result = validate_gguf_model(str(f))
        assert result["exists"] is True
        assert result["is_file"] is True
        assert result["valid_size"] is False

    def test_valid_gguf_header(self, tmp_path):
        f = tmp_path / "valid.gguf"
        f.write_bytes(b"GGUF" + b"x" * (150 * 1024 * 1024))
        result = validate_gguf_model(str(f))
        assert result["exists"] is True
        assert result["valid_size"] is True
        assert result["valid_header"] is True
        assert result["size_mb"] >= 100

    def test_invalid_gguf_header(self, tmp_path):
        f = tmp_path / "fake.gguf"
        f.write_bytes(b"NOPE" + b"x" * (150 * 1024 * 1024))
        result = validate_gguf_model(str(f))
        assert result["valid_size"] is True
        assert result["valid_header"] is False
