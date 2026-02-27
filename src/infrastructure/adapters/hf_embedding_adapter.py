# src/infrastructure/adapters/hf_embedding_adapter.py
# Propósito: Adaptador para generar incrustaciones utilizando modelos de Hugging Face.

from typing import List
from src.domain.ports.embedding_port import EmbeddingPort

class HFEmbeddingAdapter(EmbeddingPort):
    # Propósito: Implementa el EmbeddingPort utilizando modelos de Hugging Face (sentence-transformers).
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        # Propósito: Inicializa el adaptador de embeddings de Hugging Face con un modelo específico.
        # Cargar el modelo de embeddings de Hugging Face.
        pass

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        # Propósito: Genera incrustaciones para una lista de textos.
        # Utilizar el modelo de embeddings cargado para generar las incrustaciones.
        pass

    def embed_query(self, text: str) -> List[float]:
        # Propósito: Genera una incrustación para un solo texto de consulta.
        # Utilizar el modelo de embeddings cargado para generar la incrustación.
        pass
