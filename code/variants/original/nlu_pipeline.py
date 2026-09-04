import os
import re
import json
import unicodedata
import urllib.request
import urllib.parse
from typing import Dict, Any, List, Tuple

# Helper to normalize strings for matching
def _normalize_lookup(text: str) -> str:
    normalized = (text or "").strip().lower()
    return "".join(
        char for char in unicodedata.normalize("NFKD", normalized)
        if not unicodedata.combining(char)
    )

# ----------------------------------------------------
# 1. Semantic Parsers (Rules & LLM)
# ----------------------------------------------------

class RulesSemanticParser:
    """
    Rules-based Semantic Parser that extracts raw entities from user queries
    using regex and keyword lookup.
    """
    def __init__(self):
        # Mappings of raw keywords to their semantic categories.
        # These are raw Spanish/English terms extracted before normalization.
        self.commodity_words = {
            "hulla": "coal", "carbon": "coal", "carbón": "coal", "coal": "coal",
            "cobre": "copper", "copper": "copper", "cu": "copper",
            "wolframio": "tungsten", "tungsteno": "tungsten", "tungsten": "tungsten", "w": "tungsten",
            "volframio": "tungsten", "golfranio": "tungsten", # typo resolutions
            "litio": "lithium", "lithium": "lithium", "li": "lithium",
            "estaño": "tin", "estano": "tin", "tin": "tin", "sn": "tin",
            "plata": "silver", "silver": "silver", "ag": "silver",
            "oro": "gold", "gold": "gold", "au": "gold",
            "niquel": "nickel", "niquel": "nickel", "níquel": "nickel", "ni": "nickel",
            "cobalto": "cobalt", "cobalt": "cobalt", "co": "cobalt",
            "zinc": "zinc", "cinc": "zinc", "zn": "zinc",
            "plomo": "lead", "lead": "lead", "pb": "lead",
            "tantalo": "tantalum", "tántalo": "tantalum", "tantalum": "tantalum", "ta": "tantalum",
            "niobio": "niobium", "niobium": "niobium", "nb": "niobium",
            "coltan": "coltan", "coltán": "coltan",
            "hierro": "iron", "iron": "iron",
            "manganese": "manganese", "manganeso": "manganese",
            "chromium": "chromium", "cromo": "chromium",
            "platinum": "platinum", "platino": "platinum",
            "palladium": "palladium", "paladio": "palladium",
            "titanium": "titanium", "titanio": "titanium",
            "bauxite": "bauxite", "bauxita": "bauxite",
            "antimony": "antimony", "antimonio": "antimony",
            "barite": "barite", "barita": "barite",
            "beryllium": "beryllium", "berilio": "beryllium",
            "bismuth": "bismuth", "bismuto": "bismuth",
            "borate": "borate", "borato": "borate",
            "magnesium": "magnesium", "magnesio": "magnesium",
            "graphite": "graphite", "grafito": "graphite",
            "silicon": "silicon", "silicio": "silicon",
            "fluorite": "fluorite", "fluorita": "fluorite",
            "phosphate": "phosphate", "fosfato": "phosphate",
            "tierras raras": "rare earths", "rare earths": "rare earths", "ree": "rare earths",
            
            # Semantic battery materials group
            "baterias de coches electricos": ["lithium", "cobalt", "nickel"],
            "baterías de coches eléctricos": ["lithium", "cobalt", "nickel"],
            "baterias de coches": ["lithium", "cobalt", "nickel"],
            "baterias": ["lithium", "cobalt", "nickel"],
            "baterías": ["lithium", "cobalt", "nickel"],
            "rame": "copper",
            "wolfram": "tungsten"
        }
        
        self.region_words = {
            "asturias": "asturias", "principado de asturias": "asturias", "mieres": "asturias",
            "pumardongo": "asturias", "figaredo": "asturias", "nicolasa": "asturias",
            "oviedo": "asturias", "gijon": "asturias", "gijón": "asturias",
            "andalucia": "andalucia", "andalucía": "andalucia", "riotinto": "andalucia",
            "huelva": "andalucia", "sevilla": "andalucia", "cadiz": "andalucia", "cádiz": "andalucia",
            "cordoba": "andalucia", "córdoba": "andalucia", "malaga": "andalucia", "málaga": "andalucia",
            "jaen": "andalucia", "jaén": "andalucia", "granada": "andalucia", "almeria": "andalucia", "almería": "andalucia",
            "galicia": "galicia", "galiza": "galicia", "san finx": "galicia", "coruña": "galicia",
            "a coruña": "galicia", "lugo": "galicia", "orense": "galicia", "ourense": "galicia", "pontevedra": "galicia",
            "castilla y leon": "castilla y leon", "castilla y león": "castilla y leon", "salamanca": "castilla y leon",
            "los santos": "castilla y leon", "leon": "castilla y leon", "león": "castilla y leon", "zamora": "castilla y leon",
            "burgos": "castilla y leon", "palencia": "castilla y leon", "valladolid": "castilla y leon",
            "avila": "castilla y leon", "ávila": "castilla y leon", "segovia": "castilla y leon", "soria": "castilla y leon",
            "extremadura": "extremadura", "caceres": "extremadura", "cáceres": "extremadura",
            "valdeflorez": "extremadura", "valdeflórez": "extremadura", "san jose": "extremadura",
            "san josé": "extremadura", "badajoz": "extremadura",
            "alentejo": "alentejo",
            
            # Spatial synonyms / slang
            "sur de la peninsula": "andalucia",
            "sur de la península": "andalucia",
            "sur de espana": "andalucia",
            "sur de españa": "andalucia",
            "bretagne": "bretagne",
            "asturie": "asturias",
            "estremadure": "extremadura",
            "galicien": "galicia"
        }
        
        self.facility_words = {
            "escombrera": "waste dump", "escombreras": "waste dump", "spoil heap": "waste dump", "waste dump": "waste dump", "dump": "waste dump",
            "balsa de esteriles": "tailings storage facility", "balsa de estériles": "tailings storage facility", "tailings storage facility": "tailings storage facility",
            "relave": "tailings storage facility", "relaves": "tailings storage facility", "tsf": "tailings storage facility",
            
            # Balsas de decantación maps to both pond and TSF
            "balsa de decantacion": ["pond", "tailings storage facility"],
            "balsa de decantación": ["pond", "tailings storage facility"],
            "balsas de decantacion": ["pond", "tailings storage facility"],
            "balsas de decantación": ["pond", "tailings storage facility"],
            "presa de lodos": ["pond", "tailings storage facility"],
            
            # Residuos mineros
            "residuos mineros": ["waste dump", "tailings storage facility"],
            "residuos de mina": ["waste dump", "tailings storage facility"],
            "acumulacion de residuos": ["waste dump", "tailings storage facility"],
            "acumulación de residuos": ["waste dump", "tailings storage facility"],
            
            # Default balsa/balsas maps to pond
            "balsa": "pond",
            "balsas": "pond", 
            "estanque": "pond", "pond": "pond",
            "acopio": "stockpile", "stockpile": "stockpile",
            "bergehalden": "waste dump",
            "barragens": "pond",
            "bassins de decantation": "tailings storage facility",
            "bassins de décantation": "tailings storage facility",
            "bacino de decantazione": "tailings storage facility",
            "bacino di decantazione": "tailings storage facility"
        }
        
        self.material_words = {
            "esteriles": "tailings", "estériles": "tailings", "tailings": "tailings", "residuos": "tailings", "residuos mineros": "tailings",
            "waste rock": "waste rock", "roca": "waste rock", "roca esteril": "waste rock", "roca estéril": "waste rock", "inertes": "waste rock", "inerte": "waste rock",
            "lodos": "sludge", "barro": "sludge", "barros": "sludge", "sludge": "sludge",
            "escorias": "tailings", "subproductos": "tailings"
        }
        
        self.status_words = {
            "activo": "active", "activa": "active", "activos": "active", "activas": "active", "active": "active",
            "en explotacion": "active", "en explotación": "active",
            "inactivo": "inactive", "inactiva": "inactive", "inactivos": "inactive", "inactivas": "inactive", "inactive": "inactive",
            "abandonado": "inactive", "abandonada": "inactive", "parado": "inactive", "parada": "inactive", "parados": "inactive", "cerrado": "inactive",
            "cerrada": "inactive", "cerrados": "inactive", "cerradas": "inactive",
            "mantenimiento": "care and maintenance", "care and maintenance": "care and maintenance", "cuidado y mantenimiento": "care and maintenance",
            "desarrollo": "development", "development": "development", "en desarrollo": "development",
            "pasivo": "inactive", "pasivos": "inactive",
            "autorizacion de explotacion": "active", "autorización de explotación": "active",
            "inaktive": "inactive"
        }
        
        self.company_words = {
            "hunosa": "hunosa",
            "atalaya": "atalaya mining", "atalaya mining": "atalaya mining",
            "almonty": "almonty industries", "almonty industries": "almonty industries",
            "orvana": "orvana minerals", "orvana minerals": "orvana minerals",
            "infinity": "infinity lithium", "infinity lithium": "infinity lithium",
            "valoriza": "valoriza mineria", "valoriza mineria": "valoriza mineria"
        }
        
        self.site_words = {
            "san nicolas": "San Nicolas", "nicolasa": "San Nicolas",
            "pumardongo": "Pumardongo",
            "figaredo": "Figaredo", "casona": "Figaredo",
            "riotinto": "Riotinto Project", "rio tinto": "Riotinto Project",
            "valdeflores": "San José Valdeflórez", "valdeflorez": "San José Valdeflórez", "san jose valdeflorez": "San José Valdeflórez", "san josé valdeflórez": "San José Valdeflórez",
            "boinas": "El Valle-Boinás", "valle-boinas": "El Valle-Boinás", "el valle": "El Valle-Boinás",
            "los santos": "Los Santos",
            "san finx": "San Finx",
            "penouta": "Mina de Penouta", "mina de penouta": "Mina de Penouta",
            "neves-corvo": "Neves-Corvo", "neves corvo": "Neves-Corvo"
        }
        
        self.country_words = {
            "espana": "spain", "españa": "spain", "spain": "spain",
            "portugal": "portugal",
            "francia": "france", "france": "france",
            "europa": "europe", "europe": "europe"
        }

    def _extract_from_text(self, text: str) -> Dict[str, Any]:
        filters = {}
        
        # Helper to sort items by key length (descending) to match longest phrases first
        def get_sorted_items(d: Dict[str, Any]) -> List[Tuple[str, Any]]:
            return sorted(d.items(), key=lambda x: len(x[0]), reverse=True)
            
        # 1. Country
        for term, canonical in get_sorted_items(self.country_words):
            if term in text:
                filters.setdefault("country", []).append(canonical)
        
        # 2. Region
        for term, canonical in get_sorted_items(self.region_words):
            if term in text:
                filters.setdefault("region", []).append(canonical)
                
        # 3. Commodity
        for term, canonical in get_sorted_items(self.commodity_words):
            if re.search(r'\b' + re.escape(term) + r'\b', text) or (len(term) > 2 and term in text):
                if isinstance(canonical, list):
                    filters.setdefault("commodity", []).extend(canonical)
                else:
                    filters.setdefault("commodity", []).append(canonical)
                
        # 4. Storage Facility
        for term, canonical in get_sorted_items(self.facility_words):
            if term in text:
                if isinstance(canonical, list):
                    filters.setdefault("storage_facility", []).extend(canonical)
                else:
                    filters.setdefault("storage_facility", []).append(canonical)
                    
        # Apply special contextual expansion for 'balsa' / 'balsas'
        # If the query contains "decantacion" or "tierras raras", expand "pond" to also include "tailings storage facility"
        if "storage_facility" in filters and "pond" in filters["storage_facility"]:
            if "decantacion" in text or "tierras raras" in text:
                if "tailings storage facility" not in filters["storage_facility"]:
                    filters["storage_facility"].append("tailings storage facility")
                
        # 5. Material Type
        for term, canonical in get_sorted_items(self.material_words):
            if term in text:
                filters.setdefault("material_type", []).append(canonical)
                
        # 6. Status
        for term, canonical in get_sorted_items(self.status_words):
            if term in text:
                filters.setdefault("mine_status", []).append(canonical)
                
        # 7. Company
        for term, canonical in get_sorted_items(self.company_words):
            if term in text:
                filters.setdefault("company", []).append(canonical)
                
        # 8. Site
        for term, canonical in get_sorted_items(self.site_words):
            if term in text:
                filters.setdefault("site", []).append(canonical)
                
        # 9. UNFC E, F, G
        e_match = re.findall(r'\be[123]\b', text)
        if e_match:
            filters["unfc_e"] = [e.upper() for e in e_match]
        f_match = re.findall(r'\bf[1234]\b', text)
        if f_match:
            filters["unfc_f"] = [f.upper() for f in f_match]
        g_match = re.findall(r'\bg[1234]\b', text)
        if g_match:
            filters["unfc_g"] = [g.upper() for g in g_match]
            
        # 10. Restored status
        if "sin restaurar" in text or "not restored" in text:
            filters["restored"] = False
        elif "restaurado" in text or "restaurada" in text or "restored" in text:
            filters["restored"] = True
            
        # Clean duplicates
        for k in list(filters.keys()):
            if isinstance(filters[k], list):
                filters[k] = list(dict.fromkeys(filters[k]))
                if not filters[k]:
                    del filters[k]
                    
        return filters

    def parse(self, query: str) -> Dict[str, Any]:
        """
        Parses user query and returns a raw semantic JSON structure.
        """
        text = _normalize_lookup(query)
        
        # Handle conversational temporal corrections (Ah no, mejor...)
        intent_text = text
        if "ah no, mejor" in text:
            intent_text = text.split("ah no, mejor", 1)[1].strip()
            
        # Normalize double negatives
        pos_text = text
        if "no quiero proyectos que no sean de" in pos_text:
            pos_text = pos_text.replace("no quiero proyectos que no sean de", "quiero proyectos de")
            
        # Determine intent & RAG needs
        intent = "search"
        needs_rag = False
        
        # Classify hybrid intents, including informational questions (quién eres, qué es, cuáles son, etc.)
        if any(term in intent_text for term in [
            "informe", "report", "dice", "estabilidad fisica", "estabilidad física",
            "cuales son", "cuáles son", "que son", "qué son", "que es", "qué es", "quien eres", "quién eres"
        ]):
            needs_rag = True
            intent = "hybrid"
        elif any(term in intent_text for term in ["hola", "buenas", "ayudar", "quien eres", "hello", "hi"]):
            intent = "generic_qa"
            
        # Extract explicit negation clauses from text to prevent scope bleed
        neg_filters = {}
        
        # 1. Negative Region: "pero no en <region>" or "no en <region>"
        region_neg_match = re.search(r'\b(?:pero\s+no\s+en|but\s+not\s+in|mais\s+pas\s+en|nicht\s+in|no\s+en|pas\s+en|não\s+em|nao\s+em)\s+([a-zñáéíóú\s]+)', pos_text)
        if region_neg_match:
            neg_region_raw = region_neg_match.group(1)
            for term, canonical in sorted(self.region_words.items(), key=lambda x: len(x[0]), reverse=True):
                if term in neg_region_raw:
                    neg_filters.setdefault("region", []).append(canonical)
            pos_text = pos_text.replace(region_neg_match.group(0), "")
            
        # 2. Negative Company: "excepto las de <company>" or "excepto <company>"
        # Restrict company name match to a single word to prevent matching trailing region context (e.g. "excepto las de Almonty en Galicia")
        company_neg_match = re.search(r'\b(?:excepto|except|sauf|excepte|exceto|außer|ausser)\s+(?:las\s+de\s+|those\s+managed\s+by\s+|those\s+by\s+)?([a-zñáéíóú]+)', pos_text)
        if company_neg_match:
            neg_company_raw = company_neg_match.group(1)
            for term, canonical in sorted(self.company_words.items(), key=lambda x: len(x[0]), reverse=True):
                if term in neg_company_raw:
                    neg_filters.setdefault("company", []).append(canonical)
            pos_text = pos_text.replace(company_neg_match.group(0), "")
            
        # 3. Negative Commodity: "pero no de <commodity>" or "no de <commodity>"
        comm_neg_match = re.search(r'\b(?:pero\s+no\s+de|but\s+not\s+of|but\s+not|mais\s+pas\s+de|nicht|no\s+de|pas\s+de|não\s+de|nao\s+de)\s+([a-zñáéíóú\s]+)', pos_text)
        if comm_neg_match:
            neg_comm_raw = comm_neg_match.group(1)
            for term, canonical in sorted(self.commodity_words.items(), key=lambda x: len(x[0]), reverse=True):
                if term in neg_comm_raw:
                    if isinstance(canonical, list):
                        neg_filters.setdefault("commodity", []).extend(canonical)
                    else:
                        neg_filters.setdefault("commodity", []).append(canonical)
            pos_text = pos_text.replace(comm_neg_match.group(0), "")
            
        # 4. Negative Status: "ya no están en fase de desarrollo", "no explotan comercialmente", etc.
        if "no estan en fase de desarrollo" in pos_text or "no en desarrollo" in pos_text:
            neg_filters.setdefault("mine_status", []).append("development")
            pos_text = pos_text.replace("no estan en fase de desarrollo", "").replace("no en desarrollo", "")
        if "no explotan comercialmente" in pos_text or "no en explotacion" in pos_text:
            neg_filters.setdefault("mine_status", []).append("active")
            pos_text = pos_text.replace("no explotan comercialmente", "").replace("no en explotacion", "")
            
        # Fallback to general split negation if no explicit matches but negation patterns exist
        if not neg_filters:
            negation_patterns = [r"\bpero\s+que\s+no\b", r"\bpero\s+no\b", r"\bexcepto\b", r"\bno\s+en\b", r"\bbut\s+not\b", r"\bexcept\b", r"\bmais\s+pas\b", r"\bmais\s+pas\s+en\b"]
            for pattern in negation_patterns:
                split_match = re.split(pattern, pos_text, maxsplit=1)
                if len(split_match) > 1:
                    pos_text = split_match[0]
                    neg_text = split_match[1]
                    neg_filters = self._extract_from_text(neg_text)
                    break
                    
        pos_filters = self._extract_from_text(pos_text)
        
        # Clean restored from positive filters if present in negative
        if "restored" in neg_filters:
            pos_filters.pop("restored", None)
            
        # Determine fulltext constraints
        fulltext = []
        if intent in ["hybrid", "generic_qa"] or not pos_filters:
            clean_q = query
            if needs_rag:
                match = re.search(r'(estabilidad física|estabilidad fisica|presa de lodos|informe|tierras raras)', query, re.IGNORECASE)
                if match:
                    fulltext.append(match.group(0))
            else:
                fulltext.append(query.strip())
        else:
            match = re.search(r'(estabilidad física|estabilidad fisica)', query, re.IGNORECASE)
            if match:
                fulltext.append(match.group(0))
                
        result = {
            "intent": intent,
            "filters": pos_filters,
            "fulltext": fulltext,
            "needs_rag": needs_rag
        }
        if neg_filters:
            result["negated_filters"] = neg_filters
            
        return result


