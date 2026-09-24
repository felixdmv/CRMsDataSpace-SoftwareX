"""
SoftwareX Agent Orchestrator:
Combines Few-Shot prompting (v1) with JSON Schema validation (v3)
to drive Apache Solr filtering and GIS visualization on 100 European CRM sites.
"""

import json
import re
from typing import Dict, Any, List
from llm_client import call_llm, extract_json_block
from nlu_pipeline import (
    SYSTEM_PROMPT_FEWSHOT, 
    NLU_RESPONSE_SCHEMA, 
    Normalizer, 
    Validator, 
    QueryBuilder
)
from mock_api import query_data_space_solr, load_dataset

UNSUPPORTED_COUNTRY_DICT = {
    "albania": "Albania",
    "reino unido": "el Reino Unido",
    "uk": "el Reino Unido",
    "united kingdom": "el Reino Unido",
    "chile": "Chile",
    "china": "China",
    "estados unidos": "Estados Unidos",
    "usa": "Estados Unidos",
    "rusia": "Rusia",
    "russia": "Rusia",
    "noruega": "Noruega",
    "norway": "Noruega",
    "suiza": "Suiza",
    "switzerland": "Suiza",
    "serbia": "Serbia",
    "marruecos": "Marruecos",
    "morocco": "Marruecos",
    "turquia": "Turquía",
    "turquía": "Turquía",
    "turkey": "Turquía",
    "australia": "Australia",
    "canada": "Canadá",
    "canadá": "Canadá",
    "argentina": "Argentina",
    "brasil": "Brasil",
    "brazil": "Brasil",
    "ucrania": "Ucrania",
    "ukraine": "Ucrania"
}

