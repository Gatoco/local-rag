from typing import Any, cast

from langchain_community.vectorstores import Chroma

from src.domain.ports.document_store_port import DocumentStorePort
from src.domain.ports.embedding_port import EmbeddingPort


class ChromaDBError(Exception):
    """Error general de ChromaDB."""

    pass


class ChromaDBConnectionError(ChromaDBError):
    """Error de conexión con ChromaDB."""

    pass


class ChromaDBAdapter(DocumentStorePort):
    def __init__(
        self,
        embedding_port: EmbeddingPort,
        persist_directory: str = "./chroma_db",
        collection_name: str = "local_rag_docs",
    ):
        """
        Inicializa la base de datos vectorial ChromaDB.

        Args:
            embedding_port (EmbeddingPort): El adaptador de embeddings que usaremos.
            persist_directory (str): Ruta local donde se guardarán los datos (persistentes).
            collection_name (str): Nombre de la colección dentro de ChromaDB.
        """
        self.embedding_model = embedding_port.get_embeddings_model()
        self.persist_directory = persist_directory
        self.collection_name = collection_name

        # Cargamos la base de datos (o la creamos si no existe)
        self._vector_store = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embedding_model,
            persist_directory=self.persist_directory,
        )

    def add_documents(
        self, documents: list[Any], ids: list[str] | None = None, batch_size: int = 500
    ):
        """
        Añade una lista de documentos al almacén vectorial en lotes.

        Args:
            documents: Lista de documentos a añadir
            ids: Lista de IDs para los documentos (opcional)
            batch_size: Tamaño del lote para evitar límites de ChromaDB (default: 500)

        Raises:
            ChromaDBError: Si hay un error al añadir documentos
        """
        try:
            for i in range(0, len(documents), batch_size):
                batch_docs = documents[i : i + batch_size]
                batch_ids = ids[i : i + batch_size] if ids else None
                self._vector_store.add_documents(documents=batch_docs, ids=batch_ids)
        except Exception as e:
            raise ChromaDBError(f"Error adding documents to ChromaDB: {e}") from e

    def search_similar(self, query: str, k: int = 4) -> list[Any]:
        """
        Busca los documentos más parecidos semánticamente a la consulta.

        Raises:
            ChromaDBError: Si hay un error en la búsqueda
        """
        try:
            result = self._vector_store.similarity_search(query, k=k)
            return cast(list[Any], result)
        except Exception as e:
            raise ChromaDBError(f"Error searching in ChromaDB: {e}") from e

    def get_retriever(self, search_kwargs: dict[str, Any] | None = None) -> Any:
        """Devuelve un objeto retriever que LangChain usará en la pipeline RAG."""
        if search_kwargs is None:
            search_kwargs = {"k": 4}  # Por defecto recuperamos 4 fragmentos de texto
        return self._vector_store.as_retriever(search_kwargs=search_kwargs)

    def count(self) -> int:
        """Retorna el numero de documentos en el almacen vectorial."""
        try:
            return cast(int, self._vector_store._collection.count())
        except Exception as e:
            raise ChromaDBError(f"Error counting documents: {e}") from e

    def list_documents(self, limit: int = 20, offset: int = 0) -> tuple[list[dict[str, Any]], int]:
        """
        Lista documentos con paginación.

        Args:
            limit: Máximo de documentos a retornar
            offset: Offset para paginación

        Returns:
            Tuple de (lista de documentos con id y metadata, total count)
        """
        try:
            total = self.count()
            if offset >= total:
                return [], total

            results = self._vector_store._collection.get(
                skip=offset,
                limit=limit,
                include=["metadatas"],
            )

            documents = []
            for doc_id, metadata in zip(results.get("ids", []), results.get("metadatas", []), strict=True):
                documents.append({
                    "id": doc_id,
                    "metadata": metadata or {},
                })

            return documents, total
        except Exception as e:
            raise ChromaDBError(f"Error listing documents: {e}") from e

    def delete_document(self, document_id: str) -> bool:
        """
        Elimina un documento por ID.

        Args:
            document_id: ID del documento a eliminar

        Returns:
            True si se eliminó, False si no existe
        """
        try:
            self._vector_store._collection.delete(ids=[document_id])
            return True
        except Exception as e:
            raise ChromaDBError(f"Error deleting document: {e}") from e
