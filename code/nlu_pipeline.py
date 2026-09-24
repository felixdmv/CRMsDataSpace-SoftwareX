"""
NLU Pipeline module for SoftwareX:
Combines Variant 1 (Few-Shot Intent & Filter Extraction) with Variant 3 (Strict JSON Schema Enforcement).
"""

import json
from typing import Dict, Any, List

# ----------------------------------------------------------------------
# 1. Variant 3: OpenAPI / Gemini Structured JSON Schemas
# ----------------------------------------------------------------------
NLU_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "intent": {
            "type": "STRING",
            "description": "Query intent: filter_search for database search, or generic_qa for general conversation, greetings, help, and conceptual definitions",
            "enum": ["filter_search", "generic_qa", "hybrid"]
        },
        "filters": {
            "type": "OBJECT",
            "properties": {
                "countries": {"type": "ARRAY", "items": {"type": "STRING"}},
                "regions": {"type": "ARRAY", "items": {"type": "STRING"}},
                "commodities": {"type": "ARRAY", "items": {"type": "STRING"}},
                "storage_facility_types": {"type": "ARRAY", "items": {"type": "STRING"}},
                "material_types": {"type": "ARRAY", "items": {"type": "STRING"}},
                "project_status": {"type": "ARRAY", "items": {"type": "STRING"}},
                "environmental_flags": {"type": "ARRAY", "items": {"type": "STRING"}},
                "restored": {"type": "BOOLEAN"}
            }
        },
        "fulltext": {"type": "ARRAY", "items": {"type": "STRING"}},
        "unsupported_countries": {"type": "ARRAY", "items": {"type": "STRING"}},
        "needs_rag": {"type": "BOOLEAN"}
    },
    "required": ["intent", "filters", "fulltext", "needs_rag"]
}