def build_generic_qa_response(query: str, validated: Dict[str, Any]) -> str:
    """
    Builds rich, authoritative domain answers for conversational queries,
    system onboarding/help, and conceptual/regulatory questions.
    """
    q_lower = query.lower()
    is_spanish = any(w in q_lower for w in [
        "hola", "buen", "dia", "días", "tardes", "noches", "que tal", "saludos",
        "ayuda", "puedes", "cómo", "como", "sirves", "funciona", "qué", "que",
        "diferencia", "balsa", "escombrera", "relaves", "directiva", "criterios",
        "normativa", "explícame", "explicame", "cuál", "cual", "cuáles", "cuales"
    ])

    # 1. Greetings & Social Openers
    greeting_patterns = [
        r'\bhola\b', r'\bhello\b', r'\bhi\b', r'\bhey\b', 
        r'\bbuenos d[ií]as\b', r'\bbuenas tardes\b', r'\bbuenas noches\b', r'\bbuenas\b',
        r'\bgood morning\b', r'\bgood afternoon\b'
    ]
    is_pure_greeting = any(re.search(pat, q_lower) for pat in greeting_patterns) and not any(k in q_lower for k in [
        "diferencia", "directiva", "unfc", "jorc", "amd", "drenaje", "insar", "litio", "cobalto", "niquel", "wolfram"
    ])
    
    help_patterns = [
        r'en qu[eé] me puedes ayudar', r'qu[eé] puedes hacer', r'para qu[eé] sirves',
        r'c[oó]mo funciona', r'qui[eé]n eres', r'how can (you|this system) (help|assist)',
        r'what can you do', r'how to use', r'provide guidance', r'help me understand'
    ]
    is_help_request = any(re.search(pat, q_lower) for pat in help_patterns)

    if is_pure_greeting or is_help_request:
        if is_spanish:
            return (
                "👋 **¡Hola! Bienvenido al Asistente Inteligente del European CRMs Data Space.**\n\n"
                "Esta plataforma integra un motor de búsqueda semántica (NLU), Apache Solr y visualización GIS "
                "para explorar y prospectar **100 instalaciones y depósitos de residuos mineros** distribuidos en **12 países de la Unión Europea**.\n\n"
                "### 🎯 ¿En qué te puedo ayudar?\n"
                "- 🌍 **Filtrar por cobertura geográfica en la UE**:\n"
                "  España, Portugal, Francia, Alemania, Suecia, Finlandia, Polonia, Italia, Grecia, Irlanda, Austria y Chequia.\n"
                "- 💎 **Materias Primas Críticas (CRMs)**:\n"
                "  Localizar depósitos de Litio, Cobalto, Níquel, Wolframio/Tungsteno, Tierras Raras (REE), Cobre, Estaño, Tántalo/Coltán, Grafito o Titanio.\n"
                "- 🏗️ **Tipologías de depósito**:\n"
                "  Balsas de relaves (*tailings ponds*), escombreras de estériles (*waste dumps*) y acopios (*stockpiles*).\n"
                "- ⚠️ **Condición ambiental y operativa**:\n"
                "  Instalaciones activas, inactivas, en mantenimiento, restauradas o con riesgo de drenaje ácido de mina (AMD).\n"
                "- 📖 **Consultas conceptuales y normativas**:\n"
                "  Explicación de marcos internacionales (UNFC, JORC, NI 43-101), Directiva 2006/21/CE y Ley Europea de Materias Primas Fundamentales (CRMA).\n\n"
                "💡 **Ejemplos de consultas que puedes probar:**\n"
                "1. *\"Balsas de relaves de litio y cobalto activas en España y Finlandia\"*\n"
                "2. *\"Escombreras de wolframio sin restaurar en Alemania con riesgo de drenaje ácido\"*\n"
                "3. *\"Instalaciones con tierras raras (REE) en Suecia y Francia\"*\n"
                "4. *\"¿Qué diferencia técnica existe entre una balsa y una escombrera?\"*"
            )
        return (
            "👋 **Hello! Welcome to the European CRMs Data Space Explorer.**\n\n"
            "This platform provides semantic search, Apache Solr indexing, and interactive Leaflet GIS visualization across "
            "**100 synthetic mining waste facilities and tailings** located in **12 European Union Member States**.\n\n"
            "### 🎯 How can I assist you?\n"
            "- 🌍 **EU Geographical Scope**: Spain, Portugal, France, Germany, Sweden, Finland, Poland, Italy, Greece, Ireland, Austria, and Czechia.\n"
            "- 💎 **Critical Raw Materials (CRMs)**: Lithium, Cobalt, Nickel, Tungsten, Rare Earth Elements (REE), Copper, Tin, Tantalum, Graphite, Titanium.\n"
            "- 🏗️ **Facility Asset Types**: Tailings Storage Facilities (TSFs / ponds), Waste Dumps, and Stockpiles.\n"
            "- ⚠️ **Environmental Conditions**: Active, inactive, unrestored, or with Acid Mine Drainage (AMD) potential.\n"
            "- 📖 **Regulatory & Conceptual QA**: UNFC 2019, JORC Code, EU Directive 2006/21/EC, and CRMA guidelines.\n\n"
            "💡 **Example queries to try:**\n"
            "1. *\"Show active lithium and cobalt tailings ponds in Spain and Finland\"*\n"
            "2. *\"Unrestored tungsten waste dumps in Germany\"*\n"
            "3. *\"Rare earth elements facilities in Sweden and France\"*"
        )

    # 2. Conceptual: Balsa vs Escombrera (Tailings Pond vs Waste Dump)
    if any(k in q_lower for k in ["diferencia", "distinction"]) and any(k in q_lower for k in ["balsa", "tailing", "pond"]) and any(k in q_lower for k in ["escombrera", "dump", "spoil"]):
        if is_spanish:
            return (
                "🔬 **Diferencia técnica entre Balsa de Decantación (*Tailings Pond*) y Escombrera de Roca Estéril (*Waste Dump*):**\n\n"
                "1. **Balsa de Decantación / Relaves (*Tailings Storage Facility - TSF / Pond*)**:\n"
                "   - **Naturaleza del residuo**: Almacena los estériles procedentes de la planta de tratamiento mineral o concentración metalúrgica (fracción fina granulométrica: limos y arcillas suspendidos en pulpa acuosa).\n"
                "   - **Contención hidráulica**: Requiere la construcción de presas perimetrales continuas (diques de contención) para retener tanto la fracción sólida como el agua de proceso.\n"
                "   - **Riesgos críticos**: Inestabilidad por licuefacción estática o dinámica, sobrevertido por avenidas y rotura de presa (ej. catástrofes de Aznalcóllar o Brumadinho), así como lixiviación de reactivos químicos residuales (cianuro, espumantes, xantatos).\n\n"
                "2. **Escombrera (*Waste Dump / Spoil Heap*)**:\n"
                "   - **Naturaleza del residuo**: Almacena roca encajante y cobertera estéril arrancada durante las fases de destape y perforación/voladura en mina a cielo abierto o subterránea. Presenta granulometría gruesa (bloques, gravas) sin procesamiento químico previo.\n"
                "   - **Morfología**: Se conforma mediante vertido mecánico por gravedad en bancos y bermas escalonadas, sin requerir una presa hidráulica estanca.\n"
                "   - **Riesgos críticos**: Deslizamiento rotacional o planar de taludes por saturación, erosión hídrica y generación de Drenaje Ácido de Mina (AMD) si la roca contiene sulfuros reactivos.\n\n"
                "💡 *Puedes filtrar ambos tipos en el mapa buscando por ejemplo: 'balsas activas en España' o 'escombreras sin restaurar en Alemania'.*"
            )
        return (
            "🔬 **Technical distinction between Tailings Storage Facilities (Ponds) and Waste Dumps:**\n\n"
            "1. **Tailings Storage Facilities (TSFs / Tailings Ponds)**:\n"
            "   - **Material**: Fine-grained slurries (silts and clays) resulting from chemical/mineral beneficiation.\n"
            "   - **Containment**: Requires engineered perimeter retaining dams or embankments to impound solids and process water.\n"
            "   - **Failure Modes**: Static liquefaction, dam breach, overtopping, and reagent seepage.\n\n"
            "2. **Waste Dumps (Spoil Heaps)**:\n"
            "   - **Material**: Coarse run-of-mine barren rock excavated during overburden stripping, with no chemical beneficiation.\n"
            "   - **Configuration**: Constructed in tiered lifts and benches by mechanical end-dumping.\n"
            "   - **Failure Modes**: Slope instability, bench crest slumping, and Acid Mine Drainage (AMD) generation from exposed sulfides.\n\n"
            "💡 *Try querying: 'Show active tailings ponds in Spain' or 'Unrestored waste dumps in Germany'.*"
        )

    # 3. Directiva 2006/21/CE y Normativa Europea
    if "2006/21" in q_lower or any(k in q_lower for k in ["normativa europea", "directiva"]):
        if is_spanish:
            return (
                "⚖️ **Marco Normativo Europeo: Directiva 2006/21/CE sobre la gestión de residuos de las industrias extractivas**\n\n"
                "La Directiva 2006/21/CE establece el marco regulatorio comunitario para prevenir y mitigar el impacto ambiental derivado del almacenamiento de residuos mineros:\n\n"
                "1. **Instalaciones de Categoría A**: Clasifica aquellas balsas o escombreras cuyo fallo estructural o escape de sustancias peligrosas pueda causar accidentes mayores con pérdidas de vidas humanas o graves daños ambientales permanentes.\n"
                "2. **Planes de Gestión de Residuos (PGR)**: Obligación de elaborar planes detallados de caracterización del residuo, prevención de drenaje ácido y planes de emergencia exterior.\n"
                "3. **Garantías Financieras**: Exigencia legal de constituir avales financieros independientes previos al inicio de operaciones para garantizar la clausura y restauración integral del emplazamiento.\n"
                "4. **Inspecciones y Registro Público**: Inventario obligatorio de instalaciones cerradas o abandonadas con impacto ambiental significativo.\n\n"
                "💡 *Puedes consultar en la plataforma las balsas catalogadas con potencial de afección ambiental buscando 'instalaciones con riesgo de drenaje ácido'.*"
            )
        return (
            "⚖️ **EU Regulatory Framework: Directive 2006/21/EC on Mining Waste Management**\n\n"
            "Directive 2006/21/EC governs extractive waste disposal across the EU:\n"
            "1. **Category A Classification**: Designates high-hazard tailings dams and dumps where catastrophic structural failure could cause human fatalities or irreversible environmental degradation.\n"
            "2. **Waste Management Plans**: Mandatory characterization of geochemical leachability, acid-generation potential, and emergency response.\n"
            "3. **Financial Guarantees**: Operators must post independent financial security prior to commissioning to guarantee post-closure rehabilitation.\n"
            "4. **Inventory of Closed Facilities**: Requires member states to catalogue closed sites posing serious environmental hazards."
        )

    # 4. UNFC y JORC
    if any(k in q_lower for k in ["unfc", "jorc", "ni 43-101", "samrec"]):
        if is_spanish:
            return (
                "📊 **Clasificación de Recursos y Reservas Secundarias: UNFC vs Códigos CRIRSCO (JORC, NI 43-101)**\n\n"
                "1. **Marco UNFC (Naciones Unidas - UNFC 2019)**:\n"
                "   - Sistema tridimensional basado en 3 ejes: **E** (Viabilidad socioeconómica), **F** (Madurez técnica y viabilidad de ingeniería del proyecto), y **G** (Certeza geológica y caracterización del depósito).\n"
                "   - Es el estándar oficial adoptado por la Unión Europea bajo la **Ley de Materias Primas Fundamentales (CRMA)** para cuantificar recursos secundarios en relaves y escombreras antropogénicas.\n\n"
                "2. **Códigos de la familia CRIRSCO (JORC / NI 43-101 / SAMREC)**:\n"
                "   - Desarrollados para la divulgación financiera y bursátil dirigida a inversores.\n"
                "   - Exigen la firma y certificación de una **Persona Competente (*Competent Person*)** con experiencia demostrable para reclasificar un residuo minero como reserva mineral explotable tras un estudio de factibilidad técnico-económica.\n\n"
                "💡 *La base de datos de CRMsDataSpace incorpora la métrica de madurez técnica de los depósitos armonizada con los criterios UNFC de la UE.*"
            )
        return (
            "📊 **Mineral Resource Classification: UNFC-2019 vs CRIRSCO Codes (JORC / NI 43-101)**\n\n"
            "1. **UNFC-2019 (United Nations Framework Classification)**:\n"
            "   - Evaluates projects across 3 axes: **E** (Environmental-Socio-Economic viability), **F** (Technical feasibility / engineering maturity), and **G** (Geological confidence).\n"
            "   - Adopted under the EU Critical Raw Materials Act (CRMA) for harmonizing anthropogenic CRM inventories.\n\n"
            "2. **CRIRSCO Codes (JORC / NI 43-101 / SAMREC)**:\n"
            "   - Market-oriented reporting standards requiring sign-off by a registered **Competent Person (CP)**.\n"
            "   - Demands rigorous Modifying Factors (metallurgical recovery, environmental licensing, economics) to convert historical tailings into mineral reserves."
        )

    # 5. Drenaje Ácido de Mina (AMD)
    if any(k in q_lower for k in ["drenaje ácido", "drenaje acido", "acid mine drainage", "amd"]):
        if is_spanish:
            return (
                "🧪 **Drenaje Ácido de Mina (Acid Mine Drainage - AMD): Origen y Restauración Pasiva**\n\n"
                "1. **Mecanismo Biogeoquímico**:\n"
                "   - Se produce por la oxidación de minerales sulfurosos (especialmente pirita $FeS_2$ y pirrotina) al quedar expuestos al oxígeno atmosférico y al agua durante las labores mineras.\n"
                "   - Las bacterias acidófilas quimiolitótrofas (*Acidithiobacillus ferrooxidans*) catalizan la oxidación del ion ferroso a férrico, acelerando exponencialmente la reacción y generando ácido sulfúrico con pH resultante habitualmente inferior a 3.0, lo que lixivia metales pesados tóxicos en solución.\n\n"
                "2. **Técnicas de Restauración Pasiva**:\n"
                "   - **Humedales anaerobios (*constructed wetlands*)**: Utilizan bacterias sulfato-reductoras para precipitar metales pesados en forma de sulfuros insolubles.\n"
                "   - **Drenes anóxicos calizos (*Anoxic Limestone Drains - ALD*)**: Neutralizan la acidez sin precipitar hidróxidos de hierro en la superficie de la calcita.\n"
                "   - **Reactores Biorreductores de Dispersión Alcalina (SDR)**: Combinación de sustrato orgánico y material alcalinizante para tratamiento autónomo a largo plazo.\n\n"
                "💡 *Puedes visualizar en el mapa los depósitos europeos con riesgo de AMD buscando: 'instalaciones sin restaurar con potencial de drenaje ácido'.*"
            )
        return (
            "🧪 **Acid Mine Drainage (AMD): Geochemical Mechanisms & Remediation**\n\n"
            "1. **Biogeochemical Mechanism**:\n"
            "   - Initiated by the oxidation of exposed iron disulfides (pyrite $FeS_2$) in the presence of atmospheric oxygen and moisture.\n"
            "   - Acidophilic bacteria (*Acidithiobacillus ferrooxidans*) catalyze $Fe^{2+}$ oxidation, lowering pH below 3.0 and solubilizing heavy metals.\n\n"
            "2. **Passive Remediation Technologies**:\n"
            "   - **Anoxic Limestone Drains (ALDs)**: Add alkalinity without calcite armoring.\n"
            "   - **Anaerobic Bioreactors / Constructed Wetlands**: Promote microbial sulfate reduction to re-precipitate heavy metal sulfides.\n\n"
            "💡 *Search for 'unrestored facilities with acid mine drainage potential' to explore affected sites.*"
        )

    # 6. Fallback General QA / Clarification
    if is_spanish:
        return (
            "ℹ️ **Información sobre el European CRMs Data Space:**\n\n"
            "El sistema está listo para procesar consultas sobre materias primas críticas europeas.\n\n"
            "Para realizar una búsqueda cartográfica, especifica al menos un **país de la UE** (ej. España, Finlandia, Alemania), "
            "un **metal estratégico** (ej. litio, cobalto, wolframio, tierras raras) o una **tipología de instalación** (balsas de relaves, escombreras).\n\n"
            "**Ejemplos recomendados:**\n"
            "- *\"Balsas de relaves con litio en Portugal\"*\n"
            "- *\"Escombreras inactivas con wolframio en España\"*\n"
            "- *\"Instalaciones con tierras raras en Suecia y Francia\"*"
        )
    return (
        "ℹ️ **European CRMs Data Space System Notice:**\n\n"
        "To explore the dataset on the Leaflet GIS map, please specify criteria such as an **EU Country** (e.g. Spain, Germany, Sweden), "
        "a **CRM Metal** (e.g. lithium, cobalt, tungsten, rare earths), or a **Facility Type** (tailings ponds, waste dumps).\n\n"
        "**Recommended Queries:**\n"
        "- *\"Active lithium tailings ponds in Spain\"*\n"
        "- *\"Unrestored tungsten waste dumps in Germany\"*\n"
        "- *\"Rare Earth Elements facilities in Sweden and France\"*"
    )

