# src/domain/models.py
# Propósito: Define los modelos de datos fundamentales del dominio RAG.
# Estos modelos representan la esencia del negocio: Documentos, Consultas, Respuestas.
# Son completamente independientes de tecnologías externas (BD, LLM, etc).

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class Document:
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
    
    Atributos:
        page_content (str): El contenido de texto del documento/chunk
        metadata (Dict[str, Any]): Información sobre el documento (fuente, página, etc)
        id (Optional[str]): ID único generado por la BD vectorial
    
    Ejemplo:
        >>> doc = Document(
        ...     page_content="Python es un lenguaje de programación",
        ...     metadata={"source": "wikipedia", "page": 1},
        ...     id="doc_001"
        ... )
        >>> doc.page_content
        "Python es un lenguaje de programación"
    """
    
    page_content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: Optional[str] = None


@dataclass
class Query:
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
    
    Atributos:
        text (str): El texto completo de la pregunta/consulta
    
    Ejemplo:
        >>> query = Query(text="¿Qué es Python?")
        >>> query.text
        "¿Qué es Python?"
    """
    
    text: str


@dataclass
class Answer:
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
    
    Atributos:
        text (str): El texto de la respuesta generada por el LLM
        source_documents (List[Document]): Documentos base para la respuesta
    
    Ejemplo:
        >>> doc1 = Document(page_content="Python es un lenguaje interpretado...")
        >>> answer = Answer(
        ...     text="Python es un lenguaje de programación interpretado.",
        ...     source_documents=[doc1]
        ... )
        >>> answer.text
        "Python es un lenguaje de programación interpretado."
        >>> len(answer.source_documents)
        1
    """
    
    text: str
    source_documents: List[Document] = field(default_factory=list)
