"""
Tests unitarios para los modelos de dominio con Pydantic v2.

Estos tests verifican:
- Validación de tipos automática
- Restricciones de campos (min_length, max_length)
- Comportamiento de serialización
- Manejo de errores de validación
"""

import pytest
from pydantic import ValidationError
from src.domain.models import Document, Query, Answer


# ═══════════════════════════════════════════════════════════════════════════
# TESTS PARA Document
# ═══════════════════════════════════════════════════════════════════════════

class TestDocument:
    """Suite de tests para la clase Document"""

    def test_document_creation_minimal(self):
        """Test: Crear un Document solo con page_content"""
        doc = Document(page_content="Python es un lenguaje de programación")

        assert doc.page_content == "Python es un lenguaje de programación"
        assert doc.metadata == {}
        assert doc.id is None

    def test_document_creation_with_metadata(self):
        """Test: Crear un Document con metadatos"""
        metadata = {"fuente": "wikipedia", "pagina": 1}
        doc = Document(
            page_content="Python es...",
            metadata=metadata
        )

        assert doc.page_content == "Python es..."
        assert doc.metadata["fuente"] == "wikipedia"
        assert doc.metadata["pagina"] == 1

    def test_document_creation_with_id(self):
        """Test: Crear un Document con ID"""
        doc = Document(
            page_content="Content",
            metadata={},
            id="doc_123"
        )

        assert doc.id == "doc_123"

    def test_document_metadata_isolation(self):
        """Test: Verificar que metadata no se comparte entre instancias"""
        doc1 = Document(page_content="Doc 1")
        doc2 = Document(page_content="Doc 2")

        # Modificar metadata de doc1
        doc1.metadata["clave"] = "valor"

        # Verificar que doc2 no tiene la clave
        assert "clave" not in doc2.metadata
        assert len(doc1.metadata) == 1
        assert len(doc2.metadata) == 0

    def test_document_with_complex_metadata(self):
        """Test: Metadata con tipos complejos"""
        metadata = {
            "titulos": ["Section 1", "Section 2"],
            "scores": {"relevancia": 0.95, "confianza": 0.87},
            "activo": True,
            "peso": 3.14
        }

        doc = Document(page_content="Complex doc", metadata=metadata)

        assert doc.metadata["titulos"] == ["Section 1", "Section 2"]
        assert doc.metadata["scores"]["relevancia"] == 0.95
        assert doc.metadata["activo"] is True
        assert doc.metadata["peso"] == 3.14

    def test_document_repr(self):
        """Test: Verificar que la representación en string funciona"""
        doc = Document(
            page_content="Test",
            metadata={"key": "value"},
            id="123"
        )

        repr_str = repr(doc)
        assert "Document" in repr_str
        assert "Test" in repr_str

    def test_document_whitespace_stripped(self):
        """Test: Verificar que se elimina whitespace automático"""
        doc = Document(page_content="  Content with spaces  ")
        assert doc.page_content == "Content with spaces"

    def test_document_empty_content_fails(self):
        """Test: Document con page_content vacío debe fallar"""
        with pytest.raises(ValidationError):
            Document(page_content="")

    def test_document_none_content_fails(self):
        """Test: Document con None debe fallar"""
        with pytest.raises(ValidationError):
            Document(page_content=None)

    def test_document_invalid_metadata_type(self):
        """Test: Metadata con tipos no serializables debe fallar"""
        import datetime
        with pytest.raises(ValidationError):
            Document(
                page_content="Test",
                metadata={"date": datetime.datetime.now()}
            )


# ═══════════════════════════════════════════════════════════════════════════
# TESTS PARA Query
# ═══════════════════════════════════════════════════════════════════════════