def generate_natural_response(
    query: str, 
    validated_nlu: Dict[str, Any], 
    solr_results: Dict[str, Any], 
    provider: str,
    prefix_notice: str = ""
) -> str:
    """Generates a professional natural language summary of search results."""
    num_found = solr_results.get("numFound", 0)
    docs = solr_results.get("docs", [])
    
    if num_found == 0:
        is_spanish = any(w in query.lower() for w in ["dime", "muestra", "en ", "escombrera", "balsa", "donde", "hola", "que ", "de ", "los ", "las ", "paises", "países"])
        msg = prefix_notice if prefix_notice else ""
        if is_spanish:
            msg += "No se han encontrado instalaciones mineras o depósitos en el espacio de datos europeo que coincidan con estos criterios de búsqueda. Prueba a ampliar los filtros de país o materias primas."
        else:
            msg += "No European tailings or mining facilities were found matching your criteria in the data space. Try broadening the country or commodity filters."
        return msg

    # Sample top 3 sites for summary
    top_sites = docs[:3]
    summary_items = []
    for s in top_sites:
        summary_items.append(f"- **{s['site_name']}** ({s['country_name']}): {s['storage_facility_label']} with {s['commodities_label']}. Status: *{s['project_status']}*.")
        
    sites_text = "\n".join(summary_items)
    
    # Direct fast narrative generation
    narrative = prefix_notice if prefix_notice else ""
    narrative += f"Located **{num_found} synthetic European CRM facilities** matching your query filters.\n\n"
    narrative += "**Key Matching Sites:**\n" + sites_text
    if num_found > 3:
        narrative += f"\n\n*...and {num_found - 3} additional facilities visualised on the map.*"
    return narrative

