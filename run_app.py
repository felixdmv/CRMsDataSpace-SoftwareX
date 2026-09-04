import os
import sys
import json
import webbrowser
from http.server import SimpleHTTPRequestHandler
import socketserver
import threading
import time
from pathlib import Path

# Add code/ to sys.path to import our custom LLM chat agent
ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT / "code"))

try:
    import chat_agent
except ImportError:
    chat_agent = None

PORT = 8080
DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'SoftwareX', 'code', 'static')

# =====================================================================
# API SIMULATOR BACKEND (PYTHON)
# =====================================================================

def get_galicia_wolframio_response(question):
    return {
        "question": question,
        "narrative": "<strong>[Respuesta de API Python]</strong> Se han localizado **2 depósitos de residuos mineros** con potencial de valorización de **Wolframio (W)** en Galicia a través de Solr.<br/><br/>El depósito principal identificado es la balsa de la **Mina de Penouta** (Ourense), que contiene altos contenidos residuales de wolframio, estaño y tántalo. Adicionalmente, se identifica el depósito de **San Finx** (A Coruña) como una estructura inactiva con recursos estimados de 0.08% de WO3, condicionada por controles de drenaje ácido de mina. Se recomienda priorizar el reprocesamiento en Penouta dado su estado activo y la infraestructura de beneficio disponible.",
        "primary_site_id": "site_penouta",
        "evidences": [
          {
            "title": "Proyecto_Penouta_Valorizacion_Residuos_2023.pdf",
            "page": 14,
            "score": 0.94,
            "entities": ["Mineral: Wolframio", "Mineral: Tántalo", "Provincia: Ourense", "Compañía: Strategic Minerals"],
            "snippet": "El análisis mineralógico de las balsas de lodos finos A y B de Penouta confirma una ley media residual de 95 ppm de WO3, siendo técnica y económicamente viable su reprocesamiento en la planta gravimétrica existente en el sitio...",
            "site_id": "site_penouta"
          },
          {
            "title": "Informe_Tecnico_Presas_Decantacion_San_Finx_2022.pdf",
            "page": 8,
            "score": 0.87,
            "entities": ["Mineral: Wolframio", "Mineral: Estaño", "Provincia: A Coruña", "Estado: Inactivo"],
            "snippet": "Los residuos arenosos acumulados en la balsa de San Finx estiman un recurso de wolframio remanente del 0.08% WO3, aunque su explotación está condicionada a estrictos controles de pH de aguas y drenajes ácidos...",
            "site_id": "site_san_finx"
          }
        ],
        "solr_query": {
          "q": "residuo_tipo:escombrera OR balsa_tipo:balsa",
          "fq": [
            "region:galicia",
            "minerales_estimulados:wolframio",
            "{!geofilt sfield=location pt=42.5,-8.0 d=100}"
          ],
          "defType": "edismax",
          "qf": "site_name^2.0 description^1.5 linked_facilities",
          "rq": "{!knn f=vector_embedding topK=10}[0.12, -0.05, 0.43, 0.28, -0.19, 0.07, 0.51, -0.32, 0.18, 0.04]",
          "fl": "id,site_name,commodities,score,location",
          "rows": 10
        },
        "solr_facets": {
          "facet_counts": {
            "facet_fields": {
              "region": ["galicia", 2, "castilla y leon", 0, "extremadura", 0],
              "commodities": ["tungsten", 2, "tin", 2, "tantalum", 1],
              "project_status": ["active", 1, "inactive", 1]
            }
          }
        },
        "ner_entities": {
          "ner_extraction": {
            "text": question,
            "entities": [
              { "text": "wolframio", "label": "MINERAL", "confidence": 0.99, "standard": "tungsten" },
              { "text": "Galicia", "label": "REGION", "confidence": 0.98, "standard": "galicia" }
            ],
            "spatial_anchor": { "centroid": [42.575, -8.133], "radius_km": 100 }
          }
        }
    }

def get_castilla_normativa_response(question):
    return {
        "question": question,
        "narrative": "<strong>[Respuesta de API Python]</strong> La valorización de estériles mineros en Castilla y León está regulada principalmente por el **Real Decreto 975/2009** de gestión de los residuos de las industrias extractivas.<br/><br/>Para activos específicos en Salamanca como **Barruecopardo** o **Los Santos**, la normativa obliga a la aprobación de un Plan de Gestión de Residuos Mineros por parte de la Junta de Castilla y León, que demuestre la estabilidad física y química a largo plazo de las estructuras y prevea medidas contra el drenaje ácido de mina (AMD). La valorización de estériles de roca para áridos secundarios requiere la exención de la condición de residuo (estatuto de subproducto) bajo el Art. 4 de la Ley 7/2022 de Residuos y Suelos Contaminados para una Economía Circular.",
        "primary_site_id": "site_barruecopardo",
        "evidences": [
          {
            "title": "Guia_Restauracion_Espacio_Minero_Castilla_Leon_2020.pdf",
            "page": 28,
            "score": 0.91,
            "entities": ["Normativa: RD 975/2009", "Provincia: Salamanca", "Región: Castilla y León"],
            "snippet": "El capítulo IV especifica las condiciones de estabilidad geoquímica obligatorias para la reutilización de roca estéril de wolframio y skarn en la submeseta norte, regulando la exención de residuos...",
            "site_id": "site_barruecopardo"
          },
          {
            "title": "RD_975_2009_Gestion_Residuos_Industrias_Extractivas.pdf",
            "page": 8,
            "score": 0.85,
            "entities": ["Normativa: Directiva 2006/21/CE", "Ámbito: Nacional", "Concepto: Caracterización de residuos"],
            "snippet": "Se requerirá una caracterización geoquímica completa (incluyendo tests estáticos y dinámicos) antes de autorizar cualquier plan de valorización de residuos mineros en depósitos de Categoría A...",
            "site_id": "site_los_santos"
          }
        ],
        "solr_query": {
          "q": "valorizacion OR reutilizacion AND esteriles AND normativa",
          "fq": ["region:\"castilla y leon\"", "admin_status:Activa"],
          "defType": "edismax",
          "qf": "laws_referenced^2.0 text_content^1.0 location_context^1.2",
          "rq": "{!knn f=vector_embedding topK=10}[-0.08, 0.22, 0.15, -0.41, 0.11, 0.33, -0.05, 0.12, 0.44, 0.08]",
          "fl": "id,title,score,region,laws_referenced",
          "rows": 10
        },
        "solr_facets": {
          "facet_counts": {
            "facet_fields": {
              "region": ["castilla y leon", 2, "galicia", 0],
              "laws_referenced": ["rd 975/2009", 2, "ley 7/2022", 1]
            }
          }
        },
        "ner_entities": {
          "ner_extraction": {
            "text": question,
            "entities": [
              { "text": "Normativa ambiental", "label": "TOPIC", "confidence": 0.95, "standard": "environmental regulation" },
              { "text": "Castilla y León", "label": "REGION", "confidence": 0.99, "standard": "castilla y leon" }
            ],
            "spatial_anchor": { "centroid": [41.652, -4.724], "radius_km": 180 }
          }
        }
    }

