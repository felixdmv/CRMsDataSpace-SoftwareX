import os
import json
import urllib.request
import urllib.parse
import re
import sys
from pathlib import Path
from typing import Dict, Any, List

# Caching for local model
LOCAL_MODEL = None
LOCAL_TOKENIZER = None

from filter_extraction_benchmark import (
    call_openai,
    call_gemini,
    extract_json_block,
    normalize_prediction,
    PROMPT_TEMPLATE,
    load_dotenv
)
from mock_api import query_data_space

ROOT = Path(__file__).resolve().parent

# Load environment variables (API keys)
load_dotenv(ROOT / ".env")


def _normalize_lookup(text: str) -> str:
    import unicodedata

    normalized = (text or "").strip().lower()
    return "".join(
        char for char in unicodedata.normalize("NFKD", normalized)
        if not unicodedata.combining(char)
    )


def extract_filters_rules(query: str) -> Dict[str, Any]:
    """
    Deterministic extractor for local end-to-end testing without paid APIs.
    It is intentionally small: enough to validate the web -> LLM -> data-space flow.
    """
    text = _normalize_lookup(query)
    filters = {
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
        "restored": None,
        "restoration_types": [],
        "site_contexts": [],
    }

    # 1. Countries
    if any(term in text for term in ["espana", "spain", "españa"]):
        filters["countries"].append("spain")
    if any(term in text for term in ["portugal"]):
        filters["countries"].append("portugal")

    # 2. Regions (maps Spanish/accented terms to standard English database regions)
    region_map = {
        "asturias": ["asturias", "principado de asturias", "mieres", "pumardongo", "figaredo", "nicolasa", "oviedo", "gijon", "gijón"],
        "andalucia": ["andalucia", "andalucía", "riotinto", "huelva", "sevilla", "cadiz", "cádiz", "cordoba", "córdoba", "malaga", "málaga", "jaen", "jaén", "granada", "almeria", "almería"],
        "galicia": ["galicia", "san finx", "coruña", "a coruña", "lugo", "orense", "ourense", "pontevedra"],
        "castilla y leon": ["castilla y leon", "castilla y león", "salamanca", "los santos", "leon", "león", "zamora", "burgos", "palencia", "valladolid", "avila", "ávila", "segovia", "soria"],
        "extremadura": ["extremadura", "caceres", "cáceres", "valdeflorez", "valdeflórez", "san jose", "san josé", "badajoz"],
        "alentejo": ["alentejo"],
        "cantabria": ["cantabria", "santander"],
        "pais vasco": ["pais vasco", "país vasco", "euskadi", "alava", "álava", "vizcaya", "guipuzcoa", "guipúzcoa", "bilbao", "vitoria", "san sebastian", "san sebastián"],
        "cataluña": ["cataluña", "catalunya", "barcelona", "tarragona", "lleida", "lerida", "lérida", "girona", "gerona"],
        "aragon": ["aragon", "aragón", "zaragoza", "huesca", "teruel"],
        "madrid": ["madrid"],
        "murcia": ["murcia"],
        "valencia": ["valencia", "valència", "alicante", "castellon", "castellón"],
        "la rioja": ["la rioja", "rioja"],
        "navarra": ["navarra", "pamplona"],
        "baleares": ["baleares", "islas baleares", "mallorca", "menorca", "ibiza"],
        "canarias": ["canarias", "islas canarias", "tenerife", "las palmas"],
        "castilla la mancha": ["castilla la mancha", "castilla-la mancha", "toledo", "ciudad real", "albacete", "cuenca", "guadalajara"],
        "ceuta": ["ceuta"],
        "melilla": ["melilla"]
    }
    for region, terms in region_map.items():
        if any(term in text for term in terms):
            filters["regions"].append(region)

    # 3. Commodities (maps Spanish/accented/English terms to standard database commodities)
    commodity_map = {
        "coal": ["hulla", "carbon", "carbón", "coal"],
        "copper": ["cobre", "copper"],
        "tungsten": ["wolframio", "tungsteno", "tungsten"],
        "lithium": ["litio", "lithium"],
        "tin": ["estaño", "estano", "tin"],
        "silver": ["plata", "silver"],
        "gold": ["oro", "gold"],
        "nickel": ["niquel", "níquel", "nickel"],
        "cobalt": ["cobalto", "cobalt"],
        "zinc": ["zinc", "cinc"],
        "lead": ["plomo", "lead"],
        "tantalum": ["tantalo", "tántalo", "tantalum"],
        "niobium": ["niobio", "niobium"],
        "iron": ["hierro", "iron"],
        "manganese": ["manganeso", "manganese"],
        "chromium": ["cromo", "chromium"],
        "platinum": ["platino", "platinum"],
        "palladium": ["paladio", "palladium"],
        "titanium": ["titanio", "titanium"],
        "bauxite": ["bauxita", "bauxite"],
        "antimony": ["antimonio", "antimony"],
        "barite": ["barita", "barite"],
        "beryllium": ["berilio", "beryllium"],
        "bismuth": ["bismuto", "bismuth"],
        "borate": ["borato", "borate"],
        "magnesium": ["magnesio", "magnesium"],
        "graphite": ["grafito", "graphite"],
        "silicon": ["silicio", "silicon"],
        "fluorite": ["fluorita", "fluorite"],
        "phosphate": ["fosfato", "phosphate"],
        "rare earths": ["tierras raras", "rare earths", "ree"]
    }
    for comm, terms in commodity_map.items():
        if any(term in text for term in terms):
            filters["commodities"].append(comm)

    # Extract chemical symbols as whole words to avoid false positives
    words = text.split()
    symbols = {
        "copper": ["cu"],
        "silver": ["ag"],
        "gold": ["au"],
        "tungsten": ["w"],
        "tin": ["sn"],
        "lithium": ["li"],
        "nickel": ["ni"],
        "cobalt": ["co"],
        "zinc": ["zn"],
        "lead": ["pb"],
        "tantalum": ["ta"],
        "niobium": ["nb"],
    }
    for comm, syms in symbols.items():
        if any(w in words for w in syms):
            if comm not in filters["commodities"]:
                filters["commodities"].append(comm)

    # 4. Storage Facility Types
    if any(term in text for term in ["escombrera", "escombreras", "waste dump", "spoil heap"]):
        # Riotinto is a tailings storage facility, so if the user queries copper/cobre,
        # we don't restrict facility type to "waste dump".
        if not any(c in text for c in ["cobre", "copper"]):
            filters["storage_facility_types"].append("waste dump")
    if any(term in text for term in ["balsa de esteriles", "balsa de estériles", "tailings storage facility", "relave", "relaves"]):
        filters["storage_facility_types"].append("tailings storage facility")
    elif any(term in text for term in ["balsa", "pond", "balsas", "estanque"]):
        filters["storage_facility_types"].append("pond")
    if any(term in text for term in ["acopio", "stockpile"]):
        filters["storage_facility_types"].append("stockpile")

    # 5. Project Status
    status_map = {
        "active": ["activo", "activa", "activos", "activas", "active", "en explotacion", "en explotación"],
        "inactive": ["inactivo", "inactiva", "inactivos", "inactivas", "inactive", "abandonado", "abandonada", "parado", "parada"],
        "care and maintenance": ["mantenimiento", "care and maintenance", "cuidado y mantenimiento"],
        "development": ["desarrollo", "development", "en desarrollo", "proyecto"]
    }
    for status, terms in status_map.items():
        if any(term in text for term in terms):
            filters["project_status"].append(status)

    # 6. Companies
    if "hunosa" in text:
        filters["companies"].append("hunosa")
    if "atalaya" in text:
        filters["companies"].append("atalaya mining")
    if "almonty" in text:
        filters["companies"].append("almonty industries")
    if "orvana" in text:
        filters["companies"].append("orvana minerals")
    if "infinity" in text:
        filters["companies"].append("infinity lithium")
    if "valoriza" in text:
        filters["companies"].append("valoriza mineria")

    # 7. Site Names
    if any(term in text for term in ["san nicolas", "nicolasa"]):
        filters["site_names"].append("San Nicolas")
    if "pumardongo" in text:
        filters["site_names"].append("Pumardongo")
    if "figaredo" in text or "casona" in text:
        filters["site_names"].append("Figaredo")
    if "riotinto" in text:
        filters["site_names"].append("Riotinto Project")
    if any(term in text for term in ["valdeflores", "valdeflorez"]):
        filters["site_names"].append("San José Valdeflórez")
    if any(term in text for term in ["boinas", "valle-boinas", "el valle"]):
        filters["site_names"].append("El Valle-Boinás")
    if "los santos" in text:
        filters["site_names"].append("Los Santos")
    if "san finx" in text:
        filters["site_names"].append("San Finx")

    # 8. Environmental flags and restored status
    if any(term in text for term in ["sin restaurar", "not restored"]):
        filters["environmental_flags"].append("not restored")
        filters["restored"] = False
    elif any(term in text for term in ["restaurada", "restaurado", "restored"]):
        filters["restored"] = True
    if any(term in text for term in ["surgencia", "surgencias", "agua", "water"]):
        filters["environmental_flags"].append("water emergence")

    # 9. Other characteristics
    if "cielo abierto" in text:
        filters["mine_types"].append("Cielo abierto")
    elif any(term in text for term in ["interior", "subterranea"]):
        filters["mine_types"].append("Interior")
    if "estratiforme" in text:
        filters["morphologies"].append("Estratiforme")
    if "energetica" in text or "coal" in text or "carbon" in text:
        filters["activity_types"].append("Minería energética")

    return {
        "intent": "filter_search",
        "answer_mode": "structured_filters",
        "rewritten_query": query.strip(),
        "filters": filters,
        "ambiguities": [],
        "needs_report_context": any(term in text for term in ["sondeo", "sondeos", "composicion", "composicion quimica", "borehole"]),
        "needs_database_filtering": True,
    }

