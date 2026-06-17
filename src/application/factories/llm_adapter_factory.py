"""
LLM Adapter Factory - Crea instancias de adapters de LLM.

Provee metodos estaticos para crear adapters de LLM y chains RAG,
desacoplando RAGService de las implementaciones concretas.
"""

import logging

from src.application.ports.rag_chain_port import RAGChainPort
from src.domain.ports.document_store_port import DocumentStorePort
from src.domain.ports.llm_port import LLMPort

logger = logging.getLogger(__name__)

DEFAULT_RAG_PROMPT = """Eres un asistente experto en responder preguntas basadas en el contexto proporcionado.

Contexto: {context}

Pregunta: {input}

Responde de manera clara y concisa basandote unicamente en el contexto proporcionado."""


class LLMAdapterFactory:
    @staticmethod
    def create_cloud_adapter(
        provider: str,
        model: str | None = None,
        api_key: str | None = None,
    ) -> LLMPort:
        """
        Crea un adapter de LLM cloud segun el provider.

        Args:
            provider: Nombre del provider (openai, anthropic, google, groq, minimax, deepseek)
            model: Modelo especifico (None = default del provider)
            api_key: API key (None = lee de entorno)

        Returns:
            Instancia de LLMPort para el provider solicitado

        Raises:
            ValueError: Si el provider no es soportado
        """
        from src.infrastructure.adapters.cloud_llm_adapter import CloudLLMAdapter

        try:
            adapter = CloudLLMAdapter(provider=provider, model=model, api_key=api_key)
            logger.debug(f"Created CloudLLMAdapter for provider={provider}, model={model}")
            return adapter
        except Exception as e:
            logger.error(f"Error creando CloudLLMAdapter para {provider}: {e}")
            raise ValueError(f"Provider no soportado: {provider}") from e

    @staticmethod
    def create_rag_chain(
        llm_adapter: LLMPort,
        doc_store: DocumentStorePort,
        prompt_template: str | None = None,
        top_k: int = 4,
    ) -> RAGChainPort:
        """
        Crea un chain RAG usando LangChain.

        Args:
            llm_adapter: Adapter de LLM a usar
            doc_store: Adapter del almacen de documentos
            prompt_template: Template de prompt (None = default)
            top_k: Numero de documentos a recuperar

        Returns:
            Instancia de RAGChainPort
        """
        from src.infrastructure.adapters.langchain_rag_adapter import LangChainRAGAdapter

        template = prompt_template or DEFAULT_RAG_PROMPT
        try:
            chain = LangChainRAGAdapter(
                llm_adapter=llm_adapter,
                doc_store=doc_store,
                prompt_template=template,
                top_k=top_k,
            )
            logger.debug(f"Created LangChainRAGAdapter with top_k={top_k}")
            return chain
        except Exception as e:
            logger.error(f"Error creando LangChainRAGAdapter: {e}")
            raise