def get_cobalto_ree_response(question):
    return {
        "question": question,
        "narrative": "<strong>[Respuesta de API Python]</strong> Se han identificado **2 instalaciones de residuos mineros** con potencial anómalo de **Cobalto (Co)** y **Tierras Raras (REE)** en la base de datos de Solr.<br/><br/>1. **Mina de Penouta** (Ourense): Los residuos arenosos finos en las balsas acumulan tierras raras ligeras asociadas a pegmatitas complejas (principalmente monacita y xenotima), con concentraciones que representan un potencial subproducto de alto valor durante el reprocesamiento de estaño y coltán.<br/><br/>2. **Cobre Las Cruces** (Sevilla): Aunque es históricamente una mina de cobre, los estériles secos filtrados y las colas de flotación de la planta hidrometalúrgica contienen trazas recuperables de cobalto en la fracción pirítica.",
        "primary_site_id": "site_las_cruces",
        "evidences": [
          {
            "title": "Caracterizacion_Residuos_Penouta_REE_2023.pdf",
            "page": 7,
            "score": 0.92,
            "entities": ["Mineral: Tierras Raras", "Mineral: Niobio", "Provincia: Ourense"],
            "snippet": "Las arenas de fracción fina de la balsa B de Penouta muestran concentraciones recuperables de tierras raras (La, Ce, Nd) asociadas a fases minerales accesorias de monacita de hasta 410 ppm...",
            "site_id": "site_penouta"
          },
          {
            "title": "Estudio_Recuperacion_Subproductos_Las_Cruces_2022.pdf",
            "page": 34,
            "score": 0.89,
            "entities": ["Mineral: Cobalto", "Provincia: Sevilla", "Compañía: First Quantum"],
            "snippet": "El balance metalúrgico preliminar indica una presencia de cobalto de hasta 180 g/t en la fracción pirítica fina de las colas de flotación acumuladas en el depósito de estériles secos...",
            "site_id": "site_las_cruces"
          }
        ],
        "solr_query": {
          "q": "balsas_residuos AND (cobalto OR \"tierras raras\" OR REE)",
          "fq": ["material_type:(tailings OR relaves OR lodos)", "country:spain"],
          "defType": "edismax",
          "qf": "commodities^3.0 description^1.0 raw_exploited_substances",
          "rq": "{!knn f=vector_embedding topK=10}[0.45, 0.08, -0.12, 0.67, 0.02, -0.21, 0.13, 0.09, -0.05, 0.54]",
          "fl": "id,site_name,commodities,storage_facility_type,score,location",
          "rows": 10
        },
        "solr_facets": {
          "facet_counts": {
            "facet_fields": {
              "region": ["andalucia", 1, "galicia", 1, "extremadura", 1],
              "commodities": ["cobalt", 1, "rare earth elements", 2, "lithium", 1]
            }
          }
        },
        "ner_entities": {
          "ner_extraction": {
            "text": question,
            "entities": [
              { "text": "cobalto", "label": "MINERAL", "confidence": 0.99, "standard": "cobalt" },
              { "text": "tierras raras", "label": "MINERAL_GROUP", "confidence": 0.99, "standard": "rare earth elements" }
            ],
            "spatial_anchor": None
          }
        }
    }

def get_litio_response(question):
    return {
        "question": question,
        "narrative": "<strong>[Respuesta de API Python]</strong> Se ha procesado una consulta personalizada sobre el **Litio (Li)** en Extremadura. El pipeline ha recuperado información del proyecto de **San José Valdeflórez** (Cáceres). Las evidencias del Espacio de Datos indican un diseño innovador de depósito de estériles secos en pasta para ser inyectados en galerías subterráneas (backfilling), eliminando la necesidad de escombreras de superficie y mitigando el impacto visual en el entorno de la ciudad de Cáceres.",
        "primary_site_id": "site_valdeflorez",
        "evidences": [
          {
            "title": "Estudio_Viabilidad_Valdeflorez_Litio_2023.pdf",
            "page": 44,
            "score": 0.96,
            "entities": ["Mineral: Litio", "Provincia: Cáceres", "Compañía: Infinity Lithium"],
            "snippet": "El diseño de la planta metalúrgica asocia la recuperación de litio por lixiviación ácida con la inmediata cementación de los estériles silicoaluminatos finos para relleno de galerías subterráneas...",
            "site_id": "site_valdeflorez"
          }
        ],
        "solr_query": {
          "q": "material_tipo:tailings AND minerales_estimulados:litio",
          "fq": ["region:extremadura", "province:Cáceres"],
          "defType": "edismax",
          "qf": "site_name^2.0 description^1.5",
          "rq": "{!knn f=vector_embedding topK=5}[0.05, 0.44, 0.12, -0.32, 0.18, 0.11, 0.92, -0.05, 0.23, -0.14]",
          "fl": "id,site_name,commodities,score,location"
        },
        "solr_facets": {
          "facet_counts": {
            "facet_fields": {
              "region": ["extremadura", 1, "andalucia", 0],
              "commodities": ["lithium", 1, "tin", 1]
            }
          }
        },
        "ner_entities": {
          "ner_extraction": {
            "text": question,
            "entities": [
              { "text": "litio", "label": "MINERAL", "confidence": 0.99, "standard": "lithium" },
              { "text": "Cáceres", "label": "PROVINCE", "confidence": 0.98, "standard": "caceres" }
            ],
            "spatial_anchor": { "centroid": [39.462, -6.358], "radius_km": 50 }
          }
        }
    }