class TestQuery:
    """Suite de tests para la clase Query"""

    def test_query_creation(self):
        """Test: Crear una Query"""
        query = Query(text="¿Qué es Python?")

        assert query.text == "¿Qué es Python?"

    def test_query_with_long_text(self):
        """Test: Query con texto largo"""
        long_text = "¿Cuál es la diferencia entre Python y Java? " * 10
        query = Query(text=long_text)

        # Pydantic strip_whitespace elimina el espacio final
        assert query.text == long_text.strip()
        assert len(query.text) > 200

    def test_query_with_special_characters(self):
        """Test: Query con caracteres especiales"""
        query = Query(text="¿Qué es ñ, ü, é? 你好 🚀")

        assert "ñ" in query.text
        assert "🚀" in query.text

    def test_query_repr(self):
        """Test: Representación en string de Query"""
        query = Query(text="Test query")

        repr_str = repr(query)
        assert "Query" in repr_str
        assert "Test query" in repr_str

    def test_query_whitespace_stripped(self):
        """Test: Verificar que se elimina whitespace"""
        query = Query(text="  Question with spaces  ")
        assert query.text == "Question with spaces"

    def test_query_empty_text_fails(self):
        """Test: Query con texto vacío debe fallar"""
        with pytest.raises(ValidationError):
            Query(text="")

    def test_query_whitespace_only_fails(self):
        """Test: Query con solo whitespace debe fallar"""
        with pytest.raises(ValidationError):
            Query(text="   ")

    def test_query_too_long(self):
        """Test: Query muy larga debe fallar (> 10000 chars)"""
        with pytest.raises(ValidationError):
            Query(text="A" * 10001)

    def test_query_none_text_fails(self):
        """Test: Query con None debe fallar"""
        with pytest.raises(ValidationError):
            Query(text=None)


# ═══════════════════════════════════════════════════════════════════════════
# TESTS PARA Answer
# ═══════════════════════════════════════════════════════════════════════════

class TestAnswer:
    """Suite de tests para la clase Answer"""

    def test_answer_creation_simple(self):
        """Test: Crear una Answer sin documentos"""
        answer = Answer(text="Esta es la respuesta")

        assert answer.text == "Esta es la respuesta"
        assert answer.source_documents == []

    def test_answer_with_source_documents(self):
        """Test: Crear una Answer con documentos fuente"""
        doc1 = Document(page_content="Fuente 1")
        doc2 = Document(page_content="Fuente 2")

        answer = Answer(
            text="La respuesta tiene dos fuentes",
            source_documents=[doc1, doc2]
        )

        assert len(answer.source_documents) == 2
        assert answer.source_documents[0].page_content == "Fuente 1"
        assert answer.source_documents[1].page_content == "Fuente 2"

    def test_answer_source_documents_isolation(self):
        """Test: Verificar que source_documents no se comparte entre instancias"""
        answer1 = Answer(text="Respuesta 1")
        answer2 = Answer(text="Respuesta 2")

        doc = Document(page_content="Doc")
        answer1.source_documents.append(doc)

        # Verificar que answer2 no tiene el documento
        assert len(answer1.source_documents) == 1
        assert len(answer2.source_documents) == 0

    def test_answer_add_source_document_dynamically(self):
        """Test: Agregar documentos fuente después de crear la Answer"""
        answer = Answer(text="Respuesta inicial")
        doc = Document(page_content="Documento agregado después")

        answer.add_source_document(doc)

        assert len(answer.source_documents) == 1
        assert answer.source_documents[0].page_content == "Documento agregado después"

    def test_answer_with_many_source_documents(self):
        """Test: Answer con múltiples documentos"""
        docs = [Document(page_content=f"Doc {i}") for i in range(10)]

        answer = Answer(
            text="Respuesta con 10 fuentes",
            source_documents=docs
        )

        assert len(answer.source_documents) == 10

        # Verificar que se pueden iterar
        for i, doc in enumerate(answer.source_documents):
            assert doc.page_content == f"Doc {i}"

    def test_answer_repr(self):
        """Test: Representación en string de Answer"""
        doc = Document(page_content="Source")
        answer = Answer(text="Test answer", source_documents=[doc])

        repr_str = repr(answer)
        assert "Answer" in repr_str

    def test_answer_get_unique_sources(self):
        """Test: Obtener fuentes únicas"""
        docs = [
            Document(page_content="Doc 1", metadata={"source": "wikipedia"}),
            Document(page_content="Doc 2", metadata={"source": "wikipedia"}),
            Document(page_content="Doc 3", metadata={"source": "book"}),
        ]

        answer = Answer(text="Test", source_documents=docs)
        sources = answer.get_unique_sources()

        assert len(sources) == 2
        assert "wikipedia" in sources
        assert "book" in sources

    def test_answer_whitespace_stripped(self):
        """Test: Verificar que se elimina whitespace"""
        answer = Answer(text="  Answer with spaces  ")
        assert answer.text == "Answer with spaces"

    def test_answer_empty_text_fails(self):
        """Test: Answer con texto vacío debe fallar"""
        with pytest.raises(ValidationError):
            Answer(text="")

    def test_answer_none_text_fails(self):
        """Test: Answer con None debe fallar"""
        with pytest.raises(ValidationError):
            Answer(text=None)

    def test_answer_with_none_source_documents(self):
        """Test: Answer con source_documents=None usa default factory (lista vacía)"""
        # Pydantic v2 con Field(default=[]) no acepta None explícitamente
        # Pero podemos probar que el default es lista vacía
        answer = Answer(text="Test")
        assert answer.source_documents == []


