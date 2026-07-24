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
            "description": "Query intent: filter_search for database search, or generic_qa for general conversation",
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
        "needs_rag": {"type": "BOOLEAN"}
    },
    "required": ["intent", "filters", "fulltext", "needs_rag"]
}

# ----------------------------------------------------------------------
# 2. Variant 1: Few-Shot System Prompt
# ----------------------------------------------------------------------
SYSTEM_PROMPT_FEWSHOT = """You are a deterministic Semantic Parser for the European Critical Raw Materials (CRMs) Data Space.
Your sole task is to translate the user query into a clean, structured JSON search query.

Allowed filter fields:
- countries: lowercase English country names e.g. ["spain", "portugal", "germany", "france", "sweden", "finland", "poland", "italy", "greece", "ireland", "austria", "czechia"]
- commodities: lowercase English raw materials e.g. ["lithium", "cobalt", "tungsten", "rare earth elements", "nickel", "copper", "tin", "tantalum", "graphite", "titanium", "pge", "manganese"]
- storage_facility_types: asset types e.g. ["tailings storage facility", "waste dump", "stockpile", "pond"]
- project_status: status e.g. ["active", "inactive", "care and maintenance", "development"]
- environmental_flags: e.g. ["acid mine drainage potential", "water emergence", "social opposition", "not restored"]
- restored: true | false

--- FEW-SHOT EXAMPLES ---

Example 1:
User: "Muestra escombreras de litio y cobalto en España y Finlandia que estén activas"
JSON:
{
  "intent": "filter_search",
  "filters": {
    "countries": ["spain", "finland"],
    "commodities": ["lithium", "cobalt"],
    "storage_facility_types": ["waste dump", "tailings storage facility"],
    "project_status": ["active"]
  },
  "fulltext": [],
  "needs_rag": false
}

Example 2:
User: "Balsas de wolframio sin restaurar en Alemania"
JSON:
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

Example 3:
User: "Hello, how can this system assist me with European critical raw materials?"
JSON:
{
  "intent": "generic_qa",
  "filters": {},
  "fulltext": [],
  "needs_rag": false
}
"""

# ----------------------------------------------------------------------
# 3. Pipeline Stages: Normalizer, Validator, QueryBuilder
# ----------------------------------------------------------------------

class Normalizer:
    """Normalizes extracted raw LLM JSON tokens into canonical Solr terms."""
    
    COMMODITY_MAP = {
        "wolframio": "tungsten", "wolfram": "tungsten", "tungsteno": "tungsten",
        "litio": "lithium", "cobalto": "cobalt",
        "tierras raras": "rare earth elements", "ree": "rare earth elements",
        "niquel": "nickel", "níquel": "nickel",
        "cobre": "copper", "estaño": "tin",
        "tantalo": "tantalum", "tántalo": "tantalum", "coltan": "tantalum", "coltán": "tantalum",
        "grafito": "graphite", "titanio": "titanium", "manganeso": "manganese",
        "platino": "pge"
    }

    COUNTRY_MAP = {
        "españa": "spain", "espana": "spain",
        "alemania": "germany", "francia": "france",
        "suecia": "sweden", "finlandia": "finland",
        "polonia": "poland", "italia": "italy",
        "grecia": "greece", "irlanda": "ireland",
        "chequia": "czechia", "república checa": "czechia"
    }

    def normalize(self, raw_json: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(raw_json, dict):
            raw_json = {}
            
        filters = raw_json.get("filters", {})
        if not isinstance(filters, dict):
            filters = {}
            
        # Normalize commodities
        norm_comms = []
        for c in filters.get("commodities", []):
            c_clean = str(c).lower().strip()
            c_mapped = self.COMMODITY_MAP.get(c_clean, c_clean)
            if c_mapped not in norm_comms:
                norm_comms.append(c_mapped)
        filters["commodities"] = norm_comms

        # Normalize countries
        norm_countries = []
        for co in filters.get("countries", []):
            co_clean = str(co).lower().strip()
            co_mapped = self.COUNTRY_MAP.get(co_clean, co_clean)
            if co_mapped not in norm_countries:
                norm_countries.append(co_mapped)
        filters["countries"] = norm_countries

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
        q = " AND ".join(fulltext_terms) if fulltext_terms else "*:*"

        return {
            "q": q,
            "fq": fq_list,
            "defType": "edismax",
            "qf": "site_name^2.0 commodities^1.5 description^1.0",
            "fl": "id,site_name,country,region,commodities,storage_facility_type,location,project_status",
            "rows": 100
        }