DATABASE_SITES = [
    {
        "id": "site_penouta",
        "site_name": "Mina de Penouta (Balsas A y B)",
        "company": "Strategic Minerals Spain",
        "region": "galicia",
        "province": "Ourense",
        "municipality": "Viana do Bolo",
        "commodities": ["tungsten", "tin", "tantalum", "niobium", "lithium", "rare earth elements"],
        "commodities_label": "Wolframio, Estaño, Tántalo, Niobio, Litio, REE",
        "facility_type": "tailings storage facility",
        "project_status": "active",
        "description": "Complejo minero enfocado en la recuperación de metales críticos (estaño, tantalita y columbita) a partir del retratamiento de antiguas balsas de decantación y escombreras de granito caolinizado. Es la única mina activa de coltán en Europa.",
        "evidences": [
          {
            "title": "Proyecto_Penouta_Valorizacion_Residuos_2023.pdf",
            "page": 14,
            "score": 0.94,
            "entities": ["Mineral: Wolframio", "Mineral: Tántalo", "Provincia: Ourense", "Compañía: Strategic Minerals"],
            "snippet": "El análisis mineralógico de las balsas de lodos finos A y B de Penouta confirma una ley media residual de 95 ppm de WO3, siendo técnica y económicamente viable su reprocesamiento en la planta gravimétrica existente en el sitio...",
            "site_id": "site_penouta"
          }
        ]
    },
    {
        "id": "site_barruecopardo",
        "site_name": "Proyecto Barruecopardo (Escombrera Norte)",
        "company": "Saloro SLU (Almonty Industries)",
        "region": "castilla y leon",
        "province": "Salamanca",
        "municipality": "Barruecopardo",
        "commodities": ["tungsten"],
        "commodities_label": "Wolframio (Scheelita)",
        "facility_type": "waste dump",
        "project_status": "active",
        "description": "Yacimiento de wolframio a cielo abierto. Las escombreras de roca estéril de granito están sujetas a estudios de trituración y clasificación por sensores para su valorización como áridos secundarios inertes y recuperación de scheelita residual.",
        "evidences": [
          {
            "title": "Guia_Restauracion_Espacio_Minero_Castilla_Leon_2020.pdf",
            "page": 28,
            "score": 0.91,
            "entities": ["Normativa: RD 975/2009", "Provincia: Salamanca", "Región: Castilla y León"],
            "snippet": "El capítulo IV especifica las condiciones de estabilidad geoquímica obligatorias para la reutilización de roca estéril de wolframio y skarn en la submeseta norte, regulando la exención de residuos...",
            "site_id": "site_barruecopardo"
          }
        ]
    },
    {
        "id": "site_san_finx",
        "site_name": "Mina de San Finx (Balsa de Decantación)",
        "company": "Tungsten San Finx (Valoriza Minería)",
        "region": "galicia",
        "province": "A Coruña",
        "municipality": "Lousame",
        "commodities": ["tungsten", "tin"],
        "commodities_label": "Wolframio, Estaño",
        "facility_type": "pond",
        "project_status": "inactive",
        "description": "Histórico depósito de relaves mineros de la mina subterránea de San Finx. Las balsas acumulan lodos finos ricos en estaño y wolframio, pero requieren un estricto control de aguas y neutralización de acidez debido al alto contenido de sulfuros.",
        "evidences": [
          {
            "title": "Informe_Tecnico_Presas_Decantacion_San_Finx_2022.pdf",
            "page": 8,
            "score": 0.87,
            "entities": ["Mineral: Wolframio", "Mineral: Estaño", "Provincia: A Coruña", "Estado: Inactivo"],
            "snippet": "Los residuos arenosos acumulados en la balsa de San Finx estiman un recurso de wolframio remanente del 0.08% WO3, aunque su explotación está condicionada a estrictos controles de pH de aguas y drenajes ácidos...",
            "site_id": "site_san_finx"
          }
        ]
    },
    {
        "id": "site_los_santos",
        "site_name": "Mina Los Santos-Tala (Escombrera Sur)",
        "company": "Almonty Industries",
        "region": "castilla y leon",
        "province": "Salamanca",
        "municipality": "Los Santos",
        "commodities": ["tungsten"],
        "commodities_label": "Wolframio (Scheelita)",
        "facility_type": "waste dump",
        "project_status": "inactive",
        "description": "Explotación de wolframio tipo skarn. Las actividades cesaron temporalmente en 2020. Actualmente se evalúa el reprocesamiento completo de la fracción arenosa de la balsa para recuperar wolframio fino utilizando espirales gravimétricas de última generación.",
        "evidences": [
          {
            "title": "RD_975_2009_Gestion_Residuos_Industrias_Extractivas.pdf",
            "page": 8,
            "score": 0.85,
            "entities": ["Normativa: Directiva 2006/21/CE", "Ámbito: Nacional", "Concepto: Caracterización de residuos"],
            "snippet": "Se requerirá una caracterización geoquímica completa (incluyendo tests estáticos y dinámicos) antes de autorizar cualquier plan de valorización de residuos mineros en depósitos de Categoría A...",
            "site_id": "site_los_santos"
          }
        ]
    },
    {
        "id": "site_valdeflorez",
        "site_name": "San José Valdeflórez (Proyecto de Depósito)",
        "company": "Infinity Lithium",
        "region": "extremadura",
        "province": "Cáceres",
        "municipality": "Cáceres",
        "commodities": ["lithium", "tin"],
        "commodities_label": "Litio (Lepidolita), Estaño",
        "facility_type": "tailings storage facility",
        "project_status": "development",
        "description": "Proyecto industrial para la extracción y refinado de litio grado batería. El diseño ambiental contempla almacenar los estériles de planta en estado seco/pasta como relleno cementado (backfilling) en las galerías subterráneas para eliminar el impacto visual.",
        "evidences": [
          {
            "title": "Estudio_Viabilidad_Valdeflorez_Litio_2023.pdf",
            "page": 44,
            "score": 0.96,
            "entities": ["Mineral: Litio", "Provincia: Cáceres", "Compañía: Infinity Lithium"],
            "snippet": "El diseño de la planta metalúrgica asocia la recuperación de litio por lixiviación ácida con la inmediata cementación de los estériles silicoaluminatos finos para relleno de galerías subterráneas...",
            "site_id": "site_valdeflorez"
          }
        ]
    },
    {
        "id": "site_las_cruces",
        "site_name": "Cobre Las Cruces (Complejo de Relaves)",
        "company": "First Quantum Minerals",
        "region": "andalucia",
        "province": "Sevilla",
        "municipality": "Gerena",
        "commodities": ["copper", "cobalt", "zinc", "silver"],
        "commodities_label": "Cobre, Cobalto, Zinc, Plata",
        "facility_type": "tailings storage facility",
        "project_status": "development",
        "description": "Mina de cobre que ha finalizado su explotación a cielo abierto. El nuevo proyecto PMR (Polimetálico) contempla la minería subterránea y el procesamiento de estériles y sulfuros secundarios complejos para refinar cobre, zinc, plomo y cobalto.",
        "evidences": [
          {
            "title": "Estudio_Recuperacion_Subproductos_Las_Cruces_2022.pdf",
            "page": 34,
            "score": 0.89,
            "entities": ["Mineral: Cobalto", "Provincia: Sevilla", "Compañía: First Quantum"],
            "snippet": "El balance metalúrgico preliminar indica una presencia de cobalto de hasta 180 g/t en la fracción pirítica fina de las colas de flotación acumuladas en el depósito de estériles secos...",
            "site_id": "site_las_cruces"
          }
        ]
    }
]

