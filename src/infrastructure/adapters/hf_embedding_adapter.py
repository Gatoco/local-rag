from typing import Any

from langchain_huggingface import HuggingFaceEmbeddings

from src.domain.ports.embedding_port import EmbeddingPort


class HFEmbeddingAdapter(EmbeddingPort):
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Inicializa el adaptador de Hugging Face usando la librería moderna.
        """
        # Configuramos el modelo para ejecutarse localmente
        self.model = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )

    def get_embeddings_model(self) -> Any:
        return self.model

    def embed_query(self, text: str) -> list[float]:
        return self.model.embed_query(text)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.model.embed_documents(texts)
