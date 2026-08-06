"""
RAGService - Servicio de orquestación del sistema RAG.

Este servicio coordina los diferentes componentes (LLM, vector store, loader)
para implementar el flujo completo de Retrieval-Augmented Generation.

Caracteristicas:
- Validación de entrada con Pydantic
- Logging estructurado de operaciones
- Manejo robusto de errores
- Trazabilidad completa de fuentes
- DESACOPLADO de LangChain (usa RAGChainPort)
"""

import logging
from typing import Any, cast

from src.application.ports.rag_chain_port import RAGChainPort
from src.application.ports.rag_port import RAGPort
from src.domain.constants import DEFAULT_RAG_PROMPT
from src.domain.models import Answer, Document, Query
from src.domain.ports.document_loader_port import DocumentLoaderPort
from src.domain.ports.document_store_port import DocumentStorePort

logger = logging.getLogger(__name__)


class RAGServiceError(Exception):
    """Excepcion base para errores del servicio RAG."""


    pass


class RAGServiceIngestionError(RAGServiceError):
    """Error durante la ingesta de documentos."""

    pass


class RAGServiceQueryError(RAGServiceError):
    """Error durante la consulta RAG."""

    pass


class RAGService(RAGPort):
    """
    Orquesta el sistema RAG uniendo los adaptadores de infraestructura.

    Responsabilidades:
    - Coordinar ingesta de documentos
    - Ejecutar consultas RAG (retrieval + generation)
    - Validar entradas y salidas
    - Manejar errores de forma consistente
    - Proveer trazabilidad de fuentes

    DESACOPLADO DE LANGCHAIN:
    Este servicio usa RAGChainPort, no depende directamente de LangChain.
    Permite intercambiar LangChain por otra librería sin modificar esta clase.

    Attributes:
        chain: Cadena RAG (implementación abstracta)
        doc_store: Almacén de documentos vectoriales
        loader: Cargador de documentos
        top_k: Número de documentos a recuperar

    Example:
        # Con LangChain adapter
        from src.infrastructure.adapters.langchain_rag_adapter import LangChainRAGAdapter

        chain = LangChainRAGAdapter(
            llm_adapter=llm_adapter,
            doc_store=doc_store_adapter,
            prompt_template="..."
        )

        service = RAGService(chain, doc_store_adapter, loader_adapter)
        answer = service.ask("¿Qué es RAG?")
    """

    def __init__(
        self,
        chain: RAGChainPort,
        doc_store_adapter: DocumentStorePort,
        loader_adapter: DocumentLoaderPort,
        top_k: int = 4,
    ):
        """
        Inicializa el servicio RAG.

        Args:
            chain: Cadena RAG (implementa RAGChainPort)
            doc_store_adapter: Adapter para el almacén de documentos
            loader_adapter: Adapter para carga de documentos
            top_k: Número de documentos a recuperar (default: 4)

        Raises:
            ValueError: Si top_k es menor a 1
            RAGServiceError: Si hay error al inicializar componentes
        """
        self._validate_top_k(top_k)

        self.chain = chain
        self.doc_store = doc_store_adapter
        self.loader = loader_adapter
        self.top_k = top_k

        logger.info(f"RAGService inicializado con chain={type(chain).__name__}, top_k={top_k}")

    def _validate_top_k(self, top_k: int) -> None:
        """Valida que top_k sea un valor razonable."""
        if not isinstance(top_k, int) or top_k < 1:
            raise ValueError(f"top_k debe ser un entero positivo, got {top_k}")
        if top_k > 20:
            logger.warning(f"top_k={top_k} es alto, puede afectar rendimiento y costos")

    def ingest_document(self, file_path: str) -> int:
        """
        Carga, divide e indexa un documento individual.

        Args:
            file_path: Ruta al archivo a ingerir

        Raises:
            RAGServiceIngestionError: Si falla la ingesta
            FileNotFoundError: Si el archivo no existe
        """
        logger.info(f"Ingestando documento: {file_path}")

        try:
            chunks = self.loader.load_and_split(file_path)

            if not chunks:
                raise RAGServiceIngestionError(f"No se generaron fragmentos para: {file_path}")

            self.doc_store.add_documents(chunks)
            logger.info(f"Documento indexado: {file_path} ({len(chunks)} fragmentos)")

            return len(chunks)
        except FileNotFoundError:
            logger.error(f"Archivo no encontrado: {file_path}")
            raise
        except Exception as e:
            logger.error(f"Error en ingesta de {file_path}: {e}")
            raise RAGServiceIngestionError(f"Error ingesting {file_path}: {e}") from e

    def ingest_directory(self, dir_path: str) -> int:
        """
        Carga e indexa todos los documentos válidos de un directorio.

        Args:
            dir_path: Ruta al directorio a ingerir

        Raises:
            RAGServiceIngestionError: Si falla la ingesta
            FileNotFoundError: Si el directorio no existe

        Returns:
            Número de fragmentos generados
        """
        logger.info(f"Ingestando directorio: {dir_path}")

        try:
            chunks = self.loader.load_directory(dir_path)

            if not chunks:
                raise RAGServiceIngestionError(
                    f"No se encontraron documentos válidos en: {dir_path}"
                )

            self.doc_store.add_documents(chunks)
            logger.info(f"Directorio indexado: {dir_path} ({len(chunks)} fragmentos)")

            return len(chunks)
        except FileNotFoundError:
            logger.error(f"Directorio no encontrado: {dir_path}")
            raise
        except Exception as e:
            logger.error(f"Error en ingesta de directorio {dir_path}: {e}")
            raise RAGServiceIngestionError(f"Error ingesting directory {dir_path}: {e}") from e

    def ask(
        self,
        question: str,
        provider: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """
        Ejecuta el flujo RAG: Búsqueda Semántica → Generación Aumentada.

        Args:
            question: La pregunta del usuario
        # provider: Proveedor cloud
        # (openai, anthropic, google, groq, minimax, deepseek). None = local.
            model: Modelo específico del provider (None = usa default)
            api_key: API key para provider cloud (None = usa .env)

        Returns:
            Diccionario con:
                - answer: La respuesta generada
                - source_documents: Lista de documentos fuente usados

        Raises:
            RAGServiceQueryError: Si falla la consulta
            ValueError: Si la pregunta está vacía
        """
        try:
            query = Query(text=question)
        except ValueError as e:
            logger.warning(f"Consulta inválida: {e}")
            raise ValueError(f"Consulta inválida: {e}") from e

        logger.info(f"Procesando consulta: '{question[:100]}...'")

        try:
            if provider:
                result = self._ask_with_cloud_llm(query.text, provider, model, api_key)
            else:
                result = self.chain.invoke(query.text)

            answer_text = result.get("answer", "")
            if not answer_text or not answer_text.strip():
                logger.warning("Respuesta vacía del LLM")
                raise RAGServiceQueryError("LLM generated empty answer")

            context = result.get("context", [])
            source_documents = self._convert_context_to_documents(context)

            answer = Answer(text=answer_text.strip(), source_documents=source_documents)

            logger.info(
                f"Consulta completada: {len(answer.source_documents)} fuentes usadas",
                extra={
                    "question_length": len(query.text),
                    "answer_length": len(answer.text),
                    "sources_count": len(answer.source_documents),
                    "provider": provider or "local",
                },
            )

            return {
                "answer": answer.text,
                "source_documents": answer.source_documents,
            }

        except RAGServiceQueryError:
            raise
        except Exception as e:
            logger.error(f"Error en consulta RAG: {e}", exc_info=True)
            raise RAGServiceQueryError(f"Error executing RAG query: {e}") from e

    def _ask_with_cloud_llm(
        self,
        question: str,
        provider: str,
        model: str | None = None,
        api_key: str | None = None,
    ) -> dict[str, Any]:
        """
        Ejecuta consulta RAG con LLM cloud (no-LangChain).

        Cloud LLMs (LM Studio, OpenAI, Anthropic, etc.) usan HTTP API directa,
        no son compatibles con LangChainRAGAdapter. Esta implementación:
        1. Recupera documentos de ChromaDB
        2. Construye el prompt manualmente
        3. Llama generate_response() del adapter

        Args:
            question: La pregunta
            provider: Provider cloud
            model: Modelo específico (None = default)
            api_key: API key (None = .env)

        Returns:
            Dict con 'answer' y 'context'
        """
        from src.application.factories.llm_adapter_factory import LLMAdapterFactory

        try:
            cloud_llm = LLMAdapterFactory.create_cloud_adapter(
                provider=provider, model=model, api_key=api_key
            )

            retrieved = self.doc_store.search_similar(question, k=self.top_k)

            context_parts = []
            for doc in retrieved:
                content = doc.content if hasattr(doc, 'content') else str(doc)
                context_parts.append(content)
            context_text = "\n\n".join(context_parts)

            prompt = DEFAULT_RAG_PROMPT.format(
                context=context_text,
                input=question
            )

            answer_text = cloud_llm.generate_response(prompt)
            model_name = getattr(cloud_llm, 'model', model or 'unknown')
            logger.info(
                f"Consulta cloud completada con provider={provider}, model={model_name}"
            )

            return {
                "answer": answer_text,
                "context": retrieved,
            }

        except Exception as e:
            logger.error(f"Error con LLM cloud {provider}: {e}")
            raise RAGServiceQueryError(f"Cloud LLM error: {e}") from e

    def ask_stream(
        self,
        question: str,
        provider: str | None = None,
        max_tokens: int | None = None,
    ):
        """
        Ejecuta el flujo RAG con streaming token-por-token.

        Recupera documentos relevantes y emite tokens según los genera el LLM.

        Args:
            question: La pregunta del usuario
            provider: Provider cloud (None = local chain)
            max_tokens: Límite de tokens en la respuesta (solo cloud)

        Yields:
            Tokens generados por el LLM

        Raises:
            RAGServiceQueryError: Si falla la consulta
        """
        try:
            query = Query(text=question)
        except ValueError as e:
            raise ValueError(f"Consulta inválida: {e}") from e

        logger.info(f"Streaming query: '{question[:100]}...'")

        if provider:
            from src.application.factories.llm_adapter_factory import (
                LLMAdapterFactory,
            )

            try:
                cloud_llm = LLMAdapterFactory.create_cloud_adapter(provider=provider)
                retrieved = self.doc_store.search_similar(query.text, k=self.top_k)
                context_parts = [
                    doc.content if hasattr(doc, "content") else str(doc)
                    for doc in retrieved
                ]
                prompt = DEFAULT_RAG_PROMPT.format(
                    context="\n\n".join(context_parts),
                    input=query.text,
                )
                for token in cloud_llm.generate_stream(
                    prompt, max_tokens=max_tokens
                ):
                    yield token
            except Exception as e:
                logger.error(f"Cloud streaming error: {e}")
                raise RAGServiceQueryError(f"Cloud stream error: {e}") from e
        else:
            try:
                if hasattr(self.chain, "stream"):
                    for token in self.chain.stream(query.text):
                        yield token
                else:
                    result = self.chain.invoke(query.text)
                    yield result.get("answer", "")
            except Exception as e:
                logger.error(f"Local streaming error: {e}")
                raise RAGServiceQueryError(f"Local stream error: {e}") from e

    def _convert_context_to_documents(self, context: list[Any]) -> list[Document]:
        """
        Convierte el contexto de LangChain a lista de Document.

        Args:
            context: Lista de documentos de LangChain

        Returns:
            Lista de Document validados con Pydantic
        """
        documents = []

        for doc in context:
            try:
                # Manejar diferentes formatos de documento
                if hasattr(doc, "page_content") and hasattr(doc, "metadata"):
                    documents.append(
                        Document(
                            page_content=str(doc.page_content),
                            metadata=dict(doc.metadata) if doc.metadata else {},
                            id=getattr(doc, "id", None),
                        )
                    )
                elif isinstance(doc, dict):
                    documents.append(
                        Document(
                            page_content=str(doc.get("page_content", "")),
                            metadata=dict(doc.get("metadata", {})),
                            id=doc.get("id"),
                        )
                    )
                else:
                    # Fallback: crear documento con el contenido raw
                    documents.append(
                        Document(
                            page_content=str(doc),
                            metadata={"source": "unknown"},
                        )
                    )
            except Exception as e:
                logger.error(f"Error convirtiendo documento a Document: {e}")
                raise RAGServiceIngestionError(f"Error en conversión de documentos: {e}") from e

        return documents

    def get_document_count(self) -> int:
        """
        Obtiene el numero de documentos en el almacen vectorial.

        Returns:
            Numero de documentos indexados
        """
        try:
            if hasattr(self.doc_store, "count"):
                return self.doc_store.count()
            return 0
        except Exception as e:
            logger.error(f"No se pudo obtener conteo de documentos: {e}")
            raise RAGServiceError(f"Error al obtener conteo de documentos: {e}") from e

    def list_documents(self, limit: int = 20, offset: int = 0) -> dict[str, Any]:
        """
        Lista documentos con paginación.

        Args:
            limit: Máximo de documentos a retornar
            offset: Offset para paginación

        Returns:
            Dict con documents y total
        """
        try:
            if hasattr(self.doc_store, "list_documents"):
                documents, total = self.doc_store.list_documents(limit=limit, offset=offset)
                return {"documents": documents, "total": total}
            return {"documents": [], "total": 0}
        except Exception as e:
            logger.error(f"No se pudo listar documentos: {e}")
            raise RAGServiceError(f"Error al listar documentos: {e}") from e

    def delete_document(self, document_id: str) -> bool:
        """
        Elimina un documento por ID.

        Args:
            document_id: ID del documento a eliminar

        Returns:
            True si se eliminó
        """
        try:
            if hasattr(self.doc_store, "delete_document"):
                return self.doc_store.delete_document(document_id)
            return False
        except Exception as e:
            logger.error(f"No se pudo eliminar documento {document_id}: {e}")
            raise RAGServiceError(f"Error al eliminar documento: {e}") from e

    def update_top_k(self, top_k: int) -> None:
        """
        Actualiza dinámicamente el top_k para consultas futuras.

        Args:
            top_k: Nuevo número de documentos a recuperar
        """
        self._validate_top_k(top_k)
        self.top_k = top_k

        # Actualizar en la cadena RAG
        self.chain.update_retriever_config({"k": top_k})
        logger.info(f"top_k actualizado a {top_k}")

    def get_chain_info(self) -> dict[str, Any]:
        """
        Obtiene información sobre la cadena RAG configurada.

        Returns:
            Dict con información de la cadena
        """
        if hasattr(self.chain, "get_chain_info"):
            result = self.chain.get_chain_info()
            return cast(dict[str, Any], result)

        return {
            "type": type(self.chain).__name__,
            "top_k": self.top_k,
        }