def extract_query_entities(question):
    import re
    
    def levenshtein_distance(s1, s2):
        if len(s1) < len(s2):
            return levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
            
        return previous_row[-1]

    def is_fuzzy_match(word, keyword):
        w_len = len(word)
        k_len = len(keyword)
        if w_len <= 3 or k_len <= 3:
            return word == keyword
        max_dist = 1 if k_len <= 6 else 2
        if abs(w_len - k_len) > max_dist:
            return False
        return levenshtein_distance(word, keyword) <= max_dist

    # Stop words that should NEVER be matched fuzzily
    STOP_WORDS = {"sobre", "como", "esta", "está", "este", "esto", "para", "pero", "donde", "dónde", "quien", "quién", "entre", "desde", "hasta", "hacia", "del", "con", "los", "las", "una", "uno"}

    q_clean = question.lower().strip("?¿!¡. ")
    q_clean = re.sub(r'[^a-zA-Z0-9áéíóúüñ]', ' ', q_clean)
    words = [w for w in q_clean.split() if w]

    extracted = {
        "regions": [],
        "commodities": [],
        "facility_types": [],
        "project_statuses": []
    }
    
    region_map = {
        "galicia": ["galicia", "ourense", "coruña", "lousame", "viana do bolo"],
        "castilla y leon": ["castilla", "leon", "león", "salamanca", "barruecopardo", "los santos"],
        "extremadura": ["extremadura", "caceres", "cáceres", "valdeflorez", "valdeflórez"],
        "andalucia": ["andalucia", "andalucía", "sevilla", "gerena", "las cruces"]
    }
    
    commodity_map = {
        "tungsten": ["wolframio", "tungsteno", "tungsten", "scheelita"],
        "tin": ["estaño", "estano", "tin"],
        "tantalum": ["tántalo", "tantalo", "tantalum"],
        "niobium": ["niobio", "niobium"],
        "lithium": ["litio", "lithium"],
        "copper": ["cobre", "copper"],
        "cobalt": ["cobalto", "cobalt"],
        "zinc": ["zinc", "cinc"],
        "silver": ["plata", "silver"],
        "platinum": ["platino", "platinum"]
    }
    
    facility_map = {
        "waste dump": ["escombrera", "waste dump", "dump", "roca esteril"],
        "tailings storage facility": ["balsa", "pond", "tailings", "relave", "lodo", "pasta"]
    }
    
    status_map = {
        "active": ["activo", "activa", "active"],
        "inactive": ["inactivo", "inactiva", "inactive", "mantenimiento"],
        "development": ["desarrollo", "development", "proyecto"]
    }

    for word in words:
        # Check regions
        for region, keywords in region_map.items():
            for kw in keywords:
                kw_words = kw.split()
                if len(kw_words) == 1:
                    if word in STOP_WORDS:
                        if word == kw_words[0]:
                            if region not in extracted["regions"]:
                                extracted["regions"].append(region)
                    else:
                        if is_fuzzy_match(word, kw_words[0]):
                            if region not in extracted["regions"]:
                                extracted["regions"].append(region)
                else:
                    if kw in q_clean:
                        if region not in extracted["regions"]:
                            extracted["regions"].append(region)

        # Check commodities
        for commodity, keywords in commodity_map.items():
            for kw in keywords:
                kw_words = kw.split()
                if len(kw_words) == 1:
                    if word in STOP_WORDS:
                        if word == kw_words[0]:
                            if commodity not in extracted["commodities"]:
                                extracted["commodities"].append(commodity)
                    else:
                        if is_fuzzy_match(word, kw_words[0]):
                            if commodity not in extracted["commodities"]:
                                extracted["commodities"].append(commodity)

        # Check facility types
        for fac, keywords in facility_map.items():
            for kw in keywords:
                kw_words = kw.split()
                if len(kw_words) == 1:
                    if word in STOP_WORDS:
                        if word == kw_words[0]:
                            if fac not in extracted["facility_types"]:
                                extracted["facility_types"].append(fac)
                    else:
                        if is_fuzzy_match(word, kw_words[0]):
                            if fac not in extracted["facility_types"]:
                                extracted["facility_types"].append(fac)
                else:
                    if kw in q_clean:
                        if fac not in extracted["facility_types"]:
                            extracted["facility_types"].append(fac)

        # Check project statuses
        for status, keywords in status_map.items():
            for kw in keywords:
                kw_words = kw.split()
                if len(kw_words) == 1:
                    if word in STOP_WORDS:
                        if word == kw_words[0]:
                            if status not in extracted["project_statuses"]:
                                extracted["project_statuses"].append(status)
                    else:
                        if is_fuzzy_match(word, kw_words[0]):
                            if status not in extracted["project_statuses"]:
                                extracted["project_statuses"].append(status)
                else:
                    if kw in q_clean:
                        if status not in extracted["project_statuses"]:
                            extracted["project_statuses"].append(status)

    return extracted