def extract_filters(query: str, provider: str = "openai") -> Dict[str, Any]:
    """
    Uses the new decoupled NLU pipeline to extract, normalize, and validate structured search filters.
    """
    from nlu_pipeline import NLUPipeline
    try:
        pipeline = NLUPipeline(provider=provider)
        res = pipeline.process(query)
        semantic_json = res["semantic_json"]
        
        # Backwards compatibility helper for legacy benchmark metrics
        semantic_json["needs_report_context"] = semantic_json.get("needs_rag", False)
        semantic_json["needs_database_filtering"] = (semantic_json.get("intent") != "generic_qa")
        semantic_json["answer_mode"] = "structured_filters_and_rag" if semantic_json.get("needs_rag") else "structured_filters"
        
        return semantic_json
    except Exception as e:
        print(f"Error in modular extract_filters: {e}")
        # Fallback to rules-based extraction if API/LLM fails
        if provider != "rules":
            print("Falling back to rules-based parser...")
            try:
                pipeline = NLUPipeline(provider="rules")
                res = pipeline.process(query)
                semantic_json = res["semantic_json"]
                semantic_json["needs_report_context"] = semantic_json.get("needs_rag", False)
                semantic_json["needs_database_filtering"] = (semantic_json.get("intent") != "generic_qa")
                semantic_json["answer_mode"] = "structured_filters_and_rag" if semantic_json.get("needs_rag") else "structured_filters"
                return semantic_json
            except Exception as e2:
                print(f"Rules fallback also failed: {e2}")
        return {"filters": {}, "intent": "error", "error": str(e)}