# ----------------------------------------------------------------------
# 2. Variant 1: Few-Shot System Prompt
# ----------------------------------------------------------------------
SYSTEM_PROMPT_FEWSHOT = """You are an expert deterministic Semantic Parser for the European Critical Raw Materials (CRMs) Data Space.
Your task is to translate user natural language queries (in English or Spanish) into a clean, structured JSON search query for Apache Solr and Leaflet GIS visualization.

--- INTENT TAXONOMY ---
1. "filter_search": Use ONLY when the user is searching, filtering, locating, or querying specific European mining assets or waste deposits by physical/geographical criteria (countries, commodities, facility types, operational status, restoration).
2. "generic_qa": Use for:
   - Greetings & Social Openers: "Hola", "Hello", "Buenos días", "Buenas tardes", "Hi".
   - System Capabilities & Onboarding: "hola, en que me puedes ayudar", "¿qué puedes hacer?", "how can this system assist me?", "¿cómo funciona?", "ayuda".
   - Conceptual & Regulatory Definitions: Questions explaining mining concepts or regulatory frameworks without searching specific site locations (e.g., "¿Qué diferencia técnica existe entre una balsa y una escombrera?", "¿Qué es la Directiva 2006/21/CE?", "Explain UNFC vs JORC classification", "What causes Acid Mine Drainage (AMD)?").
   - Vague or conversational inputs without concrete filter criteria.
   CRITICAL RULE: Whenever intent is "generic_qa", the "filters" object MUST be empty: {} and "fulltext": [].

--- GEOGRAPHICAL SCOPE & COUNTRY BOUNDARIES ---
- The European CRMs Data Space is STRICTLY RESTRICTED to 12 European Union Member States:
  ["austria", "czechia", "finland", "france", "germany", "greece", "ireland", "italy", "poland", "portugal", "spain", "sweden"]
- Non-EU or out-of-scope countries (e.g. Albania, United Kingdom, USA, Chile, China, Russia, Norway, Switzerland, Morocco):
  * NEVER include them in filters["countries"].
  * If a query mentions an out-of-scope country alongside valid EU countries (e.g. "paises del sur de europa como grecia o albania que tengan niquel"):
    extract the valid country into filters["countries"] (["greece"]) and record the unsupported country in "unsupported_countries": ["albania"].
  * If ALL mentioned countries are out of scope (e.g. "minas de litio en Chile"), keep filters["countries"] as [] and record in "unsupported_countries": ["chile"].
- Macro-regions:
  * "sur de europa" / "southern europe": includes valid EU member states in Southern Europe: ["spain", "portugal", "italy", "greece"].
  * "norte de europa" / "northern europe": ["sweden", "finland"].

Allowed filter fields and domain mapping rules:
- countries: lowercase English country names from the 12 EU member states.
- commodities: lowercase English raw materials:
  * Rare Earth Elements: "rare earth elements" (use this exact string for any mention of "rare earth elements", "rare earths", "REE", "tierras raras", "elementos raros", "minerales raros")
  * Tungsten: "tungsten" (use for "tungsten", "wolfram", "wolframio", "tungsteno", "w")
  * Lithium: "lithium" (use for "lithium", "litio", "li")
  * Cobalt: "cobalt" (use for "cobalt", "cobalto", "co")
  * Nickel: "nickel" (use for "nickel", "niquel", "níquel", "ni")
  * Copper: "copper" (use for "copper", "cobre", "cu")
  * Tin: "tin" (use for "tin", "estaño", "estano", "sn")
  * Tantalum: "tantalum" (use for "tantalum", "tántalo", "tantalo", "coltan", "coltán", "ta")
  * Graphite: "graphite" (use for "graphite", "grafito")
  * Titanium: "titanium" (use for "titanium", "titanio", "ti")
  * Platinum Group Elements: "pge" (use for "pge", "platinum", "platino", "platinum group elements")
  * Manganese: "manganese" (use for "manganese", "manganeso", "mn")
- storage_facility_types: asset types:
  Allowed values: ["tailings storage facility", "waste dump", "stockpile", "pond"]
  * "tailings ponds" or "balsas de relaves" -> ["pond", "tailings storage facility"]
  * "ponds" / "balsas" -> ["pond"]
  * "waste dumps" / "escombreras" -> ["waste dump"]
  * "stockpiles" / "acopios" -> ["stockpile"]
  * IMPORTANT: Words like "facilities", "sites", "instalaciones", "plantas", "minas", "mines" are generic and MUST NOT be added to storage_facility_types (leave storage_facility_types as []).
- project_status: status e.g. ["active", "inactive", "care and maintenance", "development"]
- restored: true | false
- environmental_flags: e.g. ["acid mine drainage potential", "water emergence", "social opposition", "not restored"]
  * "unrestored", "sin restaurar", "no restaurada" -> set "restored": false and "environmental_flags": ["not restored"]
  * "restored", "restaurada" -> set "restored": true

--- FEW-SHOT EXAMPLES ---

Example 1 (Greeting):
User Query: "hola"
JSON Output:
{
  "intent": "generic_qa",
  "filters": {},
  "fulltext": [],
  "needs_rag": false
}

Example 2 (Help & Capabilities):
User Query: "hola, en que me puedes ayudar"
JSON Output:
{
  "intent": "generic_qa",
  "filters": {},
  "fulltext": [],
  "needs_rag": false
}

Example 3 (Conceptual Technical Question):
User Query: "¿Qué diferencia técnica existe entre una balsa de decantación y una escombrera de roca estéril?"
JSON Output:
{
  "intent": "generic_qa",
  "filters": {},
  "fulltext": [],
  "needs_rag": true
}

Example 4 (Regulatory Question):
User Query: "¿Cuál es la normativa europea sobre gestión de residuos de las industrias extractivas (Directiva 2006/21/CE)?"
JSON Output:
{
  "intent": "generic_qa",
  "filters": {},
  "fulltext": [],
  "needs_rag": true
}

Example 5 (Incongruent / Out-of-Scope Country Handling):
User Query: "paises del sur de europa como grecia o albania que tengan niquel"
JSON Output:
{
  "intent": "filter_search",
  "filters": {
    "countries": ["greece"],
    "commodities": ["nickel"],
    "storage_facility_types": []
  },
  "fulltext": [],
  "unsupported_countries": ["albania"],
  "needs_rag": false
}

Example 6 (Standard Multi-Filter Search):
User Query: "Show active lithium and cobalt waste dumps in Spain and Finland"
JSON Output:
{
  "intent": "filter_search",
  "filters": {
    "countries": ["spain", "finland"],
    "commodities": ["lithium", "cobalt"],
    "storage_facility_types": ["waste dump"],
    "project_status": ["active"]
  },
  "fulltext": [],
  "needs_rag": false
}

Example 7 (Unrestored Tailings Ponds):
User Query: "Unrestored tungsten tailings ponds in Germany"
JSON Output:
{
  "intent": "filter_search",
  "filters": {
    "countries": ["germany"],
    "commodities": ["tungsten"],
    "storage_facility_types": ["pond", "tailings storage facility"],
    "restored": false,
    "environmental_flags": ["not restored"]
  },
  "fulltext": [],
  "needs_rag": false
}

Example 8 (Rare Earths in Sweden):
User Query: "Instalaciones de elementos raros y tierras raras en Suecia"
JSON Output:
{
  "intent": "filter_search",
  "filters": {
    "countries": ["sweden"],
    "commodities": ["rare earth elements"],
    "storage_facility_types": []
  },
  "fulltext": [],
  "needs_rag": false
}

CRITICAL: Output ONLY the valid JSON object. Do not include markdown reasoning, notes, or extra conversation turns.
"""

