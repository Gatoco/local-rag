"""
Benchmarks de rendimiento para el sistema RAG.

Estos benchmarks miden:
- Latencia de consultas
- Throughput (consultas por segundo)
- Uso de memoria
- Tiempos de ingesta

Uso:
    pytest tests/benchmarks/test_performance.py --benchmark-only
    pytest tests/benchmarks/test_performance.py --benchmark-json=benchmark.json
"""

import pytest
import time
import os
from unittest.mock import Mock, patch
from typing import List, Dict


# ═══════════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def sample_questions() -> List[str]:
    """Lista de preguntas de ejemplo para benchmarks."""
    return [
        "¿Qué es Python?",
        "¿Cuál es la diferencia entre lista y tupla?",
        "Explica el concepto de decorador",
        "¿Qué es la programación orientada a objetos?",
        "¿Cómo funciona la gestión de memoria en Python?",
    ]


@pytest.fixture
def mock_rag_service():
    """Mock de RAGService para benchmarks sin dependencias reales."""
    from unittest.mock import Mock
    
    mock_service = Mock()
    mock_service.ask.return_value = {
        "answer": "Esta es una respuesta de prueba que simula la salida del LLM. " * 10,
        "source_documents": [
            Mock(page_content="Documento 1", metadata={"source": "test.pdf"}),
            Mock(page_content="Documento 2", metadata={"source": "test.pdf"}),
            Mock(page_content="Documento 3", metadata={"source": "test.pdf"}),
            Mock(page_content="Documento 4", metadata={"source": "test.pdf"}),
        ]
    }
    mock_service.get_document_count.return_value = 1000
    
    return mock_service


# ═══════════════════════════════════════════════════════════════════════════
# BENCHMARKS DE LATENCIA
# ═══════════════════════════════════════════════════════════════════════════

class TestQueryLatency:
    """Benchmarks de latencia de consultas"""

    def test_query_latency_single(self, benchmark, mock_rag_service):
        """Benchmark: Latencia de consulta individual"""
        def query():
            return mock_rag_service.ask("¿Qué es Python?")
        
        result = benchmark(query)
        
        assert result["answer"] is not None
        assert len(result["source_documents"]) == 4

    def test_query_latency_batch(self, benchmark, mock_rag_service, sample_questions):
        """Benchmark: Latencia de lote de consultas"""
        def query_batch():
            results = []
            for question in sample_questions:
                result = mock_rag_service.ask(question)
                results.append(result)
            return results
        
        results = benchmark(query_batch)
        
        assert len(results) == len(sample_questions)
        assert all(r["answer"] is not None for r in results)

    def test_query_latency_with_long_question(self, benchmark, mock_rag_service):
        """Benchmark: Latencia con pregunta larga"""
        long_question = "¿Qué es Python? " * 100  # ~1500 caracteres
        
        def query():
            return mock_rag_service.ask(long_question)
        
        result = benchmark(query)
        
        assert result["answer"] is not None


# ═══════════════════════════════════════════════════════════════════════════
# BENCHMARKS DE THROUGHPUT
# ═══════════════════════════════════════════════════════════════════════════

class TestThroughput:
    """Benchmarks de throughput (consultas por segundo)"""

    def test_queries_per_second(self, mock_rag_service):
        """Benchmark: Consultas por segundo"""
        num_queries = 10
        start_time = time.time()
        
        for i in range(num_queries):
            mock_rag_service.ask(f"Pregunta {i}")
        
        elapsed = time.time() - start_time
        qps = num_queries / elapsed
        
        print(f"\nThroughput: {qps:.2f} queries/second")
        print(f"Tiempo promedio: {elapsed/num_queries*1000:.2f} ms por consulta")
        
        assert qps > 0  # Al menos alguna consulta por segundo

    def test_concurrent_queries(self, mock_rag_service):
        """Benchmark: Consultas concurrentes (simuladas)"""
        import concurrent.futures
        
        num_workers = 5
        num_queries = 20
        
        def query_worker(question_id):
            return mock_rag_service.ask(f"Pregunta {question_id}")
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [
                executor.submit(query_worker, i)
                for i in range(num_queries)
            ]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        elapsed = time.time() - start_time
        qps = num_queries / elapsed
        
        print(f"\nThroughput concurrente: {qps:.2f} queries/second")
        print(f"Workers: {num_workers}, Queries: {num_queries}")
        
        assert len(results) == num_queries


# ═══════════════════════════════════════════════════════════════════════════
# BENCHMARKS DE MEMORIA
# ═══════════════════════════════════════════════════════════════════════════

class TestMemoryUsage:
    """Benchmarks de uso de memoria"""

    def test_memory_per_query(self, mock_rag_service):
        """Benchmark: Memoria usada por consulta"""
        try:
            import tracemalloc
            tracemalloc.start()
            
            # Ejecutar consulta
            mock_rag_service.ask("¿Qué es Python?")
            
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            peak_mb = peak / (1024 * 1024)
            print(f"\nMemoria peak: {peak_mb:.2f} MB")
            
            assert peak_mb < 500  # Menos de 500MB por consulta
            
        except ImportError:
            pytest.skip("tracemalloc no disponible")

    def test_memory_multiple_queries(self, mock_rag_service):
        """Benchmark: Memoria en múltiples consultas"""
        try:
            import tracemalloc
            tracemalloc.start()
            
            # Ejecutar 10 consultas
            for i in range(10):
                mock_rag_service.ask(f"Pregunta {i}")
            
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            peak_mb = peak / (1024 * 1024)
            print(f"\nMemoria peak (10 queries): {peak_mb:.2f} MB")
            
            # Debería ser menos de 1GB para 10 consultas
            assert peak_mb < 1000
            
        except ImportError:
            pytest.skip("tracemalloc no disponible")


