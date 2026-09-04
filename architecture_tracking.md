# Seguimiento de Arquitectura y Reorganización del Proyecto

Este documento detalla la reorganización del código y la implementación de las propuestas de arquitectura para el proyecto **CRMsDataSpace** (Espacio de Datos de Materias Primas Críticas).

---

## 1. Reorganización del Directorio `/code`

Para resolver el caos en el directorio `/code` que contenía docenas de scripts sueltos, hemos estructurado el código en subcarpetas lógicas y modulares:

*   **`/code/common/`**: Archivos y librerías comunes compartidas entre distintas variantes.
    *   `mock_api.py`: Simulador de base de datos Apache Solr / WARM.
    *   `search.py`: Motor de búsqueda semántica local (FAISS) sobre PDFs.
    *   `extract_text.py`: Extractor de texto (OCR fallback) de PDFs.
    *   `build_index.py`: Script para construir el índice de embeddings FAISS.
    *   `llm_client.py`: Cliente unificado de conexión a las APIs de OpenAI y Gemini (JSON Mode, carga de `.env`).
*   **`/code/variants/`**: Diferentes arquitecturas y pruebas del sistema para evaluar rendimiento.
    *   `v1_intent_classification/agent.py`: Orquestación mediante Few-Shot Prompting.
    *   `v2_hybrid_search_rerank/agent.py`: Búsqueda Híbrida (Solr + Vectorial) y Reranking.
    *   `v3_json_schema/agent.py`: Tipado estricto con JSON Schema / responseSchema.
    *   `v4_strict_grounding_citations/agent.py`: Mitigación de alucinaciones y citas (fuentes).
    *   `original/`: Copia de seguridad del código original (`agent.py`, `nlu_pipeline.py`) para evitar pérdidas.
*   **`/code/apps/`**: Aplicaciones interactivas e interfaces de usuario.
    *   `chat_app.py`: Interfaz interactiva principal (Gradio).
    *   `dashboard_app.py`: Cuadro de mando analítico (Streamlit).
    *   `dashboard_app_gis.py`: Cuadro de mando con mapas GIS (Streamlit).
    *   `ask.py`: Interfaz de consola CLI.
*   **`/code/evaluation/`**: Benchmarks y pruebas cuantitativas de calidad.
    *   `filter_extraction_benchmark.py`: Evaluación de extracción de entidades.
    *   `benchmark_solr_vs_llm.py`: Comparativa de precisión de recuperación.
    *   `evaluate_nlg_quality.py`: Métricas de calidad NLG.
*   **`/code/experiments/`**: Scripts de pruebas puntuales y ejecuciones de experimentos.
    *   `experiment_runner.py` / `run_queries.py`.
*   **`/code/utils/`**: Scripts auxiliares de generación de vídeo, cuadrículas y visualizaciones.
    *   `draw_grid.py` / `make_georag_walkthrough_video.py`.

---

## 2. Gateway Dinámico de Arquitectura

Para permitir que el proyecto funcione con múltiples posibilidades a la vez y sea fácil de probar sin romper nada:
1.  Hemos modificado `code/chat_agent.py` y `code/nlu_pipeline.py` para actuar como **gateways de enrutamiento dinámico**.
2.  Al arrancar la aplicación, el gateway lee la variable de entorno `CRMS_ARCH_VARIANT` de tu archivo `.env`.
3.  Automáticamente importa y ejecuta la lógica de la variante elegida de forma totalmente transparente para `run_app.py`, `chat_app.py` o los dashboards.

### Cómo cambiar de Variante en ejecución:
Abre tu archivo `code/.env` y añade o edita la línea:
```env
CRMS_ARCH_VARIANT=v4_strict_grounding_citations
```
Valores permitidos:
*   `original` (Código original antes de la restructuración)
*   `v1_intent_classification` (Few-Shot con esquema cerrado)
*   `v2_hybrid_search_rerank` (Búsqueda híbrida y filtrado de ruido)
*   `v3_json_schema` (Enforzamiento de esquema de Gemini/OpenAI)
*   `v4_strict_grounding_citations` (Mitigación de alucinaciones y citas)

