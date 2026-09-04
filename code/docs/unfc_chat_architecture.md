# UNFC + Chat Architecture Notes

Fecha de referencia de modelos: 28 de abril de 2026.

## 1. Enfoque recomendado

Para esta fase, tiene sentido **no empezar por fine-tuning**. Primero conviene separar dos capacidades:

1. **Extracción de filtros**
   El modelo recibe un prompt libre como `dime escombreras de niquel en españa` y devuelve JSON estructurado con `country`, `region`, `commodity`, `facility_type`, `UNFC`, etc.

2. **Preguntas genéricas sobre informes**
   El modelo responde apoyándose en RAG sobre informes, normas y futuros datos empresariales.

Esto os permite evaluar con expertos mucho antes de comprometeros con un pipeline de entrenamiento.

## 2. Qué meter en la web

La web de la empresa ya tiene mapa y demo, así que el encaje natural es:

- Un **chat lateral** o panel flotante.
- Un **router** detrás del chat que decida:
  - `filter_search`: convertir prompt a filtros y consultar base estructurada.
  - `generic_qa`: lanzar RAG sobre informes y normativa.
  - `hybrid`: primero filtrar activos, luego responder con contexto RAG.

Flujo recomendado:

1. Usuario escribe en lenguaje natural.
2. Modelo de extracción produce JSON de filtros.
3. Backend consulta la base estructurada de escombreras.
4. Si hace falta explicación o justificación, se recuperan fragmentos relevantes con RAG.
5. El frontend muestra:
   - respuesta natural
   - filtros detectados
   - resultados en mapa/lista
   - fuentes usadas

## 3. Cómo indexar los datos

Sí: **los informes y los futuros documentos de empresas hay que indexarlos**.

Lo recomendable es separar:

- **Base estructurada**
  - una fila por activo/escombrera/depósito
  - campos: país, región, commodity, tipo de instalación, estado del proyecto, categorías UNFC, métricas clave

- **Base documental**
  - PDFs, anexos, tablas, normativa, estudios
  - chunking + embeddings para RAG

## 4. Vector DB: qué montar

Para un primer piloto podéis seguir con FAISS local, pero para una web multiusuario es mejor pensar en:

- `PostgreSQL + pgvector` si queréis una arquitectura simple y mantenible.
- `Qdrant` si queréis separar bien la capa vectorial y filtrar por metadatos.
- `Azure AI Search`, `Vertex AI Search` o equivalentes si la empresa ya trabaja con cloud gestionado.

Recomendación práctica:

- **Structured DB**: PostgreSQL
- **Vector search**: PostgreSQL + pgvector o Qdrant
- **Blob storage**: carpeta o bucket para PDFs

## 5. RAG recomendado

Para este caso no empezaría por GraphRAG salvo que ya tengáis un grafo claro y mantenido. Antes haría:

1. RAG clásico con chunks + metadata.
2. Metadata fuerte por documento:
   - país
   - región
   - commodity
   - empresa
   - tipo de depósito
   - año
   - estándar (UNFC, CRIRSCO, NI 43-101, PERC...)
3. Re-ranking si hace falta.
4. Solo después valorar grafo para relaciones complejas:
   - activo -> empresa
   - activo -> commodity
   - activo -> ejes UNFC
   - activo -> evidencias regulatorias / ambientales

GraphRAG puede tener sentido más adelante para navegar relaciones entre normas, estudios y activos, pero no es el primer cuello de botella.

## 6. Modelos a probar primero

Verificados en documentación oficial el 28 de abril de 2026:

- OpenAI: `gpt-5.5`
  Fuente: https://developers.openai.com/api/docs/models
- Google Gemini: `gemini-2.5-pro`
  Fuente: https://ai.google.dev/gemini-api/docs/models
  Nota: la propia doc indica que Gemini 3 Pro Preview fue apagado el 9 de marzo de 2026 y recomienda migrar.
- Anthropic: `claude-opus-4-7`
  Fuente: https://platform.claude.com/docs/en/about-claude/models/overview
- xAI: `grok-4.20-reasoning`
  Fuente: https://docs.x.ai/overview

Para extracción de filtros, lo importante no es solo el modelo sino:

- prompt consistente
- schema JSON fijo
- normalización posterior
- gold set bien definido

## 7. Qué he dejado en el repo

- `code/create_expert_template.py`
  Genera una plantilla Excel y CSVs para anotación experta.
- `code/templates/unfc_expert_annotation_template.xlsx`
  Plantilla inicial para clasificación UNFC, QA y filtro gold.
- `code/filter_extraction_benchmark.py`
  Script para lanzar queries de filtrado contra OpenAI, Gemini, Claude y Grok.

## 8. Siguiente iteración lógica

Después de esta fase, el siguiente paso natural sería añadir:

1. Un esquema de base estructurada de activos.
2. Un endpoint backend tipo `/chat/query`.
3. Un evaluador para comparar:
   - filtros esperados vs predichos
   - UNFC experto vs UNFC modelo
   - QA experto vs QA modelo
