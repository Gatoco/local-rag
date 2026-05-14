"""
RAGService - Servicio de orquestación del sistema RAG.

Este servicio coordina los diferentes componentes (LLM, vector store, loader)
para implementar el flujo completo de Retrieval-Augmented Generation.

Características:
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
from src.domain.models import Answer, Document, Query
from src.domain.ports.document_loader_port import DocumentLoaderPort
from src.domain.ports.document_store_port import DocumentStorePort

logger = logging.getLogger(__name__)


class RAGServiceError(Exception):
    """Excepción base para errores del servicio RAG."""
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

    def ingest_document(self, file_path: str) -> None:
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
            print(f"[+] Documento indexado correctamente: {len(chunks)} fragmentos.")

        except FileNotFoundError:
            logger.error(f"Archivo no encontrado: {file_path}")
            raise
        except Exception as e:
            logger.error(f"Error en ingesta de {file_path}: {e}")
            raise RAGServiceIngestionError(f"Error ingesting {file_path}: {e}") from e

    def ingest_directory(self, dir_path: str) -> None:
        """
        Carga e indexa todos los documentos válidos de un directorio.

        Args:
            dir_path: Ruta al directorio a ingerir

        Raises:
            RAGServiceIngestionError: Si falla la ingesta
            FileNotFoundError: Si el directorio no existe
        """
        logger.info(f"Ingestando directorio: {dir_path}")

        try:
            chunks = self.loader.load_directory(dir_path)

            if not chunks:
                raise RAGServiceIngestionError(f"No se encontraron documentos válidos en: {dir_path}")

            self.doc_store.add_documents(chunks)
            logger.info(f"Directorio indexado: {dir_path} ({len(chunks)} fragmentos)")
            print(f"[+] Directorio indexado correctamente: {len(chunks)} fragmentos totales.")

        except FileNotFoundError:
            logger.error(f"Directorio no encontrado: {dir_path}")
            raise
        except Exception as e:
            logger.error(f"Error en ingesta de directorio {dir_path}: {e}")
            raise RAGServiceIngestionError(f"Error ingesting directory {dir_path}: {e}") from e

    def ask(self, question: str) -> dict[str, Any]:
        """
        Ejecuta el flujo RAG: Búsqueda Semántica → Generación Aumentada.

        Args:
            question: La pregunta del usuario

        Returns:
            Diccionario con:
                - answer: La respuesta generada
                - source_documents: Lista de documentos fuente usados

        Raises:
            RAGServiceQueryError: Si falla la consulta
            ValueError: Si la pregunta está vacía
        """
        # Validar entrada con Pydantic
        try:
            query = Query(text=question)
        except ValueError as e:
            logger.warning(f"Consulta inválida: {e}")
            raise ValueError(f"Consulta inválida: {e}") from e

        logger.info(f"Procesando consulta: '{question[:100]}...'")

        try:
            # Ejecutar cadena RAG (abstracta, no LangChain directamente)
            result = self.chain.invoke(query.text)

            # Validar que hay respuesta
            answer_text = result.get("answer", "")
            if not answer_text or not answer_text.strip():
                logger.warning("Respuesta vacía del LLM")
                raise RAGServiceQueryError("LLM generated empty answer")

            # Convertir contexto a documentos Pydantic
            context = result.get("context", [])
            source_documents = self._convert_context_to_documents(context)

            # Crear Answer con Pydantic para validación
            answer = Answer(
                text=answer_text.strip(),
                source_documents=source_documents
            )

            logger.info(
                f"Consulta completada: {len(answer.source_documents)} fuentes usadas",
                extra={
                    "question_length": len(query.text),
                    "answer_length": len(answer.text),
                    "sources_count": len(answer.source_documents),
                }
            )

            # Retornar dict para compatibilidad
            return {
                "answer": answer.text,
                "source_documents": answer.source_documents,
            }

        except RAGServiceQueryError:
            raise
        except Exception as e:
            logger.error(f"Error en consulta RAG: {e}", exc_info=True)
            raise RAGServiceQueryError(f"Error executing RAG query: {e}") from e

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
                if hasattr(doc, 'page_content') and hasattr(doc, 'metadata'):
                    documents.append(Document(
                        page_content=str(doc.page_content),
                        metadata=dict(doc.metadata) if doc.metadata else {},
                        id=getattr(doc, 'id', None),
                    ))
                elif isinstance(doc, dict):
                    documents.append(Document(
                        page_content=str(doc.get('page_content', '')),
                        metadata=dict(doc.get('metadata', {})),
                        id=doc.get('id'),
                    ))
                else:
                    # Fallback: crear documento con el contenido raw
                    documents.append(Document(
                        page_content=str(doc),
                        metadata={'source': 'unknown'},
                    ))
            except Exception as e:
                logger.warning(f"Error convirtiendo documento a Document: {e}")
                continue

        return documents

    def get_document_count(self) -> int:
        """
        Obtiene el número de documentos en el almacén vectorial.

        Returns:
            Número de documentos indexados
        """
        try:
            # ChromaDB tiene método _collection.count()
            if hasattr(self.doc_store, 'vector_store'):
                count = self.doc_store.vector_store._collection.count()
                return cast(int, count)
            return 0
        except Exception as e:
            logger.warning(f"No se pudo obtener conteo de documentos: {e}")
            return 0

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
        if hasattr(self.chain, 'get_chain_info'):
            result = self.chain.get_chain_info()
            return cast(dict[str, Any], result)

        return {
            "type": type(self.chain).__name__,
            "top_k": self.top_k,
        }
