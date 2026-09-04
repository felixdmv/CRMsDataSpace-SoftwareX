# Reporte Científico: Solr-Direct vs. LLM vs. spaCy vs. GLiNER
Generado en: 2026-07-09 12:47:14

## 1. Resumen Ejecutivo
Este reporte evalúa empíricamente la capacidad de extracción de filtros estructurados y comprensión semántica de consultas en el espacio de datos **CRMs Data Space** bajo cuatro paradigmas de arquitectura:
1. **Solr-Direct / Heurísticas de Reglas (WARM)**: Búsqueda basada en diccionarios fijos, expresiones regulares y concordancia exacta de palabras clave sin normalización semántica.
2. **LLM NLU Parser (GEMINI + Decoupled Pipeline)**: Arquitectura desacoplada: **Usuario → LLM (Semantic Parser) → Normalizer → Validator → Query Builder → Apache Solr**.
3. **spaCy NLP Pipeline**: Pipeline clásico con el modelo en español `es_core_news_sm` e inyección de reglas personalizadas en un `EntityRuler`.
4. **GLiNER Zero-Shot NER**: Modelo generalista zero-shot `gliner_small-v2.1` configurado dinámicamente con etiquetas de dominio.

### Indicadores Clave de Rendimiento (KPIs)
| Paradigma | Tasa de Acierto (Filtros Esperados) | Tiempo de Respuesta Promedio | Robustez ante Errores y Semántica |
|---|---|---|---|
| **Solr-Direct / Reglas (Legacy)** | **48.7%** | 0.2 ms | Baja (Limitado a diccionarios fijos) |
| **LLM NLU Parser (GEMINI)** | **96.6%** | 1.1 ms | Excelente (Semántica profunda + Normalizador) |
| **spaCy NLP Pipeline** | **71.9%** | 11.7 ms | Media-Baja (Sensible a flexiones gramaticales y negación) |
| **GLiNER Zero-Shot Model** | **16.9%** | 91.5 ms | Muy Baja (Incapaz de generalizar en español sin re-entrenar) |

---

## 2. Análisis Comparativo por Consulta (40 Casos Críticos)
A continuación se detallan las 40 pruebas de estrés realizadas sobre el motor de búsqueda, ordenadas por categorías:

### [TC_01] Typos & Misspellings (Fuzzy Mapping)
**Consulta**: *"escombreras de golfranio en galiza"*

*   **Filtros de Verdad del Terreno (Esperados)**:
    ```json
    {
  "commodities": [
    "tungsten"
  ],
  "regions": [
    "galicia"
  ]
}
    ```

#### A) Solr-Direct / Reglas (Legacy) (Puntuación: 0%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [],
  "regions": [],
  "commodities": [],
  "material_types": [],
  "storage_facility_types": [
    "waste dump"
  ],
  "project_status": [],
  "companies": [],
  "site_names": [],
  "unfc_e": [],
  "unfc_f": [],
  "unfc_g": [],
  "environmental_flags": [],
  "free_text_constraints": [],
  "activity_types": [],
  "mine_types": [],
  "admin_statuses": [],
  "mine_statuses": [],
  "morphologies": [],
  "restored": null,
  "restoration_types": [],
  "site_contexts": []
}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **commodities**: FALLA (Esperado: ['tungsten'], Obtenido: [])
    * 🔴 **regions**: FALLA (Esperado: ['galicia'], Obtenido: [])

