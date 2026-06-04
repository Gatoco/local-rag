"""
Modelos de dominio del sistema RAG.

Estos modelos representan la esencia del negocio: Documentos, Consultas, Respuestas.
Son completamente independientes de tecnologías externas (BD, LLM, etc).

Usa Pydantic v2 para validación automática de tipos y serialización.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Document(BaseModel):
    """
    Representa un fragmento de contenido de texto con metadatos opcionales.

    En el contexto de RAG, un Document es:
    - Un trozo de texto (chunk) de un documento original
    - Puede tener metadatos: dónde viene, página, sección, etc.
    - Tiene un ID opcional para tracking en la BD vectorial

    Ciclo de vida de un Document:
    1. Se CARGA de un archivo (CSV, PDF, etc) vía DocumentLoaderPort
    2. Se DIVIDE en chunks (si es muy grande) vía split_documents()
    3. Se le genera un EMBEDDING (representación vectorial) vía EmbeddingPort
    4. Se ALMACENA en ChromaDB vía DocumentStorePort.add_documents()
    5. Se RETORNA como "fuente" en Answer cuando es relevante

    Attributes:
        page_content: El contenido de texto del documento/chunk
        metadata: Información sobre el documento (fuente, página, etc)
        id: ID único generado por la BD vectorial

    Example:
        >>> doc = Document(
        ...     page_content="Python es un lenguaje de programación",
        ...     metadata={"source": "wikipedia", "page": 1},
        ...     id="doc_001"
        ... )
        >>> doc.page_content
        'Python es un lenguaje de programación'
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    page_content: str = Field(
        ..., min_length=1, description="El contenido de texto del documento/chunk"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Información sobre el documento (fuente, página, etc)"
    )
    id: str | None = Field(default=None, description="ID único generado por la BD vectorial")

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Valida que los valores del metadata sean serializables."""
        for key, value in v.items():
            if not isinstance(value, (str, int, float, bool, type(None), list, dict)):
                raise ValueError(
                    f"Metadata value for '{key}' must be JSON serializable, got {type(value)}"
                )
        return v

    def __repr__(self) -> str:
        content_preview = (
            self.page_content[:50] + "..." if len(self.page_content) > 50 else self.page_content
        )
        return f"Document(id={self.id!r}, content={content_preview!r})"


class Query(BaseModel):
    """
    Representa una consulta (pregunta) del usuario al sistema RAG.

    Es deliberadamente sencilla porque:
    - La complejidad está en PROCESAR la query, no en representarla
    - Solo necesitamos el texto de la pregunta
    - El sistema decide cómo procesarla

    Ciclo de vida de una Query:
    1. Usuario escribe: "¿Cuál es el impacto financiero?"
    2. Se crea Query(text="¿Cuál es el impacto financiero?")
    3. RAGService.query() recibe esta Query
    4. Se genera embedding de la query
    5. Se buscan documentos similares
    6. Se retorna una Answer

    Attributes:
        text: El texto completo de la pregunta/consulta

    Example:
        >>> query = Query(text="¿Qué es Python?")
        >>> query.text
        '¿Qué es Python?'
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    text: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="El texto completo de la pregunta/consulta",
    )

    @field_validator("text")
    @classmethod
    def validate_text_not_empty(cls, v: str) -> str:
        """Valida que el texto no esté vacío o solo whitespace."""
        if not v.strip():
            raise ValueError("Query text cannot be empty or whitespace only")
        return v

    def __repr__(self) -> str:
        text_preview = self.text[:50] + "..." if len(self.text) > 50 else self.text
        return f"Query(text={text_preview!r})"


class Answer(BaseModel):
    """
    Representa la respuesta generada por el sistema RAG.

    Contiene dos partes clave:
    1. text: El contenido de la respuesta (generado por LLM)
    2. source_documents: Los documentos que sustentan esta respuesta

    ¿Por qué incluir source_documents?
    - TRAZABILIDAD: El usuario sabe en qué se basa la respuesta
    - AUDITORÍA: Puedes verificar si la IA usó buenas fuentes
    - CONFIANZA: Las respuestas con fuentes son más creíbles
    - DEBUGGING: Si la respuesta es mala, puedes mirar qué documentos se usaron

    Ciclo de vida de una Answer:
    1. RAGService.query() recibe una Query
    2. Busca documentos similares
    3. Construye un prompt con esos documentos
    4. LLM genera respuesta
    5. Se crea Answer(text=respuesta_generada, source_documents=docs_usados)
    6. Se retorna al usuario con trazabilidad completa

    Attributes:
        text: El texto de la respuesta generada por el LLM
        source_documents: Documentos base para la respuesta

    Example:
        >>> doc1 = Document(page_content="Python es un lenguaje interpretado...")
        >>> answer = Answer(
        ...     text="Python es un lenguaje de programación interpretado.",
        ...     source_documents=[doc1]
        ... )
        >>> answer.text
        'Python es un lenguaje de programación interpretado.'
        >>> len(answer.source_documents)
        1
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    text: str = Field(
        ..., min_length=1, description="El texto de la respuesta generada por el LLM"
    )
    source_documents: list[Document] = Field(
        default=[], description="Documentos fuente que sustentan la respuesta"
    )

    def add_source_document(self, document: Document) -> None:
        """
        Agrega un documento fuente a la respuesta.

        Args:
            document: El documento a agregar
        """
        self.source_documents.append(document)

    def get_unique_sources(self) -> list[str]:
        """
        Obtiene una lista de fuentes únicas de los documentos.

        Returns:
            Lista de strings con las fuentes únicas
        """
        sources = set()
        for doc in self.source_documents:
            source = doc.metadata.get("source", "desconocido")
            sources.add(source)
        return list(sources)

    def __repr__(self) -> str:
        text_preview = self.text[:50] + "..." if len(self.text) > 50 else self.text
        n_docs = len(self.source_documents)
        return f"Answer(text={text_preview!r}, sources={n_docs})"