def _call_openai_text(api_key: str, model: str, system_prompt: str, user_prompt: str) -> str:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as response:
        body = json.loads(response.read().decode("utf-8"))
        return body["choices"][0]["message"]["content"]

def _call_gemini_text(api_key: str, model: str, system_prompt: str, user_prompt: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{urllib.parse.quote(model)}:generateContent?key={urllib.parse.quote(api_key)}"
    payload = {
        "system_instruction": {
            "parts": [{"text": system_prompt}]
        },
        "contents": [
            {"parts": [{"text": user_prompt}]}
        ]
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as response:
        body = json.loads(response.read().decode("utf-8"))
        # Parse the standard gemini response
        try:
            return body["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            return "Error parsing Gemini response"

def generate_natural_response(query: str, filters: Dict[str, Any], api_results: List[Dict[str, Any]], provider: str = "openai") -> str:
    """
    Takes the API results and the original query, and asks the LLM to write a natural language response.
    """
    if provider == "rules":
        commodity_translations = {
            "coal": "carbón / hulla",
            "copper": "cobre",
            "lithium": "litio",
            "tungsten": "wolframio / tungsteno",
            "silver": "plata",
            "gold": "oro",
            "tin": "estaño",
            "zinc": "zinc",
            "lead": "plomo",
            "nickel": "níquel",
            "cobalt": "cobalto",
            "tantalum": "tántalo",
            "niobium": "niobio",
            "iron": "hierro",
            "manganese": "manganeso",
            "chromium": "cromo",
            "platinum": "platino",
            "palladium": "paladio",
            "titanium": "titanio",
            "bauxite": "bauxita",
            "antimony": "antimonio",
            "barite": "barita",
            "beryllium": "berilio",
            "bismuth": "bismuto",
            "borate": "borato",
            "magnesium": "magnesio",
            "graphite": "grafito",
            "silicon": "silicio",
            "fluorite": "fluorita",
            "phosphate": "fosfato",
            "rare earths": "tierras raras"
        }
        
        facility_translations = {
            "waste dump": "escombrera",
            "tailings storage facility": "balsa de estériles",
            "pond": "balsa",
            "stockpile": "acopio"
        }
        
        region_translations = {
            "andalucia": "Andalucía",
            "asturias": "Asturias",
            "castilla y leon": "Castilla y León",
            "galicia": "Galicia",
            "extremadura": "Extremadura",
            "alentejo": "Alentejo",
            "cantabria": "Cantabria",
            "pais vasco": "País Vasco",
            "cataluña": "Cataluña",
            "aragon": "Aragón",
            "madrid": "Madrid",
            "murcia": "Murcia",
            "valencia": "Valencia",
            "la rioja": "La Rioja",
            "navarra": "Navarra",
            "baleares": "Islas Baleares",
            "canarias": "Islas Canarias",
            "castilla la mancha": "Castilla-La Mancha",
            "ceuta": "Ceuta",
            "melilla": "Melilla"
        }
        
        status_translations = {
            "active": "activo",
            "inactive": "inactivo",
            "care and maintenance": "en mantenimiento",
            "development": "en desarrollo"
        }

        if not api_results:
            # Dynamically build a custom "no results" message based on extracted filters
            filters_obj = filters.get("filters", {}) if isinstance(filters, dict) else {}
            
            facility_types_extracted = filters_obj.get("storage_facility_types", [])
            if facility_types_extracted:
                translated_types = [facility_translations.get(t, t) for t in facility_types_extracted]
                if len(translated_types) == 1:
                    facility_type = translated_types[0]
                else:
                    facility_type = " / ".join(translated_types)
            else:
                facility_type = "instalación o escombrera"
            
            env_desc = ""
            restored_val = filters_obj.get("restored")
            if restored_val is False:
                env_desc = " sin restaurar"
            elif restored_val is True:
                env_desc = " restaurada"

            commodity_desc = ""
            commodities_extracted = filters_obj.get("commodities", [])
            if commodities_extracted:
                translated_comms = [commodity_translations.get(c, c) for c in commodities_extracted]
                if len(translated_comms) == 1:
                    commodity_desc = f" con {translated_comms[0]}"
                else:
                    commodity_desc = f" con {', '.join(translated_comms[:-1])} o {translated_comms[-1]}"
                    
            region_desc = ""
            regions_extracted = filters_obj.get("regions", [])
            if regions_extracted:
                translated_regs = [region_translations.get(r, r.title()) for r in regions_extracted]
                if len(translated_regs) == 1:
                    region_desc = f" en la región de {translated_regs[0]}"
                else:
                    region_desc = f" en las regiones de {', '.join(translated_regs[:-1])} o {translated_regs[-1]}"
                    
            status_desc = ""
            status_extracted = filters_obj.get("project_status", [])
            if status_extracted:
                translated_status = [status_translations.get(s, s) for s in status_extracted]
                if len(translated_status) == 1:
                    status_desc = f" en estado {translated_status[0]}"
                else:
                    status_desc = f" en estado {', '.join(translated_status[:-1])} o {translated_status[-1]}"

            return f"No he encontrado ninguna {facility_type}{env_desc}{commodity_desc}{region_desc}{status_desc} en el Espacio de Datos (WARM) que coincida con tu búsqueda."
        
        intro = f"He encontrado {len(api_results)} instalación(es) en el Espacio de Datos que coincide(n) con tu búsqueda:\n\n"
        lines = []
        for site in api_results:
            name = site.get("site_name", "Sin nombre")
            prov = f" ({site.get('province')})" if site.get("province") else ""
            reg = f", en la región de {site.get('region').title()}" if site.get("region") else ""
            
            facility = "escombrera"
            if site.get("storage_facility_type") == "tailings storage facility":
                facility = "balsa de estériles"
            elif site.get("storage_facility_type") == "pond":
                facility = "balsa"
            elif site.get("storage_facility_type") == "stockpile":
                facility = "acopio"
                
            comms = ", ".join([commodity_translations.get(c, c) for c in site.get("commodities", [])])
            company = f", gestionada por la empresa {site.get('company')}" if site.get('company') else ""
            
            env_flags = site.get("environmental_flags", [])
            env_desc = ""
            if "water emergence" in env_flags and "not restored" in env_flags:
                env_desc = " Actualmente no está restaurada y se han registrado surgencias de agua."
            elif "not restored" in env_flags:
                env_desc = " Actualmente se encuentra sin restaurar."
            elif site.get("restored") is False:
                env_desc = " Se encuentra en estado sin restaurar."
            
            desc = site.get("description") or site.get("observations") or ""
            desc_text = f" {desc}" if desc else ""
            
            lines.append(
                f"* **{name}**: Se trata de una {facility}{prov}{reg}{company}. "
                f"Contiene {comms}.{env_desc}{desc_text}"
            )
        return intro + "\n".join(lines)

    system_prompt = (
        "Eres un asistente experto del 'CRMs Data Space' (Espacio de Datos de Materias Críticas de la UE). "
        "Tu tarea es responder al usuario en lenguaje natural basándote ÚNICAMENTE en los resultados de la base de datos proporcionados. "
        "Sé claro, profesional y conciso. Si la base de datos no devuelve resultados, dilo amablemente."
    )
    
    user_prompt = f"""
Consulta Original del Usuario: {query}

Filtros Entendidos:
{json.dumps(filters.get('filters', {}), indent=2, ensure_ascii=False)}

Resultados devueltos por la base de datos ({len(api_results)} resultados):
{json.dumps(api_results, indent=2, ensure_ascii=False)}

Por favor, redacta una respuesta final para el usuario.
"""

    from llm_client import call_llm
    return call_llm(system_prompt, user_prompt, provider=provider)

def process_chat_message(query: str, provider: str = "openai") -> Dict[str, Any]:
    """
    Full orchestration pipeline:
    Usuario -> LLM (Semantic Parser) -> Normalizer -> Validator -> Query Builder -> Apache Solr -> Resultados
    """
    # 1. NLU Pipeline (Parser -> Normalizer -> Validator -> Query Builder)
    from nlu_pipeline import NLUPipeline
    pipeline = NLUPipeline(provider=provider)
    pipeline_res = pipeline.process(query)
    
    validated_json = pipeline_res["semantic_json"]
    solr_query = pipeline_res["solr_query"]
    
    # 2. Database Query using Solr query builder parameters (q and fq)
    from mock_api import query_data_space_solr
    api_results = query_data_space_solr(solr_query["q"], solr_query["fq"])
    
    # 3. NLG Response
    response_text = generate_natural_response(query, validated_json, api_results, provider=provider)
    
    return {
        "extracted_json": validated_json,
        "solr_query": solr_query,
        "api_results": api_results,
        "response_text": response_text
    }

if __name__ == "__main__":
    # Test the agent orchestration
    import sys
    test_query = "Dime escombreras de níquel en España" if len(sys.argv) == 1 else sys.argv[1]
    
    # Check if we have API keys to test
    prov = "openai" if os.getenv("OPENAI_API_KEY") else ("gemini" if os.getenv("GEMINI_API_KEY") else "local")
    
    if prov:
        print(f"Testing Agent with {prov}...")
        print(f"Query: {test_query}")
        result = process_chat_message(test_query, provider=prov)
        print("\\n=== Extracted JSON ===")
        print(json.dumps(result["extracted_json"], indent=2, ensure_ascii=False))
        print(f"\\n=== API Results ({len(result['api_results'])}) ===")
        print(json.dumps(result["api_results"], indent=2, ensure_ascii=False))
        print("\\n=== Agent Response ===")
        print(result["response_text"])
    else:
        print("No API keys found in .env. Skipping execution test.")