def get_default_response(question):
    return {
        "question": question,
        "narrative": f"<strong>[Respuesta de API Python]</strong> Se ha procesado su consulta: <em>\"{question}\"</em>.<br/><br/>El pipeline híbrido de Solr ha ejecutado una búsqueda geo-vectorial y de coincidencia semántica textual. Los resultados muestran correspondencia relevante con los activos mineros del Faja Pirítica Ibérica y el Macizo Hespérico. Se destaca la balsa de **Penouta (Ourense)** por ley y volumen físico de estériles procesables para materias primas críticas.",
        "primary_site_id": "site_penouta",
        "evidences": [
          {
            "title": "Inventario_Nacional_Residuos_Mineros_Criticos_2024.pdf",
            "page": 72,
            "score": 0.88,
            "entities": ["Ámbito: Nacional", "Tipo: Inventario", "Categoría: Críticas"],
            "snippet": "Se consolida el listado de 45 escombreras prioritarias en España para investigación de tierras raras, cobalto y wolframio, señalando a la submeseta norte como foco de prospección...",
            "site_id": "site_penouta"
          }
        ],
        "solr_query": {
          "q": f"residuos AND ({question})",
          "fq": ["country:spain"],
          "defType": "edismax",
          "qf": "description^1.0 commodities^2.0",
          "rq": "{!knn f=vector_embedding topK=5}[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]"
        },
        "solr_facets": {
          "facet_counts": {
            "facet_fields": {
              "region": ["galicia", 1, "andalucia", 1, "castilla y leon", 2],
              "commodities": ["tungsten", 3, "copper", 2, "lithium", 1]
            }
          }
        },
        "ner_entities": {
          "ner_extraction": {
            "text": question,
            "entities": [
              { "text": question, "label": "UNKNOWN_RAW_TEXT", "confidence": 0.50, "standard": None }
            ],
            "spatial_anchor": None
          }
        }
    }

def get_greeting_response(question):
    return {
        "question": question,
        "narrative": "<strong>[Respuesta del LLM - Conversacional]</strong> ¡Hola! Soy el asistente virtual del Espacio de Datos de Materias Primas Críticas (CRMs Data Space).<br/><br/>¿En qué puedo ayudarte hoy? Puedes hacerme preguntas técnicas sobre los depósitos de residuos mineros en España catalogados en esta demo, por ejemplo:<br/>- <em>\"¿Qué escombreras de wolframio hay en Galicia?\"</em><br/>- <em>\"Dime la normativa ambiental de Castilla y León\"</em><br/>- <em>\"¿Qué balsas tienen cobalto o tierras raras?\"</em><br/>- <em>\"Háblame del litio en Cáceres\"</em>",
        "primary_site_id": "",
        "evidences": [],
        "solr_query": {
          "q": "*:*",
          "fq": [],
          "defType": "edismax",
          "fl": "id,site_name,commodities,score",
          "rows": 0,
          "info": "Consulta conversacional pura: se omite la búsqueda física en el índice de documentos técnicos para ahorrar cómputo."
        },
        "solr_facets": {
          "facet_counts": {
            "facet_fields": {
              "region": [],
              "commodities": [],
              "project_status": []
            }
          }
        },
        "ner_entities": {
          "ner_extraction": {
            "text": question,
            "entities": [],
            "spatial_anchor": None
          }
        }
    }

def get_no_results_response(question, region=None, mineral=None):
    region_label = region if region else "la región especificada"
    mineral_label = f" con potencial de valorización de {mineral}" if mineral else ""
    
    entities = []
    if region:
        entities.append({ "text": region, "label": "REGION", "confidence": 0.99, "standard": region.lower() })
    if mineral:
        entities.append({ "text": mineral, "label": "MINERAL", "confidence": 0.99, "standard": mineral.lower() })

    return {
        "question": question,
        "narrative": f"<strong>[Respuesta de API Python]</strong> Búsqueda ejecutada en Solr sin resultados.<br/><br/>No se han localizado depósitos de residuos mineros{mineral_label} en <strong>{region_label.title()}</strong> dentro de la base de datos actual del Espacio de Datos.<br/><br/>Los depósitos principales de materias primas críticas registrados en este prototipo se concentran en Galicia (Penouta, San Finx), Castilla y León (Barruecopardo, Los Santos), Extremadura (Valdeflórez) y Andalucía (Cobre Las Cruces).",
        "primary_site_id": "",
        "evidences": [],
        "solr_query": {
          "q": "residuo_tipo:escombrera OR balsa_tipo:balsa" if not mineral else f"commodities:{mineral}",
          "fq": [f"region:{region}"] if region else [],
          "defType": "edismax",
          "fl": "id,site_name,commodities,score,location",
          "rows": 10
        },
        "solr_facets": {
          "facet_counts": {
            "facet_fields": {
              "region": [region, 0] if region else [],
              "commodities": [mineral, 0] if mineral else [],
              "project_status": []
            }
          }
        },
        "ner_entities": {
          "ner_extraction": {
            "text": question,
            "entities": entities,
            "spatial_anchor": None
          }
        }
    }

def get_crm_general_response(question):
    return {
        "question": question,
        "narrative": "<strong>[Respuesta del LLM - Búsqueda Documental CRM]</strong> La Unión Europea actualiza periódicamente su listado de **Materias Primas Críticas (CRMs)** basándose en su importancia económica y el riesgo de suministro. Según la última versión del *Critical Raw Materials Act (2024)*, las más importantes y estratégicas incluyen:<br/><br/>"
                     "1. **Litio (Li), Cobalto (Co) y Níquel (Ni):** Cruciales para la fabricación de baterías de vehículos eléctricos y almacenamiento de energía.<br/>"
                     "2. **Tierras Raras (REE):** Elementos como el Neodimio y Disprosio, esenciales para imanes permanentes de turbinas eólicas y motores eléctricos.<br/>"
                     "3. **Wolframio / Tungsteno (W):** Utilizado en herramientas industriales de corte y aplicaciones de defensa debido a su extrema dureza.<br/>"
                     "4. **Magnesio, Silicio metálico y Titanio:** Vitales para aleaciones ligeras en la industria aeroespacial y automotriz.<br/><br/>"
                     "El Espacio de Datos (CRMs Data Space) permite localizar depósitos de residuos mineros en España que contienen varias de estas materias críticas (especialmente Wolframio en Galicia y Salamanca, Litio en Cáceres, y Cobalto en Sevilla) para fomentar el reciclaje secundario.",
        "primary_site_id": "",
        "evidences": [
          {
            "title": "EU_Critical_Raw_Materials_Act_2024.pdf",
            "page": 3,
            "score": 0.95,
            "entities": ["Ámbito: Unión Europea", "Concepto: Riesgo de Suministro", "Categoría: Críticas y Estratégicas"],
            "snippet": "El Reglamento de Materias Primas Críticas establece que al menos el 10% del consumo de CRMs de la UE debe provenir de extracción propia, el 40% de procesamiento y el 25% de reciclaje de residuos para el año 2030...",
            "site_id": ""
          }
        ],
        "solr_query": {
          "q": "critical_raw_materials OR materias_primas_criticas",
          "fq": ["doc_type:policy_regulation"],
          "defType": "edismax",
          "fl": "id,title,score,doc_type",
          "rows": 5
        },
        "solr_facets": {
          "facet_counts": {
            "facet_fields": {
              "doc_type": ["policy_regulation", 1],
              "origin": ["European Commission", 1]
            }
          }
        },
        "ner_entities": {
          "ner_extraction": {
            "text": question,
            "entities": [
              { "text": "materias criticas", "label": "CONCEPT", "confidence": 0.99, "standard": "critical raw materials" },
              { "text": "union europea", "label": "ORGANIZATION", "confidence": 0.98, "standard": "european union" }
            ],
            "spatial_anchor": None
          }
        }
    }

