import csv
import json
import os
from typing import Any, cast

from langchain.schema import Document
from langchain_community.document_loaders import (
    BSHTMLLoader,
    CSVLoader,
    Docx2txtLoader,
    PyPDFLoader,
    TextLoader,
    UnstructuredExcelLoader,
    UnstructuredImageLoader,
    UnstructuredPowerPointLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.domain.ports.document_loader_port import DocumentLoaderPort


class LangChainLoaderAdapter(DocumentLoaderPort):
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 150):
        """
        Inicializa el adaptador para cargar y dividir documentos.

        Args:
            chunk_size (int): Tamaño de cada fragmento de texto (en caracteres).
            chunk_overlap (int): Superposición entre fragmentos para no perder contexto en los bordes.
        """
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False
        )

    def load_and_split(self, file_path: str) -> list[Any]:
        """Carga un archivo basándose en su extensión y lo divide en fragmentos."""
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"No existe el archivo: {file_path}")

        loader: Any = None
        if file_path.endswith('.pdf'):
            return self._load_pdf_with_ocr(file_path)
        elif file_path.endswith('.docx'):
            loader = Docx2txtLoader(file_path)
        elif file_path.endswith('.txt'):
            loader = TextLoader(file_path, encoding="utf-8")
        elif file_path.endswith('.md'):
            loader = TextLoader(file_path, encoding="utf-8")
        elif file_path.endswith('.json'):
            return self._load_json_as_documents(file_path)
        elif file_path.endswith(('.xlsx', '.xls')):
            loader = UnstructuredExcelLoader(file_path, mode="elements")
        elif file_path.endswith('.pptx'):
            loader = UnstructuredPowerPointLoader(file_path, mode="elements")
        elif file_path.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp')):
            loader = UnstructuredImageLoader(file_path, mode="elements")
        elif file_path.endswith(('.html', '.htm')):
            loader = BSHTMLLoader(file_path)
        elif file_path.endswith('.csv'):
            try:
                loader = CSVLoader(file_path, source_column="student_id")
                docs = loader.load()
            except Exception:
                docs = self._load_csv_as_text(file_path)
            return cast(list[Any], self.text_splitter.split_documents(docs))

    def _load_json_as_documents(self, file_path: str) -> list[Any]:
        """
        Carga un archivo JSON y lo convierte a documentos LangChain.
        Maneja tanto listas de objetos como estructuras anidadas.
        """
        with open(file_path, encoding='utf-8') as f:
            data = json.load(f)

        documents = []

        # Si es una lista de objetos
        if isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, dict):
                    # Convertir dict a texto legible
                    text = self._dict_to_text(item)
                    documents.append(Document(
                        page_content=text,
                        metadata={"source": file_path, "index": i}
                    ))
        # Si es un dict con una lista
        elif isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, list):
                    for i, item in enumerate(value):
                        if isinstance(item, dict):
                            text = self._dict_to_text(item)
                            documents.append(Document(
                                page_content=text,
                                metadata={"source": file_path, "category": key, "index": i}
                            ))
                else:
                    # Dict simple
                    text = self._dict_to_text({key: value})
                    documents.append(Document(
                        page_content=text,
                        metadata={"source": file_path}
                    ))

        # Dividir en chunks
        return cast(list[Any], self.text_splitter.split_documents(documents))

    def _load_pdf_with_ocr(self, file_path: str) -> list[Any]:
        """
        Carga un PDF extrayendo texto e imágenes con OCR.
        Usa PyPDF2 para texto e imágenes, y optionally tesseract para OCR.
        """
        docs = []

        try:
            from pypdf import PdfReader
        except ImportError:
            return self._load_pdf_fallback(file_path)

        try:
            reader = PdfReader(file_path)

            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()

                if text and text.strip():
                    page_docs = self.text_splitter.split_documents([
                        Document(page_content=text, metadata={"source": file_path, "page": page_num + 1})
                    ])
                    docs.extend(page_docs)

                images = page.images
                if images:
                    for img_idx, img_info in enumerate(images):
                        try:
                            img_text = self._extract_image_text(img_info, page_num, img_idx)
                            if img_text:
                                img_docs = self.text_splitter.split_documents([
                                    Document(page_content=img_text, metadata={
                                        "source": file_path,
                                        "page": page_num + 1,
                                        "type": "image",
                                        "image_index": img_idx
                                    })
                                ])
                                docs.extend(img_docs)
                        except Exception:
                            continue

        except Exception:
            return self._load_pdf_fallback(file_path)

        return cast(list[Any], docs) if docs else self._load_pdf_fallback(file_path)

    def _extract_image_text(self, img_info: Any, page_num: int, img_idx: int) -> str:
        """Intenta OCR en imagen con tesseract si está disponible."""
        try:
            import io

            import pytesseract
            from PIL import Image

            img_data = img_info.get_data()
            if img_data:
                img = Image.open(io.BytesIO(img_data))
                return f"[Image from page {page_num + 1}, image {img_idx + 1}]\n{pytesseract.image_to_string(img)}"
        except Exception:
            return f"[Image from page {page_num + 1}, image {img_idx + 1} - OCR not available]"
        return "[Image data unavailable]"

    def _load_pdf_fallback(self, file_path: str) -> list[Any]:
        """Fallback para PDFs sin OCR."""
        loader = PyPDFLoader(file_path)
        docs = loader.load()
        return cast(list[Any], self.text_splitter.split_documents(docs))

    def _load_python_file(self, file_path: str) -> list[Any]:
        """
        Carga un archivo Python extrayendo: docstrings, funciones, clases, comments.
        Preserva estructura del código para mejor retrieval.
        """
        with open(file_path, encoding='utf-8') as f:
            content = f.read()

        chunks = []
        current_module = []

        lines = content.split('\n')
        for line in lines:
            if line.strip().startswith('#') and not line.strip().startswith('#!'):
                current_module.append(line)
            elif line.strip().startswith('"""') or line.strip().startswith("'''"):
                current_module.append(line)
            elif 'def ' in line or 'class ' in line or 'import ' in line or 'from ' in line:
                if current_module:
                    chunk_text = '\n'.join(current_module)
                    if chunk_text.strip():
                        chunks.append(Document(
                            page_content=chunk_text,
                            metadata={"source": file_path, "type": "python_comment"}
                        ))
                    current_module = []
                current_module.append(line)
            else:
                if current_module or line.strip():
                    current_module.append(line)

        if current_module:
            chunk_text = '\n'.join(current_module)
            if chunk_text.strip():
                chunks.append(Document(
                    page_content=chunk_text,
                    metadata={"source": file_path, "type": "python_code"}
                ))

        if not chunks:
            chunks = [Document(page_content=content, metadata={"source": file_path, "type": "python_raw"})]

        return cast(list[Any], self.text_splitter.split_documents(chunks))

    def _load_csv_as_text(self, file_path: str) -> list[Any]:
        """Load CSV as text documents, one row per document."""
        documents = []
        with open(file_path, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                text = self._dict_to_text(row)
                documents.append(Document(
                    page_content=text,
                    metadata={"source": file_path, "row": i + 1}
                ))
        return cast(list[Any], documents)

    def _dict_to_text(self, d: dict, indent: int = 0) -> str:
        """Convierte un diccionario a texto formateado."""
        lines = []
        for key, value in d.items():
            prefix = "  " * indent
            if isinstance(value, dict):
                lines.append(f"{prefix}{key}:")
                lines.append(self._dict_to_text(value, indent + 1))
            elif isinstance(value, list):
                lines.append(f"{prefix}{key}:")
                for item in value:
                    if isinstance(item, dict):
                        lines.append(f"{prefix}  - {self._dict_to_text(item, indent + 2)}")
                    else:
                        lines.append(f"{prefix}  - {item}")
            else:
                lines.append(f"{prefix}{key}: {value}")
        return "\n".join(lines)

    def load_directory(self, dir_path: str) -> list[Any]:
        """Escanea un directorio y carga todos los documentos soportados."""
        if not os.path.isdir(dir_path):
            raise FileNotFoundError(f"No existe el directorio: {dir_path}")

        all_splits = []
        supported_extensions = [
            '.pdf', '.txt', '.docx', '.md', '.json',
            '.xlsx', '.xls', '.pptx',
            '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp',
            '.html', '.htm', '.csv', '.py'
        ]
        for root, _, files in os.walk(dir_path):
            for filename in files:
                file_path = os.path.join(root, filename)
                if any(file_path.lower().endswith(ext) for ext in supported_extensions):
                    try:
                        splits = self.load_and_split(file_path)
                        all_splits.extend(splits)
                    except Exception as e:
                        print(f"Error cargando {file_path}: {e}")
        return all_splits
