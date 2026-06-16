"""
Tests para LangChainLoaderAdapter (carga y split de documentos).

Run: pytest tests/unit/test_langchain_loader_adapter.py -v
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.documents import Document

from src.infrastructure.adapters.langchain_loader_adapter import LangChainLoaderAdapter


@pytest.fixture
def loader():
    return LangChainLoaderAdapter(chunk_size=100, chunk_overlap=20)


class TestInit:
    def test_default_params(self):
        l = LangChainLoaderAdapter()
        assert l.text_splitter is not None

    def test_custom_params(self):
        l = LangChainLoaderAdapter(chunk_size=500, chunk_overlap=50)
        assert l.text_splitter is not None


class TestLoadAndSplitErrors:
    def test_nonexistent_file_raises(self, loader, tmp_path):
        with pytest.raises(FileNotFoundError):
            loader.load_and_split(str(tmp_path / "no_existe.pdf"))

    def test_unsupported_extension_raises(self, loader, tmp_path):
        f = tmp_path / "archivo.xyz"
        f.write_text("hola")
        with pytest.raises(ValueError, match="no soportada"):
            loader.load_and_split(str(f))


class TestLoadText:
    def test_txt_file(self, loader, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("Hola mundo. " * 50, encoding="utf-8")
        result = loader.load_and_split(str(f))
        assert result is not None
        assert len(result) > 0
        assert "Hola" in result[0].page_content

    def test_md_file(self, loader, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("# Título\n\nContenido del documento.", encoding="utf-8")
        result = loader.load_and_split(str(f))
        assert result is not None
        assert any("Título" in d.page_content for d in result)


class TestLoadJSON:
    def test_json_list(self, loader, tmp_path):
        data = [{"name": "Ana", "age": 30}, {"name": "Bob", "age": 25}]
        f = tmp_path / "data.json"
        f.write_text(json.dumps(data), encoding="utf-8")
        result = loader.load_and_split(str(f))
        assert result is not None
        assert len(result) == 2
        assert "Ana" in result[0].page_content

    def test_json_dict_with_list(self, loader, tmp_path):
        data = {"users": [{"id": 1}, {"id": 2}]}
        f = tmp_path / "data.json"
        f.write_text(json.dumps(data), encoding="utf-8")
        result = loader.load_and_split(str(f))
        assert result is not None
        assert len(result) == 2

    def test_json_simple_dict(self, loader, tmp_path):
        data = {"key": "value", "number": 42}
        f = tmp_path / "data.json"
        f.write_text(json.dumps(data), encoding="utf-8")
        result = loader.load_and_split(str(f))
        assert result is not None
        assert len(result) >= 1


class TestLoadCSV:
    def test_csv_with_pandas(self, loader, tmp_path):
        f = tmp_path / "data.csv"
        f.write_text("name,age\nAna,30\nBob,25\n", encoding="utf-8")
        with patch(
            "src.infrastructure.adapters.langchain_loader_adapter.CSVLoader"
        ) as mock_loader_cls:
            mock_instance = MagicMock()
            mock_instance.load.return_value = [
                Document(page_content="Ana 30", metadata={"source": str(f)}),
                Document(page_content="Bob 25", metadata={"source": str(f)}),
            ]
            mock_loader_cls.return_value = mock_instance
            result = loader.load_and_split(str(f))
            assert result is not None
            assert len(result) >= 1


class TestLoadPDFMocked:
    def test_pdf_with_pypdf(self, loader, tmp_path):
        f = tmp_path / "test.pdf"
        f.write_bytes(b"%PDF-1.4 fake")
        with patch("pypdf.PdfReader") as mock_reader_cls:
            mock_page = MagicMock()
            mock_page.extract_text.return_value = "Contenido del PDF página 1"
            mock_page.images = []
            mock_reader_cls.return_value.pages = [mock_page]
            result = loader.load_and_split(str(f))
            assert result is not None
            assert any("Contenido" in d.page_content for d in result)


class TestChunking:
    def test_large_text_is_split(self, loader, tmp_path):
        long_text = "Oración uno. " * 100
        f = tmp_path / "long.txt"
        f.write_text(long_text, encoding="utf-8")
        result = loader.load_and_split(str(f))
        assert result is not None
        assert len(result) > 1