def process_chat_message(query: str, provider: str = "mock") -> Dict[str, Any]:
    """
    Main entry point for processing chat queries in SoftwareX application.
    Orchestrates semantic extraction, out-of-scope country validation, Solr querying, and response generation.
    """
    # 1. Semantic parsing with v1 Few-Shot + v3 JSON Schema
    raw_response = call_llm(
        system_prompt=SYSTEM_PROMPT_FEWSHOT,
        user_prompt=f"User Query: \"{query}\"\nJSON Output:",
        provider=provider,
        json_mode=True,
        response_schema=NLU_RESPONSE_SCHEMA
    )
    
    raw_json = extract_json_block(raw_response)
    
    # 2. Pipeline normalization and validation
    normalizer = Normalizer()
    validator = Validator()
    query_builder = QueryBuilder()
    
    normalized = normalizer.normalize(raw_json)
    validated = validator.validate(normalized)
    
    print(f"[NLU Agent] Model/Provider: {provider} | Query: '{query}'")
    print(f"[NLU Agent] Parsed Filters: {validated.get('filters')}")

    intent = validated.get("intent", "filter_search")
    filters = validated.get("filters", {})
    q_lower = query.lower()

    # 3. Detect Out-of-Scope / Unsupported Countries
    unsupported_found = list(validated.get("unsupported_countries", []))
    for ukw, ulabel in UNSUPPORTED_COUNTRY_DICT.items():
        if re.search(r'\b' + re.escape(ukw) + r'\b', q_lower) and ulabel not in unsupported_found:
            unsupported_found.append(ulabel)

    has_valid_filters = any([
        filters.get("countries"),
        filters.get("commodities"),
        filters.get("storage_facility_types"),
        filters.get("project_status"),
        filters.get("restored") is not None
    ])

    # 4. Handle "generic_qa" intent (greetings, onboarding, help, conceptual domain queries)
    if intent == "generic_qa":
        response_text = build_generic_qa_response(query, validated)
        return {
            "query": query,
            "extracted_json": validated,
            "solr_query": {"q": "*:*", "fq": []},
            "num_found": 0,
            "total_dataset": 100,
            "matched_ids": [],
            "active_map_filters": [],
            "facets": {},
            "response_text": response_text,
            "docs": []
        }

    # 5. Handle Unsupported Countries in filter queries
    prefix_notice = ""
    if unsupported_found:
        is_spanish = any(w in q_lower for w in ["paises", "países", "como", "que", "tengan", "en ", "de "])
        country_names_str = ", ".join(unsupported_found)
        has_valid_country = bool(filters.get("countries"))
        if has_valid_country:
            # Partially valid query: e.g. "paises del sur de europa como grecia o albania que tengan niquel"
            if is_spanish:
                prefix_notice = (
                    f"⚠️ **Aclaración sobre la consulta y cobertura geográfica**:\n"
                    f"Has consultado por **{country_names_str}**, pero el repositorio europeo CRMsDataSpace está actualmente limitado a "
                    f"**12 países miembros de la Unión Europea** (España, Portugal, Francia, Alemania, Suecia, Finlandia, Polonia, Italia, Grecia, Irlanda, Austria y Chequia). "
                    f"**{country_names_str}** no forma parte de este conjunto de datos comunitario.\n\n"
                    f"No obstante, para los países del sur de Europa integrados en el sistema, se han identificado las siguientes instalaciones que cumplen tus criterios de búsqueda:\n\n"
                )
            else:
                prefix_notice = (
                    f"⚠️ **Geographical Scope Notice**:\n"
                    f"You inquired about **{country_names_str}**, which is outside the European CRMs Data Space (restricted to 12 EU Member States). "
                    f"Results below represent matching facilities in covered EU member states:\n\n"
                )
        else:
            # Query has ONLY unsupported countries (e.g. "minas en Albania" or "litio en Chile")
            if is_spanish:
                response_text = (
                    f"⚠️ **País fuera de cobertura geográfica**:\n\n"
                    f"Has solicitado instalaciones en **{country_names_str}**, pero el espacio de datos europeo CRMsDataSpace está delimitado exclusivamente a "
                    f"**12 países miembros de la Unión Europea** (Austria, Chequia, Finlandia, Francia, Alemania, Grecia, Irlanda, Italia, Polonia, Portugal, España y Suecia).\n\n"
                    f"Países como **{country_names_str}** no están cubiertos en esta versión del repositorio.\n\n"
                    f"💡 *Prueba a consultar depósitos en países del sur de Europa incluidos en el sistema, como España, Portugal, Italia o Grecia.*"
                )
            else:
                response_text = (
                    f"⚠️ **Out-of-Scope Country**:\n\n"
                    f"The European CRMs Data Space is restricted to 12 European Union Member States. "
                    f"Facilities in **{country_names_str}** are not included in this repository.\n\n"
                    f"💡 *Try querying facilities in covered EU countries such as Spain, Portugal, Italy, or Greece.*"
                )
            return {
                "query": query,
                "extracted_json": validated,
                "solr_query": {"q": "*:*", "fq": []},
                "num_found": 0,
                "total_dataset": 100,
                "matched_ids": [],
                "active_map_filters": [],
                "facets": {},
                "response_text": response_text,
                "docs": []
            }

    # 6. Handle vague queries with zero search criteria (prevent dumping all 100 sites on vague queries)
    if not has_valid_filters and not any(w in q_lower for w in ["todas", "todo", "todos", "all", "dataset"]):
        response_text = build_generic_qa_response(query, validated)
        return {
            "query": query,
            "extracted_json": validated,
            "solr_query": {"q": "*:*", "fq": []},
            "num_found": 0,
            "total_dataset": 100,
            "matched_ids": [],
            "active_map_filters": [],
            "facets": {},
            "response_text": response_text,
            "docs": []
        }

    # 7. Solr query construction & execution for valid filter searches
    solr_query = query_builder.build(validated)
    solr_results = query_data_space_solr(solr_query["q"], solr_query["fq"])
    
    matched_docs = solr_results.get("docs", [])
    matched_ids = [d["id"] for d in matched_docs]
    
    # 8. Extract active filter badges for visual GIS map display
    active_map_filters = []
    if filters.get("countries"):
        active_map_filters.append({"type": "Country", "label": "Countries", "values": filters["countries"]})
    if filters.get("commodities"):
        active_map_filters.append({"type": "Commodity", "label": "CRM Metal", "values": filters["commodities"]})
    if filters.get("storage_facility_types"):
        active_map_filters.append({"type": "Facility", "label": "Facility Type", "values": filters["storage_facility_types"]})
    if filters.get("project_status"):
        active_map_filters.append({"type": "Status", "label": "Status", "values": filters["project_status"]})
    if filters.get("restored") is not None:
        active_map_filters.append({"type": "Restoration", "label": "Restored", "values": [str(filters["restored"])]})

    # 9. Generate natural language response
    response_text = generate_natural_response(query, validated, solr_results, provider, prefix_notice=prefix_notice)
        
    return {
        "query": query,
        "extracted_json": validated,
        "solr_query": solr_query,
        "num_found": solr_results.get("numFound", 0),
        "total_dataset": solr_results.get("totalDatasetSize", 100),
        "matched_ids": matched_ids,
        "active_map_filters": active_map_filters,
        "facets": solr_results.get("facets", {}),
        "response_text": response_text,
        "docs": matched_docs
    }