class LLMSemanticParser:
    """
    LLM-based Semantic Parser that instructs the LLM to output a clean
    semantic JSON schema representing the contract.
    """
    def __init__(self, provider="gemini"):
        self.provider = provider
        
        self.prompt_template = """You are a Semantic Parser for a mining database.
Convert the user search query into a compact, normalized JSON contract.

Your response MUST be ONLY valid JSON, with no explanation or markdown wrapper. Do not wrap in ```json ... ```.

Use this JSON schema exactly:
{{
  "intent": "search" | "hybrid" | "generic_qa",
  "filters": {{
    "commodity": ["..."],
    "region": ["..."],
    "country": ["..."],
    "company": ["..."],
    "site": ["..."],
    "storage_facility": ["..."],
    "material_type": ["..."],
    "project_status": ["..."],
    "restored": true | false,
    "unfc_e": ["..."],
    "unfc_f": ["..."],
    "unfc_g": ["..."]
  }},
  "negated_filters": {{
    // Include only keys that are explicitly negated or excluded by the user.
    // Example: "pero no en Extremadura" -> "region": ["extremadura"]
  }},
  "fulltext": ["..."],
  "needs_rag": true | false
}}

Rules:
1. "intent":
   - "search" for standard structured searches.
   - "generic_qa" for greetings, off-topic, or basic helper questions.
   - "hybrid" for queries requiring both structured database filtering and reading document context (RAG).
2. "filters" and "negated_filters":
   - Include ONLY keys that are actually detected in the query.
   - DO NOT include keys with empty lists or null values. If a key has no values, omit it.
3. Extract raw terms as written by the user (can be Spanish or English). The downstream Normalizer will map synonyms.
4. "fulltext": List of free-text phrases or terms that do not correspond to structured fields but should be searched in database text fields (e.g. "estabilidad física").
5. "needs_rag": Set to true if the query requires reading a report context (e.g., questions about stability, observations, chemical composition in reports).

Examples:
- User: "escombreras de golfranio en galiza"
  JSON:
  {{
    "intent": "search",
    "filters": {{
      "storage_facility": ["escombreras"],
      "commodity": ["golfranio"],
      "region": ["galiza"]
    }},
    "fulltext": [],
    "needs_rag": false
  }}

- User: "balsas de litio en españa pero que no estén en extremadura"
  JSON:
  {{
    "intent": "search",
    "filters": {{
      "storage_facility": ["balsas"],
      "commodity": ["litio"],
      "country": ["españa"]
    }},
    "negated_filters": {{
      "region": ["extremadura"]
    }},
    "fulltext": [],
    "needs_rag": false
  }}

- User: "¿qué dice el informe sobre la estabilidad física de la presa de lodos de penouta?"
  JSON:
  {{
    "intent": "hybrid",
    "filters": {{
      "storage_facility": ["presa de lodos"],
      "site": ["penouta"]
    }},
    "fulltext": ["estabilidad física"],
    "needs_rag": true
  }}

User Query: "{query}"
JSON Output:"""

    def parse(self, query: str) -> Dict[str, Any]:
        prompt = self.prompt_template.format(query=query.strip())
        
        from llm_client import call_llm, extract_json_block
        system_prompt = "You are a database semantic extraction assistant. Return ONLY valid JSON block. Do not include markdown code block syntax."
        text = call_llm(system_prompt=system_prompt, user_prompt=prompt, provider=self.provider, json_mode=True)
            
        try:
            return extract_json_block(text)
        except Exception as e:
            print(f"[Error] Failed to parse JSON from LLM response: {e}. Raw response: {text}")
            return {"intent": "search", "filters": {}, "fulltext": [], "needs_rag": False}


