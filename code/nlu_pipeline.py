"""
NLU Pipeline module for SoftwareX:
Combines Variant 1 (Few-Shot Intent & Filter Extraction) with Variant 3 (Strict JSON Schema Enforcement).
"""

import json
import re
from typing import Dict, Any, List, Optional, Tuple

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
        "dialogue_action": {
            "type": "STRING",
            "description": "Dialogue state action: new_search (default), expand (additive OR), refine (narrowing AND), remove (exclusion), or reset",
            "enum": ["new_search", "expand", "refine", "remove", "reset"]
        },
        "filters": {
            "type": "OBJECT",
            "properties": {
                "countries": {"type": "ARRAY", "items": {"type": "STRING"}},
                "regions": {"type": "ARRAY", "items": {"type": "STRING"}},
                "commodities": {"type": "ARRAY", "items": {"type": "STRING"}},
                "commodity_operator": {"type": "STRING", "enum": ["AND", "OR", "COMPOUND"]},
                "commodities_and": {"type": "ARRAY", "items": {"type": "STRING"}},
                "commodities_or": {"type": "ARRAY", "items": {"type": "STRING"}},
                "storage_facility_types": {"type": "ARRAY", "items": {"type": "STRING"}},
                "material_types": {"type": "ARRAY", "items": {"type": "STRING"}},
                "project_status": {"type": "ARRAY", "items": {"type": "STRING"}},
                "environmental_flags": {"type": "ARRAY", "items": {"type": "STRING"}},
                "restored": {"type": "BOOLEAN"}
            }
        },
        "remove_filters": {
            "type": "OBJECT",
            "properties": {
                "countries": {"type": "ARRAY", "items": {"type": "STRING"}},
                "commodities": {"type": "ARRAY", "items": {"type": "STRING"}},
                "storage_facility_types": {"type": "ARRAY", "items": {"type": "STRING"}},
                "project_status": {"type": "ARRAY", "items": {"type": "STRING"}},
                "environmental_flags": {"type": "ARRAY", "items": {"type": "STRING"}}
            }
        },
        "fulltext": {"type": "ARRAY", "items": {"type": "STRING"}},
        "unsupported_countries": {"type": "ARRAY", "items": {"type": "STRING"}},
        "needs_rag": {"type": "BOOLEAN"}
    },
    "required": ["intent", "filters", "fulltext", "needs_rag"]
}

# ----------------------------------------------------------------------
# 2. Variant 1: Few-Shot System Prompt with Conversational Memory (DST)
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

--- CONVERSATIONAL MEMORY & DIALOGUE STATE TRACKING (DST) ---
When previous conversation context and active filters are present, determine the "dialogue_action":
- "new_search": Default for independent search queries that establish new criteria from scratch.
- "expand": Additive expansion (OR). Used when the user adds more items to an existing dimension without dropping previous ones.
  Triggers: "y además", "y ademas", "también", "y en", "y las de", "añade", "agrega", "and also", "additionally", "as well as", "plus".
- "refine": Progressive narrowing (AND). Used when the user filters down previous results by specifying constraints on new dimensions.
  Triggers: "de esas, solo las que...", "de estas", "de los anteriores", "solo las que contengan", "únicamente", "acota a", "of those", "from these", "only those with".
- "remove": Exclusion / subtraction. Used when the user explicitly requests to drop or exclude specific entities from the active filters.
  Triggers: "ahora quita...", "elimina las de...", "descarta...", "sin...", "excepto...", "remove", "drop", "without", "exclude".
  In this case, put the targets to drop in "remove_filters" or "filters".
- "reset": Clearing conversation memory and starting over from scratch.
  Triggers: "empezar de nuevo", "nueva búsqueda", "limpiar", "borrar filtros", "reset", "start over", "clear".

--- GEOGRAPHICAL SCOPE & GEO-ENTITY GROUNDING ---
- The European CRMs Data Space is STRICTLY RESTRICTED to 12 European Union Member States:
  ["austria", "czechia", "finland", "france", "germany", "greece", "ireland", "italy", "poland", "portugal", "spain", "sweden"]