---

## 3. Implementación de las Nuevas Variantes (Propuestas de Gemini)

Hemos diseñado e implementado 4 variantes para probar las ideas recopiladas:

### Variante 1: Few-Shot Intent Classification & Closed API Schema
*   **Propuesta**: Evitar alucinaciones de API limitando estrictamente los campos permitidos y educando al LLM con ejemplos de mapeo.
*   **Implementación**: El prompt del sistema incluye una definición cerrada del esquema de la base de datos y 5 ejemplos de mapeo Few-Shot detallados (User Query -> JSON de filtros).
*   **Diagrama**: Generado en `geo-rag-explorer/georag_v1.png`.

### Variante 2: Hybrid Search & Context Curation (Reranking)
*   **Propuesta**: Combinar búsqueda léxica y semántica, y limpiar el contexto enviado al LLM para evitar sobrecarga de ventana de contexto (ruido).
*   **Implementación**: Si la query es de tipo híbrido (RAG), se cruza la consulta a Solr con una consulta vectorial FAISS en los PDFs locales. Los fragmentos vectoriales recuperados se pasan por un Reranker de umbral y score para descartar ruido y enviar solo el Top-3 de alta densidad de información.
*   **Diagrama**: Generado en `geo-rag-explorer/georag_v2.png`.

### Variante 3: Structured Responses & Schema Enforcement
*   **Propuesta**: Forzar tipado estricto a nivel de decodificación de tokens para asegurar que la salida JSON sea siempre válida.
*   **Implementación**: Uso del parámetro nativo de Gemini `responseSchema` (y de OpenAI JSON Mode) tanto en el parser NLU como en la síntesis NLG. Se definen esquemas específicos para obligar al modelo a estructurar su respuesta en un JSON con campos definidos de salida.
*   **Diagrama**: Generado en `geo-rag-explorer/georag_v3.png`.

### Variante 4: Strict Context Grounding & Traceability (Citations)
*   **Propuesta**: Evitar alucinaciones devolviendo un error estándar si el RAG no encuentra información en los documentos, y proporcionar trazabilidad de las fuentes.
*   **Implementación**: Prompt del sistema hiper-estricto que anula conocimiento externo. Si la base de datos devuelve 0 resultados, se activa un Guard de salida anticipada (sin llamar al LLM) que retorna `{"error": "Información no disponible en el espacio de datos"}`. Las respuestas correctas contienen obligatoriamente un nodo de citas (`fuentes`) con `doc_id`, `seccion` y `score_confianza`.
*   **Diagrama**: Generado en `geo-rag-explorer/georag_v4.png`.

---

## 4. Visualización de Estructuras (Diagramas PNG)

Hemos generado y guardado 4 diagramas detallados representando cada una de las arquitecturas:
*   [Diagrama Variante 1 (Few-Shot)](file:///C:/Users/felix/OneDrive%20-%20Universidad%20de%20Burgos/Documentos/CRMsDataSpace/geo-rag-explorer/georag_v1.png)
*   [Diagrama Variante 2 (Hybrid Rerank)](file:///C:/Users/felix/OneDrive%20-%20Universidad%20de%20Burgos/Documentos/CRMsDataSpace/geo-rag-explorer/georag_v2.png)
*   [Diagrama Variante 3 (JSON Schema)](file:///C:/Users/felix/OneDrive%20-%20Universidad%20de%20Burgos/Documentos/CRMsDataSpace/geo-rag-explorer/georag_v3.png)
*   [Diagrama Variante 4 (Strict Grounding)](file:///C:/Users/felix/OneDrive%20-%20Universidad%20de%20Burgos/Documentos/CRMsDataSpace/geo-rag-explorer/georag_v4.png)

Cada diagrama muestra detalladamente el flujo de tokens, la orquestación, las validaciones y los componentes involucrados, adaptándose a las dimensiones requeridas de 1376x768 píxeles.