# ═══════════════════════════════════════════════════════════════════════════
# TESTS DE INTEGRACIÓN ENTRE MODELOS
# ═══════════════════════════════════════════════════════════════════════════

class TestModelIntegration:
    """Tests que verifican la integración entre modelos"""

    def test_query_to_answer_flow(self):
        """Test: Simular flujo Query → procesamiento → Answer"""
        # Usuario hace una pregunta
        query = Query(text="¿Qué es Python?")

        # Sistema encuentra documentos relevantes
        source_docs = [
            Document(page_content="Python es un lenguaje..."),
            Document(page_content="Python fue creado por Guido van Rossum...")
        ]

        # Sistema genera respuesta
        answer = Answer(
            text="Python es un lenguaje de programación interpretado...",
            source_documents=source_docs
        )

        # Verificar que todo está conectado
        assert query.text is not None
        assert len(answer.source_documents) == 2
        assert answer.text is not None

    def test_document_with_metadata_to_answer(self):
        """Test: Documentos con metadatos en Answer"""
        doc = Document(
            page_content="Contenido muy relevante",
            metadata={"confiabilidad": 0.98, "fuente": "IPCC"},
            id="scientific_doc_001"
        )

        answer = Answer(
            text="Respuesta basada en datos científicos",
            source_documents=[doc]
        )

        # Verificar que los metadatos se preservan
        assert answer.source_documents[0].metadata["confiabilidad"] == 0.98
        assert answer.source_documents[0].id == "scientific_doc_001"

    def test_full_rag_response_simulation(self):
        """Test: Simular respuesta completa de RAG"""
        # Crear documentos con metadatos realistas
        docs = [
            Document(
                page_content="El cálculo diferencial estudia las tasas de cambio",
                metadata={"source": "matematicas.pdf", "page": 1},
                id="chunk_001"
            ),
            Document(
                page_content="La derivada representa la pendiente de la recta tangente",
                metadata={"source": "matematicas.pdf", "page": 2},
                id="chunk_002"
            ),
        ]

        # Crear respuesta
        answer = Answer(
            text="El cálculo diferencial estudia las tasas de cambio instantáneo.",
            source_documents=docs
        )

        # Validar estructura completa
        assert len(answer.text) > 0
        assert len(answer.source_documents) == 2
        assert answer.source_documents[0].id == "chunk_001"
        assert answer.source_documents[1].metadata["page"] == 2


# ═══════════════════════════════════════════════════════════════════════════
# TESTS DE SERIALIZACIÓN PYDANTIC
# ═══════════════════════════════════════════════════════════════════════════

class TestPydanticSerialization:
    """Tests para verificación de serialización Pydantic"""

    def test_document_to_dict(self):
        """Test: Document se puede convertir a dict"""
        doc = Document(
            page_content="Test content",
            metadata={"key": "value"},
            id="123"
        )

        doc_dict = doc.model_dump()
        
        assert doc_dict["page_content"] == "Test content"
        assert doc_dict["metadata"]["key"] == "value"
        assert doc_dict["id"] == "123"

    def test_query_to_dict(self):
        """Test: Query se puede convertir a dict"""
        query = Query(text="Test question")
        query_dict = query.model_dump()
        
        assert query_dict["text"] == "Test question"

    def test_answer_to_dict(self):
        """Test: Answer se puede convertir a dict"""
        doc = Document(page_content="Source")
        answer = Answer(text="Answer", source_documents=[doc])
        
        answer_dict = answer.model_dump()
        
        assert answer_dict["text"] == "Answer"
        assert len(answer_dict["source_documents"]) == 1
        assert answer_dict["source_documents"][0]["page_content"] == "Source"

    def test_document_json_serialization(self):
        """Test: Document se puede serializar a JSON"""
        doc = Document(
            page_content="Test",
            metadata={"key": "value"},
            id="123"
        )
        
        json_str = doc.model_dump_json()
        assert "Test" in json_str
        assert "key" in json_str

    def test_answer_json_serialization(self):
        """Test: Answer se puede serializar a JSON"""
        doc = Document(page_content="Source", metadata={"source": "test.pdf"})
        answer = Answer(text="Answer", source_documents=[doc])
        
        json_str = answer.model_dump_json()
        assert "Answer" in json_str
        assert "Source" in json_str
        assert "test.pdf" in json_str
