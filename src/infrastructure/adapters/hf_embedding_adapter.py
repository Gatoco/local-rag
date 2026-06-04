from typing import Any, cast

from langchain_huggingface import HuggingFaceEmbeddings

from src.domain.ports.embedding_port import EmbeddingPort


class HFEmbeddingAdapter(EmbeddingPort):
    def __init__(self, model_name: str = "BAAI/bge-large-en-v1.5"):
        """
        Inicializa el adaptador de Hugging Face usando la librería moderna.

        Modelos disponibles:
        - BAAI/bge-large-en-v1.5 (1024 dims, mejor calidad, ~1GB)
        - BAAI/bge-small-en-v1.5 (384 dims, rápido, buena calidad)
        - sentence-transformers/all-MiniLM-L6-v2 (384 dims, default original)
        """
        self.model_name = model_name
        self.model = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True, "batch_size": 16},
        )

    def get_embeddings_model(self) -> Any:
        return self.model

    def embed_query(self, text: str) -> list[float]:
        result = self.model.embed_query(text)
        return cast(list[float], result)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        result = self.model.embed_documents(texts)
        return cast(list[list[float]], result)
