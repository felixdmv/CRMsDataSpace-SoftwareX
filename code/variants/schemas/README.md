# Esquemas de Arquitectura de las Variantes de Agente (CRMsDataSpace)

Este directorio contiene las representaciones gráficas minimalistas (en formatos vectoriales **SVG** y de alta resolución **PNG**) que describen el flujo de datos desde la consulta inicial del usuario hasta la síntesis final del LLM para cada variante del sistema.

Para cada arquitectura, se detalla el procesamiento en cada nodo, la dirección de las flechas de flujo y las tecnologías clave involucradas.

---

## Índice de Variantes y Diagramas

### 0. Arquitectura Base (Original)
Línea base original que procesa consultas a través del pipeline NLU modular y realiza una búsqueda tradicional en Apache Solr.
*   **Archivos**:
    *   [original_architecture.png](file:///C:/Users/fdemiguel/OneDrive%20-%20Universidad%20de%20Burgos/Documentos/CRMsDataSpace/code/variants/schemas/original_architecture.png)
    *   [original_architecture.svg](file:///C:/Users/fdemiguel/OneDrive%20-%20Universidad%20de%20Burgos/Documentos/CRMsDataSpace/code/variants/schemas/original_architecture.svg)
*   **Flujo**:
    1.  `User Query` *(NL String)*
    2.  `NLU Pipeline` *(LLM / Regex)*: Extrae intenciones y filtros básicos.
    3.  `Query Builder` *(Python)*: Traduce filtros JSON a parámetros de Solr.
    4.  `Solr Database` *(Apache Solr)*: Recupera registros coincidentes.
    5.  `NLG Synthesizer` *(LLM)*: Genera respuesta final.

### 1. Variante 1: Few-Shot Intent Classification & Closed API Schema
Previene alucinaciones del esquema de filtros limitando los campos a un esquema cerrado y educando al parser NLU mediante 5 ejemplos Few-Shot específicos.
*   **Archivos**:
    *   [v1_few_shot_intent.png](file:///C:/Users/fdemiguel/OneDrive%20-%20Universidad%20de%20Burgos/Documentos/CRMsDataSpace/code/variants/schemas/v1_few_shot_intent.png)
    *   [v1_few_shot_intent.svg](file:///C:/Users/fdemiguel/OneDrive%20-%20Universidad%20de%20Burgos/Documentos/CRMsDataSpace/code/variants/schemas/v1_few_shot_intent.svg)
*   **Flujo**:
    1.  `User Query` *(NL String)*
    2.  `Few-Shot LLM Parser` *(LLM Few-Shot)*: Clasifica intención (filter_search, hybrid, generic_qa) y mapea filtros en esquema rígido.
    3.  `Normalizer & Validator` *(Python)*: Normaliza términos (e.g. "españa" -> "spain") y valida tipos.
        *   *Bypass*: Si el intent es `generic_qa`, salta Solr y va directo al NLG.
    4.  `Solr Database` *(Apache Solr)*: Ejecuta consulta.
    5.  `NLG Synthesizer` *(LLM / Python)*: Genera respuesta.

### 2. Variante 2: Hybrid Search & Context Curation (Rerank)
Combina la recuperación estructurada de Solr con la búsqueda vectorial semántica en documentos PDF locales, filtrando y reordenando fragmentos para evitar ruido de contexto.
*   **Archivos**:
    *   [v2_hybrid_search_rerank.png](file:///C:/Users/fdemiguel/OneDrive%20-%20Universidad%20de%20Burgos/Documentos/CRMsDataSpace/code/variants/schemas/v2_hybrid_search_rerank.png)
    *   [v2_hybrid_search_rerank.svg](file:///C:/Users/fdemiguel/OneDrive%20-%20Universidad%20de%20Burgos/Documentos/CRMsDataSpace/code/variants/schemas/v2_hybrid_search_rerank.svg)
*   **Flujo**:
    1.  `User Query` *(NL String)*
    2.  `NLU Parser` *(LLM)*: Extrae filtros y activa RAG si la query requiere análisis documental.
    3.  **Doble Recuperación**:
        *   `Solr DB Query` *(Solr)*: Registros de base de datos WARM.
        *   `FAISS Vector Search` *(FAISS + Sentence-Transformers)*: Recupera 10 fragmentos de PDFs.
    4.  `Reranker & Curator` *(Python)*: Filtra por score (threshold >= 0.15) y selecciona los 3 fragmentos con mayor densidad de información.
    5.  `Hybrid NLG Synthesizer` *(LLM)*: Fusiona registros y textos curados para la respuesta.

### 3. Variante 3: Structured Responses & Schema Enforcement
Garantiza que tanto la salida NLU como el resumen NLG tengan una estructura JSON 100% parseable, forzando la API del LLM a ajustarse a esquemas estrictos a nivel de tokens.
*   **Archivos**:
    *   [v3_json_schema.png](file:///C:/Users/fdemiguel/OneDrive%20-%20Universidad%20de%20Burgos/Documentos/CRMsDataSpace/code/variants/schemas/v3_json_schema.png)
    *   [v3_json_schema.svg](file:///C:/Users/fdemiguel/OneDrive%20-%20Universidad%20de%20Burgos/Documentos/CRMsDataSpace/code/variants/schemas/v3_json_schema.svg)
*   **Flujo**:
    1.  `User Query` *(NL String)*
    2.  `Schema-Enforced Parser` *(LLM)*: Fuerza salida conforme a `NLU_RESPONSE_SCHEMA` (intent, filters, needs_rag).
    3.  `Normalizer & Query Builder` *(Python)*: Traduce a parámetros Solr.
    4.  `Solr Database` *(Apache Solr)*: Recupera registros.
    5.  `Schema-Enforced NLG` *(LLM)*: Fuerza salida conforme a `NLG_RESPONSE_SCHEMA` (respuesta, hallazgos_clave, fuentes).
    6.  `Final Output` *(Chat UI)*: Parsea JSON y rellena componentes visuales estructurados.

### 4. Variante 4: Strict Context Grounding & Citations
Mitiga alucinaciones científicas aplicando una salida anticipada sin llamada al LLM si la búsqueda Solr retorna vacío, y obligando al modelo a justificar cada dato con citas.
*   **Archivos**:
    *   [v4_strict_grounding_citations.png](file:///C:/Users/fdemiguel/OneDrive%20-%20Universidad%20de%20Burgos/Documentos/CRMsDataSpace/code/variants/schemas/v4_strict_grounding_citations.png)
    *   [v4_strict_grounding_citations.svg](file:///C:/Users/fdemiguel/OneDrive%20-%20Universidad%20de%20Burgos/Documentos/CRMsDataSpace/code/variants/schemas/v4_strict_grounding_citations.svg)
*   **Flujo**:
    1.  `User Query` *(NL String)*
    2.  `NLU Parser` *(LLM)*: Extrae filtros.
    3.  `Solr Database Query` *(Apache Solr)*: Recupera registros.
    4.  `Early Exit Guard` *(Python)*: Verifica cantidad de resultados.
        *   **Si N = 0**: Retorna directamente `{"error": "Información no disponible..."}` sin llamar al LLM.
        *   **Si N > 0**: Envía los resultados al sintetizador.
    5.  `Grounded NLG Synthesizer` *(LLM)*: Redacta respuesta únicamente con el contexto de base de datos y adjunta citas exactas con `doc_id`, `seccion` y `score_confianza`.
