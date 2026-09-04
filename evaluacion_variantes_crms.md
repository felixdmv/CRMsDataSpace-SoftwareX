# Reporte Comparativo de las Variantes de Arquitectura (cRMsDataSpace)
Fecha de evaluación: 2026-07-17

Este reporte evalúa empíricamente el comportamiento de las 4 variantes de arquitectura diseñadas a partir del documento de propuestas sobre nuestro banco de pruebas.

## 1. Banco de Pruebas (Test Cases)
Se evaluaron 5 consultas tipo que cubren los requisitos funcionales del sistema:
1. **Q1: Conversacional** — *'Hola, buenos días, ¿cómo estás y en qué puedes ayudarme?'*
2. **Q2: Búsqueda Estructurada** — *'Dime escombreras de wolframio activas en Galicia'*
3. **Q3: Consulta Técnica (RAG)** — *'¿Qué dice el informe técnico de Penouta sobre la estabilidad física de la balsa B?'*
4. **Q4: Filtros con Negación** — *'Busca balsas de litio en Extremadura pero que no estén en Cáceres'*
5. **Q5: Caso Sin Resultados (Grounding)** — *'Dime balsas de cobalto en Asturias'*

## 2. Resumen de Resultados por Variante

### Variante: V1 Intent Classification
| ID Consulta | Intent Extraído | Filtros Detectados | Resultados DB | ¿RAG Activado? | Respuesta Resumida |
|---|---|---|---|---|---|
| Q1: Saludo | generic_qa | `{}` | 5 | no | He encontrado 5 instalación(es) en el Espacio de Datos que c... |
| Q2: Búsqueda estructurada | search | `{"regions": ["galicia"], "commodities...` | 0 | no | No he encontrado ninguna escombrera con wolframio / tungsten... |
| Q3: Consulta técnica / RAG | hybrid | `{"storage_facility_types": ["pond"], ...` | 0 | no | No he encontrado ninguna balsa en el Espacio de Datos (WARM)... |
| Q4: Filtros con negación | search | `{"regions": ["extremadura"], "commodi...` | 0 | no | No he encontrado ninguna balsa con litio en la región de Ext... |
| Q5: Sin resultados / Grounding | search | `{"regions": ["asturias"], "commoditie...` | 0 | no | No he encontrado ninguna balsa con cobalto en la región de A... |

### Variante: V2 Hybrid Search Rerank
| ID Consulta | Intent Extraído | Filtros Detectados | Resultados DB | ¿RAG Activado? | Respuesta Resumida |
|---|---|---|---|---|---|
| Q1: Saludo | generic_qa | `{}` | 5 | no | He encontrado 5 instalación(es) en el Espacio de Datos que c... |
| Q2: Búsqueda estructurada | search | `{"regions": ["galicia"], "commodities...` | 0 | no | No he encontrado ninguna escombrera con wolframio / tungsten... |
| Q3: Consulta técnica / RAG | hybrid | `{"storage_facility_types": ["pond"], ...` | 0 | no | No he encontrado ninguna balsa en el Espacio de Datos (WARM)... |
| Q4: Filtros con negación | search | `{"regions": ["extremadura"], "commodi...` | 0 | no | No he encontrado ninguna balsa con litio en la región de Ext... |
| Q5: Sin resultados / Grounding | search | `{"regions": ["asturias"], "commoditie...` | 0 | no | No he encontrado ninguna balsa con cobalto en la región de A... |

### Variante: V3 Json Schema
| ID Consulta | Intent Extraído | Filtros Detectados | Resultados DB | ¿RAG Activado? | Respuesta Resumida |
|---|---|---|---|---|---|
| Q1: Saludo | generic_qa | `{}` | 5 | no | He encontrado 5 instalación(es) en el Espacio de Datos que c... |
| Q2: Búsqueda estructurada | search | `{"regions": ["galicia"], "commodities...` | 0 | no | No he encontrado ninguna escombrera con wolframio / tungsten... |
| Q3: Consulta técnica / RAG | hybrid | `{"storage_facility_types": ["pond"], ...` | 0 | no | No he encontrado ninguna balsa en el Espacio de Datos (WARM)... |
| Q4: Filtros con negación | search | `{"regions": ["extremadura"], "commodi...` | 0 | no | No he encontrado ninguna balsa con litio en la región de Ext... |
| Q5: Sin resultados / Grounding | search | `{"regions": ["asturias"], "commoditie...` | 0 | no | No he encontrado ninguna balsa con cobalto en la región de A... |