# ----------------------------------------------------------------------
# 3. Pipeline Stages: Normalizer, Validator, QueryBuilder
# ----------------------------------------------------------------------

class Normalizer:
    """Normalizes extracted raw LLM JSON tokens into canonical Solr terms."""
    
    COMMODITY_MAP = {
        # Rare Earth Elements & Synonyms
        "rare earth elements": "rare earth elements",
        "rare earth elements (ree)": "rare earth elements",
        "rare earths": "rare earth elements",
        "rare earth": "rare earth elements",
        "tierras raras": "rare earth elements",
        "tierra rara": "rare earth elements",
        "elementos raros": "rare earth elements",
        "elemento raro": "rare earth elements",
        "minerales raros": "rare earth elements",
        "ree": "rare earth elements",
        "rees": "rare earth elements",
        # Tungsten
        "tungsten": "tungsten", "wolframio": "tungsten", "wolfram": "tungsten", "tungsteno": "tungsten",
        # Lithium & Cobalt
        "lithium": "lithium", "litio": "lithium",
        "cobalt": "cobalt", "cobalto": "cobalt",
        # Base & Special Metals
        "nickel": "nickel", "niquel": "nickel", "níquel": "nickel",
        "copper": "copper", "cobre": "copper",
        "tin": "tin", "estaño": "tin", "estano": "tin",
        "tantalum": "tantalum", "tantalo": "tantalum", "tántalo": "tantalum", "coltan": "tantalum", "coltán": "tantalum",
        "graphite": "graphite", "grafito": "graphite",
        "titanium": "titanium", "titanio": "titanium",
        "manganese": "manganese", "manganeso": "manganese",
        "pge": "pge", "platino": "pge", "platinum": "pge", "platinum group elements": "pge"
    }

    COUNTRY_MAP = {
        "españa": "spain", "espana": "spain", "spain": "spain", "spanish": "spain",
        "alemania": "germany", "germany": "germany", "german": "germany",
        "francia": "france", "france": "france", "french": "france",
        "suecia": "sweden", "sweden": "sweden", "swedish": "sweden",
        "finlandia": "finland", "finland": "finland", "finnish": "finland",
        "polonia": "poland", "poland": "poland", "polish": "poland",
        "italia": "italy", "italy": "italy", "italian": "italy",
        "grecia": "greece", "greece": "greece", "greek": "greece",
        "irlanda": "ireland", "ireland": "ireland", "irish": "ireland",
        "austria": "austria", "austrian": "austria",
        "portugal": "portugal", "portuguese": "portugal", "portugués": "portugal",
        "chequia": "czechia", "república checa": "czechia", "republica checa": "czechia", "czechia": "czechia", "czech": "czechia"
    }

    GENERIC_FACILITY_TERMS = {
        "facility", "facilities", "site", "sites", "plant", "plants",
        "instalacion", "instalaciones", "instalación", "mina", "minas",
        "mine", "mines", "all", "deposit", "deposits", "depósito", "depósitos"
    }

    FACILITY_MAP = {
        "tailings storage facility": ["tailings storage facility"],
        "tailings": ["tailings storage facility"],
        "relave": ["tailings storage facility"],
        "relaves": ["tailings storage facility"],
        "tsf": ["tailings storage facility"],
        "waste dump": ["waste dump"],
        "dump": ["waste dump"],
        "dumps": ["waste dump"],
        "escombrera": ["waste dump"],
        "escombreras": ["waste dump"],
        "vertedero": ["waste dump"],
        "pond": ["pond"],
        "ponds": ["pond"],
        "balsa": ["pond"],
        "balsas": ["pond"],
        "decantacion": ["pond"],
        "decantación": ["pond"],
        "tailings pond": ["pond", "tailings storage facility"],
        "tailings ponds": ["pond", "tailings storage facility"],
        "balsas de relaves": ["pond", "tailings storage facility"],
        "balsa de relaves": ["pond", "tailings storage facility"],
        "stockpile": ["stockpile"],
        "stockpiles": ["stockpile"],
        "acopio": ["stockpile"],
        "acopios": ["stockpile"]
    }

    def normalize(self, raw_json: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(raw_json, dict):
            raw_json = {}
            
        filters = raw_json.get("filters", {})
        if not isinstance(filters, dict):
            filters = {}
            
        # 1. Normalize commodities with dictionary and robust fuzzy patterns
        norm_comms = []
        for c in filters.get("commodities", []):
            c_clean = str(c).lower().strip()
            # Direct mapping
            c_mapped = self.COMMODITY_MAP.get(c_clean)
            if not c_mapped:
                # Fuzzy checks for REE / Rare Earths / Elementos Raros
                if any(term in c_clean for term in ["rare earth", "tierras rara", "tierra rara", "elementos raro", "elemento raro", "ree"]):
                    c_mapped = "rare earth elements"
                elif any(term in c_clean for term in ["wolfram", "tungsten"]):
                    c_mapped = "tungsten"
                elif "liti" in c_clean or "lith" in c_clean:
                    c_mapped = "lithium"
                elif "cobalt" in c_clean:
                    c_mapped = "cobalt"
                elif "niquel" in c_clean or "níquel" in c_clean or "nickel" in c_clean:
                    c_mapped = "nickel"
                elif "cobre" in c_clean or "copper" in c_clean:
                    c_mapped = "copper"
                elif "estañ" in c_clean or "tin" == c_clean:
                    c_mapped = "tin"
                elif "tantal" in c_clean or "coltan" in c_clean or "coltán" in c_clean:
                    c_mapped = "tantalum"
                elif "grafit" in c_clean or "graphite" in c_clean:
                    c_mapped = "graphite"
                elif "titan" in c_clean:
                    c_mapped = "titanium"
                elif "mangan" in c_clean:
                    c_mapped = "manganese"
                elif "platin" in c_clean or "pge" in c_clean:
                    c_mapped = "pge"
                else:
                    c_mapped = c_clean

            if c_mapped and c_mapped not in norm_comms:
                norm_comms.append(c_mapped)
        filters["commodities"] = norm_comms

        # 2. Normalize countries
        norm_countries = []
        for co in filters.get("countries", []):
            co_clean = str(co).lower().strip()
            co_mapped = self.COUNTRY_MAP.get(co_clean, co_clean)
            if co_mapped not in norm_countries:
                norm_countries.append(co_mapped)
        filters["countries"] = norm_countries

        # 3. Normalize storage facility types (filter out generic "facilities" and map specific types)
        norm_facilities = []
        for sf in filters.get("storage_facility_types", []):
            sf_clean = str(sf).lower().strip()
            if sf_clean in self.GENERIC_FACILITY_TERMS:
                continue
            mapped_types = self.FACILITY_MAP.get(sf_clean)
            if mapped_types:
                for mt in mapped_types:
                    if mt not in norm_facilities:
                        norm_facilities.append(mt)
            elif sf_clean in ["pond", "stockpile", "tailings storage facility", "waste dump"]:
                if sf_clean not in norm_facilities:
                    norm_facilities.append(sf_clean)
        filters["storage_facility_types"] = norm_facilities

        # 4. Normalize restoration boolean and environmental flags
        if "restored" in filters and filters["restored"] is not None:
            val = filters["restored"]
            if isinstance(val, str):
                filters["restored"] = val.lower() in ["true", "1", "yes", "si", "sí"]
            else:
                filters["restored"] = bool(val)

        env_flags = filters.get("environmental_flags", [])
        if not isinstance(env_flags, list):
            env_flags = [str(env_flags)]
        if filters.get("restored") is False and "not restored" not in env_flags:
            env_flags.append("not restored")
        filters["environmental_flags"] = env_flags

        raw_json["filters"] = filters
        return raw_json

class Validator:
    """Ensures structure compliance and fills missing default keys."""
    
    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        intent = data.get("intent", "filter_search")
        if intent not in ["filter_search", "generic_qa", "hybrid"]:
            intent = "filter_search"
            
        filters = data.get("filters", {})
        validated_filters = {
            "countries": filters.get("countries", []),
            "regions": filters.get("regions", []),
            "commodities": filters.get("commodities", []),
            "storage_facility_types": filters.get("storage_facility_types", []),
            "material_types": filters.get("material_types", []),
            "project_status": filters.get("project_status", []),
            "environmental_flags": filters.get("environmental_flags", []),
            "restored": filters.get("restored", None)
        }
        
        return {
            "intent": intent,
            "filters": validated_filters,
            "fulltext": data.get("fulltext", []),
            "unsupported_countries": data.get("unsupported_countries", []),
            "needs_rag": data.get("needs_rag", False)
        }

class QueryBuilder:
    """Translates normalized NLU JSON into canonical Apache Solr filter queries (fq) and query string (q)."""
    
    def build(self, validated_nlu: Dict[str, Any]) -> Dict[str, Any]:
        filters = validated_nlu.get("filters", {})
        fq_list = []

        if filters.get("countries"):
            c_str = " OR ".join(f'"{c}"' for c in filters["countries"])
            fq_list.append(f"country:({c_str})")

        if filters.get("regions"):
            r_str = " OR ".join(f'"{r}"' for r in filters["regions"])
            fq_list.append(f"region:({r_str})")

        if filters.get("commodities"):
            cm_str = " OR ".join(f'"{cm}"' for cm in filters["commodities"])
            fq_list.append(f"commodities:({cm_str})")

        if filters.get("storage_facility_types"):
            sf_str = " OR ".join(f'"{sf}"' for sf in filters["storage_facility_types"])
            fq_list.append(f"storage_facility_type:({sf_str})")

        if filters.get("project_status"):
            st_str = " OR ".join(f'"{st}"' for st in filters["project_status"])
            fq_list.append(f"project_status:({st_str})")

        if filters.get("restored") is not None:
            fq_list.append(f"restored:{str(filters['restored']).lower()}")

        fulltext_terms = validated_nlu.get("fulltext", [])
        unsupported = [c.lower() for c in validated_nlu.get("unsupported_countries", [])]
        search_terms = [t for t in fulltext_terms if t.lower() not in unsupported]
        q = " AND ".join(search_terms) if search_terms else "*:*"

        return {
            "q": q,
            "fq": fq_list,
            "defType": "edismax",
            "qf": "site_name^2.0 commodities^1.5 description^1.0",
            "fl": "id,site_name,country,region,commodities,storage_facility_type,location,project_status",
            "rows": 100
        }