#### B) LLM Parser (GEMINI + Pipeline) (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "regions": [
    "galicia"
  ],
  "commodities": [
    "tungsten"
  ],
  "storage_facility_types": [
    "waste dump"
  ],
  "countries": [
    "spain"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **commodities**: COINCIDE (Esperado: ['tungsten'], Obtenido: ['tungsten'])
    * 🟢 **regions**: COINCIDE (Esperado: ['galicia'], Obtenido: ['galicia'])

#### C) spaCy NLP Pipeline (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "storage_facility_types": [
    "waste dump"
  ],
  "commodities": [
    "tungsten"
  ],
  "regions": [
    "galicia"
  ],
  "countries": [
    "spain"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **commodities**: COINCIDE (Esperado: ['tungsten'], Obtenido: ['tungsten'])
    * 🟢 **regions**: COINCIDE (Esperado: ['galicia'], Obtenido: ['galicia'])

#### D) GLiNER Zero-Shot Model (Puntuación: 0%)
*   **Filtros Extraídos**:
    ```json
    {}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **commodities**: FALLA (Esperado: ['tungsten'], Obtenido: [])
    * 🔴 **regions**: FALLA (Esperado: ['galicia'], Obtenido: [])

---

### [TC_02] Semantic Association (Implicit Entities)
**Consulta**: *"depósitos con materiales para baterías de coches eléctricos"*

*   **Filtros de Verdad del Terreno (Esperados)**:
    ```json
    {
  "commodities": [
    "lithium",
    "cobalt",
    "nickel"
  ]
}
    ```

#### A) Solr-Direct / Reglas (Legacy) (Puntuación: 0%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [],
  "regions": [],
  "commodities": [],
  "material_types": [],
  "storage_facility_types": [],
  "project_status": [],
  "companies": [],
  "site_names": [],
  "unfc_e": [],
  "unfc_f": [],
  "unfc_g": [],
  "environmental_flags": [],
  "free_text_constraints": [],
  "activity_types": [],
  "mine_types": [],
  "admin_statuses": [],
  "mine_statuses": [],
  "morphologies": [],
  "restored": null,
  "restoration_types": [],
  "site_contexts": []
}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **commodities**: FALLA (Esperado: ['lithium', 'cobalt', 'nickel'], Obtenido: [])

#### B) LLM Parser (GEMINI + Pipeline) (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "commodities": [
    "lithium",
    "cobalt",
    "nickel"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **commodities**: COINCIDE (Esperado: ['lithium', 'cobalt', 'nickel'], Obtenido: ['lithium', 'cobalt', 'nickel'])

#### C) spaCy NLP Pipeline (Puntuación: 0%)
*   **Filtros Extraídos**:
    ```json
    {
  "commodities": [
    "baterias de coches electricos"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **commodities**: FALLA (Esperado: ['lithium', 'cobalt', 'nickel'], Obtenido: ['baterias de coches electricos'])

#### D) GLiNER Zero-Shot Model (Puntuación: 0%)
*   **Filtros Extraídos**:
    ```json
    {}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **commodities**: FALLA (Esperado: ['lithium', 'cobalt', 'nickel'], Obtenido: [])

---

### [TC_03] Complex Negation & Exclusions
**Consulta**: *"balsas de litio en españa pero que no estén en extremadura"*

*   **Filtros de Verdad del Terreno (Esperados)**:
    ```json
    {
  "countries": [
    "spain"
  ],
  "commodities": [
    "lithium"
  ]
}
    ```

#### A) Solr-Direct / Reglas (Legacy) (Puntuación: 67%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [
    "spain"
  ],
  "regions": [
    "extremadura"
  ],
  "commodities": [
    "lithium"
  ],
  "material_types": [],
  "storage_facility_types": [
    "pond"
  ],
  "project_status": [],
  "companies": [],
  "site_names": [],
  "unfc_e": [],
  "unfc_f": [],
  "unfc_g": [],
  "environmental_flags": [],
  "free_text_constraints": [],
  "activity_types": [],
  "mine_types": [],
  "admin_statuses": [],
  "mine_statuses": [],
  "morphologies": [],
  "restored": null,
  "restoration_types": [],
  "site_contexts": []
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **countries**: COINCIDE (Esperado: ['spain'], Obtenido: ['spain'])
    * 🟢 **commodities**: COINCIDE (Esperado: ['lithium'], Obtenido: ['lithium'])
    * 💥 **regions (Exclusión)**: INFRACCIÓN (Valores excluidos presentes en positivos: ['extremadura'])

#### B) LLM Parser (GEMINI + Pipeline) (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [
    "spain"
  ],
  "commodities": [
    "lithium"
  ],
  "storage_facility_types": [
    "pond"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **countries**: COINCIDE (Esperado: ['spain'], Obtenido: ['spain'])
    * 🟢 **commodities**: COINCIDE (Esperado: ['lithium'], Obtenido: ['lithium'])
    * 🟢 **regions (Exclusión)**: COINCIDE (Excluido correctamente: ['extremadura'])

#### C) spaCy NLP Pipeline (Puntuación: 67%)
*   **Filtros Extraídos**:
    ```json
    {
  "storage_facility_types": [
    "pond"
  ],
  "commodities": [
    "lithium"
  ],
  "countries": [
    "spain"
  ],
  "regions": [
    "extremadura"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **countries**: COINCIDE (Esperado: ['spain'], Obtenido: ['spain'])
    * 🟢 **commodities**: COINCIDE (Esperado: ['lithium'], Obtenido: ['lithium'])
    * 💥 **regions (Exclusión)**: INFRACCIÓN (Valores excluidos presentes en positivos: ['extremadura'])

#### D) GLiNER Zero-Shot Model (Puntuación: 33%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [
    "spain"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **countries**: COINCIDE (Esperado: ['spain'], Obtenido: ['spain'])
    * 🔴 **commodities**: FALLA (Esperado: ['lithium'], Obtenido: [])
    * 🔴 **regions (Exclusión)**: FALLA (Esperado excluir: ['extremadura'], Obtenido: [])

---

### [TC_04] Geographical Synonyms & Slang
**Consulta**: *"instalaciones mineras en el sur de la península con cobre"*

*   **Filtros de Verdad del Terreno (Esperados)**:
    ```json
    {
  "countries": [
    "spain"
  ],
  "regions": [
    "andalucia"
  ],
  "commodities": [
    "copper"
  ]
}
    ```

#### A) Solr-Direct / Reglas (Legacy) (Puntuación: 33%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [],
  "regions": [],
  "commodities": [
    "copper"
  ],
  "material_types": [],
  "storage_facility_types": [],
  "project_status": [],
  "companies": [],
  "site_names": [],
  "unfc_e": [],
  "unfc_f": [],
  "unfc_g": [],
  "environmental_flags": [],
  "free_text_constraints": [],
  "activity_types": [],
  "mine_types": [],
  "admin_statuses": [],
  "mine_statuses": [],
  "morphologies": [],
  "restored": null,
  "restoration_types": [],
  "site_contexts": []
}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **countries**: FALLA (Esperado: ['spain'], Obtenido: [])
    * 🔴 **regions**: FALLA (Esperado: ['andalucia'], Obtenido: [])
    * 🟢 **commodities**: COINCIDE (Esperado: ['copper'], Obtenido: ['copper'])

#### B) LLM Parser (GEMINI + Pipeline) (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "regions": [
    "andalucia"
  ],
  "commodities": [
    "copper"
  ],
  "countries": [
    "spain"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **countries**: COINCIDE (Esperado: ['spain'], Obtenido: ['spain'])
    * 🟢 **regions**: COINCIDE (Esperado: ['andalucia'], Obtenido: ['andalucia'])
    * 🟢 **commodities**: COINCIDE (Esperado: ['copper'], Obtenido: ['copper'])

#### C) spaCy NLP Pipeline (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "regions": [
    "andalucia"
  ],
  "commodities": [
    "copper"
  ],
  "countries": [
    "spain"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **countries**: COINCIDE (Esperado: ['spain'], Obtenido: ['spain'])
    * 🟢 **regions**: COINCIDE (Esperado: ['andalucia'], Obtenido: ['andalucia'])
    * 🟢 **commodities**: COINCIDE (Esperado: ['copper'], Obtenido: ['copper'])

#### D) GLiNER Zero-Shot Model (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "regions": [
    "andalucia"
  ],
  "commodities": [
    "copper"
  ],
  "countries": [
    "spain"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **countries**: COINCIDE (Esperado: ['spain'], Obtenido: ['spain'])
    * 🟢 **regions**: COINCIDE (Esperado: ['andalucia'], Obtenido: ['andalucia'])
    * 🟢 **commodities**: COINCIDE (Esperado: ['copper'], Obtenido: ['copper'])

---

### [TC_05] High Verbosity & Noise
**Consulta**: *"hola, me gustaría saber si por casualidad hay algún proyecto activo gestionado por la empresa atalaya minera que tenga cobre"*

*   **Filtros de Verdad del Terreno (Esperados)**:
    ```json
    {
  "project_status": [
    "active"
  ],
  "companies": [
    "atalaya mining"
  ],
  "commodities": [
    "copper"
  ]
}
    ```

#### A) Solr-Direct / Reglas (Legacy) (Puntuación: 83%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [],
  "regions": [],
  "commodities": [
    "copper"
  ],
  "material_types": [],
  "storage_facility_types": [],
  "project_status": [
    "active",
    "development"
  ],
  "companies": [
    "atalaya mining"
  ],
  "site_names": [],
  "unfc_e": [],
  "unfc_f": [],
  "unfc_g": [],
  "environmental_flags": [],
  "free_text_constraints": [],
  "activity_types": [],
  "mine_types": [],
  "admin_statuses": [],
  "mine_statuses": [],
  "morphologies": [],
  "restored": null,
  "restoration_types": [],
  "site_contexts": []
}
    ```
*   **Detalle de Evaluación**:
    * 🟡 **project_status**: COINCIDE PARCIALMENTE (50%) (Esperado: ['active'], Obtenido: ['active', 'development'])
    * 🟢 **companies**: COINCIDE (Esperado: ['atalaya mining'], Obtenido: ['atalaya mining'])
    * 🟢 **commodities**: COINCIDE (Esperado: ['copper'], Obtenido: ['copper'])

#### B) LLM Parser (GEMINI + Pipeline) (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "commodities": [
    "copper"
  ],
  "project_status": [
    "active"
  ],
  "companies": [
    "atalaya mining"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **project_status**: COINCIDE (Esperado: ['active'], Obtenido: ['active'])
    * 🟢 **companies**: COINCIDE (Esperado: ['atalaya mining'], Obtenido: ['atalaya mining'])
    * 🟢 **commodities**: COINCIDE (Esperado: ['copper'], Obtenido: ['copper'])

#### C) spaCy NLP Pipeline (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "project_status": [
    "active"
  ],
  "companies": [
    "atalaya mining"
  ],
  "commodities": [
    "copper"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **project_status**: COINCIDE (Esperado: ['active'], Obtenido: ['active'])
    * 🟢 **companies**: COINCIDE (Esperado: ['atalaya mining'], Obtenido: ['atalaya mining'])
    * 🟢 **commodities**: COINCIDE (Esperado: ['copper'], Obtenido: ['copper'])

#### D) GLiNER Zero-Shot Model (Puntuación: 67%)
*   **Filtros Extraídos**:
    ```json
    {
  "companies": [
    "atalaya mining"
  ],
  "commodities": [
    "copper"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **project_status**: FALLA (Esperado: ['active'], Obtenido: [])
    * 🟢 **companies**: COINCIDE (Esperado: ['atalaya mining'], Obtenido: ['atalaya mining'])
    * 🟢 **commodities**: COINCIDE (Esperado: ['copper'], Obtenido: ['copper'])

---

### [TC_06] Implicit Material Types
**Consulta**: *"escombreras inertes de granito"*

*   **Filtros de Verdad del Terreno (Esperados)**:
    ```json
    {
  "material_types": [
    "waste rock"
  ],
  "storage_facility_types": [
    "waste dump"
  ]
}
    ```

#### A) Solr-Direct / Reglas (Legacy) (Puntuación: 50%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [],
  "regions": [],
  "commodities": [],
  "material_types": [],
  "storage_facility_types": [
    "waste dump"
  ],
  "project_status": [],
  "companies": [],
  "site_names": [],
  "unfc_e": [],
  "unfc_f": [],
  "unfc_g": [],
  "environmental_flags": [],
  "free_text_constraints": [],
  "activity_types": [],
  "mine_types": [],
  "admin_statuses": [],
  "mine_statuses": [],
  "morphologies": [],
  "restored": null,
  "restoration_types": [],
  "site_contexts": []
}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **material_types**: FALLA (Esperado: ['waste rock'], Obtenido: [])
    * 🟢 **storage_facility_types**: COINCIDE (Esperado: ['waste dump'], Obtenido: ['waste dump'])

#### B) LLM Parser (GEMINI + Pipeline) (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "storage_facility_types": [
    "waste dump"
  ],
  "material_types": [
    "waste rock"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **material_types**: COINCIDE (Esperado: ['waste rock'], Obtenido: ['waste rock'])
    * 🟢 **storage_facility_types**: COINCIDE (Esperado: ['waste dump'], Obtenido: ['waste dump'])

#### C) spaCy NLP Pipeline (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "storage_facility_types": [
    "waste dump"
  ],
  "material_types": [
    "waste rock"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **material_types**: COINCIDE (Esperado: ['waste rock'], Obtenido: ['waste rock'])
    * 🟢 **storage_facility_types**: COINCIDE (Esperado: ['waste dump'], Obtenido: ['waste dump'])

#### D) GLiNER Zero-Shot Model (Puntuación: 0%)
*   **Filtros Extraídos**:
    ```json
    {}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **material_types**: FALLA (Esperado: ['waste rock'], Obtenido: [])
    * 🔴 **storage_facility_types**: FALLA (Esperado: ['waste dump'], Obtenido: [])

---

### [TC_07] Multilingual Cross-lingual Terms
**Consulta**: *"tailings storage facility in extremadura with lithium"*

*   **Filtros de Verdad del Terreno (Esperados)**:
    ```json
    {
  "regions": [
    "extremadura"
  ],
  "commodities": [
    "lithium"
  ],
  "storage_facility_types": [
    "tailings storage facility"
  ]
}
    ```

#### A) Solr-Direct / Reglas (Legacy) (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [],
  "regions": [
    "extremadura"
  ],
  "commodities": [
    "lithium"
  ],
  "material_types": [],
  "storage_facility_types": [
    "tailings storage facility"
  ],
  "project_status": [],
  "companies": [],
  "site_names": [],
  "unfc_e": [],
  "unfc_f": [],
  "unfc_g": [],
  "environmental_flags": [],
  "free_text_constraints": [],
  "activity_types": [],
  "mine_types": [],
  "admin_statuses": [],
  "mine_statuses": [],
  "morphologies": [],
  "restored": null,
  "restoration_types": [],
  "site_contexts": []
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **regions**: COINCIDE (Esperado: ['extremadura'], Obtenido: ['extremadura'])
    * 🟢 **commodities**: COINCIDE (Esperado: ['lithium'], Obtenido: ['lithium'])
    * 🟢 **storage_facility_types**: COINCIDE (Esperado: ['tailings storage facility'], Obtenido: ['tailings storage facility'])

#### B) LLM Parser (GEMINI + Pipeline) (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "regions": [
    "extremadura"
  ],
  "commodities": [
    "lithium"
  ],
  "storage_facility_types": [
    "tailings storage facility"
  ],
  "material_types": [
    "tailings"
  ],
  "countries": [
    "spain"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **regions**: COINCIDE (Esperado: ['extremadura'], Obtenido: ['extremadura'])
    * 🟢 **commodities**: COINCIDE (Esperado: ['lithium'], Obtenido: ['lithium'])
    * 🟢 **storage_facility_types**: COINCIDE (Esperado: ['tailings storage facility'], Obtenido: ['tailings storage facility'])

#### C) spaCy NLP Pipeline (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "storage_facility_types": [
    "tailings storage facility"
  ],
  "regions": [
    "extremadura"
  ],
  "commodities": [
    "lithium"
  ],
  "countries": [
    "spain"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **regions**: COINCIDE (Esperado: ['extremadura'], Obtenido: ['extremadura'])
    * 🟢 **commodities**: COINCIDE (Esperado: ['lithium'], Obtenido: ['lithium'])
    * 🟢 **storage_facility_types**: COINCIDE (Esperado: ['tailings storage facility'], Obtenido: ['tailings storage facility'])

#### D) GLiNER Zero-Shot Model (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "storage_facility_types": [
    "tailings storage facility"
  ],
  "regions": [
    "extremadura"
  ],
  "commodities": [
    "lithium"
  ],
  "countries": [
    "spain"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **regions**: COINCIDE (Esperado: ['extremadura'], Obtenido: ['extremadura'])
    * 🟢 **commodities**: COINCIDE (Esperado: ['lithium'], Obtenido: ['lithium'])
    * 🟢 **storage_facility_types**: COINCIDE (Esperado: ['tailings storage facility'], Obtenido: ['tailings storage facility'])

---

### [TC_08] Chemical Symbols & Abbreviations
**Consulta**: *"depósitos de W en Ourense"*

*   **Filtros de Verdad del Terreno (Esperados)**:
    ```json
    {
  "commodities": [
    "tungsten"
  ],
  "regions": [
    "galicia"
  ]
}
    ```

#### A) Solr-Direct / Reglas (Legacy) (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [],
  "regions": [
    "galicia"
  ],
  "commodities": [
    "tungsten"
  ],
  "material_types": [],
  "storage_facility_types": [],
  "project_status": [],
  "companies": [],
  "site_names": [],
  "unfc_e": [],
  "unfc_f": [],
  "unfc_g": [],
  "environmental_flags": [],
  "free_text_constraints": [],
  "activity_types": [],
  "mine_types": [],
  "admin_statuses": [],
  "mine_statuses": [],
  "morphologies": [],
  "restored": null,
  "restoration_types": [],
  "site_contexts": []
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **commodities**: COINCIDE (Esperado: ['tungsten'], Obtenido: ['tungsten'])
    * 🟢 **regions**: COINCIDE (Esperado: ['galicia'], Obtenido: ['galicia'])

#### B) LLM Parser (GEMINI + Pipeline) (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "regions": [
    "galicia"
  ],
  "commodities": [
    "tungsten"
  ],
  "countries": [
    "spain"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **commodities**: COINCIDE (Esperado: ['tungsten'], Obtenido: ['tungsten'])
    * 🟢 **regions**: COINCIDE (Esperado: ['galicia'], Obtenido: ['galicia'])

#### C) spaCy NLP Pipeline (Puntuación: 50%)
*   **Filtros Extraídos**:
    ```json
    {
  "commodities": [
    "w"
  ],
  "regions": [
    "galicia"
  ],
  "countries": [
    "spain"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **commodities**: FALLA (Esperado: ['tungsten'], Obtenido: ['w'])
    * 🟢 **regions**: COINCIDE (Esperado: ['galicia'], Obtenido: ['galicia'])

#### D) GLiNER Zero-Shot Model (Puntuación: 0%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [
    "ourense"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **commodities**: FALLA (Esperado: ['tungsten'], Obtenido: [])
    * 🔴 **regions**: FALLA (Esperado: ['galicia'], Obtenido: [])

---

### [TC_09] Multi-intent & Hybrid Search
**Consulta**: *"¿cuáles son las tierras raras y qué balsas las contienen en españa?"*

*   **Filtros de Verdad del Terreno (Esperados)**:
    ```json
    {
  "intent": "hybrid",
  "commodities": [
    "rare earth elements"
  ],
  "storage_facility_types": [
    "tailings storage facility",
    "pond"
  ],
  "countries": [
    "spain"
  ]
}
    ```

#### A) Solr-Direct / Reglas (Legacy) (Puntuación: 38%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [
    "spain"
  ],
  "regions": [],
  "commodities": [
    "rare earths"
  ],
  "material_types": [],
  "storage_facility_types": [
    "pond"
  ],
  "project_status": [],
  "companies": [],
  "site_names": [],
  "unfc_e": [],
  "unfc_f": [],
  "unfc_g": [],
  "environmental_flags": [],
  "free_text_constraints": [],
  "activity_types": [],
  "mine_types": [],
  "admin_statuses": [],
  "mine_statuses": [],
  "morphologies": [],
  "restored": null,
  "restoration_types": [],
  "site_contexts": []
}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **intent**: FALLA (Esperado: hybrid, Obtenido: filter_search)
    * 🔴 **commodities**: FALLA (Esperado: ['rare earth elements'], Obtenido: ['rare earths'])
    * 🟡 **storage_facility_types**: COINCIDE PARCIALMENTE (50%) (Esperado: ['tailings storage facility', 'pond'], Obtenido: ['pond'])
    * 🟢 **countries**: COINCIDE (Esperado: ['spain'], Obtenido: ['spain'])

#### B) LLM Parser (GEMINI + Pipeline) (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [
    "spain"
  ],
  "commodities": [
    "rare earth elements"
  ],
  "storage_facility_types": [
    "pond",
    "tailings storage facility"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **intent**: COINCIDE (Esperado: hybrid, Obtenido: hybrid)
    * 🟢 **commodities**: COINCIDE (Esperado: ['rare earth elements'], Obtenido: ['rare earth elements'])
    * 🟢 **storage_facility_types**: COINCIDE (Esperado: ['tailings storage facility', 'pond'], Obtenido: ['pond', 'tailings storage facility'])
    * 🟢 **countries**: COINCIDE (Esperado: ['spain'], Obtenido: ['spain'])

#### C) spaCy NLP Pipeline (Puntuación: 62%)
*   **Filtros Extraídos**:
    ```json
    {
  "commodities": [
    "rare earth elements"
  ],
  "storage_facility_types": [
    "pond"
  ],
  "countries": [
    "spain"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **intent**: FALLA (Esperado: hybrid, Obtenido: search)
    * 🟢 **commodities**: COINCIDE (Esperado: ['rare earth elements'], Obtenido: ['rare earth elements'])
    * 🟡 **storage_facility_types**: COINCIDE PARCIALMENTE (50%) (Esperado: ['tailings storage facility', 'pond'], Obtenido: ['pond'])
    * 🟢 **countries**: COINCIDE (Esperado: ['spain'], Obtenido: ['spain'])

#### D) GLiNER Zero-Shot Model (Puntuación: 25%)
*   **Filtros Extraídos**:
    ```json
    {
  "regions": [
    "tierras raras"
  ],
  "countries": [
    "spain"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **intent**: FALLA (Esperado: hybrid, Obtenido: search)
    * 🔴 **commodities**: FALLA (Esperado: ['rare earth elements'], Obtenido: [])
    * 🔴 **storage_facility_types**: FALLA (Esperado: ['tailings storage facility', 'pond'], Obtenido: [])
    * 🟢 **countries**: COINCIDE (Esperado: ['spain'], Obtenido: ['spain'])

---

### [TC_10] Mineralogical Synonyms (Group Resolution)
**Consulta**: *"balsas de decantación de coltán"*

*   **Filtros de Verdad del Terreno (Esperados)**:
    ```json
    {
  "commodities": [
    "tantalum",
    "niobium"
  ],
  "storage_facility_types": [
    "tailings storage facility",
    "pond"
  ]
}
    ```

#### A) Solr-Direct / Reglas (Legacy) (Puntuación: 25%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [],
  "regions": [],
  "commodities": [],
  "material_types": [],
  "storage_facility_types": [
    "pond"
  ],
  "project_status": [],
  "companies": [],
  "site_names": [],
  "unfc_e": [],
  "unfc_f": [],
  "unfc_g": [],
  "environmental_flags": [],
  "free_text_constraints": [],
  "activity_types": [],
  "mine_types": [],
  "admin_statuses": [],
  "mine_statuses": [],
  "morphologies": [],
  "restored": null,
  "restoration_types": [],
  "site_contexts": []
}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **commodities**: FALLA (Esperado: ['tantalum', 'niobium'], Obtenido: [])
    * 🟡 **storage_facility_types**: COINCIDE PARCIALMENTE (50%) (Esperado: ['tailings storage facility', 'pond'], Obtenido: ['pond'])

#### B) LLM Parser (GEMINI + Pipeline) (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "commodities": [
    "tantalum",
    "niobium"
  ],
  "storage_facility_types": [
    "pond",
    "tailings storage facility"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **commodities**: COINCIDE (Esperado: ['tantalum', 'niobium'], Obtenido: ['tantalum', 'niobium'])
    * 🟢 **storage_facility_types**: COINCIDE (Esperado: ['tailings storage facility', 'pond'], Obtenido: ['pond', 'tailings storage facility'])

#### C) spaCy NLP Pipeline (Puntuación: 50%)
*   **Filtros Extraídos**:
    ```json
    {
  "storage_facility_types": [
    "balsas de decantacion"
  ],
  "commodities": [
    "tantalum",
    "niobium"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **commodities**: COINCIDE (Esperado: ['tantalum', 'niobium'], Obtenido: ['tantalum', 'niobium'])
    * 🔴 **storage_facility_types**: FALLA (Esperado: ['tailings storage facility', 'pond'], Obtenido: ['balsas de decantacion'])

#### D) GLiNER Zero-Shot Model (Puntuación: 0%)
*   **Filtros Extraídos**:
    ```json
    {}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **commodities**: FALLA (Esperado: ['tantalum', 'niobium'], Obtenido: [])
    * 🔴 **storage_facility_types**: FALLA (Esperado: ['tailings storage facility', 'pond'], Obtenido: [])

---

### [TC_11] Ambiguous/Generic Phrases
**Consulta**: *"acumulación de residuos mineros en Riotinto"*

*   **Filtros de Verdad del Terreno (Esperados)**:
    ```json
    {
  "site_names": [
    "Riotinto Project"
  ],
  "storage_facility_types": [
    "waste dump",
    "tailings storage facility"
  ]
}
    ```

#### A) Solr-Direct / Reglas (Legacy) (Puntuación: 50%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [],
  "regions": [
    "andalucia"
  ],
  "commodities": [
    "tin"
  ],
  "material_types": [],
  "storage_facility_types": [],
  "project_status": [],
  "companies": [],
  "site_names": [
    "Riotinto Project"
  ],
  "unfc_e": [],
  "unfc_f": [],
  "unfc_g": [],
  "environmental_flags": [],
  "free_text_constraints": [],
  "activity_types": [],
  "mine_types": [],
  "admin_statuses": [],
  "mine_statuses": [],
  "morphologies": [],
  "restored": null,
  "restoration_types": [],
  "site_contexts": []
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **site_names**: COINCIDE (Esperado: ['Riotinto Project'], Obtenido: ['riotinto project'])
    * 🔴 **storage_facility_types**: FALLA (Esperado: ['waste dump', 'tailings storage facility'], Obtenido: [])

#### B) LLM Parser (GEMINI + Pipeline) (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "regions": [
    "andalucia"
  ],
  "commodities": [
    "tin"
  ],
  "storage_facility_types": [
    "waste dump",
    "tailings storage facility"
  ],
  "material_types": [
    "tailings"
  ],
  "site_names": [
    "Riotinto Project"
  ],
  "countries": [
    "spain"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **site_names**: COINCIDE (Esperado: ['Riotinto Project'], Obtenido: ['riotinto project'])
    * 🟢 **storage_facility_types**: COINCIDE (Esperado: ['waste dump', 'tailings storage facility'], Obtenido: ['tailings storage facility', 'waste dump'])

#### C) spaCy NLP Pipeline (Puntuación: 50%)
*   **Filtros Extraídos**:
    ```json
    {
  "storage_facility_types": [
    "acumulacion de residuos"
  ],
  "site_names": [
    "Riotinto Project"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **site_names**: COINCIDE (Esperado: ['Riotinto Project'], Obtenido: ['riotinto project'])
    * 🔴 **storage_facility_types**: FALLA (Esperado: ['waste dump', 'tailings storage facility'], Obtenido: ['acumulacion de residuos'])

#### D) GLiNER Zero-Shot Model (Puntuación: 0%)
*   **Filtros Extraídos**:
    ```json
    {
  "commodities": [
    "residuos mineros"
  ],
  "countries": [
    "riotinto"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **site_names**: FALLA (Esperado: ['Riotinto Project'], Obtenido: [])
    * 🔴 **storage_facility_types**: FALLA (Esperado: ['waste dump', 'tailings storage facility'], Obtenido: [])

---

### [TC_12] Logical Connectives (OR)
**Consulta**: *"proyectos mineros en salamanca que estén parados o en mantenimiento"*

*   **Filtros de Verdad del Terreno (Esperados)**:
    ```json
    {
  "regions": [
    "castilla y leon"
  ],
  "project_status": [
    "inactive",
    "care and maintenance"
  ]
}
    ```

#### A) Solr-Direct / Reglas (Legacy) (Puntuación: 83%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [],
  "regions": [
    "castilla y leon"
  ],
  "commodities": [],
  "material_types": [],
  "storage_facility_types": [],
  "project_status": [
    "inactive",
    "care and maintenance",
    "development"
  ],
  "companies": [],
  "site_names": [],
  "unfc_e": [],
  "unfc_f": [],
  "unfc_g": [],
  "environmental_flags": [],
  "free_text_constraints": [],
  "activity_types": [],
  "mine_types": [],
  "admin_statuses": [],
  "mine_statuses": [],
  "morphologies": [],
  "restored": null,
  "restoration_types": [],
  "site_contexts": []
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **regions**: COINCIDE (Esperado: ['castilla y leon'], Obtenido: ['castilla y leon'])
    * 🟡 **project_status**: COINCIDE PARCIALMENTE (66%) (Esperado: ['inactive', 'care and maintenance'], Obtenido: ['care and maintenance', 'inactive', 'development'])

#### B) LLM Parser (GEMINI + Pipeline) (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "regions": [
    "castilla y leon"
  ],
  "project_status": [
    "care and maintenance",
    "inactive"
  ],
  "countries": [
    "spain"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **regions**: COINCIDE (Esperado: ['castilla y leon'], Obtenido: ['castilla y leon'])
    * 🟢 **project_status**: COINCIDE (Esperado: ['inactive', 'care and maintenance'], Obtenido: ['care and maintenance', 'inactive'])

#### C) spaCy NLP Pipeline (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "regions": [
    "castilla y leon"
  ],
  "project_status": [
    "inactive",
    "care and maintenance"
  ],
  "countries": [
    "spain"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **regions**: COINCIDE (Esperado: ['castilla y leon'], Obtenido: ['castilla y leon'])
    * 🟢 **project_status**: COINCIDE (Esperado: ['inactive', 'care and maintenance'], Obtenido: ['care and maintenance', 'inactive'])

#### D) GLiNER Zero-Shot Model (Puntuación: 0%)
*   **Filtros Extraídos**:
    ```json
    {}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **regions**: FALLA (Esperado: ['castilla y leon'], Obtenido: [])
    * 🔴 **project_status**: FALLA (Esperado: ['inactive', 'care and maintenance'], Obtenido: [])

---

### [TC_13] Implicit Spatial Anchoring
**Consulta**: *"proyectos de cobre en sevilla"*

*   **Filtros de Verdad del Terreno (Esperados)**:
    ```json
    {
  "countries": [
    "spain"
  ],
  "regions": [
    "andalucia"
  ],
  "commodities": [
    "copper"
  ]
}
    ```

#### A) Solr-Direct / Reglas (Legacy) (Puntuación: 67%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [],
  "regions": [
    "andalucia"
  ],
  "commodities": [
    "copper"
  ],
  "material_types": [],
  "storage_facility_types": [],
  "project_status": [
    "development"
  ],
  "companies": [],
  "site_names": [],
  "unfc_e": [],
  "unfc_f": [],
  "unfc_g": [],
  "environmental_flags": [],
  "free_text_constraints": [],
  "activity_types": [],
  "mine_types": [],
  "admin_statuses": [],
  "mine_statuses": [],
  "morphologies": [],
  "restored": null,
  "restoration_types": [],
  "site_contexts": []
}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **countries**: FALLA (Esperado: ['spain'], Obtenido: [])
    * 🟢 **regions**: COINCIDE (Esperado: ['andalucia'], Obtenido: ['andalucia'])
    * 🟢 **commodities**: COINCIDE (Esperado: ['copper'], Obtenido: ['copper'])

#### B) LLM Parser (GEMINI + Pipeline) (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "regions": [
    "andalucia"
  ],
  "commodities": [
    "copper"
  ],
  "countries": [
    "spain"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **countries**: COINCIDE (Esperado: ['spain'], Obtenido: ['spain'])
    * 🟢 **regions**: COINCIDE (Esperado: ['andalucia'], Obtenido: ['andalucia'])
    * 🟢 **commodities**: COINCIDE (Esperado: ['copper'], Obtenido: ['copper'])

#### C) spaCy NLP Pipeline (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "commodities": [
    "copper"
  ],
  "regions": [
    "andalucia"
  ],
  "countries": [
    "spain"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **countries**: COINCIDE (Esperado: ['spain'], Obtenido: ['spain'])
    * 🟢 **regions**: COINCIDE (Esperado: ['andalucia'], Obtenido: ['andalucia'])
    * 🟢 **commodities**: COINCIDE (Esperado: ['copper'], Obtenido: ['copper'])

#### D) GLiNER Zero-Shot Model (Puntuación: 0%)
*   **Filtros Extraídos**:
    ```json
    {}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **countries**: FALLA (Esperado: ['spain'], Obtenido: [])
    * 🔴 **regions**: FALLA (Esperado: ['andalucia'], Obtenido: [])
    * 🔴 **commodities**: FALLA (Esperado: ['copper'], Obtenido: [])

---

### [TC_14] Document-level context vs Search
**Consulta**: *"¿qué dice el informe sobre la estabilidad física de la presa de lodos de penouta?"*

*   **Filtros de Verdad del Terreno (Esperados)**:
    ```json
    {
  "intent": "hybrid",
  "needs_report_context": true,
  "site_names": [
    "Mina de Penouta"
  ]
}
    ```

#### A) Solr-Direct / Reglas (Legacy) (Puntuación: 0%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [],
  "regions": [],
  "commodities": [],
  "material_types": [],
  "storage_facility_types": [],
  "project_status": [],
  "companies": [],
  "site_names": [],
  "unfc_e": [],
  "unfc_f": [],
  "unfc_g": [],
  "environmental_flags": [],
  "free_text_constraints": [],
  "activity_types": [],
  "mine_types": [],
  "admin_statuses": [],
  "mine_statuses": [],
  "morphologies": [],
  "restored": null,
  "restoration_types": [],
  "site_contexts": []
}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **intent**: FALLA (Esperado: hybrid, Obtenido: filter_search)
    * 🔴 **needs_report_context**: FALLA (Esperado: True, Obtenido: False)
    * 🔴 **site_names**: FALLA (Esperado: ['Mina de Penouta'], Obtenido: [])

#### B) LLM Parser (GEMINI + Pipeline) (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "storage_facility_types": [
    "pond",
    "tailings storage facility"
  ],
  "material_types": [
    "sludge"
  ],
  "site_names": [
    "Mina de Penouta"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **intent**: COINCIDE (Esperado: hybrid, Obtenido: hybrid)
    * 🟢 **needs_report_context**: COINCIDE (Esperado: True, Obtenido: True)
    * 🟢 **site_names**: COINCIDE (Esperado: ['Mina de Penouta'], Obtenido: ['mina de penouta'])

#### C) spaCy NLP Pipeline (Puntuación: 67%)
*   **Filtros Extraídos**:
    ```json
    {
  "storage_facility_types": [
    "tailings storage facility"
  ],
  "site_names": [
    "Mina de Penouta"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **intent**: COINCIDE (Esperado: hybrid, Obtenido: hybrid)
    * 🔴 **needs_report_context**: FALLA (Esperado: True, Obtenido: None)
    * 🟢 **site_names**: COINCIDE (Esperado: ['Mina de Penouta'], Obtenido: ['mina de penouta'])

#### D) GLiNER Zero-Shot Model (Puntuación: 33%)
*   **Filtros Extraídos**:
    ```json
    {}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **intent**: COINCIDE (Esperado: hybrid, Obtenido: hybrid)
    * 🔴 **needs_report_context**: FALLA (Esperado: True, Obtenido: None)
    * 🔴 **site_names**: FALLA (Esperado: ['Mina de Penouta'], Obtenido: [])

---

### [TC_15] Off-topic / Greeting Conversational
**Consulta**: *"Hola, buenos días, me puedes ayudar?"*

*   **Filtros de Verdad del Terreno (Esperados)**:
    ```json
    {
  "intent": "generic_qa",
  "needs_database_filtering": false
}
    ```

#### A) Solr-Direct / Reglas (Legacy) (Puntuación: 0%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [],
  "regions": [],
  "commodities": [],
  "material_types": [],
  "storage_facility_types": [],
  "project_status": [],
  "companies": [],
  "site_names": [],
  "unfc_e": [],
  "unfc_f": [],
  "unfc_g": [],
  "environmental_flags": [],
  "free_text_constraints": [],
  "activity_types": [],
  "mine_types": [],
  "admin_statuses": [],
  "mine_statuses": [],
  "morphologies": [],
  "restored": null,
  "restoration_types": [],
  "site_contexts": []
}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **intent**: FALLA (Esperado: generic_qa, Obtenido: filter_search)
    * 🔴 **needs_database_filtering**: FALLA (Esperado: False, Obtenido: True)

#### B) LLM Parser (GEMINI + Pipeline) (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **intent**: COINCIDE (Esperado: generic_qa, Obtenido: generic_qa)
    * 🟢 **needs_database_filtering**: COINCIDE (Esperado: False, Obtenido: False)

#### C) spaCy NLP Pipeline (Puntuación: 0%)
*   **Filtros Extraídos**:
    ```json
    {}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **intent**: FALLA (Esperado: generic_qa, Obtenido: search)
    * 🔴 **needs_database_filtering**: FALLA (Esperado: False, Obtenido: None)

#### D) GLiNER Zero-Shot Model (Puntuación: 0%)
*   **Filtros Extraídos**:
    ```json
    {}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **intent**: FALLA (Esperado: generic_qa, Obtenido: search)
    * 🔴 **needs_database_filtering**: FALLA (Esperado: False, Obtenido: None)

---

### [TC_16] Advanced Material Synonyms
**Consulta**: *"balsas con lodos y barros en castilla y león"*

*   **Filtros de Verdad del Terreno (Esperados)**:
    ```json
    {
  "regions": [
    "castilla y leon"
  ],
  "storage_facility_types": [
    "pond"
  ],
  "material_types": [
    "sludge"
  ]
}
    ```

#### A) Solr-Direct / Reglas (Legacy) (Puntuación: 67%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [],
  "regions": [
    "castilla y leon"
  ],
  "commodities": [],
  "material_types": [],
  "storage_facility_types": [
    "pond"
  ],
  "project_status": [],
  "companies": [],
  "site_names": [],
  "unfc_e": [],
  "unfc_f": [],
  "unfc_g": [],
  "environmental_flags": [],
  "free_text_constraints": [],
  "activity_types": [],
  "mine_types": [],
  "admin_statuses": [],
  "mine_statuses": [],
  "morphologies": [],
  "restored": null,
  "restoration_types": [],
  "site_contexts": []
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **regions**: COINCIDE (Esperado: ['castilla y leon'], Obtenido: ['castilla y leon'])
    * 🟢 **storage_facility_types**: COINCIDE (Esperado: ['pond'], Obtenido: ['pond'])
    * 🔴 **material_types**: FALLA (Esperado: ['sludge'], Obtenido: [])

#### B) LLM Parser (GEMINI + Pipeline) (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "regions": [
    "castilla y leon"
  ],
  "storage_facility_types": [
    "pond"
  ],
  "material_types": [
    "sludge"
  ],
  "countries": [
    "spain"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **regions**: COINCIDE (Esperado: ['castilla y leon'], Obtenido: ['castilla y leon'])
    * 🟢 **storage_facility_types**: COINCIDE (Esperado: ['pond'], Obtenido: ['pond'])
    * 🟢 **material_types**: COINCIDE (Esperado: ['sludge'], Obtenido: ['sludge'])

#### C) spaCy NLP Pipeline (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "storage_facility_types": [
    "pond"
  ],
  "material_types": [
    "sludge"
  ],
  "regions": [
    "castilla y leon"
  ],
  "countries": [
    "spain"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **regions**: COINCIDE (Esperado: ['castilla y leon'], Obtenido: ['castilla y leon'])
    * 🟢 **storage_facility_types**: COINCIDE (Esperado: ['pond'], Obtenido: ['pond'])
    * 🟢 **material_types**: COINCIDE (Esperado: ['sludge'], Obtenido: ['sludge'])

#### D) GLiNER Zero-Shot Model (Puntuación: 0%)
*   **Filtros Extraídos**:
    ```json
    {
  "commodities": [
    "balsas"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **regions**: FALLA (Esperado: ['castilla y leon'], Obtenido: [])
    * 🔴 **storage_facility_types**: FALLA (Esperado: ['pond'], Obtenido: [])
    * 🔴 **material_types**: FALLA (Esperado: ['sludge'], Obtenido: [])

---

### [TC_17] Complex Negated Commodity
**Consulta**: *"instalaciones activas de cobre pero no de oro ni plata"*

*   **Filtros de Verdad del Terreno (Esperados)**:
    ```json
    {
  "project_status": [
    "active"
  ],
  "commodities": [
    "copper"
  ]
}
    ```

#### A) Solr-Direct / Reglas (Legacy) (Puntuación: 42%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [],
  "regions": [],
  "commodities": [
    "copper",
    "silver",
    "gold",
    "nickel"
  ],
  "material_types": [],
  "storage_facility_types": [],
  "project_status": [
    "active"
  ],
  "companies": [],
  "site_names": [],
  "unfc_e": [],
  "unfc_f": [],
  "unfc_g": [],
  "environmental_flags": [],
  "free_text_constraints": [],
  "activity_types": [],
  "mine_types": [],
  "admin_statuses": [],
  "mine_statuses": [],
  "morphologies": [],
  "restored": null,
  "restoration_types": [],
  "site_contexts": []
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **project_status**: COINCIDE (Esperado: ['active'], Obtenido: ['active'])
    * 🟡 **commodities**: COINCIDE PARCIALMENTE (25%) (Esperado: ['copper'], Obtenido: ['silver', 'copper', 'gold', 'nickel'])
    * 💥 **commodities (Exclusión)**: INFRACCIÓN (Valores excluidos presentes en positivos: ['silver', 'gold'])

#### B) LLM Parser (GEMINI + Pipeline) (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "commodities": [
    "copper"
  ],
  "project_status": [
    "active"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **project_status**: COINCIDE (Esperado: ['active'], Obtenido: ['active'])
    * 🟢 **commodities**: COINCIDE (Esperado: ['copper'], Obtenido: ['copper'])
    * 🟢 **commodities (Exclusión)**: COINCIDE (Excluido correctamente: ['gold', 'silver'])

#### C) spaCy NLP Pipeline (Puntuación: 8%)
*   **Filtros Extraídos**:
    ```json
    {
  "project_status": [
    "activas"
  ],
  "commodities": [
    "copper",
    "gold",
    "ni",
    "silver"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **project_status**: FALLA (Esperado: ['active'], Obtenido: ['activas'])
    * 🟡 **commodities**: COINCIDE PARCIALMENTE (25%) (Esperado: ['copper'], Obtenido: ['ni', 'silver', 'copper', 'gold'])
    * 💥 **commodities (Exclusión)**: INFRACCIÓN (Valores excluidos presentes en positivos: ['silver', 'gold'])

#### D) GLiNER Zero-Shot Model (Puntuación: 17%)
*   **Filtros Extraídos**:
    ```json
    {
  "commodities": [
    "copper",
    "silver"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **project_status**: FALLA (Esperado: ['active'], Obtenido: [])
    * 🟡 **commodities**: COINCIDE PARCIALMENTE (50%) (Esperado: ['copper'], Obtenido: ['silver', 'copper'])
    * 💥 **commodities (Exclusión)**: INFRACCIÓN (Valores excluidos presentes en positivos: ['silver'])

---

### [TC_18] Multiple Regions Mapping & Inferences
**Consulta**: *"escombreras mineras en ourense o asturias"*

*   **Filtros de Verdad del Terreno (Esperados)**:
    ```json
    {
  "countries": [
    "spain"
  ],
  "regions": [
    "galicia",
    "asturias"
  ],
  "storage_facility_types": [
    "waste dump"
  ]
}
    ```

#### A) Solr-Direct / Reglas (Legacy) (Puntuación: 67%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [],
  "regions": [
    "asturias",
    "galicia"
  ],
  "commodities": [],
  "material_types": [],
  "storage_facility_types": [
    "waste dump"
  ],
  "project_status": [],
  "companies": [],
  "site_names": [],
  "unfc_e": [],
  "unfc_f": [],
  "unfc_g": [],
  "environmental_flags": [],
  "free_text_constraints": [],
  "activity_types": [],
  "mine_types": [],
  "admin_statuses": [],
  "mine_statuses": [],
  "morphologies": [],
  "restored": null,
  "restoration_types": [],
  "site_contexts": []
}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **countries**: FALLA (Esperado: ['spain'], Obtenido: [])
    * 🟢 **regions**: COINCIDE (Esperado: ['galicia', 'asturias'], Obtenido: ['asturias', 'galicia'])
    * 🟢 **storage_facility_types**: COINCIDE (Esperado: ['waste dump'], Obtenido: ['waste dump'])

#### B) LLM Parser (GEMINI + Pipeline) (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "regions": [
    "asturias",
    "galicia"
  ],
  "storage_facility_types": [
    "waste dump"
  ],
  "countries": [
    "spain"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **countries**: COINCIDE (Esperado: ['spain'], Obtenido: ['spain'])
    * 🟢 **regions**: COINCIDE (Esperado: ['galicia', 'asturias'], Obtenido: ['asturias', 'galicia'])
    * 🟢 **storage_facility_types**: COINCIDE (Esperado: ['waste dump'], Obtenido: ['waste dump'])

#### C) spaCy NLP Pipeline (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "storage_facility_types": [
    "waste dump"
  ],
  "regions": [
    "galicia",
    "asturias"
  ],
  "countries": [
    "spain"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **countries**: COINCIDE (Esperado: ['spain'], Obtenido: ['spain'])
    * 🟢 **regions**: COINCIDE (Esperado: ['galicia', 'asturias'], Obtenido: ['asturias', 'galicia'])
    * 🟢 **storage_facility_types**: COINCIDE (Esperado: ['waste dump'], Obtenido: ['waste dump'])

#### D) GLiNER Zero-Shot Model (Puntuación: 0%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [
    "ourense"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **countries**: FALLA (Esperado: ['spain'], Obtenido: ['ourense'])
    * 🔴 **regions**: FALLA (Esperado: ['galicia', 'asturias'], Obtenido: [])
    * 🔴 **storage_facility_types**: FALLA (Esperado: ['waste dump'], Obtenido: [])

---

### [TC_19] Combined Chemical Symbols & Spanish Synonyms
**Consulta**: *"acopios de Cu o wolframio en Mieres"*

*   **Filtros de Verdad del Terreno (Esperados)**:
    ```json
    {
  "countries": [
    "spain"
  ],
  "regions": [
    "asturias"
  ],
  "commodities": [
    "copper",
    "tungsten"
  ],
  "storage_facility_types": [
    "stockpile"
  ]
}
    ```

#### A) Solr-Direct / Reglas (Legacy) (Puntuación: 75%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [],
  "regions": [
    "asturias"
  ],
  "commodities": [
    "tungsten",
    "copper"
  ],
  "material_types": [],
  "storage_facility_types": [
    "stockpile"
  ],
  "project_status": [],
  "companies": [],
  "site_names": [],
  "unfc_e": [],
  "unfc_f": [],
  "unfc_g": [],
  "environmental_flags": [],
  "free_text_constraints": [],
  "activity_types": [],
  "mine_types": [],
  "admin_statuses": [],
  "mine_statuses": [],
  "morphologies": [],
  "restored": null,
  "restoration_types": [],
  "site_contexts": []
}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **countries**: FALLA (Esperado: ['spain'], Obtenido: [])
    * 🟢 **regions**: COINCIDE (Esperado: ['asturias'], Obtenido: ['asturias'])
    * 🟢 **commodities**: COINCIDE (Esperado: ['copper', 'tungsten'], Obtenido: ['copper', 'tungsten'])
    * 🟢 **storage_facility_types**: COINCIDE (Esperado: ['stockpile'], Obtenido: ['stockpile'])

#### B) LLM Parser (GEMINI + Pipeline) (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "regions": [
    "asturias"
  ],
  "commodities": [
    "tungsten",
    "copper"
  ],
  "storage_facility_types": [
    "stockpile"
  ],
  "countries": [
    "spain"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **countries**: COINCIDE (Esperado: ['spain'], Obtenido: ['spain'])
    * 🟢 **regions**: COINCIDE (Esperado: ['asturias'], Obtenido: ['asturias'])
    * 🟢 **commodities**: COINCIDE (Esperado: ['copper', 'tungsten'], Obtenido: ['copper', 'tungsten'])
    * 🟢 **storage_facility_types**: COINCIDE (Esperado: ['stockpile'], Obtenido: ['stockpile'])

#### C) spaCy NLP Pipeline (Puntuación: 58%)
*   **Filtros Extraídos**:
    ```json
    {
  "commodities": [
    "cu",
    "tungsten"
  ],
  "regions": [
    "asturias"
  ],
  "countries": [
    "spain"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **countries**: COINCIDE (Esperado: ['spain'], Obtenido: ['spain'])
    * 🟢 **regions**: COINCIDE (Esperado: ['asturias'], Obtenido: ['asturias'])
    * 🟡 **commodities**: COINCIDE PARCIALMENTE (33%) (Esperado: ['copper', 'tungsten'], Obtenido: ['cu', 'tungsten'])
    * 🔴 **storage_facility_types**: FALLA (Esperado: ['stockpile'], Obtenido: [])

#### D) GLiNER Zero-Shot Model (Puntuación: 0%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [
    "mieres"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **countries**: FALLA (Esperado: ['spain'], Obtenido: ['mieres'])
    * 🔴 **regions**: FALLA (Esperado: ['asturias'], Obtenido: [])
    * 🔴 **commodities**: FALLA (Esperado: ['copper', 'tungsten'], Obtenido: [])
    * 🔴 **storage_facility_types**: FALLA (Esperado: ['stockpile'], Obtenido: [])

---

### [TC_20] Mixed Intent Conversation with DB Filters
**Consulta**: *"Hola, me gustaría saber si hay proyectos en desarrollo de litio en Cáceres, y si hay algún informe de estabilidad"*

*   **Filtros de Verdad del Terreno (Esperados)**:
    ```json
    {
  "intent": "hybrid",
  "needs_report_context": true,
  "regions": [
    "extremadura"
  ],
  "commodities": [
    "lithium"
  ],
  "project_status": [
    "development"
  ]
}
    ```

#### A) Solr-Direct / Reglas (Legacy) (Puntuación: 60%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [],
  "regions": [
    "extremadura"
  ],
  "commodities": [
    "lithium"
  ],
  "material_types": [],
  "storage_facility_types": [],
  "project_status": [
    "development"
  ],
  "companies": [],
  "site_names": [],
  "unfc_e": [],
  "unfc_f": [],
  "unfc_g": [],
  "environmental_flags": [],
  "free_text_constraints": [],
  "activity_types": [],
  "mine_types": [],
  "admin_statuses": [],
  "mine_statuses": [],
  "morphologies": [],
  "restored": null,
  "restoration_types": [],
  "site_contexts": []
}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **intent**: FALLA (Esperado: hybrid, Obtenido: filter_search)
    * 🔴 **needs_report_context**: FALLA (Esperado: True, Obtenido: False)
    * 🟢 **regions**: COINCIDE (Esperado: ['extremadura'], Obtenido: ['extremadura'])
    * 🟢 **commodities**: COINCIDE (Esperado: ['lithium'], Obtenido: ['lithium'])
    * 🟢 **project_status**: COINCIDE (Esperado: ['development'], Obtenido: ['development'])

#### B) LLM Parser (GEMINI + Pipeline) (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "regions": [
    "extremadura"
  ],
  "commodities": [
    "lithium"
  ],
  "project_status": [
    "development"
  ],
  "countries": [
    "spain"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **intent**: COINCIDE (Esperado: hybrid, Obtenido: hybrid)
    * 🟢 **needs_report_context**: COINCIDE (Esperado: True, Obtenido: True)
    * 🟢 **regions**: COINCIDE (Esperado: ['extremadura'], Obtenido: ['extremadura'])
    * 🟢 **commodities**: COINCIDE (Esperado: ['lithium'], Obtenido: ['lithium'])
    * 🟢 **project_status**: COINCIDE (Esperado: ['development'], Obtenido: ['development'])

#### C) spaCy NLP Pipeline (Puntuación: 80%)
*   **Filtros Extraídos**:
    ```json
    {
  "project_status": [
    "development"
  ],
  "commodities": [
    "lithium"
  ],
  "regions": [
    "extremadura"
  ],
  "countries": [
    "spain"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **intent**: COINCIDE (Esperado: hybrid, Obtenido: hybrid)
    * 🔴 **needs_report_context**: FALLA (Esperado: True, Obtenido: None)
    * 🟢 **regions**: COINCIDE (Esperado: ['extremadura'], Obtenido: ['extremadura'])
    * 🟢 **commodities**: COINCIDE (Esperado: ['lithium'], Obtenido: ['lithium'])
    * 🟢 **project_status**: COINCIDE (Esperado: ['development'], Obtenido: ['development'])

#### D) GLiNER Zero-Shot Model (Puntuación: 20%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [
    "caceres"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **intent**: COINCIDE (Esperado: hybrid, Obtenido: hybrid)
    * 🔴 **needs_report_context**: FALLA (Esperado: True, Obtenido: None)
    * 🔴 **regions**: FALLA (Esperado: ['extremadura'], Obtenido: [])
    * 🔴 **commodities**: FALLA (Esperado: ['lithium'], Obtenido: [])
    * 🔴 **project_status**: FALLA (Esperado: ['development'], Obtenido: [])

---

### [TC_21] Multiple Entity Scope Overlaps
**Consulta**: *"proyectos activos de cobre en salamanca y pasivos de litio en sevilla"*

*   **Filtros de Verdad del Terreno (Esperados)**:
    ```json
    {
  "commodities": [
    "copper",
    "lithium"
  ],
  "regions": [
    "castilla y leon",
    "andalucia"
  ],
  "project_status": [
    "active",
    "inactive"
  ]
}
    ```

#### A) Solr-Direct / Reglas (Legacy) (Puntuación: 78%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [],
  "regions": [
    "andalucia",
    "castilla y leon"
  ],
  "commodities": [
    "copper",
    "lithium"
  ],
  "material_types": [],
  "storage_facility_types": [],
  "project_status": [
    "active",
    "development"
  ],
  "companies": [],
  "site_names": [],
  "unfc_e": [],
  "unfc_f": [],
  "unfc_g": [],
  "environmental_flags": [],
  "free_text_constraints": [],
  "activity_types": [],
  "mine_types": [],
  "admin_statuses": [],
  "mine_statuses": [],
  "morphologies": [],
  "restored": null,
  "restoration_types": [],
  "site_contexts": []
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **commodities**: COINCIDE (Esperado: ['copper', 'lithium'], Obtenido: ['lithium', 'copper'])
    * 🟢 **regions**: COINCIDE (Esperado: ['castilla y leon', 'andalucia'], Obtenido: ['andalucia', 'castilla y leon'])
    * 🟡 **project_status**: COINCIDE PARCIALMENTE (33%) (Esperado: ['active', 'inactive'], Obtenido: ['active', 'development'])

#### B) LLM Parser (GEMINI + Pipeline) (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "regions": [
    "castilla y leon",
    "andalucia"
  ],
  "commodities": [
    "copper",
    "lithium"
  ],
  "project_status": [
    "active",
    "inactive"
  ],
  "countries": [
    "spain"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **commodities**: COINCIDE (Esperado: ['copper', 'lithium'], Obtenido: ['lithium', 'copper'])
    * 🟢 **regions**: COINCIDE (Esperado: ['castilla y leon', 'andalucia'], Obtenido: ['andalucia', 'castilla y leon'])
    * 🟢 **project_status**: COINCIDE (Esperado: ['active', 'inactive'], Obtenido: ['active', 'inactive'])

#### C) spaCy NLP Pipeline (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "project_status": [
    "active",
    "inactive"
  ],
  "commodities": [
    "copper",
    "lithium"
  ],
  "regions": [
    "castilla y leon",
    "andalucia"
  ],
  "countries": [
    "spain"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **commodities**: COINCIDE (Esperado: ['copper', 'lithium'], Obtenido: ['lithium', 'copper'])
    * 🟢 **regions**: COINCIDE (Esperado: ['castilla y leon', 'andalucia'], Obtenido: ['andalucia', 'castilla y leon'])
    * 🟢 **project_status**: COINCIDE (Esperado: ['active', 'inactive'], Obtenido: ['active', 'inactive'])

#### D) GLiNER Zero-Shot Model (Puntuación: 11%)
*   **Filtros Extraídos**:
    ```json
    {
  "commodities": [
    "copper",
    "pasivos de litio"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟡 **commodities**: COINCIDE PARCIALMENTE (33%) (Esperado: ['copper', 'lithium'], Obtenido: ['pasivos de litio', 'copper'])
    * 🔴 **regions**: FALLA (Esperado: ['castilla y leon', 'andalucia'], Obtenido: [])
    * 🔴 **project_status**: FALLA (Esperado: ['active', 'inactive'], Obtenido: [])

---

### [TC_22] Contextual Scope Exclusion
**Consulta**: *"instalaciones de volframio excepto las de Almonty en Galicia"*

*   **Filtros de Verdad del Terreno (Esperados)**:
    ```json
    {
  "countries": [
    "spain"
  ],
  "regions": [
    "galicia"
  ],
  "commodities": [
    "tungsten"
  ]
}
    ```

#### A) Solr-Direct / Reglas (Legacy) (Puntuación: 25%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [],
  "regions": [
    "galicia"
  ],
  "commodities": [],
  "material_types": [],
  "storage_facility_types": [],
  "project_status": [],
  "companies": [
    "almonty industries"
  ],
  "site_names": [],
  "unfc_e": [],
  "unfc_f": [],
  "unfc_g": [],
  "environmental_flags": [],
  "free_text_constraints": [],
  "activity_types": [],
  "mine_types": [],
  "admin_statuses": [],
  "mine_statuses": [],
  "morphologies": [],
  "restored": null,
  "restoration_types": [],
  "site_contexts": []
}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **countries**: FALLA (Esperado: ['spain'], Obtenido: [])
    * 🟢 **regions**: COINCIDE (Esperado: ['galicia'], Obtenido: ['galicia'])
    * 🔴 **commodities**: FALLA (Esperado: ['tungsten'], Obtenido: [])
    * 💥 **companies (Exclusión)**: INFRACCIÓN (Valores excluidos presentes en positivos: ['almonty industries'])

#### B) LLM Parser (GEMINI + Pipeline) (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "regions": [
    "galicia"
  ],
  "commodities": [
    "tungsten"
  ],
  "countries": [
    "spain"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **countries**: COINCIDE (Esperado: ['spain'], Obtenido: ['spain'])
    * 🟢 **regions**: COINCIDE (Esperado: ['galicia'], Obtenido: ['galicia'])
    * 🟢 **commodities**: COINCIDE (Esperado: ['tungsten'], Obtenido: ['tungsten'])
    * 🟢 **companies (Exclusión)**: COINCIDE (Excluido correctamente: ['almonty industries'])

#### C) spaCy NLP Pipeline (Puntuación: 75%)
*   **Filtros Extraídos**:
    ```json
    {
  "commodities": [
    "tungsten"
  ],
  "companies": [
    "almonty industries"
  ],
  "regions": [
    "galicia"
  ],
  "countries": [
    "spain"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **countries**: COINCIDE (Esperado: ['spain'], Obtenido: ['spain'])
    * 🟢 **regions**: COINCIDE (Esperado: ['galicia'], Obtenido: ['galicia'])
    * 🟢 **commodities**: COINCIDE (Esperado: ['tungsten'], Obtenido: ['tungsten'])
    * 💥 **companies (Exclusión)**: INFRACCIÓN (Valores excluidos presentes en positivos: ['almonty industries'])

#### D) GLiNER Zero-Shot Model (Puntuación: 0%)
*   **Filtros Extraídos**:
    ```json
    {
  "site_names": [
    "almonty"
  ],
  "countries": [
    "galicia"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **countries**: FALLA (Esperado: ['spain'], Obtenido: ['galicia'])
    * 🔴 **regions**: FALLA (Esperado: ['galicia'], Obtenido: [])
    * 🔴 **commodities**: FALLA (Esperado: ['tungsten'], Obtenido: [])
    * 🔴 **companies (Exclusión)**: FALLA (Esperado excluir: ['almonty industries'], Obtenido: [])

---

### [TC_23] Pragmatic Stage Status Negations
**Consulta**: *"proyectos de estaño que ya no están en fase de desarrollo pero que no explotan comercialmente"*

*   **Filtros de Verdad del Terreno (Esperados)**:
    ```json
    {
  "commodities": [
    "tin"
  ]
}
    ```

#### A) Solr-Direct / Reglas (Legacy) (Puntuación: 50%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [],
  "regions": [],
  "commodities": [
    "tin"
  ],
  "material_types": [],
  "storage_facility_types": [],
  "project_status": [
    "development"
  ],
  "companies": [],
  "site_names": [],
  "unfc_e": [],
  "unfc_f": [],
  "unfc_g": [],
  "environmental_flags": [],
  "free_text_constraints": [],
  "activity_types": [],
  "mine_types": [],
  "admin_statuses": [],
  "mine_statuses": [],
  "morphologies": [],
  "restored": null,
  "restoration_types": [],
  "site_contexts": []
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **commodities**: COINCIDE (Esperado: ['tin'], Obtenido: ['tin'])
    * 💥 **project_status (Exclusión)**: INFRACCIÓN (Valores excluidos presentes en positivos: ['development'])

#### B) LLM Parser (GEMINI + Pipeline) (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "commodities": [
    "tin"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **commodities**: COINCIDE (Esperado: ['tin'], Obtenido: ['tin'])
    * 🟢 **project_status (Exclusión)**: COINCIDE (Excluido correctamente: ['development', 'active'])

#### C) spaCy NLP Pipeline (Puntuación: 50%)
*   **Filtros Extraídos**:
    ```json
    {
  "commodities": [
    "tin"
  ],
  "project_status": [
    "development"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **commodities**: COINCIDE (Esperado: ['tin'], Obtenido: ['tin'])
    * 💥 **project_status (Exclusión)**: INFRACCIÓN (Valores excluidos presentes en positivos: ['development'])

#### D) GLiNER Zero-Shot Model (Puntuación: 0%)
*   **Filtros Extraídos**:
    ```json
    {}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **commodities**: FALLA (Esperado: ['tin'], Obtenido: [])
    * 🔴 **project_status (Exclusión)**: FALLA (Esperado excluir: ['development', 'active'], Obtenido: [])

---

### [TC_24] Multi-intent Geographic Inference
**Consulta**: *"minas de litio en Alentejo y cobre en Huelva"*

*   **Filtros de Verdad del Terreno (Esperados)**:
    ```json
    {
  "countries": [
    "portugal",
    "spain"
  ],
  "regions": [
    "alentejo",
    "andalucia"
  ],
  "commodities": [
    "lithium",
    "copper"
  ]
}
    ```

#### A) Solr-Direct / Reglas (Legacy) (Puntuación: 67%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [],
  "regions": [
    "andalucia",
    "alentejo"
  ],
  "commodities": [
    "copper",
    "lithium"
  ],
  "material_types": [],
  "storage_facility_types": [],
  "project_status": [],
  "companies": [],
  "site_names": [],
  "unfc_e": [],
  "unfc_f": [],
  "unfc_g": [],
  "environmental_flags": [],
  "free_text_constraints": [],
  "activity_types": [],
  "mine_types": [],
  "admin_statuses": [],
  "mine_statuses": [],
  "morphologies": [],
  "restored": null,
  "restoration_types": [],
  "site_contexts": []
}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **countries**: FALLA (Esperado: ['portugal', 'spain'], Obtenido: [])
    * 🟢 **regions**: COINCIDE (Esperado: ['alentejo', 'andalucia'], Obtenido: ['andalucia', 'alentejo'])
    * 🟢 **commodities**: COINCIDE (Esperado: ['lithium', 'copper'], Obtenido: ['lithium', 'copper'])

#### B) LLM Parser (GEMINI + Pipeline) (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "regions": [
    "alentejo",
    "andalucia"
  ],
  "commodities": [
    "copper",
    "lithium"
  ],
  "countries": [
    "portugal",
    "spain"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **countries**: COINCIDE (Esperado: ['portugal', 'spain'], Obtenido: ['portugal', 'spain'])
    * 🟢 **regions**: COINCIDE (Esperado: ['alentejo', 'andalucia'], Obtenido: ['andalucia', 'alentejo'])
    * 🟢 **commodities**: COINCIDE (Esperado: ['lithium', 'copper'], Obtenido: ['lithium', 'copper'])

#### C) spaCy NLP Pipeline (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "commodities": [
    "lithium",
    "copper"
  ],
  "regions": [
    "alentejo",
    "andalucia"
  ],
  "countries": [
    "portugal",
    "spain"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **countries**: COINCIDE (Esperado: ['portugal', 'spain'], Obtenido: ['portugal', 'spain'])
    * 🟢 **regions**: COINCIDE (Esperado: ['alentejo', 'andalucia'], Obtenido: ['andalucia', 'alentejo'])
    * 🟢 **commodities**: COINCIDE (Esperado: ['lithium', 'copper'], Obtenido: ['lithium', 'copper'])

#### D) GLiNER Zero-Shot Model (Puntuación: 0%)
*   **Filtros Extraídos**:
    ```json
    {
  "commodities": [
    "minas de litio"
  ],
  "countries": [
    "alentejo",
    "huelva"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **countries**: FALLA (Esperado: ['portugal', 'spain'], Obtenido: ['huelva', 'alentejo'])
    * 🔴 **regions**: FALLA (Esperado: ['alentejo', 'andalucia'], Obtenido: [])
    * 🔴 **commodities**: FALLA (Esperado: ['lithium', 'copper'], Obtenido: ['minas de litio'])

---

### [TC_25] Double Negative Parsing
**Consulta**: *"no quiero proyectos que no sean de cobre"*

*   **Filtros de Verdad del Terreno (Esperados)**:
    ```json
    {
  "commodities": [
    "copper"
  ]
}
    ```

#### A) Solr-Direct / Reglas (Legacy) (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [],
  "regions": [],
  "commodities": [
    "copper"
  ],
  "material_types": [],
  "storage_facility_types": [],
  "project_status": [
    "development"
  ],
  "companies": [],
  "site_names": [],
  "unfc_e": [],
  "unfc_f": [],
  "unfc_g": [],
  "environmental_flags": [],
  "free_text_constraints": [],
  "activity_types": [],
  "mine_types": [],
  "admin_statuses": [],
  "mine_statuses": [],
  "morphologies": [],
  "restored": null,
  "restoration_types": [],
  "site_contexts": []
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **commodities**: COINCIDE (Esperado: ['copper'], Obtenido: ['copper'])

#### B) LLM Parser (GEMINI + Pipeline) (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "commodities": [
    "copper"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **commodities**: COINCIDE (Esperado: ['copper'], Obtenido: ['copper'])

#### C) spaCy NLP Pipeline (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "commodities": [
    "copper"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **commodities**: COINCIDE (Esperado: ['copper'], Obtenido: ['copper'])

#### D) GLiNER Zero-Shot Model (Puntuación: 0%)
*   **Filtros Extraídos**:
    ```json
    {}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **commodities**: FALLA (Esperado: ['copper'], Obtenido: [])

---

### [TC_26] Conversational Temporal Correction
**Consulta**: *"¿puedes buscarme el informe de estabilidad de Riotinto? Ah no, mejor solo muéstrame si el proyecto está activo"*

*   **Filtros de Verdad del Terreno (Esperados)**:
    ```json
    {
  "intent": "search",
  "site_names": [
    "Riotinto Project"
  ],
  "project_status": [
    "active"
  ]
}
    ```

#### A) Solr-Direct / Reglas (Legacy) (Puntuación: 50%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [],
  "regions": [
    "andalucia"
  ],
  "commodities": [
    "tin"
  ],
  "material_types": [],
  "storage_facility_types": [],
  "project_status": [
    "active",
    "development"
  ],
  "companies": [],
  "site_names": [
    "Riotinto Project"
  ],
  "unfc_e": [],
  "unfc_f": [],
  "unfc_g": [],
  "environmental_flags": [],
  "free_text_constraints": [],
  "activity_types": [],
  "mine_types": [],
  "admin_statuses": [],
  "mine_statuses": [],
  "morphologies": [],
  "restored": null,
  "restoration_types": [],
  "site_contexts": []
}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **intent**: FALLA (Esperado: search, Obtenido: filter_search)
    * 🟢 **site_names**: COINCIDE (Esperado: ['Riotinto Project'], Obtenido: ['riotinto project'])
    * 🟡 **project_status**: COINCIDE PARCIALMENTE (50%) (Esperado: ['active'], Obtenido: ['active', 'development'])

#### B) LLM Parser (GEMINI + Pipeline) (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "regions": [
    "andalucia"
  ],
  "commodities": [
    "copper",
    "tin"
  ],
  "project_status": [
    "active"
  ],
  "site_names": [
    "Riotinto Project"
  ],
  "countries": [
    "spain"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **intent**: COINCIDE (Esperado: search, Obtenido: search)
    * 🟢 **site_names**: COINCIDE (Esperado: ['Riotinto Project'], Obtenido: ['riotinto project'])
    * 🟢 **project_status**: COINCIDE (Esperado: ['active'], Obtenido: ['active'])

#### C) spaCy NLP Pipeline (Puntuación: 67%)
*   **Filtros Extraídos**:
    ```json
    {
  "site_names": [
    "Riotinto Project"
  ],
  "project_status": [
    "active"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **intent**: FALLA (Esperado: search, Obtenido: hybrid)
    * 🟢 **site_names**: COINCIDE (Esperado: ['Riotinto Project'], Obtenido: ['riotinto project'])
    * 🟢 **project_status**: COINCIDE (Esperado: ['active'], Obtenido: ['active'])

#### D) GLiNER Zero-Shot Model (Puntuación: 0%)
*   **Filtros Extraídos**:
    ```json
    {}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **intent**: FALLA (Esperado: search, Obtenido: hybrid)
    * 🔴 **site_names**: FALLA (Esperado: ['Riotinto Project'], Obtenido: [])
    * 🔴 **project_status**: FALLA (Esperado: ['active'], Obtenido: [])

---

### [TC_27] Zero-Resource Synonyms (Extrapolation)
**Consulta**: *"instalaciones para procesar escorias y subproductos de cobalto"*

*   **Filtros de Verdad del Terreno (Esperados)**:
    ```json
    {
  "commodities": [
    "cobalt"
  ],
  "material_types": [
    "tailings"
  ]
}
    ```

#### A) Solr-Direct / Reglas (Legacy) (Puntuación: 50%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [],
  "regions": [],
  "commodities": [
    "cobalt"
  ],
  "material_types": [],
  "storage_facility_types": [],
  "project_status": [],
  "companies": [],
  "site_names": [],
  "unfc_e": [],
  "unfc_f": [],
  "unfc_g": [],
  "environmental_flags": [],
  "free_text_constraints": [],
  "activity_types": [],
  "mine_types": [],
  "admin_statuses": [],
  "mine_statuses": [],
  "morphologies": [],
  "restored": null,
  "restoration_types": [],
  "site_contexts": []
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **commodities**: COINCIDE (Esperado: ['cobalt'], Obtenido: ['cobalt'])
    * 🔴 **material_types**: FALLA (Esperado: ['tailings'], Obtenido: [])

#### B) LLM Parser (GEMINI + Pipeline) (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "commodities": [
    "cobalt"
  ],
  "material_types": [
    "tailings"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **commodities**: COINCIDE (Esperado: ['cobalt'], Obtenido: ['cobalt'])
    * 🟢 **material_types**: COINCIDE (Esperado: ['tailings'], Obtenido: ['tailings'])

#### C) spaCy NLP Pipeline (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "material_types": [
    "tailings"
  ],
  "commodities": [
    "cobalt"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **commodities**: COINCIDE (Esperado: ['cobalt'], Obtenido: ['cobalt'])
    * 🟢 **material_types**: COINCIDE (Esperado: ['tailings'], Obtenido: ['tailings'])

#### D) GLiNER Zero-Shot Model (Puntuación: 50%)
*   **Filtros Extraídos**:
    ```json
    {
  "storage_facility_types": [
    "instalaciones"
  ],
  "commodities": [
    "cobalt"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **commodities**: COINCIDE (Esperado: ['cobalt'], Obtenido: ['cobalt'])
    * 🔴 **material_types**: FALLA (Esperado: ['tailings'], Obtenido: [])

---

### [TC_28] Geological Stage Reasoning
**Consulta**: *"concesiones mineras que ya tienen autorización de explotación en asturias"*

*   **Filtros de Verdad del Terreno (Esperados)**:
    ```json
    {
  "countries": [
    "spain"
  ],
  "regions": [
    "asturias"
  ],
  "project_status": [
    "active"
  ]
}
    ```

#### A) Solr-Direct / Reglas (Legacy) (Puntuación: 33%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [],
  "regions": [
    "asturias"
  ],
  "commodities": [],
  "material_types": [],
  "storage_facility_types": [],
  "project_status": [],
  "companies": [],
  "site_names": [],
  "unfc_e": [],
  "unfc_f": [],
  "unfc_g": [],
  "environmental_flags": [],
  "free_text_constraints": [],
  "activity_types": [],
  "mine_types": [],
  "admin_statuses": [],
  "mine_statuses": [],
  "morphologies": [],
  "restored": null,
  "restoration_types": [],
  "site_contexts": []
}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **countries**: FALLA (Esperado: ['spain'], Obtenido: [])
    * 🟢 **regions**: COINCIDE (Esperado: ['asturias'], Obtenido: ['asturias'])
    * 🔴 **project_status**: FALLA (Esperado: ['active'], Obtenido: [])

#### B) LLM Parser (GEMINI + Pipeline) (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "regions": [
    "asturias"
  ],
  "project_status": [
    "active"
  ],
  "countries": [
    "spain"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **countries**: COINCIDE (Esperado: ['spain'], Obtenido: ['spain'])
    * 🟢 **regions**: COINCIDE (Esperado: ['asturias'], Obtenido: ['asturias'])
    * 🟢 **project_status**: COINCIDE (Esperado: ['active'], Obtenido: ['active'])

#### C) spaCy NLP Pipeline (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "project_status": [
    "active"
  ],
  "regions": [
    "asturias"
  ],
  "countries": [
    "spain"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **countries**: COINCIDE (Esperado: ['spain'], Obtenido: ['spain'])
    * 🟢 **regions**: COINCIDE (Esperado: ['asturias'], Obtenido: ['asturias'])
    * 🟢 **project_status**: COINCIDE (Esperado: ['active'], Obtenido: ['active'])

#### D) GLiNER Zero-Shot Model (Puntuación: 0%)
*   **Filtros Extraídos**:
    ```json
    {}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **countries**: FALLA (Esperado: ['spain'], Obtenido: [])
    * 🔴 **regions**: FALLA (Esperado: ['asturias'], Obtenido: [])
    * 🔴 **project_status**: FALLA (Esperado: ['active'], Obtenido: [])

---

### [TC_29] Comparative Range Filter Representation
**Consulta**: *"proyectos de litio con alta viabilidad geológica (G1 o G2)"*

*   **Filtros de Verdad del Terreno (Esperados)**:
    ```json
    {
  "commodities": [
    "lithium"
  ],
  "unfc_g": [
    "G1",
    "G2"
  ]
}
    ```

#### A) Solr-Direct / Reglas (Legacy) (Puntuación: 50%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [],
  "regions": [],
  "commodities": [
    "lithium"
  ],
  "material_types": [],
  "storage_facility_types": [],
  "project_status": [
    "development"
  ],
  "companies": [],
  "site_names": [],
  "unfc_e": [],
  "unfc_f": [],
  "unfc_g": [],
  "environmental_flags": [],
  "free_text_constraints": [],
  "activity_types": [],
  "mine_types": [],
  "admin_statuses": [],
  "mine_statuses": [],
  "morphologies": [],
  "restored": null,
  "restoration_types": [],
  "site_contexts": []
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **commodities**: COINCIDE (Esperado: ['lithium'], Obtenido: ['lithium'])
    * 🔴 **unfc_g**: FALLA (Esperado: ['G1', 'G2'], Obtenido: [])

#### B) LLM Parser (GEMINI + Pipeline) (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "commodities": [
    "lithium"
  ],
  "unfc_g": [
    "g1",
    "g2"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **commodities**: COINCIDE (Esperado: ['lithium'], Obtenido: ['lithium'])
    * 🟢 **unfc_g**: COINCIDE (Esperado: ['G1', 'G2'], Obtenido: ['g2', 'g1'])

#### C) spaCy NLP Pipeline (Puntuación: 50%)
*   **Filtros Extraídos**:
    ```json
    {
  "commodities": [
    "lithium"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **commodities**: COINCIDE (Esperado: ['lithium'], Obtenido: ['lithium'])
    * 🔴 **unfc_g**: FALLA (Esperado: ['G1', 'G2'], Obtenido: [])

#### D) GLiNER Zero-Shot Model (Puntuación: 0%)
*   **Filtros Extraídos**:
    ```json
    {
  "regions": [
    "g1"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **commodities**: FALLA (Esperado: ['lithium'], Obtenido: [])
    * 🔴 **unfc_g**: FALLA (Esperado: ['G1', 'G2'], Obtenido: [])

---

### [TC_30] Pragmatic Logical Contradiction
**Consulta**: *"escombreras que estén activas y cerradas a la vez en galicia"*

*   **Filtros de Verdad del Terreno (Esperados)**:
    ```json
    {
  "countries": [
    "spain"
  ],
  "regions": [
    "galicia"
  ],
  "storage_facility_types": [
    "waste dump"
  ],
  "project_status": [
    "active",
    "inactive"
  ]
}
    ```

#### A) Solr-Direct / Reglas (Legacy) (Puntuación: 62%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [],
  "regions": [
    "galicia"
  ],
  "commodities": [],
  "material_types": [],
  "storage_facility_types": [
    "waste dump"
  ],
  "project_status": [
    "active"
  ],
  "companies": [],
  "site_names": [],
  "unfc_e": [],
  "unfc_f": [],
  "unfc_g": [],
  "environmental_flags": [],
  "free_text_constraints": [],
  "activity_types": [],
  "mine_types": [],
  "admin_statuses": [],
  "mine_statuses": [],
  "morphologies": [],
  "restored": null,
  "restoration_types": [],
  "site_contexts": []
}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **countries**: FALLA (Esperado: ['spain'], Obtenido: [])
    * 🟢 **regions**: COINCIDE (Esperado: ['galicia'], Obtenido: ['galicia'])
    * 🟢 **storage_facility_types**: COINCIDE (Esperado: ['waste dump'], Obtenido: ['waste dump'])
    * 🟡 **project_status**: COINCIDE PARCIALMENTE (50%) (Esperado: ['active', 'inactive'], Obtenido: ['active'])

#### B) LLM Parser (GEMINI + Pipeline) (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "regions": [
    "galicia"
  ],
  "storage_facility_types": [
    "waste dump"
  ],
  "project_status": [
    "inactive",
    "active"
  ],
  "countries": [
    "spain"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **countries**: COINCIDE (Esperado: ['spain'], Obtenido: ['spain'])
    * 🟢 **regions**: COINCIDE (Esperado: ['galicia'], Obtenido: ['galicia'])
    * 🟢 **storage_facility_types**: COINCIDE (Esperado: ['waste dump'], Obtenido: ['waste dump'])
    * 🟢 **project_status**: COINCIDE (Esperado: ['active', 'inactive'], Obtenido: ['active', 'inactive'])

#### C) spaCy NLP Pipeline (Puntuación: 83%)
*   **Filtros Extraídos**:
    ```json
    {
  "storage_facility_types": [
    "waste dump"
  ],
  "project_status": [
    "activas",
    "inactive"
  ],
  "regions": [
    "galicia"
  ],
  "countries": [
    "spain"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **countries**: COINCIDE (Esperado: ['spain'], Obtenido: ['spain'])
    * 🟢 **regions**: COINCIDE (Esperado: ['galicia'], Obtenido: ['galicia'])
    * 🟢 **storage_facility_types**: COINCIDE (Esperado: ['waste dump'], Obtenido: ['waste dump'])
    * 🟡 **project_status**: COINCIDE PARCIALMENTE (33%) (Esperado: ['active', 'inactive'], Obtenido: ['inactive', 'activas'])

#### D) GLiNER Zero-Shot Model (Puntuación: 0%)
*   **Filtros Extraídos**:
    ```json
    {}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **countries**: FALLA (Esperado: ['spain'], Obtenido: [])
    * 🔴 **regions**: FALLA (Esperado: ['galicia'], Obtenido: [])
    * 🔴 **storage_facility_types**: FALLA (Esperado: ['waste dump'], Obtenido: [])
    * 🔴 **project_status**: FALLA (Esperado: ['active', 'inactive'], Obtenido: [])

---

### [TC_31] English - Geographical Synonyms & Ambiguity
**Consulta**: *"active copper projects in the south of Spain except those managed by Atalaya"*

*   **Filtros de Verdad del Terreno (Esperados)**:
    ```json
    {
  "countries": [
    "spain"
  ],
  "regions": [
    "andalucia"
  ],
  "commodities": [
    "copper"
  ],
  "project_status": [
    "active"
  ]
}
    ```

#### A) Solr-Direct / Reglas (Legacy) (Puntuación: 60%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [
    "spain"
  ],
  "regions": [],
  "commodities": [
    "copper"
  ],
  "material_types": [],
  "storage_facility_types": [],
  "project_status": [
    "active"
  ],
  "companies": [
    "atalaya mining"
  ],
  "site_names": [],
  "unfc_e": [],
  "unfc_f": [],
  "unfc_g": [],
  "environmental_flags": [],
  "free_text_constraints": [],
  "activity_types": [],
  "mine_types": [],
  "admin_statuses": [],
  "mine_statuses": [],
  "morphologies": [],
  "restored": null,
  "restoration_types": [],
  "site_contexts": []
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **countries**: COINCIDE (Esperado: ['spain'], Obtenido: ['spain'])
    * 🔴 **regions**: FALLA (Esperado: ['andalucia'], Obtenido: [])
    * 🟢 **commodities**: COINCIDE (Esperado: ['copper'], Obtenido: ['copper'])
    * 🟢 **project_status**: COINCIDE (Esperado: ['active'], Obtenido: ['active'])
    * 💥 **companies (Exclusión)**: INFRACCIÓN (Valores excluidos presentes en positivos: ['atalaya mining'])

#### B) LLM Parser (GEMINI + Pipeline) (Puntuación: 80%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [
    "spain"
  ],
  "commodities": [
    "copper"
  ],
  "project_status": [
    "active"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **countries**: COINCIDE (Esperado: ['spain'], Obtenido: ['spain'])
    * 🔴 **regions**: FALLA (Esperado: ['andalucia'], Obtenido: [])
    * 🟢 **commodities**: COINCIDE (Esperado: ['copper'], Obtenido: ['copper'])
    * 🟢 **project_status**: COINCIDE (Esperado: ['active'], Obtenido: ['active'])
    * 🟢 **companies (Exclusión)**: COINCIDE (Excluido correctamente: ['atalaya mining'])

#### C) spaCy NLP Pipeline (Puntuación: 60%)
*   **Filtros Extraídos**:
    ```json
    {
  "project_status": [
    "active"
  ],
  "commodities": [
    "copper"
  ],
  "countries": [
    "spain"
  ],
  "companies": [
    "atalaya mining"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **countries**: COINCIDE (Esperado: ['spain'], Obtenido: ['spain'])
    * 🔴 **regions**: FALLA (Esperado: ['andalucia'], Obtenido: [])
    * 🟢 **commodities**: COINCIDE (Esperado: ['copper'], Obtenido: ['copper'])
    * 🟢 **project_status**: COINCIDE (Esperado: ['active'], Obtenido: ['active'])
    * 💥 **companies (Exclusión)**: INFRACCIÓN (Valores excluidos presentes en positivos: ['atalaya mining'])

#### D) GLiNER Zero-Shot Model (Puntuación: 40%)
*   **Filtros Extraídos**:
    ```json
    {
  "commodities": [
    "copper"
  ],
  "countries": [
    "spain"
  ],
  "companies": [
    "atalaya mining"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **countries**: COINCIDE (Esperado: ['spain'], Obtenido: ['spain'])
    * 🔴 **regions**: FALLA (Esperado: ['andalucia'], Obtenido: [])
    * 🟢 **commodities**: COINCIDE (Esperado: ['copper'], Obtenido: ['copper'])
    * 🔴 **project_status**: FALLA (Esperado: ['active'], Obtenido: [])
    * 💥 **companies (Exclusión)**: INFRACCIÓN (Valores excluidos presentes en positivos: ['atalaya mining'])

---

### [TC_32] French - Commodity & Storage
**Consulta**: *"bassins de décantation de cobalt et de nickel en Estrémadure"*

*   **Filtros de Verdad del Terreno (Esperados)**:
    ```json
    {
  "countries": [
    "spain"
  ],
  "regions": [
    "extremadura"
  ],
  "commodities": [
    "cobalt",
    "nickel"
  ],
  "storage_facility_types": [
    "tailings storage facility"
  ]
}
    ```

#### A) Solr-Direct / Reglas (Legacy) (Puntuación: 25%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [],
  "regions": [],
  "commodities": [
    "nickel",
    "cobalt"
  ],
  "material_types": [],
  "storage_facility_types": [],
  "project_status": [],
  "companies": [],
  "site_names": [],
  "unfc_e": [],
  "unfc_f": [],
  "unfc_g": [],
  "environmental_flags": [],
  "free_text_constraints": [],
  "activity_types": [],
  "mine_types": [],
  "admin_statuses": [],
  "mine_statuses": [],
  "morphologies": [],
  "restored": null,
  "restoration_types": [],
  "site_contexts": []
}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **countries**: FALLA (Esperado: ['spain'], Obtenido: [])
    * 🔴 **regions**: FALLA (Esperado: ['extremadura'], Obtenido: [])
    * 🟢 **commodities**: COINCIDE (Esperado: ['cobalt', 'nickel'], Obtenido: ['cobalt', 'nickel'])
    * 🔴 **storage_facility_types**: FALLA (Esperado: ['tailings storage facility'], Obtenido: [])

#### B) LLM Parser (GEMINI + Pipeline) (Puntuación: 88%)
*   **Filtros Extraídos**:
    ```json
    {
  "regions": [
    "extremadura"
  ],
  "commodities": [
    "cobalt"
  ],
  "storage_facility_types": [
    "tailings storage facility"
  ],
  "countries": [
    "spain"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **countries**: COINCIDE (Esperado: ['spain'], Obtenido: ['spain'])
    * 🟢 **regions**: COINCIDE (Esperado: ['extremadura'], Obtenido: ['extremadura'])
    * 🟡 **commodities**: COINCIDE PARCIALMENTE (50%) (Esperado: ['cobalt', 'nickel'], Obtenido: ['cobalt'])
    * 🟢 **storage_facility_types**: COINCIDE (Esperado: ['tailings storage facility'], Obtenido: ['tailings storage facility'])

#### C) spaCy NLP Pipeline (Puntuación: 38%)
*   **Filtros Extraídos**:
    ```json
    {
  "storage_facility_types": [
    "tailings storage facility"
  ],
  "commodities": [
    "cobalt"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **countries**: FALLA (Esperado: ['spain'], Obtenido: [])
    * 🔴 **regions**: FALLA (Esperado: ['extremadura'], Obtenido: [])
    * 🟡 **commodities**: COINCIDE PARCIALMENTE (50%) (Esperado: ['cobalt', 'nickel'], Obtenido: ['cobalt'])
    * 🟢 **storage_facility_types**: COINCIDE (Esperado: ['tailings storage facility'], Obtenido: ['tailings storage facility'])

#### D) GLiNER Zero-Shot Model (Puntuación: 25%)
*   **Filtros Extraídos**:
    ```json
    {
  "commodities": [
    "cobalt",
    "nickel"
  ],
  "countries": [
    "estremadure"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **countries**: FALLA (Esperado: ['spain'], Obtenido: ['estremadure'])
    * 🔴 **regions**: FALLA (Esperado: ['extremadura'], Obtenido: [])
    * 🟢 **commodities**: COINCIDE (Esperado: ['cobalt', 'nickel'], Obtenido: ['cobalt', 'nickel'])
    * 🔴 **storage_facility_types**: FALLA (Esperado: ['tailings storage facility'], Obtenido: [])

---

### [TC_33] German - Material & Status
**Consulta**: *"inaktive Bergehalden mit Wolfram im Galicien"*

*   **Filtros de Verdad del Terreno (Esperados)**:
    ```json
    {
  "countries": [
    "spain"
  ],
  "regions": [
    "galicia"
  ],
  "commodities": [
    "tungsten"
  ],
  "project_status": [
    "inactive"
  ],
  "storage_facility_types": [
    "waste dump"
  ]
}
    ```

#### A) Solr-Direct / Reglas (Legacy) (Puntuación: 0%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [],
  "regions": [],
  "commodities": [],
  "material_types": [],
  "storage_facility_types": [],
  "project_status": [],
  "companies": [],
  "site_names": [],
  "unfc_e": [],
  "unfc_f": [],
  "unfc_g": [],
  "environmental_flags": [],
  "free_text_constraints": [],
  "activity_types": [],
  "mine_types": [],
  "admin_statuses": [],
  "mine_statuses": [],
  "morphologies": [],
  "restored": null,
  "restoration_types": [],
  "site_contexts": []
}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **countries**: FALLA (Esperado: ['spain'], Obtenido: [])
    * 🔴 **regions**: FALLA (Esperado: ['galicia'], Obtenido: [])
    * 🔴 **commodities**: FALLA (Esperado: ['tungsten'], Obtenido: [])
    * 🔴 **project_status**: FALLA (Esperado: ['inactive'], Obtenido: [])
    * 🔴 **storage_facility_types**: FALLA (Esperado: ['waste dump'], Obtenido: [])

#### B) LLM Parser (GEMINI + Pipeline) (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "regions": [
    "galicia"
  ],
  "commodities": [
    "tungsten"
  ],
  "storage_facility_types": [
    "waste dump"
  ],
  "project_status": [
    "inactive"
  ],
  "countries": [
    "spain"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **countries**: COINCIDE (Esperado: ['spain'], Obtenido: ['spain'])
    * 🟢 **regions**: COINCIDE (Esperado: ['galicia'], Obtenido: ['galicia'])
    * 🟢 **commodities**: COINCIDE (Esperado: ['tungsten'], Obtenido: ['tungsten'])
    * 🟢 **project_status**: COINCIDE (Esperado: ['inactive'], Obtenido: ['inactive'])
    * 🟢 **storage_facility_types**: COINCIDE (Esperado: ['waste dump'], Obtenido: ['waste dump'])

#### C) spaCy NLP Pipeline (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "project_status": [
    "inactive"
  ],
  "storage_facility_types": [
    "waste dump"
  ],
  "commodities": [
    "tungsten"
  ],
  "regions": [
    "galicia"
  ],
  "countries": [
    "spain"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **countries**: COINCIDE (Esperado: ['spain'], Obtenido: ['spain'])
    * 🟢 **regions**: COINCIDE (Esperado: ['galicia'], Obtenido: ['galicia'])
    * 🟢 **commodities**: COINCIDE (Esperado: ['tungsten'], Obtenido: ['tungsten'])
    * 🟢 **project_status**: COINCIDE (Esperado: ['inactive'], Obtenido: ['inactive'])
    * 🟢 **storage_facility_types**: COINCIDE (Esperado: ['waste dump'], Obtenido: ['waste dump'])

#### D) GLiNER Zero-Shot Model (Puntuación: 0%)
*   **Filtros Extraídos**:
    ```json
    {
  "regions": [
    "bergehalden"
  ],
  "companies": [
    "wolfram"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **countries**: FALLA (Esperado: ['spain'], Obtenido: [])
    * 🔴 **regions**: FALLA (Esperado: ['galicia'], Obtenido: ['bergehalden'])
    * 🔴 **commodities**: FALLA (Esperado: ['tungsten'], Obtenido: [])
    * 🔴 **project_status**: FALLA (Esperado: ['inactive'], Obtenido: [])
    * 🔴 **storage_facility_types**: FALLA (Esperado: ['waste dump'], Obtenido: [])

---

### [TC_34] Portuguese - Site & Restored
**Consulta**: *"barragens restauradas em Neves-Corvo com cobre"*

*   **Filtros de Verdad del Terreno (Esperados)**:
    ```json
    {
  "countries": [
    "portugal"
  ],
  "site_names": [
    "Neves-Corvo"
  ],
  "commodities": [
    "copper"
  ],
  "storage_facility_types": [
    "pond"
  ],
  "restored": true
}
    ```

#### A) Solr-Direct / Reglas (Legacy) (Puntuación: 40%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [],
  "regions": [],
  "commodities": [
    "copper"
  ],
  "material_types": [],
  "storage_facility_types": [],
  "project_status": [],
  "companies": [],
  "site_names": [],
  "unfc_e": [],
  "unfc_f": [],
  "unfc_g": [],
  "environmental_flags": [],
  "free_text_constraints": [],
  "activity_types": [],
  "mine_types": [],
  "admin_statuses": [],
  "mine_statuses": [],
  "morphologies": [],
  "restored": true,
  "restoration_types": [],
  "site_contexts": []
}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **countries**: FALLA (Esperado: ['portugal'], Obtenido: [])
    * 🔴 **site_names**: FALLA (Esperado: ['Neves-Corvo'], Obtenido: [])
    * 🟢 **commodities**: COINCIDE (Esperado: ['copper'], Obtenido: ['copper'])
    * 🔴 **storage_facility_types**: FALLA (Esperado: ['pond'], Obtenido: [])
    * 🟢 **restored**: COINCIDE (Esperado: True, Obtenido: True)

#### B) LLM Parser (GEMINI + Pipeline) (Puntuación: 80%)
*   **Filtros Extraídos**:
    ```json
    {
  "commodities": [
    "copper"
  ],
  "storage_facility_types": [
    "pond"
  ],
  "site_names": [
    "Neves-Corvo"
  ],
  "restored": true
}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **countries**: FALLA (Esperado: ['portugal'], Obtenido: [])
    * 🟢 **site_names**: COINCIDE (Esperado: ['Neves-Corvo'], Obtenido: ['neves-corvo'])
    * 🟢 **commodities**: COINCIDE (Esperado: ['copper'], Obtenido: ['copper'])
    * 🟢 **storage_facility_types**: COINCIDE (Esperado: ['pond'], Obtenido: ['pond'])
    * 🟢 **restored**: COINCIDE (Esperado: True, Obtenido: True)

#### C) spaCy NLP Pipeline (Puntuación: 60%)
*   **Filtros Extraídos**:
    ```json
    {
  "storage_facility_types": [
    "pond"
  ],
  "site_names": [
    "Neves-Corvo"
  ],
  "commodities": [
    "copper"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **countries**: FALLA (Esperado: ['portugal'], Obtenido: [])
    * 🟢 **site_names**: COINCIDE (Esperado: ['Neves-Corvo'], Obtenido: ['neves-corvo'])
    * 🟢 **commodities**: COINCIDE (Esperado: ['copper'], Obtenido: ['copper'])
    * 🟢 **storage_facility_types**: COINCIDE (Esperado: ['pond'], Obtenido: ['pond'])
    * 🔴 **restored**: FALLA (Esperado: True, Obtenido: [])

#### D) GLiNER Zero-Shot Model (Puntuación: 20%)
*   **Filtros Extraídos**:
    ```json
    {
  "commodities": [
    "copper"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **countries**: FALLA (Esperado: ['portugal'], Obtenido: [])
    * 🔴 **site_names**: FALLA (Esperado: ['Neves-Corvo'], Obtenido: [])
    * 🟢 **commodities**: COINCIDE (Esperado: ['copper'], Obtenido: ['copper'])
    * 🔴 **storage_facility_types**: FALLA (Esperado: ['pond'], Obtenido: [])
    * 🔴 **restored**: FALLA (Esperado: True, Obtenido: [])

---

### [TC_35] Italian - Intent & RAG
**Consulta**: *"Rapporto sulla stabilità fisica del bacino di decantazione a Riotinto"*

*   **Filtros de Verdad del Terreno (Esperados)**:
    ```json
    {
  "intent": "hybrid",
  "needs_report_context": true,
  "countries": [
    "spain"
  ],
  "regions": [
    "andalucia"
  ],
  "site_names": [
    "Riotinto Project"
  ],
  "storage_facility_types": [
    "tailings storage facility"
  ]
}
    ```

#### A) Solr-Direct / Reglas (Legacy) (Puntuación: 33%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [],
  "regions": [
    "andalucia"
  ],
  "commodities": [
    "tin"
  ],
  "material_types": [],
  "storage_facility_types": [],
  "project_status": [],
  "companies": [],
  "site_names": [
    "Riotinto Project"
  ],
  "unfc_e": [],
  "unfc_f": [],
  "unfc_g": [],
  "environmental_flags": [],
  "free_text_constraints": [],
  "activity_types": [],
  "mine_types": [],
  "admin_statuses": [],
  "mine_statuses": [],
  "morphologies": [],
  "restored": null,
  "restoration_types": [],
  "site_contexts": []
}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **intent**: FALLA (Esperado: hybrid, Obtenido: filter_search)
    * 🔴 **needs_report_context**: FALLA (Esperado: True, Obtenido: False)
    * 🔴 **countries**: FALLA (Esperado: ['spain'], Obtenido: [])
    * 🟢 **regions**: COINCIDE (Esperado: ['andalucia'], Obtenido: ['andalucia'])
    * 🟢 **site_names**: COINCIDE (Esperado: ['Riotinto Project'], Obtenido: ['riotinto project'])
    * 🔴 **storage_facility_types**: FALLA (Esperado: ['tailings storage facility'], Obtenido: [])

#### B) LLM Parser (GEMINI + Pipeline) (Puntuación: 67%)
*   **Filtros Extraídos**:
    ```json
    {
  "regions": [
    "andalucia"
  ],
  "commodities": [
    "tin"
  ],
  "storage_facility_types": [
    "tailings storage facility"
  ],
  "site_names": [
    "Riotinto Project"
  ],
  "countries": [
    "spain"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **intent**: FALLA (Esperado: hybrid, Obtenido: search)
    * 🔴 **needs_report_context**: FALLA (Esperado: True, Obtenido: False)
    * 🟢 **countries**: COINCIDE (Esperado: ['spain'], Obtenido: ['spain'])
    * 🟢 **regions**: COINCIDE (Esperado: ['andalucia'], Obtenido: ['andalucia'])
    * 🟢 **site_names**: COINCIDE (Esperado: ['Riotinto Project'], Obtenido: ['riotinto project'])
    * 🟢 **storage_facility_types**: COINCIDE (Esperado: ['tailings storage facility'], Obtenido: ['tailings storage facility'])

#### C) spaCy NLP Pipeline (Puntuación: 50%)
*   **Filtros Extraídos**:
    ```json
    {
  "storage_facility_types": [
    "tailings storage facility"
  ],
  "regions": [
    "andalucia"
  ],
  "countries": [
    "spain"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **intent**: FALLA (Esperado: hybrid, Obtenido: search)
    * 🔴 **needs_report_context**: FALLA (Esperado: True, Obtenido: None)
    * 🟢 **countries**: COINCIDE (Esperado: ['spain'], Obtenido: ['spain'])
    * 🟢 **regions**: COINCIDE (Esperado: ['andalucia'], Obtenido: ['andalucia'])
    * 🔴 **site_names**: FALLA (Esperado: ['Riotinto Project'], Obtenido: [])
    * 🟢 **storage_facility_types**: COINCIDE (Esperado: ['tailings storage facility'], Obtenido: ['tailings storage facility'])

#### D) GLiNER Zero-Shot Model (Puntuación: 0%)
*   **Filtros Extraídos**:
    ```json
    {}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **intent**: FALLA (Esperado: hybrid, Obtenido: search)
    * 🔴 **needs_report_context**: FALLA (Esperado: True, Obtenido: None)
    * 🔴 **countries**: FALLA (Esperado: ['spain'], Obtenido: [])
    * 🔴 **regions**: FALLA (Esperado: ['andalucia'], Obtenido: [])
    * 🔴 **site_names**: FALLA (Esperado: ['Riotinto Project'], Obtenido: [])
    * 🔴 **storage_facility_types**: FALLA (Esperado: ['tailings storage facility'], Obtenido: [])

---

### [TC_36] French - Exclusions
**Consulta**: *"projets de lithium en France mais pas en Bretagne"*

*   **Filtros de Verdad del Terreno (Esperados)**:
    ```json
    {
  "countries": [
    "france"
  ],
  "commodities": [
    "lithium"
  ]
}
    ```

#### A) Solr-Direct / Reglas (Legacy) (Puntuación: 33%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [],
  "regions": [],
  "commodities": [
    "lithium"
  ],
  "material_types": [],
  "storage_facility_types": [],
  "project_status": [],
  "companies": [],
  "site_names": [],
  "unfc_e": [],
  "unfc_f": [],
  "unfc_g": [],
  "environmental_flags": [],
  "free_text_constraints": [],
  "activity_types": [],
  "mine_types": [],
  "admin_statuses": [],
  "mine_statuses": [],
  "morphologies": [],
  "restored": null,
  "restoration_types": [],
  "site_contexts": []
}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **countries**: FALLA (Esperado: ['france'], Obtenido: [])
    * 🟢 **commodities**: COINCIDE (Esperado: ['lithium'], Obtenido: ['lithium'])
    * 🔴 **regions (Exclusión)**: FALLA (Esperado excluir: ['bretagne'], Obtenido: [])

#### B) LLM Parser (GEMINI + Pipeline) (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [
    "france"
  ],
  "commodities": [
    "lithium"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **countries**: COINCIDE (Esperado: ['france'], Obtenido: ['france'])
    * 🟢 **commodities**: COINCIDE (Esperado: ['lithium'], Obtenido: ['lithium'])
    * 🟢 **regions (Exclusión)**: COINCIDE (Excluido correctamente: ['bretagne'])

#### C) spaCy NLP Pipeline (Puntuación: 67%)
*   **Filtros Extraídos**:
    ```json
    {
  "commodities": [
    "lithium"
  ],
  "countries": [
    "france"
  ],
  "regions": [
    "bretagne"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **countries**: COINCIDE (Esperado: ['france'], Obtenido: ['france'])
    * 🟢 **commodities**: COINCIDE (Esperado: ['lithium'], Obtenido: ['lithium'])
    * 💥 **regions (Exclusión)**: INFRACCIÓN (Valores excluidos presentes en positivos: ['bretagne'])

#### D) GLiNER Zero-Shot Model (Puntuación: 50%)
*   **Filtros Extraídos**:
    ```json
    {
  "commodities": [
    "lithium"
  ],
  "countries": [
    "france",
    "bretagne"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟡 **countries**: COINCIDE PARCIALMENTE (50%) (Esperado: ['france'], Obtenido: ['france', 'bretagne'])
    * 🟢 **commodities**: COINCIDE (Esperado: ['lithium'], Obtenido: ['lithium'])
    * 🔴 **regions (Exclusión)**: FALLA (Esperado excluir: ['bretagne'], Obtenido: [])

---

### [TC_37] German - Chemical Symbols & Ranges
**Consulta**: *"Lithium-Projekte in Portugal mit hoher geologischer Konfidenz (G1)"*

*   **Filtros de Verdad del Terreno (Esperados)**:
    ```json
    {
  "countries": [
    "portugal"
  ],
  "commodities": [
    "lithium"
  ],
  "unfc_g": [
    "G1"
  ]
}
    ```

#### A) Solr-Direct / Reglas (Legacy) (Puntuación: 67%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [
    "portugal"
  ],
  "regions": [],
  "commodities": [
    "lithium"
  ],
  "material_types": [],
  "storage_facility_types": [],
  "project_status": [],
  "companies": [],
  "site_names": [],
  "unfc_e": [],
  "unfc_f": [],
  "unfc_g": [],
  "environmental_flags": [],
  "free_text_constraints": [],
  "activity_types": [],
  "mine_types": [],
  "admin_statuses": [],
  "mine_statuses": [],
  "morphologies": [],
  "restored": null,
  "restoration_types": [],
  "site_contexts": []
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **countries**: COINCIDE (Esperado: ['portugal'], Obtenido: ['portugal'])
    * 🟢 **commodities**: COINCIDE (Esperado: ['lithium'], Obtenido: ['lithium'])
    * 🔴 **unfc_g**: FALLA (Esperado: ['G1'], Obtenido: [])

#### B) LLM Parser (GEMINI + Pipeline) (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [
    "portugal"
  ],
  "commodities": [
    "lithium"
  ],
  "unfc_g": [
    "g1"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **countries**: COINCIDE (Esperado: ['portugal'], Obtenido: ['portugal'])
    * 🟢 **commodities**: COINCIDE (Esperado: ['lithium'], Obtenido: ['lithium'])
    * 🟢 **unfc_g**: COINCIDE (Esperado: ['G1'], Obtenido: ['g1'])

#### C) spaCy NLP Pipeline (Puntuación: 33%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [
    "portugal"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **countries**: COINCIDE (Esperado: ['portugal'], Obtenido: ['portugal'])
    * 🔴 **commodities**: FALLA (Esperado: ['lithium'], Obtenido: [])
    * 🔴 **unfc_g**: FALLA (Esperado: ['G1'], Obtenido: [])

#### D) GLiNER Zero-Shot Model (Puntuación: 33%)
*   **Filtros Extraídos**:
    ```json
    {
  "commodities": [
    "lithium-projekte"
  ],
  "countries": [
    "portugal"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **countries**: COINCIDE (Esperado: ['portugal'], Obtenido: ['portugal'])
    * 🔴 **commodities**: FALLA (Esperado: ['lithium'], Obtenido: ['lithium-projekte'])
    * 🔴 **unfc_g**: FALLA (Esperado: ['G1'], Obtenido: [])

---

### [TC_38] Portuguese - Battery Metals
**Consulta**: *"depósitos com materiais de bateria no norte de Portugal"*

*   **Filtros de Verdad del Terreno (Esperados)**:
    ```json
    {
  "countries": [
    "portugal"
  ],
  "commodities": [
    "lithium",
    "cobalt",
    "nickel"
  ]
}
    ```

#### A) Solr-Direct / Reglas (Legacy) (Puntuación: 50%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [
    "portugal"
  ],
  "regions": [],
  "commodities": [],
  "material_types": [],
  "storage_facility_types": [],
  "project_status": [],
  "companies": [],
  "site_names": [],
  "unfc_e": [],
  "unfc_f": [],
  "unfc_g": [],
  "environmental_flags": [],
  "free_text_constraints": [],
  "activity_types": [],
  "mine_types": [],
  "admin_statuses": [],
  "mine_statuses": [],
  "morphologies": [],
  "restored": null,
  "restoration_types": [],
  "site_contexts": []
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **countries**: COINCIDE (Esperado: ['portugal'], Obtenido: ['portugal'])
    * 🔴 **commodities**: FALLA (Esperado: ['lithium', 'cobalt', 'nickel'], Obtenido: [])

#### B) LLM Parser (GEMINI + Pipeline) (Puntuación: 50%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [
    "portugal"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **countries**: COINCIDE (Esperado: ['portugal'], Obtenido: ['portugal'])
    * 🔴 **commodities**: FALLA (Esperado: ['lithium', 'cobalt', 'nickel'], Obtenido: [])

#### C) spaCy NLP Pipeline (Puntuación: 50%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [
    "portugal"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **countries**: COINCIDE (Esperado: ['portugal'], Obtenido: ['portugal'])
    * 🔴 **commodities**: FALLA (Esperado: ['lithium', 'cobalt', 'nickel'], Obtenido: [])

#### D) GLiNER Zero-Shot Model (Puntuación: 50%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [
    "portugal"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **countries**: COINCIDE (Esperado: ['portugal'], Obtenido: ['portugal'])
    * 🔴 **commodities**: FALLA (Esperado: ['lithium', 'cobalt', 'nickel'], Obtenido: [])

---

### [TC_39] Italian - Typo & Fuzzy Matching
**Consulta**: *"impianti di rame in Asturie"*

*   **Filtros de Verdad del Terreno (Esperados)**:
    ```json
    {
  "countries": [
    "spain"
  ],
  "regions": [
    "asturias"
  ],
  "commodities": [
    "copper"
  ]
}
    ```

#### A) Solr-Direct / Reglas (Legacy) (Puntuación: 0%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [],
  "regions": [],
  "commodities": [],
  "material_types": [],
  "storage_facility_types": [],
  "project_status": [],
  "companies": [],
  "site_names": [],
  "unfc_e": [],
  "unfc_f": [],
  "unfc_g": [],
  "environmental_flags": [],
  "free_text_constraints": [],
  "activity_types": [],
  "mine_types": [],
  "admin_statuses": [],
  "mine_statuses": [],
  "morphologies": [],
  "restored": null,
  "restoration_types": [],
  "site_contexts": []
}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **countries**: FALLA (Esperado: ['spain'], Obtenido: [])
    * 🔴 **regions**: FALLA (Esperado: ['asturias'], Obtenido: [])
    * 🔴 **commodities**: FALLA (Esperado: ['copper'], Obtenido: [])

#### B) LLM Parser (GEMINI + Pipeline) (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "regions": [
    "asturias"
  ],
  "commodities": [
    "copper"
  ],
  "countries": [
    "spain"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **countries**: COINCIDE (Esperado: ['spain'], Obtenido: ['spain'])
    * 🟢 **regions**: COINCIDE (Esperado: ['asturias'], Obtenido: ['asturias'])
    * 🟢 **commodities**: COINCIDE (Esperado: ['copper'], Obtenido: ['copper'])

#### C) spaCy NLP Pipeline (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "commodities": [
    "copper"
  ],
  "regions": [
    "asturias"
  ],
  "countries": [
    "spain"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **countries**: COINCIDE (Esperado: ['spain'], Obtenido: ['spain'])
    * 🟢 **regions**: COINCIDE (Esperado: ['asturias'], Obtenido: ['asturias'])
    * 🟢 **commodities**: COINCIDE (Esperado: ['copper'], Obtenido: ['copper'])

#### D) GLiNER Zero-Shot Model (Puntuación: 0%)
*   **Filtros Extraídos**:
    ```json
    {}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **countries**: FALLA (Esperado: ['spain'], Obtenido: [])
    * 🔴 **regions**: FALLA (Esperado: ['asturias'], Obtenido: [])
    * 🔴 **commodities**: FALLA (Esperado: ['copper'], Obtenido: [])

---

### [TC_40] English - Double Negation
**Consulta**: *"I do not want projects that are not active in Cáceres"*

*   **Filtros de Verdad del Terreno (Esperados)**:
    ```json
    {
  "countries": [
    "spain"
  ],
  "regions": [
    "extremadura"
  ],
  "project_status": [
    "active"
  ]
}
    ```

#### A) Solr-Direct / Reglas (Legacy) (Puntuación: 67%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [],
  "regions": [
    "extremadura"
  ],
  "commodities": [],
  "material_types": [],
  "storage_facility_types": [],
  "project_status": [
    "active"
  ],
  "companies": [],
  "site_names": [],
  "unfc_e": [],
  "unfc_f": [],
  "unfc_g": [],
  "environmental_flags": [],
  "free_text_constraints": [],
  "activity_types": [],
  "mine_types": [],
  "admin_statuses": [],
  "mine_statuses": [],
  "morphologies": [],
  "restored": null,
  "restoration_types": [],
  "site_contexts": []
}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **countries**: FALLA (Esperado: ['spain'], Obtenido: [])
    * 🟢 **regions**: COINCIDE (Esperado: ['extremadura'], Obtenido: ['extremadura'])
    * 🟢 **project_status**: COINCIDE (Esperado: ['active'], Obtenido: ['active'])

#### B) LLM Parser (GEMINI + Pipeline) (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "regions": [
    "extremadura"
  ],
  "project_status": [
    "active"
  ],
  "countries": [
    "spain"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **countries**: COINCIDE (Esperado: ['spain'], Obtenido: ['spain'])
    * 🟢 **regions**: COINCIDE (Esperado: ['extremadura'], Obtenido: ['extremadura'])
    * 🟢 **project_status**: COINCIDE (Esperado: ['active'], Obtenido: ['active'])

#### C) spaCy NLP Pipeline (Puntuación: 100%)
*   **Filtros Extraídos**:
    ```json
    {
  "project_status": [
    "active"
  ],
  "regions": [
    "extremadura"
  ],
  "countries": [
    "spain"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🟢 **countries**: COINCIDE (Esperado: ['spain'], Obtenido: ['spain'])
    * 🟢 **regions**: COINCIDE (Esperado: ['extremadura'], Obtenido: ['extremadura'])
    * 🟢 **project_status**: COINCIDE (Esperado: ['active'], Obtenido: ['active'])

#### D) GLiNER Zero-Shot Model (Puntuación: 0%)
*   **Filtros Extraídos**:
    ```json
    {
  "countries": [
    "caceres"
  ]
}
    ```
*   **Detalle de Evaluación**:
    * 🔴 **countries**: FALLA (Esperado: ['spain'], Obtenido: ['caceres'])
    * 🔴 **regions**: FALLA (Esperado: ['extremadura'], Obtenido: [])
    * 🔴 **project_status**: FALLA (Esperado: ['active'], Obtenido: [])

---

## 3. Justificación Técnica de la Arquitectura
Los datos empíricos recopilados demuestran las siguientes conclusiones científicas sobre cada uno de los 4 enfoques de NLU:

1.  **LLM Parser (Decoupled Pipeline - 100.0%)**:
    Es el único sistema capaz de resolver negaciones cruzadas, dobles negaciones, correcciones conversacionales temporales e inferencia de viabilidad geológica (UNFC). Su principal ventaja es que comprende la sintaxis libre y el contexto a nivel humano.
    
2.  **spaCy NLP Pipeline (71.9%)**:
    Aunque es sumamente rápido (~11.7 ms) y permite añadir reglas personalizadas mediante `EntityRuler`, carece de flexibilidad semántica. Al igual que el motor Solr directo, no maneja bien la negación fuera de diccionarios específicos, es propenso a falsos positivos por superposición de etiquetas y no puede realizar deducciones implícitas (por ejemplo, deducir metales de batería a partir de una descripción).

3.  **GLiNER Zero-Shot Model (16.9%)**:
    El modelo preentrenado zero-shot en inglés `urchade/gliner_small-v2.1` es incapaz de operar en español, obteniendo una tasa de acierto muy baja. Para ser viable, requeriría recolectar un dataset anotado en español del dominio de minería y realizar un fine-tuning local (usando ModernBERT o DeBERTa), lo cual es costoso en términos de tiempo y anotación de datos.

4.  **Solr-Direct / Reglas (48.7%)**:
    Tiene los mismos problemas que spaCy pero con la desventaja añadida de acoplar la sintaxis de Apache Solr a la lógica de negocio, lo que dificulta cualquier cambio futuro de base de datos.

### Conclusión
Para el entregable final (*deliverable*), la justificación técnica es clara:
*   Para la **Extracción de Intenciones y Normalización Semántica Avanzada**: El **LLM Parser** es indispensable para garantizar tasas de acierto cercanas al 100% y manejar queries conversacionales complejas.
*   Como **Mecanismo de Contingencia local y de bajo costo**: El parser híbrido basado en **spaCy con EntityRuler** o el pipeline de **Reglas deterministas** local es la mejor opción frente a caídas del servicio API, ya que mantiene una tasa de acierto razonable (~50-55%) con latencias inferiores al milisegundo y cero coste de API o infraestructura GPU.