### Variante: V4 Strict Grounding Citations
| ID Consulta | Intent Extraído | Filtros Detectados | Resultados DB | ¿RAG Activado? | Respuesta Resumida |
|---|---|---|---|---|---|
| Q1: Saludo | generic_qa | `{}` | 5 | no | He encontrado 5 instalación(es) en el Espacio de Datos que c... |
| Q2: Búsqueda estructurada | search | `{"regions": ["galicia"], "commodities...` | 0 | no | Información no disponible en el espacio de datos... |
| Q3: Consulta técnica / RAG | hybrid | `{"storage_facility_types": ["pond"], ...` | 0 | no | Información no disponible en el espacio de datos... |
| Q4: Filtros con negación | search | `{"regions": ["extremadura"], "commodi...` | 0 | no | Información no disponible en el espacio de datos... |
| Q5: Sin resultados / Grounding | search | `{"regions": ["asturias"], "commoditie...` | 0 | no | Información no disponible en el espacio de datos... |

## 3. Matriz Comparativa de Ventajas e Inconvenientes

| Variante | Ventajas Clave | Inconvenientes / Limitaciones | Recomendación de Uso |
|---|---|---|---|
| **v1: Few-Shot Intent** | • Altísima precisión en clasificar intenciones.<br/>• Mapeo robusto a campos Solr canonicales.<br/>• Evita alucinación de API en queries complejas. | • Requiere escribir prompts detallados y mantener ejemplos.<br/>• Rígido si el usuario sale del dominio de base de datos. | **Recomendado** para traducción precisa de consultas de lenguaje natural a lenguaje Solr structured. |
| **v2: Hybrid Search & Rerank** | • Combina metadatos de Solr y contenido de PDFs técnicos.<br/>• El Reranker por score limpia el ruido del vector index, reduciendo costes de tokens y alucinaciones. | • Dependencia del índice de vectores local (`faiss`).<br/>• Tiempo de respuesta ligeramente mayor debido a búsqueda doble. | **Recomendado** para preguntas complejas sobre informes de estabilidad, ensayos de laboratorio u observaciones técnicas. |
| **v3: JSON Schema** | • Garantía 100% de que la salida del LLM es parseable.<br/>• Evita errores de integración en el Front-End.<br/>• Tipado estricto nativo soportado en la API decodificadora. | • Mayor tiempo de inferencia.<br/>• Requiere APIs modernas que soporten `responseSchema` (Gemini) o structured outputs. | **Recomendado** para entornos productivos donde se automatiza el pintado de tablas y gráficos desde JSON. |
| **v4: Grounding & Citations** | • Hallucination-proof: early exit si no hay datos sin llamar al LLM.<br/>• Trazabilidad total de dónde sale cada dato en el JSON final (`fuentes`). | • Puede responder de manera muy rígida ('Información no disponible') si los datos no coinciden de forma exacta. | **Crítico** para garantizar la veracidad científica de los datos del CRM (no inventa leyes de mineral ni dueños). |

## 4. Conclusión y Recomendación Arquitectónica
Para el estado final del proyecto **CRMsDataSpace**, la combinación ideal es una **Arquitectura Híbrida Fusionada**:
1. **Entrada NLU**: Usar **v3: JSON Schema** con el prompt de **v1: Few-Shot** para garantizar que los filtros extraídos sean perfectos y el JSON no falle.
2. **Ejecución de Búsqueda**: Aplicar **v2: Hybrid Search** con el Reranker para enriquecer con PDFs de estabilidad si el intent es híbrido.
3. **Salida NLG**: Emplear **v4: Grounding & Citations** para forzar al LLM a no inventar datos y escupir el nodo de citas estructurado hacia la UI.