- Cities and regions must be resolved to their canonical EU Member State:
  * "paris" / "parís" -> "france"
  * "berlin" / "berlín" / "munich" / "frankfurt" -> "germany"
  * "madrid" / "barcelona" / "sevilla" / "galicia" -> "spain"
  * "lisboa" / "lisbon" / "porto" -> "portugal"
  * "roma" / "rome" / "milano" -> "italy"
  * "stockholm" / "estocolmo" / "kiruna" -> "sweden"
  * "helsinki" / "espoo" -> "finland"
  * "warsaw" / "varsovia" / "krakow" -> "poland"
  * "vienna" / "viena" -> "austria"
  * "athens" / "atenas" -> "greece"
  * "dublin" / "dublín" -> "ireland"
  * "prague" / "praga" -> "czechia"
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
  * Rare Earth Elements: "rare earth elements" (use for "rare earth elements", "rare earths", "REE", "tierras raras", "elementos raros", "minerales raros")
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
  * MULTI-ELEMENT BOOLEAN LOGIC (AND vs OR):
    - Conjunction (Both together / AND): When query asks for deposits containing multiple elements simultaneously (e.g., "escombreras en españa con litio y estaño", "facilities with lithium and cobalt", "ambos elementos", "juntos"): set "commodity_operator": "AND", "commodities_and": [elements], "commodities": [elements].
    - Disjunction (Either / OR): When query asks for deposits with either element separately (e.g., "litio o estaño", "lithium or tin", "por separado"): set "commodity_operator": "OR", "commodities_or": [elements], "commodities": [elements].
    - Compound: When query mixes both (e.g. "litio o (estaño y cobalto)"): set "commodity_operator": "COMPOUND", "commodities_or": ["lithium"], "commodities_and": ["tin", "cobalt"].
- storage_facility_types: asset types:
  Allowed values: ["tailings storage facility", "waste dump", "stockpile", "pond"]
  * "tailings ponds" or "balsas de relaves" -> ["pond", "tailings storage facility"]
  * "ponds" / "balsas" -> ["pond"]
  * "waste dumps" / "escombreras" -> ["waste dump"]
  * "stockpiles" / "acopios" -> ["stockpile"]
  * IMPORTANT: Words like "facilities", "sites", "instalaciones", "plantas", "minas", "mines" are generic and MUST NOT be added to storage_facility_types.
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
  "dialogue_action": "new_search",
  "filters": {},
  "fulltext": [],
  "needs_rag": false
}

Example 2 (Help & Capabilities):
User Query: "hola, en que me puedes ayudar"
JSON Output:
{
  "intent": "generic_qa",
  "dialogue_action": "new_search",
  "filters": {},
  "fulltext": [],
  "needs_rag": false
}

Example 3 (Multi-turn Sequence - Turn 1 Initial City Grounding):
User Query: "dime escombreras cerca de paris"
JSON Output:
{
  "intent": "filter_search",
  "dialogue_action": "new_search",
  "filters": {
    "countries": ["france"],
    "commodities": [],
    "storage_facility_types": ["waste dump"]
  },
  "fulltext": [],
  "needs_rag": false
}

Example 4 (Multi-turn Sequence - Turn 2 Additive Expansion):
Active Filters: {"countries": ["france"], "storage_facility_types": ["waste dump"]}
User Query: "y ademas las que esten cerca de berlin"
JSON Output:
{
  "intent": "filter_search",
  "dialogue_action": "expand",
  "filters": {
    "countries": ["germany"]
  },
  "fulltext": [],
  "needs_rag": false
}

Example 5 (Multi-turn Sequence - Turn 3 Progressive Refinement with Conjunction AND):
Active Filters: {"countries": ["france", "germany"], "storage_facility_types": ["waste dump"]}
User Query: "de esas, solo las que contengan litio y cobalto"
JSON Output:
{
  "intent": "filter_search",
  "dialogue_action": "refine",
  "filters": {
    "commodities": ["lithium", "cobalt"],
    "commodity_operator": "AND",
    "commodities_and": ["lithium", "cobalt"],
    "commodities_or": []
  },
  "fulltext": [],
  "needs_rag": false
}