# ═══════════════════════════════════════════════════════════════════════════
# BENCHMARKS DE INGESTA
# ═══════════════════════════════════════════════════════════════════════════

class TestIngestion:
    """Benchmarks de ingesta de documentos"""

    def test_ingest_single_document(self, benchmark):
        """Benchmark: Tiempo de ingesta de documento individual"""
        from unittest.mock import Mock

        mock_service = Mock()
        mock_service.ingest_document.return_value = None

        def ingest():
            mock_service.ingest_document("./test/doc.pdf")

        result = benchmark(ingest)

        assert result is None
        assert mock_service.ingest_document.call_count >= 1

    def test_ingest_directory(self, benchmark):
        """Benchmark: Tiempo de ingesta de directorio"""
        from unittest.mock import Mock

        mock_service = Mock()
        mock_service.ingest_directory.return_value = None

        def ingest_dir():
            mock_service.ingest_directory("./test/docs")

        result = benchmark(ingest_dir)

        assert result is None
        assert mock_service.ingest_directory.call_count >= 1


# ═══════════════════════════════════════════════════════════════════════════
# BENCHMARKS DE SERIALIZACIÓN
# ═══════════════════════════════════════════════════════════════════════════

class TestSerialization:
    """Benchmarks de serialización Pydantic"""

    def test_document_serialization(self, benchmark):
        """Benchmark: Serialización de Document"""
        from src.domain.models import Document
        
        doc = Document(
            page_content="Contenido de prueba " * 100,
            metadata={"source": "test.pdf", "page": 1},
            id="doc_001"
        )
        
        def serialize():
            return doc.model_dump()
        
        result = benchmark(serialize)
        
        assert result["page_content"] is not None
        assert result["metadata"]["source"] == "test.pdf"

    def test_answer_serialization(self, benchmark):
        """Benchmark: Serialización de Answer"""
        from src.domain.models import Document, Answer
        
        answer = Answer(
            text="Respuesta de prueba " * 100,
            source_documents=[
                Document(page_content="Doc 1", metadata={"source": "test1.pdf"}),
                Document(page_content="Doc 2", metadata={"source": "test2.pdf"}),
            ]
        )
        
        def serialize():
            return answer.model_dump()
        
        result = benchmark(serialize)
        
        assert result["text"] is not None
        assert len(result["source_documents"]) == 2


# ═══════════════════════════════════════════════════════════════════════════
# BENCHMARKS DE API REST
# ═══════════════════════════════════════════════════════════════════════════

class TestAPIPerformance:
    """Benchmarks de rendimiento de API REST"""

    def test_health_endpoint_latency(self, benchmark):
        """Benchmark: Latencia de health endpoint"""
        from unittest.mock import Mock

        mock_service = Mock()
        mock_service.get_document_count.return_value = 100
        mock_service.llm = Mock()
        mock_service.llm.model_path = "./models/TinyLlama-1.1B-Q4_K_M.gguf"

        from src.infrastructure.entrypoints.fastapi_adapter import create_app
        from fastapi.testclient import TestClient

        app = create_app(mock_service, enable_auth=False)
        client = TestClient(app)

        def health_check():
            return client.get("/api/v1/health")

        result = benchmark(health_check)

        assert result.status_code == 200

    def test_query_endpoint_latency(self, benchmark):
        """Benchmark: Latencia de query endpoint"""
        from unittest.mock import Mock, PropertyMock

        mock_service = Mock()
        mock_service.ask.return_value = {
            "answer": "Respuesta de prueba",
            "source_documents": []
        }
        mock_service.llm = PropertyMock()
        mock_service.llm.model_path = "./models/TinyLlama-1.1B-Q4_K_M.gguf"

        from src.infrastructure.entrypoints.fastapi_adapter import create_app
        from fastapi.testclient import TestClient

        app = create_app(mock_service, enable_auth=False)
        client = TestClient(app)
        
        def query():
            return client.post(
                "/api/v1/query",
                json={"question": "¿Qué es Python?", "top_k": 4}
            )
        
        result = benchmark(query)
        
        assert result.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════
# REPORTES DE BENCHMARKS
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def benchmark_report():
    """Fixture para generar reporte de benchmarks."""
    report = {
        "timestamp": time.time(),
        "tests": {},
    }
    yield report
    
    # Imprimir reporte al final
    print("\n" + "="*70)
    print("REPORTE DE BENCHMARKS".center(70))
    print("="*70)
    
    for test_name, metrics in report["tests"].items():
        print(f"\n{test_name}:")
        for metric, value in metrics.items():
            print(f"  {metric}: {value}")


class TestBenchmarkReporting:
    """Tests que generan reporte de benchmarks"""

    def test_query_performance_report(self, benchmark, mock_rag_service, benchmark_report):
        """Benchmark: Reporte de rendimiento de consultas"""
        times = []
        
        def query_and_track():
            start = time.time()
            result = mock_rag_service.ask("¿Qué es Python?")
            times.append(time.time() - start)
            return result
        
        result = benchmark(query_and_track)
        
        avg_time = sum(times) / len(times) * 1000  # ms
        
        benchmark_report["tests"]["query_performance"] = {
            "avg_latency_ms": round(avg_time, 2),
            "min_latency_ms": round(min(times) * 1000, 2),
            "max_latency_ms": round(max(times) * 1000, 2),
            "total_queries": len(times),
        }
