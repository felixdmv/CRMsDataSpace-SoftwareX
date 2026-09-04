# Integracion WARM - LLM

## Resumen ejecutivo

El Excel `BBDD_propuesta_LLM_WARM.xlsx` es exactamente el tipo de pieza que necesitabamos para pasar de una demo con datos inventados a una demo conectada con la logica del espacio de datos.

Contiene dos capas utiles:

- `tabla`: registros estructurados de tres escombreras HUNOSA: San Nicolas / Arroyo de la Nicolasa, Pumardongo y Figaredo.
- `metadatos`: traduccion de campos del inventario IGME al modelo WARM.

Para LLMs, esto sirve como primera base estructurada para busqueda por filtros y como diccionario semantico para explicar al modelo que significa cada campo.

## Que podemos usar ya

### 1. Busqueda estructurada

La hoja `tabla` ya permite responder consultas del tipo:

- "dime escombreras de carbon en Asturias"
- "escombreras de HUNOSA"
- "sitios en Mieres"
- "San Nicolas"
- "escombreras sin restaurar"
- "escombreras con surgencias de agua"

Campos directamente utiles para filtros:

- `id_site`
- `country_code`
- `nuts3_code`
- `nuts3_label`
- `province`
- `municipality`
- `locality`
- `local_name`
- `utm_x`
- `utm_y`
- `alt`
- `exp_subs_1/2/3`
- `debris_lit_1/2/3`
- `act_type`
- `expl_type`
- `company`
- `admin_status`
- `mine_status`
- `dep_type`
- `morphology`
- `area`
- `restored`
- `rest_type`
- `site_context`
- `observations`
- `source`

### 2. Mapeo semantico IGME -> WARM

La hoja `metadatos` es muy util para orientar al LLM y para el ETL:

- Permite explicar que `id_site` corresponde a `id` en WARM.
- Permite mapear localizacion a `IndustrialWaste/Location`.
- Permite mapear sustancias a `IndustrialActivity/Product` y `IndustrialActivity/Commodity`.
- Permite mapear litologia a `IndustrialWaste/EarthMaterialConstituent`.
- Permite mapear estado/restauracion a `IndustrialWaste/Environmental`.
- Permite mapear observaciones y fuente.

No todos los campos tienen traduccion directa a WARM. Eso es normal y hay que conservarlo como metadato de trazabilidad, no forzar una equivalencia falsa.

### 3. RAG documental

El PDF `D2.1 Closed extractive coal waste facilities information.pdf` aporta contexto descriptivo que no esta en la tabla.

Para San Nicolas aporta:

- identificacion del activo
- contexto historico HUNOSA
- materiales presentes: shales/slates, sandstones, conglomerates, limestones, coal
- coordenadas WGS84 y UTM
- area aproximada de 5.18 ha
- dimensiones aproximadas de 590 m x 110 m
- volumen aproximado de 700,000 m3
- propiedades fisicas de esteriles
- composicion quimica media de coal waste: SiO2, Al2O3, Fe2O3, K2O, MgO, TiO2, CaO, Stotal
- informacion de siete sondeos en San Nicolas

Esto debe indexarse para preguntas genericas o tecnicas:

- "que composicion tiene San Nicolas?"
- "cuantos sondeos hay?"
- "que volumen aproximado tiene la escombrera?"
- "que materiales aparecen en el residuo?"

### 4. WARM como modelo canonico

La presentacion `2026.04.16 - SATEC - 2nd partner meeting CRMsDataSpace.pdf` confirma que WARM es el modelo canonico esperado.

Puntos relevantes:

- WARM significa `Waste As a Resource Model`.
- El centro del modelo es la instalacion de almacenamiento industrial o multi-source site.
- WARM incluye descripcion, localizacion, partes de la instalacion, trabajo de campo, sondeos, muestreo, observaciones, contexto geologico y actividad industrial.
- La arquitectura propuesta incluye ingestion, QA, QC, transformacion, enriquecimiento, modelo canonico WARM, capa curated/trusted, APIs, GIS web portal y conectores.
- Tambien aparece una propuesta de alineacion UNFC con variables socioeconomicas, ambientales, estado de proyecto, evaluacion de recursos y ejecuciones de modelos.

## Como encaja con nuestro LLM

La arquitectura recomendada queda asi:

1. El usuario pregunta en lenguaje natural.
2. El LLM clasifica la intencion:
   - busqueda por filtros
   - pregunta documental
   - caso mixto
3. Si es busqueda, el LLM extrae filtros estructurados.
4. Los filtros consultan registros WARM estructurados.
5. Si es pregunta tecnica, se recuperan fragmentos de PDFs indexados mediante RAG.
6. Si es mixto, primero se filtra el activo y despues se recuperan documentos asociados.

Ejemplo:

Usuario: "dime escombreras de carbon en Asturias"

Salida esperada del extractor:

```json
{
  "countries": ["spain"],
  "regions": ["asturias"],
  "commodities": ["coal"],
  "storage_facility_types": ["waste dump"]
}
```

Consulta estructurada:

- devuelve San Nicolas / Arroyo de la Nicolasa
- devuelve Pumardongo
- devuelve Figaredo

Usuario: "que datos de sondeos hay en San Nicolas?"

Flujo esperado:

- filtro por `site_names = ["San Nicolas"]`
- recuperacion documental del PDF D2.1, paginas 99-101
- respuesta con referencia a los sondeos SN-1, SN-1 BIS, SN-2, SN-3, SN-4, SN-4 BIS y SN-5

## Que falta

El Excel es suficiente para una primera demo, pero no para evaluaciones UNFC completas.

Faltan o son todavia debiles:

- cantidades por sustancia aprovechable
- concentraciones o leyes por elemento critico
- resultados analiticos reales por muestra
- relacion muestra-sondeo-profundidad
- clasificacion UNFC validada
- evidencia E/F/G revisada por expertos
- permisos y regulacion detallada
- informacion economica
- aceptacion social
- restricciones ambientales cuantificadas

Por eso el Excel no sustituye la plantilla de expertos. La complementa.

## Decision practica

Usar tres capas:

- `WARM estructurado`: busqueda, filtros, mapa, tabla de activos.
- `Documentos indexados`: RAG para informes, entregables, normativa y justificaciones.
- `Gold experto`: evaluacion de modelos, UNFC y pares pregunta-respuesta.

## Trabajo hecho en el repositorio

Se ha creado:

- `code/export_warm_sites.py`
- `code/data/warm_sites.json`
- `code/data/warm_field_mapping.json`

Tambien se ha actualizado `code/mock_api.py` para cargar `warm_sites.json` si existe.

Esto permite que el prototipo empiece a consultar registros WARM reales en lugar de usar solo datos mock inventados.

## Siguientes pasos recomendados

1. Indexar `D2.1 Closed extractive coal waste facilities information.pdf` en el RAG.
2. Asociar documentos a `id_site`, especialmente San Nicolas.
3. Ampliar el extractor de filtros para reconocer:
   - HUNOSA
   - San Nicolas / Nicolasa
   - Pumardongo
   - Figaredo
   - coal / hulla / carbon
   - waste dump / escombrera
   - not restored / sin restaurar
4. Pedir a SATEC/consorcio el esquema WARM final o una exportacion JSON/API cuando este disponible.
5. Mantener la plantilla de expertos para UNFC y evaluacion de modelos, porque WARM por si solo no nos da todavia la clasificacion experta.