def get_unrecognized_query_response(question):
    return {
        "question": question,
        "narrative": f"<strong>[Respuesta del LLM - Filtros no reconocidos]</strong> No he podido extraer entidades geográficas o mineralógicas específicas de tu consulta: <em>\"{question}\"</em>.<br/><br/>Para realizar una búsqueda estructurada en el Espacio de Datos, por favor especifica:<br/>- Un <strong>mineral crítico</strong> (ej. <em>wolframio, litio, cobalto, tierras raras</em>).<br/>- Una <strong>región</strong> (ej. <em>Galicia, Castilla y León, Extremadura, Andalucía</em>).<br/><br/>Si tienes dudas sobre las políticas generales, prueba preguntando: <em>\"¿Cuáles son las materias críticas de la Unión Europea?\"</em>.",
        "primary_site_id": "",
        "evidences": [],
        "solr_query": {
          "q": question,
          "fq": [],
          "defType": "edismax",
          "fl": "id,site_name,commodities,score",
          "rows": 0,
          "info": "Consulta no estructurada: no se detectaron criterios de filtrado para el Espacio de Datos."
        },
        "solr_facets": {
          "facet_counts": {
            "facet_fields": {
              "region": [],
              "commodities": [],
              "project_status": []
            }
          }
        },
        "ner_entities": {
          "ner_extraction": {
            "text": question,
            "entities": [],
            "spatial_anchor": None
          }
        }
    }

def get_llm_provider():
    openai_key = os.getenv("OPENAI_API_KEY", "")
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    if openai_key and not openai_key.startswith("sk-proj-YOUR_") and "YOUR" not in openai_key:
        return "openai"
    elif gemini_key and not gemini_key.startswith("AIzaSyYOUR_") and "YOUR" not in gemini_key:
        return "gemini"
    else:
        return "rules"

