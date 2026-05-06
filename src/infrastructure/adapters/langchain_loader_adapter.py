import json
import os
from typing import Any

from langchain.schema import Document
from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader, TextLoader
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

        loader = None
        if file_path.endswith('.pdf'):
            loader = PyPDFLoader(file_path)
        elif file_path.endswith('.docx'):
            loader = Docx2txtLoader(file_path)
        elif file_path.endswith('.txt'):
            loader = TextLoader(file_path, encoding="utf-8")
        elif file_path.endswith('.md'):
            # Markdown: cargar como texto plano
            loader = TextLoader(file_path, encoding="utf-8")
        elif file_path.endswith('.json'):
            # JSON: convertir a formato legible
            return self._load_json_as_documents(file_path)
        else:
            raise ValueError(f"Formato de archivo no soportado: {file_path}")

        # Cargamos los datos
        docs = loader.load()
        # Los dividimos en fragmentos manejables
        return self.text_splitter.split_documents(docs)

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
        return self.text_splitter.split_documents(documents)

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
        for root, _, files in os.walk(dir_path):
            for filename in files:
                file_path = os.path.join(root, filename)
                # Soportar más formatos: pdf, txt, docx, md, json
                if any(file_path.lower().endswith(ext) for ext in ['.pdf', '.txt', '.docx', '.md', '.json']):
                    try:
                        splits = self.load_and_split(file_path)
                        all_splits.extend(splits)
                    except Exception as e:
                        print(f"Error cargando {file_path}: {e}")
        return all_splits
