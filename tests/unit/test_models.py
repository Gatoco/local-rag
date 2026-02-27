# tests/unit/test_models.py
# Propósito: Tests unitarios para verificar que los modelos funcionan correctamente.

import pytest
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
        
        assert query.text == long_text
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
        
        answer.source_documents.append(doc)
        
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


# ═══════════════════════════════════════════════════════════════════════════
# TESTS DE VALIDACIÓN Y EDGE CASES
# ═══════════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    """Tests para casos límite y bordes"""
    
    def test_document_with_empty_string(self):
        """Test: Document con page_content vacío"""
        doc = Document(page_content="")
        
        assert doc.page_content == ""
    
    def test_query_with_empty_string(self):
        """Test: Query con texto vacío"""
        query = Query(text="")
        
        assert query.text == ""
    
    def test_answer_with_empty_string(self):
        """Test: Answer con texto vacío"""
        answer = Answer(text="")
        
        assert answer.text == ""
    
    def test_document_with_very_long_content(self):
        """Test: Document con contenido muy largo"""
        long_content = "A" * 100000
        doc = Document(page_content=long_content)
        
        assert len(doc.page_content) == 100000
    
    def test_empty_source_documents_list(self):
        """Test: Answer con lista de documentos vacía"""
        answer = Answer(text="Respuesta sin fuentes")
        
        assert answer.source_documents == []
        
        # Verificar que se puede iterar sin errores
        count = 0
        for _ in answer.source_documents:
            count += 1
        assert count == 0


# ═══════════════════════════════════════════════════════════════════════════
# TESTS DE ERRORES
# ═══════════════════════════════════════════════════════════════════════════

class TestErrorHandling:
    """Tests que verifican el manejo de errores"""
    
    def test_document_requires_page_content(self):
        """Test: Document REQUIERE page_content"""
        with pytest.raises(TypeError):
            Document()  # Falta page_content
    
    def test_query_requires_text(self):
        """Test: Query REQUIERE text"""
        with pytest.raises(TypeError):
            Query()  # Falta text
    
    def test_answer_requires_text(self):
        """Test: Answer REQUIERE text"""
        with pytest.raises(TypeError):
            Answer()  # Falta text
    
    def test_document_type_checking_page_content(self):
        """Test: page_content debe ser string"""
        # Nota: Python no valida tipos en runtime por defecto,
        # pero podemos verificar que se asigna
        doc = Document(page_content=123)  # Esto funciona pero es incorrecto
        
        # Verificamos que se asignó
        assert doc.page_content == 123
        # (En una aplicación real, usarías un validador como Pydantic)