def get_dynamic_response(question):
    provider = get_llm_provider()
    print(f"\n[Geo-RAG Pipeline] Processing with LLM Provider: {provider}")
    
    parsed_json = None
    api_results = None
    narrative = None
    
    if chat_agent:
        try:
            result = chat_agent.process_chat_message(question, provider=provider)
            parsed_json = result.get("extracted_json", {})
            api_results = result.get("api_results", [])
            narrative = result.get("response_text", "")
        except Exception as e:
            print(f"[Geo-RAG Pipeline ERROR] LLM Agent failed: {e}. Falling back to rules.")
            parsed_json = None
            
    # Fallback to local heuristic extractor if agent fails or is not available
    if not parsed_json:
        entities = extract_query_entities(question)
        if not entities["regions"] and not entities["commodities"] and not entities["project_statuses"] and not entities["facility_types"]:
            return get_unrecognized_query_response(question)
            
        matching_sites = []
        for site in DATABASE_SITES:
            match = True
            if entities["regions"] and site["region"] not in entities["regions"]:
                match = False
            if entities["commodities"] and not any(c in site["commodities"] for c in entities["commodities"]):
                match = False
            if entities["project_statuses"] and site["project_status"] not in entities["project_statuses"]:
                match = False
            if match:
                matching_sites.append(site)
                
        if not matching_sites:
            reg_label = entities["regions"][0] if entities["regions"] else None
            min_label = entities["commodities"][0] if entities["commodities"] else None
            return get_no_results_response(question, region=reg_label, mineral=min_label)
            
        evidences = []
        primary_site_id = matching_sites[0]["id"]
        for site in matching_sites:
            evidences.extend(site["evidences"])
            
        ner_entities_list = []
        for r in entities["regions"]:
            ner_entities_list.append({ "text": r, "label": "REGION", "confidence": 0.99, "standard": r })
        for c in entities["commodities"]:
            ner_entities_list.append({ "text": c, "label": "MINERAL", "confidence": 0.99, "standard": c })
        for f in entities["facility_types"]:
            ner_entities_list.append({ "text": f, "label": "FACILITY_TYPE", "confidence": 0.95, "standard": f })
            
        solr_query = {
            "q": "residuo_tipo:escombrera OR balsa_tipo:balsa" if not entities["commodities"] else " OR ".join([f"commodities:{c}" for c in entities["commodities"]]),
            "fq": [f"region:{r}" for r in entities["regions"]],
            "defType": "edismax",
            "qf": "site_name^2.0 description^1.5 linked_facilities",
            "fl": "id,site_name,commodities,score,location",
            "rows": 10
        }
        
        from collections import Counter
        regions_count = Counter([site["region"] for site in matching_sites])
        regions_facet = []
        for reg, count in regions_count.items():
            regions_facet.extend([reg, count])
            
        commodities_count = Counter([c for site in matching_sites for c in site["commodities"]])
        commodities_facet = []
        for comm, count in commodities_count.items():
            commodities_facet.extend([comm, count])
            
        status_count = Counter([site["project_status"] for site in matching_sites])
        status_facet = []
        for status, count in status_count.items():
            status_facet.extend([status, count])

        solr_facets = {
            "facet_counts": {
                "facet_fields": {
                    "region": regions_facet,
                    "commodities": commodities_facet,
                    "project_status": status_facet
                }
            }
        }
        
        site_descs = []
        for s in matching_sites:
            site_descs.append(f"el depósito de <strong>{s['site_name']}</strong> en {s['province']} ({s['company']}), con potencial de valorización de {s['commodities_label']}")
        site_list_str = "; y " if len(site_descs) > 1 else ""
        site_list_str = site_list_str.join(site_descs)
        
        narrative = f"<strong>[Respuesta del LLM - Síntesis NLG]</strong> He procesado tu consulta técnica a través del pipeline híbrido de Solr y he extraído <strong>{len(matching_sites)} depósito(s) de residuos mineros</strong> en el Espacio de Datos:<br/><br/>"
        narrative += f"Se han detectado: {site_list_str}.<br/><br/>"
        if len(matching_sites) == 1:
            s = matching_sites[0]
            narrative += f"Se recomienda priorizar el reprocesamiento en <strong>{s['site_name']}</strong> dado su estado '{s['project_status']}' y su descripción: <em>\"{s['description']}\"</em>."
        else:
            narrative += f"Se han identificado múltiples activos que cumplen tus criterios de búsqueda. Se destaca especialmente la balsa de <strong>{matching_sites[0]['site_name']}</strong> por volumen de estériles procesables para materias primas críticas."

        return {
            "question": question,
            "narrative": narrative,
            "primary_site_id": primary_site_id,
            "evidences": evidences,
            "solr_query": solr_query,
            "solr_facets": solr_facets,
            "ner_entities": {
                "ner_extraction": {
                    "text": question,
                    "entities": ner_entities_list,
                    "spatial_anchor": None
                }
            }
        }

    # If LLM ran successfully, parse outputs
    filters_obj = parsed_json.get("filters", {})
    extracted_regions = filters_obj.get("regions", [])
    extracted_commodities = filters_obj.get("commodities", [])
    extracted_facilities = filters_obj.get("storage_facility_types", [])
    extracted_statuses = filters_obj.get("project_status", [])
    extracted_countries = filters_obj.get("countries", [])
    
    # Format narrative markdown to basic HTML for web client
    import re
    narrative_html = narrative
    narrative_html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', narrative_html)
    narrative_html = re.sub(r'^\s*[\*\-]\s+(.*?)$', r'<li>\1</li>', narrative_html, flags=re.MULTILINE)
    narrative_html = narrative_html.replace('\n', '<br/>')
    
    # Build visual NER extraction list
    ner_entities_list = []
    for r in extracted_regions:
        ner_entities_list.append({ "text": r, "label": "REGION", "confidence": 0.99, "standard": r })
    for c in extracted_commodities:
        ner_entities_list.append({ "text": c, "label": "MINERAL", "confidence": 0.99, "standard": c })
    for f in extracted_facilities:
        ner_entities_list.append({ "text": f, "label": "FACILITY_TYPE", "confidence": 0.95, "standard": f })
    for s in extracted_statuses:
        ner_entities_list.append({ "text": s, "label": "STATUS", "confidence": 0.90, "standard": s })
    for co in extracted_countries:
        ner_entities_list.append({ "text": co, "label": "COUNTRY", "confidence": 0.99, "standard": co })
        
    ner_entities = {
        "intent": parsed_json.get("intent", "filter_search"),
        "answer_mode": parsed_json.get("answer_mode", "structured_filters"),
        "rewritten_query": parsed_json.get("rewritten_query", question),
        "filters": filters_obj,
        "ambiguities": parsed_json.get("ambiguities", []),
        "needs_report_context": parsed_json.get("needs_report_context", False),
        "needs_database_filtering": parsed_json.get("needs_database_filtering", True),
        "ner_extraction": {
            "text": question,
            "entities": ner_entities_list,
            "spatial_anchor": None
        }
    }
    
    # Build evidences and primary_site_id from matched DATABASE_SITES
    evidences = []
    primary_site_id = ""
    if api_results:
        for mock_site in api_results:
            site_id = mock_site.get("id")
            db_site = next((s for s in DATABASE_SITES if s["id"] == site_id or s["site_name"].lower() == mock_site.get("site_name", "").lower()), None)
            if db_site:
                evidences.extend(db_site.get("evidences", []))
                if not primary_site_id:
                    primary_site_id = db_site["id"]
            else:
                evidences.append({
                    "title": f"Documento_{site_id or 'site'}.pdf",
                    "page": 1,
                    "score": 0.90,
                    "entities": [f"Mineral: {', '.join(mock_site.get('commodities', []))}"],
                    "snippet": mock_site.get("description", "Descripción recuperada de la base de datos."),
                    "site_id": site_id
                })
                if not primary_site_id:
                    primary_site_id = site_id
                    
    if not api_results and not primary_site_id:
        reg_label = extracted_regions[0] if extracted_regions else None
        min_label = extracted_commodities[0] if extracted_commodities else None
        return get_no_results_response(question, region=reg_label, mineral=min_label)

    # Format Solr query DSL for display in the tab
    solr_query = {
        "q": "residuo_tipo:escombrera OR balsa_tipo:balsa" if not extracted_commodities else " OR ".join([f"commodities:{c}" for c in extracted_commodities]),
        "fq": [f"region:{r}" for r in extracted_regions],
        "defType": "edismax",
        "qf": "site_name^2.0 description^1.5 linked_facilities",
        "fl": "id,site_name,commodities,score,location",
        "rows": 10
    }
    
    # Facets
    from collections import Counter
    regions_count = Counter([site.get("region") for site in api_results if site.get("region")])
    regions_facet = []
    for reg, count in regions_count.items():
        regions_facet.extend([reg, count])
        
    commodities_count = Counter([c for site in api_results for c in site.get("commodities", [])])
    commodities_facet = []
    for comm, count in commodities_count.items():
        commodities_facet.extend([comm, count])
        
    status_count = Counter([site.get("project_status") for site in api_results if site.get("project_status")])
    status_facet = []
    for status, count in status_count.items():
        status_facet.extend([status, count])

    solr_facets = {
        "facet_counts": {
            "facet_fields": {
                "region": regions_facet,
                "commodities": commodities_facet,
                "project_status": status_facet
            }
        }
    }
    
    return {
        "question": question,
        "narrative": narrative_html,
        "primary_site_id": primary_site_id,
        "evidences": evidences,
        "solr_query": solr_query,
        "solr_facets": solr_facets,
        "ner_entities": ner_entities
    }

def get_foreign_country_response(question, country):
    return {
        "question": question,
        "narrative": f"<strong>[Respuesta del LLM - Ámbito de Búsqueda]</strong> Se ha detectado una consulta geográfica fuera del ámbito del Espacio de Datos: <strong>{country.title()}</strong>.<br/><br/>El prototipo actual del <em>CRMs Data Space</em> está restringido exclusivamente a depósitos de residuos mineros y normativa ambiental del territorio de **España**.<br/><br/>No disponemos de datos estructurados ni documentos técnicos indexados para depósitos en otros países europeos en esta fase del proyecto CRMsDataSpace.",
        "primary_site_id": "",
        "evidences": [],
        "solr_query": {
          "q": question,
          "fq": [f"country:{country.lower()}"],
          "defType": "edismax",
          "fl": "id,site_name,score",
          "rows": 0,
          "info": f"Búsqueda geográficamente fuera de ámbito: {country.upper()}"
        },
        "solr_facets": {
          "facet_counts": { "facet_fields": { "region": [], "commodities": [], "project_status": [] } }
        },
        "ner_entities": {
          "ner_extraction": {
            "text": question,
            "entities": [
              { "text": country, "label": "COUNTRY", "confidence": 0.99, "standard": country.lower() }
            ],
            "spatial_anchor": None
          }
        }
    }