Example 5b (Independent Search with Active Filters - Standalone Query):
Active Filters: {"countries": ["spain", "germany"], "storage_facility_types": ["waste dump"], "project_status": ["active"]}
User Query: "show all facilities of lithium or cobalt in finland"
JSON Output:
{
  "intent": "filter_search",
  "dialogue_action": "new_search",
  "filters": {
    "countries": ["finland"],
    "commodities": ["lithium", "cobalt"],
    "commodity_operator": "OR",
    "commodities_or": ["lithium", "cobalt"],
    "commodities_and": [],
    "storage_facility_types": [],
    "project_status": []
  },
  "fulltext": [],
  "needs_rag": false
}

Example 6 (Multi-turn Sequence - Turn 4 Subtraction / Removal):
Active Filters: {"countries": ["france", "germany"], "commodities": ["lithium", "cobalt"], "storage_facility_types": ["waste dump"]}
User Query: "ahora quita las de cobalto"
JSON Output:
{
  "intent": "filter_search",
  "dialogue_action": "remove",
  "filters": {
    "commodities": ["cobalt"]
  },
  "remove_filters": {
    "commodities": ["cobalt"]
  },
  "fulltext": [],
  "needs_rag": false
}

Example 7 (Multi-turn Sequence - Turn 5 Reset):
User Query: "empezar de nuevo"
JSON Output:
{
  "intent": "filter_search",
  "dialogue_action": "reset",
  "filters": {},
  "fulltext": [],
  "needs_rag": false
}

Example 8 (Incongruent / Out-of-Scope Country Handling):
User Query: "paises del sur de europa como grecia o albania que tengan niquel"
JSON Output:
{
  "intent": "filter_search",
  "dialogue_action": "new_search",
  "filters": {
    "countries": ["greece"],
    "commodities": ["nickel"],
    "storage_facility_types": []
  },
  "fulltext": [],
  "unsupported_countries": ["albania"],
  "needs_rag": false
}