# ----------------------------------------------------
# 2. Normalizer
# ----------------------------------------------------

class Normalizer:
    """
    Transforms raw user entities into canonical values and keys as defined by database schema.
    Also handles multilingual resolution and database inference.
    """
    def __init__(self):
        self.key_mapping = {
            "commodity": "commodities",
            "region": "regions",
            "country": "countries",
            "company": "companies",
            "site": "site_names",
            "storage_facility": "storage_facility_types",
            "material_type": "material_types",
            "project_status": "project_status",
            "mine_status": "project_status",
            "unfc_e": "unfc_e",
            "unfc_f": "unfc_f",
            "unfc_g": "unfc_g",
            "restored": "restored"
        }
        
        # Mappings of raw/alias values to database canonical terms
        self.commodity_map = {
            "coal": "coal", "hulla": "coal", "carbon": "coal",
            "copper": "copper", "cobre": "copper",
            "tungsten": "tungsten", "wolframio": "tungsten", "tungsteno": "tungsten",
            "lithium": "lithium", "litio": "lithium",
            "tin": "tin", "estaño": "tin", "estano": "tin",
            "silver": "silver", "plata": "silver",
            "gold": "gold", "oro": "gold",
            "nickel": "nickel", "niquel": "nickel", "níquel": "nickel",
            "cobalt": "cobalt", "cobalto": "cobalt",
            "lead": "lead", "plomo": "lead",
            "zinc": "zinc", "cinc": "zinc",
            "tantalum": "tantalum", "tantalo": "tantalum", "tántalo": "tantalum",
            "niobium": "niobium", "niobio": "niobium",
            "iron": "iron", "hierro": "iron",
            "rare earth elements": "rare earth elements", "rare earths": "rare earth elements", "tierras raras": "rare earth elements", "ree": "rare earth elements",
            "coltan": ["tantalum", "niobium"],
            "golfranio": "tungsten",
            "volframio": "tungsten",
            "rame": "copper",
            "wolfram": "tungsten"
        }
        
        self.facility_map = {
            "waste dump": "waste dump", "escombrera": "waste dump", "escombreras": "waste dump", "spoil heap": "waste dump", "dump": "waste dump",
            "bergehalden": "waste dump",
            "barragens": "pond",
            "bassins de decantation": "tailings storage facility",
            "bassins de décantation": "tailings storage facility",
            "bacino de decantazione": "tailings storage facility",
            "bacino di decantazione": "tailings storage facility",
            "tailings storage facility": "tailings storage facility", "balsa de esteriles": "tailings storage facility", "balsa de estériles": "tailings storage facility", "relave": "tailings storage facility", "relaves": "tailings storage facility", "tsf": "tailings storage facility", "presa de lodos": "tailings storage facility",
            "pond": "pond", 
            
            # Map "balsa" and "balsas" to pond (rules parser dynamically expands contextually)
            "balsa": "pond", 
            "balsas": "pond", 
            "estanque": "pond", 
            
            "stockpile": "stockpile", "acopio": "stockpile"
        }
        
        self.material_map = {
            "tailings": "tailings", "esteriles": "tailings", "estériles": "tailings", "residuos": "tailings", "residuos mineros": "tailings",
            "waste rock": "waste rock", "roca": "waste rock", "roca esteril": "waste rock", "roca estéril": "waste rock", "inertes": "waste rock", "inerte": "waste rock",
            "sludge": "sludge", "lodos": "sludge", "barro": "sludge", "barros": "sludge",
            "escorias": "tailings", "subproductos": "tailings"
        }
        
        self.status_map = {
            "active": "active", "activo": "active", "activa": "active", "activos": "active", "en explotacion": "active", "en explotación": "active",
            "inactive": "inactive", "inactivo": "inactive", "inactiva": "inactive", "abandonado": "inactive", "abandonada": "inactive", "parado": "inactive", "parada": "inactive", "parados": "inactive", "cerrado": "inactive",
            "cerrada": "inactive", "cerrados": "inactive", "cerradas": "inactive",
            "care and maintenance": "care and maintenance", "mantenimiento": "care and maintenance", "cuidado y mantenimiento": "care and maintenance",
            "development": "development", "desarrollo": "development", "proyecto": "development", "en desarrollo": "development",
            "pasivo": "inactive", "pasivos": "inactive",
            "autorizacion de explotacion": "active", "autorización de explotación": "active",
            "inaktive": "inactive"
        }
        
        self.region_map = {
            "asturias": "asturias", "principado de asturias": "asturias", "mieres": "asturias", "pumardongo": "asturias", "figaredo": "asturias", "nicolasa": "asturias",
            "andalucia": "andalucia", "andalucía": "andalucia", "riotinto": "andalucia", "sevilla": "andalucia", "huelva": "andalucia",
            "galicia": "galicia", "galiza": "galicia", "san finx": "galicia", "ourense": "galicia", "orense": "galicia",
            "castilla y leon": "castilla y leon", "castilla y león": "castilla y leon", "salamanca": "castilla y leon", "los santos": "castilla y leon",
            "extremadura": "extremadura", "caceres": "extremadura", "cáceres": "extremadura", "valdeflorez": "extremadura", "valdeflórez": "extremadura",
            "alentejo": "alentejo",
            "sur de la peninsula": "andalucia",
            "sur de la península": "andalucia",
            "sur de espana": "andalucia",
            "sur de españa": "andalucia",
            "bretagne": "bretagne",
            "asturie": "asturias",
            "estremadure": "extremadura",
            "galicien": "galicia"
        }
        
        self.company_map = {
            "hunosa": "hunosa",
            "atalaya mining": "atalaya mining", "atalaya minera": "atalaya mining", "atalaya": "atalaya mining",
            "almonty industries": "almonty industries", "almonty": "almonty industries",
            "orvana minerals": "orvana minerals", "orvana": "orvana minerals",
            "infinity lithium": "infinity lithium", "infinity": "infinity lithium",
            "valoriza mineria": "valoriza mineria", "valoriza": "valoriza mineria"
        }
        
        self.site_map = {
            "san nicolas": "San Nicolas", "nicolasa": "San Nicolas",
            "pumardongo": "Pumardongo",
            "figaredo": "Figaredo",
            "riotinto project": "Riotinto Project", "riotinto": "Riotinto Project", "rio tinto": "Riotinto Project",
            "san jose valdeflorez": "San José Valdeflórez", "san josé valdeflórez": "San José Valdeflórez", "valdeflorez": "San José Valdeflórez", "valdeflores": "San José Valdeflórez",
            "el valle-boinas": "El Valle-Boinás", "boinas": "El Valle-Boinás", "valle-boinas": "El Valle-Boinás", "el valle": "El Valle-Boinás",
            "los santos": "Los Santos",
            "san finx": "San Finx",
            "mina de penouta": "Mina de Penouta", "penouta": "Mina de Penouta",
            "neves-corvo": "Neves-Corvo", "neves corvo": "Neves-Corvo"
        }
        
        self.country_map = {
            "spain": "spain", "espana": "spain", "españa": "spain",
            "portugal": "portugal",
            "france": "france", "francia": "france"
        }
        
        self.region_to_country = {
            "asturias": "spain",
            "andalucia": "spain",
            "galicia": "spain",
            "castilla y leon": "spain",
            "extremadura": "spain",
            "alentejo": "portugal",
            "bretagne": "france",
            "asturie": "spain",
            "estremadure": "spain",
            "galicien": "spain"
        }

    def _normalize_dict_filters(self, filters_dict: Dict[str, Any]) -> Dict[str, Any]:
        normalized = {}
        for raw_k, raw_vals in filters_dict.items():
            canonical_k = self.key_mapping.get(raw_k.strip().lower())
            if not canonical_k:
                canonical_k = raw_k.strip().lower()
                
            if canonical_k == "restored":
                if isinstance(raw_vals, list):
                    val = raw_vals[0] if len(raw_vals) > 0 else None
                else:
                    val = raw_vals
                    
                if val is not None:
                    if isinstance(val, str):
                        normalized["restored"] = val.strip().lower() in ("true", "1", "yes")
                    else:
                        normalized["restored"] = bool(val)
                continue
                
            if not isinstance(raw_vals, list):
                raw_vals = [raw_vals] if raw_vals is not None else []
                
            cleaned_vals = []
            for item in raw_vals:
                norm_item = _normalize_lookup(str(item))
                if not norm_item:
                    continue
                
                mapped_item = None
                if canonical_k == "commodities":
                    mapped_item = self.commodity_map.get(norm_item, norm_item)
                elif canonical_k == "storage_facility_types":
                    mapped_item = self.facility_map.get(norm_item, norm_item)
                elif canonical_k == "material_types":
                    mapped_item = self.material_map.get(norm_item, norm_item)
                elif canonical_k == "project_status":
                    mapped_item = self.status_map.get(norm_item, norm_item)
                elif canonical_k == "regions":
                    mapped_item = self.region_map.get(norm_item, norm_item)
                elif canonical_k == "companies":
                    mapped_item = self.company_map.get(norm_item, norm_item)
                elif canonical_k == "site_names":
                    mapped_item = self.site_map.get(norm_item, norm_item)
                elif canonical_k == "countries":
                    mapped_item = self.country_map.get(norm_item, norm_item)
                else:
                    mapped_item = norm_item
                    
                if mapped_item is not None:
                    if isinstance(mapped_item, list):
                        for sub_item in mapped_item:
                            if sub_item not in cleaned_vals:
                                cleaned_vals.append(sub_item)
                    else:
                        if mapped_item not in cleaned_vals:
                            cleaned_vals.append(mapped_item)
                            
            if cleaned_vals:
                normalized[canonical_k] = cleaned_vals
                
        # Perform geographical inference
        if "regions" in normalized:
            inferred_countries = []
            for r in normalized["regions"]:
                country = self.region_to_country.get(r)
                if country:
                    inferred_countries.append(country)
            if inferred_countries:
                existing_countries = normalized.setdefault("countries", [])
                for c in inferred_countries:
                    if c not in existing_countries:
                        existing_countries.append(c)
                        
        return normalized

    def normalize(self, raw_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Translates fields and values to database standards.
        """
        result = {
            "intent": str(raw_json.get("intent", "search")).strip().lower(),
            "filters": {},
            "fulltext": [str(x).strip() for x in raw_json.get("fulltext", []) if str(x).strip()],
            "needs_rag": bool(raw_json.get("needs_rag", False))
        }
        
        raw_filters = raw_json.get("filters", {})
        if isinstance(raw_filters, dict) and raw_filters:
            result["filters"] = self._normalize_dict_filters(raw_filters)
            
        raw_neg_filters = raw_json.get("negated_filters", {})
        if isinstance(raw_neg_filters, dict) and raw_neg_filters:
            normalized_neg = self._normalize_dict_filters(raw_neg_filters)
            if normalized_neg:
                result["negated_filters"] = normalized_neg
                
        return result


# ----------------------------------------------------
# 3. Validator
# ----------------------------------------------------

class Validator:
    """
    Validates structure, keys, types, and values in the normalized semantic JSON.
    """
    def __init__(self):
        self.allowed_fields = {
            "countries",
            "regions",
            "commodities",
            "material_types",
            "storage_facility_types",
            "project_status",
            "companies",
            "site_names",
            "unfc_e",
            "unfc_f",
            "unfc_g",
            "restored"
        }
        self.allowed_intents = {"search", "hybrid", "generic_qa"}

    def _validate_dict_filters(self, filters_dict: Dict[str, Any]) -> Dict[str, Any]:
        validated = {}
        for k, v in filters_dict.items():
            if k not in self.allowed_fields:
                print(f"[Validator Warning] Removing unallowed filter field: '{k}'")
                continue
                
            if k == "restored":
                if not isinstance(v, bool):
                    print(f"[Validator Warning] Field 'restored' must be boolean, got '{type(v)}'. Removing.")
                    continue
                validated["restored"] = v
            else:
                if not isinstance(v, list):
                    print(f"[Validator Warning] Field '{k}' must be a list, got '{type(v)}'. Converting.")
                    v = [v] if v is not None else []
                str_list = [str(x).strip() for x in v if x is not None and str(x).strip()]
                if str_list:
                    validated[k] = str_list
        return validated

    def validate(self, normalized_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates keys, intent, and types. Removes illegal elements.
        """
        intent = normalized_json.get("intent", "search")
        if intent not in self.allowed_intents:
            intent = "search"
            
        validated = {
            "intent": intent,
            "filters": {},
            "fulltext": [str(x).strip() for x in normalized_json.get("fulltext", []) if str(x).strip()],
            "needs_rag": bool(normalized_json.get("needs_rag", False))
        }
        
        pos_filters = normalized_json.get("filters", {})
        if isinstance(pos_filters, dict):
            validated["filters"] = self._validate_dict_filters(pos_filters)
            
        neg_filters = normalized_json.get("negated_filters", {})
        if isinstance(neg_filters, dict) and neg_filters:
            valid_neg = self._validate_dict_filters(neg_filters)
            if valid_neg:
                validated["negated_filters"] = valid_neg
                
        return validated


# ----------------------------------------------------
# 4. Query Builder
# ----------------------------------------------------

class QueryBuilder:
    """
    Translates the validated semantic JSON into Solr q and fq query parameters.
    """
    def build(self, validated_json: Dict[str, Any]) -> Dict[str, Any]:
        q_list = validated_json.get("fulltext", [])
        
        if q_list:
            escaped_terms = []
            for term in q_list:
                cleaned = term.replace('"', '\\"')
                if " " in cleaned:
                    escaped_terms.append(f'"{cleaned}"')
                else:
                    escaped_terms.append(cleaned)
            q_str = " ".join(escaped_terms)
        else:
            q_str = "*:*"
            
        fq_list = []
        
        # 1. Positive filters
        pos_filters = validated_json.get("filters", {})
        for field, values in pos_filters.items():
            if field == "restored":
                fq_list.append(f"restored:{str(values).lower()}")
            else:
                if len(values) == 1:
                    fq_list.append(f'{field}:"{values[0]}"')
                elif len(values) > 1:
                    or_expr = " OR ".join(f'"{v}"' for v in values)
                    fq_list.append(f"{field}:({or_expr})")
                    
        # 2. Negated filters
        neg_filters = validated_json.get("negated_filters", {})
        for field, values in neg_filters.items():
            if field == "restored":
                fq_list.append(f"-restored:{str(values).lower()}")
            else:
                if len(values) == 1:
                    fq_list.append(f'-{field}:"{values[0]}"')
                elif len(values) > 1:
                    or_expr = " OR ".join(f'"{v}"' for v in values)
                    fq_list.append(f"-{field}:({or_expr})")
                    
        return {
            "q": q_str,
            "fq": fq_list
        }


# ----------------------------------------------------
# 5. Pipeline Orchestrator
# ----------------------------------------------------

class NLUPipeline:
    """
    Full pipeline: Semantic Parser -> Normalizer -> Validator -> Query Builder.
    """
    def __init__(self, provider="openai"):
        self.provider = provider
        if provider == "rules":
            self.parser = RulesSemanticParser()
        else:
            self.parser = LLMSemanticParser(provider=provider)
            
        self.normalizer = Normalizer()
        self.validator = Validator()
        self.query_builder = QueryBuilder()

    def process(self, query: str) -> Dict[str, Any]:
        raw_json = self.parser.parse(query)
        normalized = self.normalizer.normalize(raw_json)
        validated = self.validator.validate(normalized)
        solr_query = self.query_builder.build(validated)
        
        return {
            "semantic_json": validated,
            "solr_query": solr_query
        }