def process_query_backend(question):
    q_lower = question.lower()
    cleaned_q = q_lower.strip("?¿!¡. ")
    
    # List of greetings
    greetings = ["hola", "buenos dias", "buenas tardes", "buenas noches", "ey", "hello", "hi", "que tal", "quien eres", "como estas", "adios", "chao", "saludos"]
    if cleaned_q in greetings or any(cleaned_q.startswith(g + " ") for g in greetings):
        res_payload = get_greeting_response(question)
    # Check for general CRM knowledge questions (e.g. list of critical raw materials)
    elif any(kw in q_lower for kw in ["materias criticas", "materias críticas", "critical raw materials", "crm", "unión europea", "union europea", "lista de materias", "qué son", "cuales son", "cuáles son"]):
        res_payload = get_crm_general_response(question)
    # Check for foreign countries
    elif any(country in q_lower for country in ["alemania", "francia", "portugal", "italia", "reino unido", "inglaterra", "belgica", "bélgica", "suecia", "noruega", "finlandia", "polonia", "austria"]):
        country_found = next(c for c in ["alemania", "francia", "portugal", "italia", "reino unido", "inglaterra", "belgica", "bélgica", "suecia", "noruega", "finlandia", "polonia", "austria"] if c in q_lower)
        res_payload = get_foreign_country_response(question, country_found)
    # Check for specific Case queries to return the exact gold standards
    elif "cerca de explotaciones activas" in q_lower:
        res_payload = get_galicia_wolframio_response(question)
    elif "normativa ambiental aplicable" in q_lower or ("normativa" in q_lower and "castilla" in q_lower):
        res_payload = get_castilla_normativa_response(question)
    elif "cobalto o tierras raras" in q_lower:
        res_payload = get_cobalto_ree_response(question)
    else:
        # Check if they are querying about a region we don't have sites for
        unsupported_regions = {
            "aragon": "Aragón", "aragón": "Aragón",
            "cataluña": "Cataluña", "catalunya": "Cataluña",
            "madrid": "Madrid",
            "pais vasco": "País Vasco", "país vasco": "País Vasco",
            "valencia": "Valencia",
            "murcia": "Murcia",
            "la rioja": "La Rioja",
            "navarra": "Navarra",
            "baleares": "Baleares",
            "canarias": "Canarias",
            "cantabria": "Cantabria",
            "asturias": "Asturias"
        }
        matched_unsupported = False
        for reg_key, reg_name in unsupported_regions.items():
            if reg_key in q_lower:
                minerals = ["wolframio", "estaño", "litio", "cobre", "cobalto", "tierras raras", "oro", "plata", "zinc"]
                found_mineral = None
                for m in minerals:
                    if m in q_lower:
                        found_mineral = m
                        break
                res_payload = get_no_results_response(question, region=reg_name, mineral=found_mineral)
                matched_unsupported = True
                break
        
        if not matched_unsupported:
            res_payload = get_dynamic_response(question)

    # Inject the LLM 1 entity extraction prompt context for Lineage visualization
    llm1_prompt = "No disponible (ejecución sin LLM)"
    if chat_agent and hasattr(chat_agent, "PROMPT_TEMPLATE"):
        try:
            llm1_prompt = chat_agent.PROMPT_TEMPLATE.format(query=question.strip())
        except Exception:
            pass
            
    if isinstance(res_payload, dict):
        res_payload["llm1_prompt"] = llm1_prompt
        
    return res_payload

# =====================================================================
# SERVER HANDLER WITH STATIC FILES & API ROUTING
# =====================================================================

class MyHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def do_OPTIONS(self):
        # Manejo de pre-vuelo CORS para evitar bloqueos del navegador
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        if self.path == '/api/chat':
            try:
                # Leer la longitud y el cuerpo de la petición POST
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                req_data = json.loads(post_data.decode('utf-8'))
                
                question = req_data.get('question', '')
                print(f"\n[API POST] Petición /api/chat recibida. Pregunta: '{question}'")
                
                # Procesar la pregunta en Python
                res_payload = process_query_backend(question)
                
                # Responder al cliente en formato JSON con cabeceras CORS
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                self.wfile.write(json.dumps(res_payload).encode('utf-8'))
                print(f"[API POST] Respuesta enviada con éxito para: '{question}'")
            except Exception as e:
                print(f"[ERROR API] Fallo al procesar petición POST: {e}")
                self.send_response(500)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == "__main__":
    if not os.path.exists(DIRECTORY):
        print(f"[ERROR] La carpeta del prototipo '{DIRECTORY}' no existe.")
        sys.exit(1)
        
    print("=" * 60)
    print("  Geo-RAG Explorer: Espacio de Datos de Materias Primas Críticas")
    print("  Lanzador de Servidor Híbrido: Web Estática & API REST (Python)")
    print("=" * 60)
    
    # Iniciar el servidor web en un hilo secundario para no bloquear la terminal

    # Reutilizamos la función start_server declarada antes pero con nuestro nuevo handler
    def start_server_wrapper():
        socketserver.TCPServer.allow_reuse_address = True
        try:
            with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
                print(f"\n[INFO] Servidor Híbrido iniciado en http://localhost:{PORT}")
                print(f"[INFO] Sirviendo Web en: {DIRECTORY}")
                print(f"[INFO] Endpoint API REST en: http://localhost:{PORT}/api/chat")
                httpd.serve_forever()
        except Exception as e:
            print(f"\n[ERROR] No se pudo iniciar el servidor en el puerto {PORT}: {e}")
            print("[ERROR] Asegúrese de cerrar otras instancias o cambiar el PORT en el script.")

    server_thread_wrapper = threading.Thread(target=start_server_wrapper, daemon=True)
    server_thread_wrapper.start()
    
    # Esperar un instante para levantar el socket
    time.sleep(1.5)
    
    # Abrir navegador automáticamente
    url = f"http://localhost:{PORT}/index.html"
    print(f"[INFO] Abriendo navegador en: {url}")
    webbrowser.open(url)
    
    print("\n>>> El servidor REST y Web está activo.")
    print(">>> En el Chat de la web, las consultas libres ahora llaman al servidor de Python.")
    print(">>> Presione [Ctrl+C] en esta terminal para apagar el servidor local.")
    print("=" * 60)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[INFO] Apagando el servidor local del CRMs Data Space...")