Example 9 (Unrestored Tailings Ponds):
User Query: "Unrestored tungsten tailings ponds in Germany"
JSON Output:
{
  "intent": "filter_search",
  "dialogue_action": "new_search",
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
        "tantalum": "tantalum", "tantalo": "tantalum", "tántalo": "tantalum", "tantalio": "tantalum", "coltan": "tantalum", "coltán": "tantalum",
        "graphite": "graphite", "grafito": "graphite",
        "titanium": "titanium", "titanio": "titanium",
        "manganese": "manganese", "manganeso": "manganese",
        "pge": "pge", "platino": "pge", "platinum": "pge", "paladio": "pge", "palladium": "pge", "platinum group elements": "pge",
        "germanium": "germanium", "germanio": "germanium",
        "gallium": "gallium", "galio": "gallium"
    }

    CITY_COUNTRY_MAP = {
        # France
        "paris": "france", "parís": "france", "lyon": "france", "marseille": "france", "marsella": "france",
        "toulouse": "france", "bordeaux": "france", "burdeos": "france", "nantes": "france", "lille": "france",
        # Germany
        "berlin": "germany", "berlín": "germany", "munich": "germany", "múnich": "germany", "muenchen": "germany",
        "frankfurt": "germany", "hamburg": "germany", "hamburgo": "germany", "cologne": "germany", "colonia": "germany",
        "stuttgart": "germany", "dresden": "germany", "dusseldorf": "germany", "düsseldorf": "germany",
        "hannover": "germany", "leipzig": "germany", "nuremberg": "germany",
        # Spain
        "madrid": "spain", "barcelona": "spain", "sevilla": "spain", "valencia": "spain", "ourense": "spain",
        "zamora": "spain", "salamanca": "spain", "huelva": "spain", "asturias": "spain", "oviedo": "spain",
        "leon": "spain", "león": "spain", "bilbao": "spain", "zaragoza": "spain", "caceres": "spain", "cáceres": "spain",
        "badajoz": "spain", "andalucia": "spain", "andalucía": "spain", "galicia": "spain",
        # Portugal
        "lisboa": "portugal", "lisbon": "portugal", "porto": "portugal", "oporto": "portugal", "braga": "portugal", "coimbra": "portugal",
        # Italy
        "roma": "italy", "rome": "italy", "milan": "italy", "milán": "italy", "milano": "italy", "turin": "italy", "turín": "italy", "torino": "italy", "napoli": "italy", "napoles": "italy", "nápoles": "italy", "sardinia": "italy", "cerdeña": "italy",
        # Sweden
        "stockholm": "sweden", "estocolmo": "sweden", "kiruna": "sweden", "gothenburg": "sweden", "gotemburgo": "sweden", "malmo": "sweden", "malmö": "sweden",
        # Finland
        "helsinki": "finland", "espoo": "finland", "tampere": "finland", "oulu": "finland", "turku": "finland",
        # Poland
        "warsaw": "poland", "varsovia": "poland", "krakow": "poland", "cracovia": "poland", "wroclaw": "poland", "katowice": "poland", "lubin": "poland", "gdansk": "poland", "poznan": "poland",
        # Austria
        "vienna": "austria", "viena": "austria", "salzburg": "austria", "salzburgo": "austria", "graz": "austria", "innsbruck": "austria",
        # Greece
        "athens": "greece", "atenas": "greece", "thessaloniki": "greece", "tesalonica": "greece", "tesalónica": "greece",
        # Ireland
        "dublin": "ireland", "dublín": "ireland", "cork": "ireland", "galway": "ireland",
        # Czechia
        "prague": "czechia", "praga": "czechia", "brno": "czechia", "ostrava": "czechia"
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
        "chequia": "czechia", "república checa": "czechia", "republica checa": "czechia", "czechia": "czechia", "czech": "czechia",
        **CITY_COUNTRY_MAP
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

        # 5. Dialogue action normalization
        action = str(raw_json.get("dialogue_action", "new_search")).lower().strip()
        if action not in ["new_search", "expand", "refine", "remove", "reset"]:
            action = "new_search"
        raw_json["dialogue_action"] = action

        # 6. Normalize remove_filters if present
        rem_raw = raw_json.get("remove_filters", {})
        if isinstance(rem_raw, dict) and rem_raw:
            norm_rem = {}
            if "commodities" in rem_raw:
                norm_c = []
                for c in rem_raw["commodities"]:
                    cc = self.COMMODITY_MAP.get(str(c).lower().strip(), str(c).lower().strip())
                    if cc not in norm_c: norm_c.append(cc)
                norm_rem["commodities"] = norm_c
            if "countries" in rem_raw:
                norm_co = []
                for co in rem_raw["countries"]:
                    coc = self.COUNTRY_MAP.get(str(co).lower().strip(), str(co).lower().strip())
                    if coc not in norm_co: norm_co.append(coc)
                norm_rem["countries"] = norm_co
            if "storage_facility_types" in rem_raw:
                norm_f = []
                for f in rem_raw["storage_facility_types"]:
                    fc = str(f).lower().strip()
                    mapped = self.FACILITY_MAP.get(fc, [fc])
                    for m in mapped:
                        if m not in norm_f: norm_f.append(m)
                norm_rem["storage_facility_types"] = norm_f
            raw_json["remove_filters"] = norm_rem
        else:
            raw_json["remove_filters"] = {}

        return raw_json

class Validator:
    """Ensures structure compliance and fills missing default keys."""
    
    def validate(self, data: Dict[str, Any], query: str = "") -> Dict[str, Any]:
        intent = data.get("intent", "filter_search")
        if intent not in ["filter_search", "generic_qa", "hybrid"]:
            intent = "filter_search"
            
        filters = data.get("filters", {})
        comm_op = filters.get("commodity_operator", "OR")
        comms_and = filters.get("commodities_and", [])
        comms_or = filters.get("commodities_or", [])
        comms = filters.get("commodities", [])

        # If query is provided, verify/infer Boolean operator deterministically
        if query and len(comms) > 1:
            q_lower = query.lower()
            has_or_word = bool(re.search(r'\b(o|or|u|either|por separado|separately)\b', q_lower))
            has_and_word = bool(re.search(r'\b(y|and|e|both|ambos|ambas|juntos|juntas|together|a la vez|simult[aá]neamente)\b', q_lower))
            
            # Check for compound
            if has_or_word and has_and_word:
                comm_op = "COMPOUND"
            elif has_and_word and not has_or_word:
                comm_op = "AND"
                comms_and = list(comms)
                comms_or = []
            elif has_or_word and not has_and_word:
                comm_op = "OR"
                comms_or = list(comms)
                comms_and = []

        # Harmonize commodities if not explicitly split
        if not comms_and and not comms_or and comms:
            if comm_op == "AND":
                comms_and = list(comms)
            else:
                comms_or = list(comms)
        elif (comms_and or comms_or) and not comms:
            comms = list(dict.fromkeys(comms_and + comms_or))

        validated_filters = {
            "countries": filters.get("countries", []),
            "regions": filters.get("regions", []),
            "commodities": comms,
            "commodity_operator": comm_op,
            "commodities_and": comms_and,
            "commodities_or": comms_or,
            "is_ambiguous_commodities": bool(filters.get("is_ambiguous_commodities", False)),
            "storage_facility_types": filters.get("storage_facility_types", []),
            "material_types": filters.get("material_types", []),
            "project_status": filters.get("project_status", []),
            "environmental_flags": filters.get("environmental_flags", []),
            "restored": filters.get("restored", None)
        }
        
        return {
            "intent": intent,
            "dialogue_action": data.get("dialogue_action", "new_search"),
            "filters": validated_filters,
            "remove_filters": data.get("remove_filters", {}),
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

        comm_op = filters.get("commodity_operator", "OR")
        comms_and = filters.get("commodities_and", [])
        comms_or = filters.get("commodities_or", [])
        comms = filters.get("commodities", [])

        if comm_op == "AND" or (comms_and and not comms_or):
            target_and = comms_and or comms
            for cm in target_and:
                fq_list.append(f'commodities:"{cm}"')
        elif comm_op == "COMPOUND" and (comms_and and comms_or):
            or_parts = " OR ".join(f'"{c}"' for c in comms_or)
            and_parts = " AND ".join(f'commodities:"{c}"' for c in comms_and)
            fq_list.append(f'(commodities:({or_parts}) OR ({and_parts}))')
        elif comms_or or comms:
            target_or = comms_or or comms
            cm_str = " OR ".join(f'"{cm}"' for cm in target_or)
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

class DialogueStateTracker:
    """
    Dialogue State Tracking (DST) engine for SoftwareX conversational search.
    Maintains accumulative filter memory, resolves conversational actions
    (new_search, expand, refine, remove, reset), and synthesizes contextual narrative notices.
    """
    
    @staticmethod
    def detect_dialogue_action(query: str, current_filters: Optional[Dict[str, Any]] = None) -> str:
        q = (query or "").lower().strip()
        
        # 1. Reset
        reset_cues = [
            r'\breset\b', r'\breiniciar\b', r'\blimpiar\b', r'\bempezar de nuevo\b',
            r'\bnueva b[uú]squeda\b', r'\bolvida lo anterior\b', r'\bolvida todo\b',
            r'\bborrar filtros\b', r'\bclear\b', r'\bstart over\b', r'\bnew search\b'
        ]
        if any(re.search(pat, q) for pat in reset_cues):
            return "reset"
            
        has_existing = False
        if current_filters:
            for k in ["countries", "commodities", "storage_facility_types", "project_status", "environmental_flags"]:
                if current_filters.get(k):
                    has_existing = True
                    break
            if current_filters.get("restored") is not None:
                has_existing = True
                
        if not has_existing:
            return "new_search"

        # Explicit new search cues that start a brand new search topic or reset scope
        new_search_cues = [
            r'\b(show all facilities|show all|find all facilities|find all|list all facilities|list all)\b',
            r'\b(ver todas las instalaciones|muestra todas las instalaciones|todas las instalaciones|buscar todas)\b',
            r'\b(buscar desde cero|nueva consulta)\b'
        ]
        if any(re.search(pat, q) for pat in new_search_cues):
            return "new_search"
            
        # 2. Removal / Exclusion
        remove_cues = [
            r'\bquita\b', r'\bquitar\b', r'\belimina\b', r'\beliminar\b', r'\bdescarta\b',
            r'\bsin\b', r'\bexcepto\b', r'\bmenos\b', r'\bya no quiero\b', r'\bborra\b',
            r'\bremove\b', r'\bexclude\b', r'\bdrop\b', r'\bwithout\b', r'\bexcept\b', r'\bdelete\b',
            r'\bforget\s+about\b', r'\bdiscard\b'
        ]
        if any(re.search(pat, q) for pat in remove_cues):
            return "remove"
            
        # 3. Refinement / Narrowing (AND constraint on existing set)
        refine_cues = [
            r'\bde es[ao]s\b', r'\bde est[ao]s\b', r'\bde ell[ao]s\b', r'\bde los anteriores\b',
            r'\bsolo las que\b', r'\bsolo los que\b', r'\b[uú]nicamente\b', r'\bunicamente\b',
            r'\bque contengan\b', r'\bque tengan\b', r'\bpero solo\b', r'\bde ah[ií] solo\b',
            r'\bacota\b', r'\bfiltra por\b', r'\bfiltradas por\b', r'\bof those\b', r'\bfrom these\b',
            r'\bonly (those|that|the|ones)\b', r'\bkeep only\b', r'\bfilter to\b', r'\bonly interested in\b',
            r'\bnarrow down\b', r'\bjust the ones\b', r'\bonly active\b', r'\bonly unrestored\b', r'\bonly restored\b'
        ]
        if any(re.search(pat, q) for pat in refine_cues):
            return "refine"
            
        # 4. Expansion / Additive (OR expansion)
        expand_cues = [
            r'\by adem[aá]s\b', r'\btambi[eé]n\b', r'\ba[ñn]ade\b', r'\bagrega\b', r'\bsuma\b',
            r'\by en\b', r'\by las de\b', r'\by los de\b', r'\by cerca de\b', r'\bo en\b',
            r'\band also\b', r'\balso add\b', r'\binclude also\b', r'\bshow also\b',
            r'\badditionally\b', r'\bas well as\b', r'\bplus\b', r'\binclude\b', r'\bwhat about\b'
        ]
        if any(re.search(pat, q) for pat in expand_cues):
            return "expand"
            
        return "new_search"

    @staticmethod
    def update_state(
        current_filters: Dict[str, Any], 
        extracted_filters: Dict[str, Any], 
        action: str,
        remove_filters: Optional[Dict[str, Any]] = None,
        query: str = ""
    ) -> Dict[str, Any]:
        """
        Reconciles previous state with new extracted filters based on dialogue action.
        """
        keys_list = ["countries", "regions", "commodities", "storage_facility_types", "material_types", "project_status", "environmental_flags"]
        
        state = {
            k: list(current_filters.get(k, [])) if current_filters else [] for k in keys_list
        }
        state["restored"] = current_filters.get("restored", None) if current_filters else None
        state["commodity_operator"] = (extracted_filters.get("commodity_operator") or (current_filters.get("commodity_operator") if current_filters else "OR"))
        state["commodities_and"] = list(extracted_filters.get("commodities_and") or (current_filters.get("commodities_and", []) if current_filters else []))
        state["commodities_or"] = list(extracted_filters.get("commodities_or") or (current_filters.get("commodities_or", []) if current_filters else []))
        state["is_ambiguous_commodities"] = bool(extracted_filters.get("is_ambiguous_commodities", False))

        if action == "reset":
            res = {k: ([] if k != "restored" else None) for k in state}
            res["commodity_operator"] = "OR"
            res["commodities_and"] = []
            res["commodities_or"] = []
            res["is_ambiguous_commodities"] = False
            return res

        if action == "new_search":
            for k in keys_list:
                state[k] = list(extracted_filters.get(k, []))
            state["restored"] = extracted_filters.get("restored", None)
            state["commodity_operator"] = extracted_filters.get("commodity_operator", "OR")
            state["commodities_and"] = list(extracted_filters.get("commodities_and", []))
            state["commodities_or"] = list(extracted_filters.get("commodities_or", []))
            state["is_ambiguous_commodities"] = bool(extracted_filters.get("is_ambiguous_commodities", False))
            return state

        if action == "expand":
            # Additive / OR expansion: merge new entities into each category without duplicates
            for k in keys_list:
                for val in extracted_filters.get(k, []):
                    if val not in state[k]:
                        state[k].append(val)
            if extracted_filters.get("restored") is not None:
                state["restored"] = extracted_filters.get("restored")
            if extracted_filters.get("commodities_or"):
                for val in extracted_filters["commodities_or"]:
                    if val not in state["commodities_or"]:
                        state["commodities_or"].append(val)
            return state

        if action == "refine":
            # Progressive narrowing (AND): keep dimensions not specified, override dimensions that were specified
            for k in keys_list:
                extracted_vals = extracted_filters.get(k, [])
                if extracted_vals:
                    state[k] = list(extracted_vals)
            
            # If query explicitly says 'all facilities' / 'todas las instalaciones', clear facility restriction
            if query and re.search(r'\b(all facilities|all sites|all deposits|todas las instalaciones|todos los yacimientos)\b', query.lower()):
                state["storage_facility_types"] = []

            if extracted_filters.get("restored") is not None:
                state["restored"] = extracted_filters.get("restored")
            if extracted_filters.get("commodity_operator"):
                state["commodity_operator"] = extracted_filters["commodity_operator"]
            if extracted_filters.get("commodities_and"):
                state["commodities_and"] = list(extracted_filters["commodities_and"])
            if extracted_filters.get("commodities_or"):
                state["commodities_or"] = list(extracted_filters["commodities_or"])
            return state

        if action == "remove":
            # Subtraction: remove targets from current state
            removals = remove_filters if remove_filters else extracted_filters
            for k in keys_list:
                to_drop = set(removals.get(k, []))
                state[k] = [v for v in state[k] if v not in to_drop]
            if "commodities" in removals:
                to_drop_c = set(removals["commodities"])
                state["commodities_and"] = [v for v in state["commodities_and"] if v not in to_drop_c]
                state["commodities_or"] = [v for v in state["commodities_or"] if v not in to_drop_c]
            return state

        return state

    @staticmethod
    def format_transition_notice(
        action: str, 
        current_filters: Dict[str, Any], 
        updated_filters: Dict[str, Any], 
        is_spanish: bool = False
    ) -> str:
        """Generates a conversational prefix explaining the state transition."""
        if action == "reset":
            return "🧹 **Filtros de conversación reiniciados** (mostrando el catálogo completo europeo).\n\n" if is_spanish else "🧹 **Conversation filters reset** (showing full European data space).\n\n"
            
        if action == "expand":
            added_countries = [c for c in updated_filters.get("countries", []) if c not in (current_filters or {}).get("countries", [])]
            added_comms = [c for c in updated_filters.get("commodities", []) if c not in (current_filters or {}).get("commodities", [])]
            details = []
            if added_countries:
                details.append(f"países: {', '.join(added_countries).title()}" if is_spanish else f"countries: {', '.join(added_countries).title()}")
            if added_comms:
                details.append(f"materias primas: {', '.join(added_comms).title()}" if is_spanish else f"commodities: {', '.join(added_comms).title()}")
            detail_str = f" ({'; '.join(details)})" if details else ""
            
            if is_spanish:
                return f"🔄 **Ampliando la búsqueda (OR)**{detail_str} y manteniendo los criterios anteriores:\n\n"
            return f"🔄 **Expanding search criteria (OR)**{detail_str} while preserving prior context:\n\n"

        if action == "refine":
            new_comms = updated_filters.get("commodities", [])
            new_status = updated_filters.get("project_status", [])
            details = []
            if new_comms:
                details.append(f"minerales: {', '.join(new_comms).title()}" if is_spanish else f"commodities: {', '.join(new_comms).title()}")
            if new_status:
                details.append(f"estado: {', '.join(new_status)}" if is_spanish else f"status: {', '.join(new_status)}")
            detail_str = f" a {'; '.join(details)}" if details else ""

            if is_spanish:
                return f"🎯 **Refinando sobre los resultados anteriores (AND)**{detail_str}:\n\n"
            return f"🎯 **Refining previous results (AND)**{detail_str}:\n\n"

        if action == "remove":
            dropped_countries = [c for c in (current_filters or {}).get("countries", []) if c not in updated_filters.get("countries", [])]
            dropped_comms = [c for c in (current_filters or {}).get("commodities", []) if c not in updated_filters.get("commodities", [])]
            dropped_fac = [c for c in (current_filters or {}).get("storage_facility_types", []) if c not in updated_filters.get("storage_facility_types", [])]
            dropped = []
            if dropped_countries: dropped.extend(dropped_countries)
            if dropped_comms: dropped.extend(dropped_comms)
            if dropped_fac: dropped.extend(dropped_fac)
            dropped_str = f" **{', '.join(dropped).title()}**" if dropped else ""

            if is_spanish:
                return f"✂️ **Excluyendo{dropped_str}** de los criterios activos y conservando el resto de filtros:\n\n"
            return f"✂️ **Removing{dropped_str}** from active filters while preserving the remaining criteria:\n\n"

        return ""
