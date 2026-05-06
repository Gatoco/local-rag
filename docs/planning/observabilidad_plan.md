# 📊 Plan de Implementación de Observabilidad

Este documento detalla la hoja de ruta para integrar capacidades de observabilidad en el proyecto **Local-RAG**. El objetivo es transformar el sistema de una "caja negra" a un sistema transparente, medible y optimizable, manteniendo el principio de ejecución local.

## 🎯 Objetivos
1. **Tracing:** Visualizar el flujo completo de una consulta (Query -> Retrieval -> LLM).
2. **Métricas:** Medir latencias, uso de tokens y eficiencia de la caché.
3. **Evaluación:** Cuantificar la calidad de las respuestas (evitar alucinaciones).

---

## Fase 1: Tracing de Cadenas (Arize Phoenix)
*Prioridad: Alta. Permite depurar por qué el RAG da respuestas incorrectas.*

- [ ] **Configuración del Entorno**
    - [ ] Investigar compatibilidad de Arize Phoenix con la versión actual de LangChain.
    - [ ] Añadir `arize-phoenix` y `openinference-instrumentation-langchain` a `requirements.txt`.
    - [ ] Actualizar `docker-compose.yml` para incluir el servicio de Phoenix (puerto 6006).
- [ ] **Instrumentación del Código**
    - [ ] Configurar el `TracerProvider` en `src/infrastructure/adapters/langchain_rag_adapter.py`.
    - [ ] Implementar el exportador de OpenTelemetry hacia el colector local de Phoenix.
- [ ] **Validación**
    - [ ] Verificar que las trazas de `Retrieval` muestran los documentos exactos recuperados de ChromaDB.
    - [ ] Confirmar que se capturan los tiempos de ejecución de cada nodo de la cadena.

## Fase 2: Métricas y Dashboards (Prometheus/Grafana)
*Prioridad: Media. Útil para monitorizar la salud del servicio en "producción local".*

- [ ] **Exposición de Métricas**
    - [ ] Instalar `prometheus-fastapi-instrumentator`.
    - [ ] Configurar el middleware en `src/infrastructure/entrypoints/fastapi_adapter.py`.
- [ ] **Infraestructura de Monitoreo**
    - [ ] Añadir Prometheus al `docker-compose.yml` con configuración de scraping al endpoint `/metrics`.
    - [ ] Añadir Grafana al `docker-compose.yml`.
- [ ] **Visualización**
    - [ ] Crear un dashboard en Grafana que incluya:
        - [ ] Latencia P95 de la API.
        - [ ] Tiempo de búsqueda en ChromaDB vs Tiempo de inferencia LLM.
        - [ ] Hit Rate del `semantic_cache.py`.
        - [ ] Consumo de memoria del proceso de Llama.cpp/Ollama.

## Fase 3: Evaluación de Calidad (RAGAS Framework)
*Prioridad: Alta (Científica). Permite medir si las mejoras en el código realmente mejoran las respuestas.*

- [ ] **Dataset de Evaluación**
    - [ ] Crear un "Gold Dataset" en `docs/evaluation/test_set.json` con preguntas y respuestas de referencia.
- [ ] **Implementación de Evaluación**
    - [ ] Crear un script `evaluate_rag.py` que utilice la librería `ragas`.
    - [ ] Configurar métricas clave:
        - [ ] **Faithfulness:** ¿La respuesta proviene solo del contexto?
        - [ ] **Answer Relevance:** ¿Responde realmente a la pregunta?
        - [ ] **Context Precision:** ¿Los documentos recuperados eran los correctos?
- [ ] **Automatización**
    - [ ] Integrar la evaluación en el flujo de `tests/benchmarks/`.

## Fase 4: Logs Estructurados y Correlación
*Prioridad: Baja (Mantenimiento).*

- [ ] **Refactorización de Logs**
    - [ ] Modificar `src/infrastructure/utils/logging_config.py` para emitir logs en formato JSON.
- [ ] **Correlación**
    - [ ] Inyectar el `trace_id` de OpenTelemetry en los logs de cada petición para cruzar logs con trazas.

---

## 🛠 Herramientas Seleccionadas
| Capacidad | Herramienta | Motivo |
| :--- | :--- | :--- |
| **Tracing** | Arize Phoenix | Open Source, Local-first, excelente integración con LangChain. |
| **Métricas** | Prometheus | Estándar de la industria, ligero. |
| **Dashboards** | Grafana | Visualización profesional. |
| **Evaluación** | RAGAS | El estándar para evaluar pipelines de RAG cuantitativamente. |
