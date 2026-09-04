import os
import sys
import json
from pathlib import Path
from typing import Dict, Any

# Adjust paths to import common modules
ROOT = Path(__file__).resolve().parents[3]
CODE_DIR = ROOT / "code"
sys.path.extend([str(CODE_DIR), str(CODE_DIR / "common")])

from llm_client import call_llm, extract_json_block
from mock_api import query_data_space_solr
from nlu_pipeline import Normalizer, Validator, QueryBuilder

# 1. Define JSON schemas for Gemini responseSchema enforcement
NLU_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "intent": {
            "type": "STRING",
            "description": "Classification of search query: filter_search, hybrid, or generic_qa",
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
                "companies": {"type": "ARRAY", "items": {"type": "STRING"}},
                "site_names": {"type": "ARRAY", "items": {"type": "STRING"}},
                "environmental_flags": {"type": "ARRAY", "items": {"type": "STRING"}},
                "restored": {"type": "BOOLEAN"}
            }
        },
        "fulltext": {"type": "ARRAY", "items": {"type": "STRING"}},
        "needs_rag": {"type": "BOOLEAN"}
    },
    "required": ["intent", "filters", "fulltext", "needs_rag"]
}

NLG_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "respuesta": {
            "type": "STRING",
            "description": "Natural language summary of findings, localized in Spanish"
        },
        "hallazgos_clave": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
            "description": "List of key facts extracted from the database results"
        },
        "fuentes": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "doc_id": {"type": "STRING", "description": "ID or name of site/document"},
                    "seccion": {"type": "STRING", "description": "Section, province, or region reference"},
                    "score_confianza": {"type": "NUMBER", "description": "Confidence score between 0 and 1"}
                },
                "required": ["doc_id", "score_confianza"]
            }
        }
    },
    "required": ["respuesta", "hallazgos_clave", "fuentes"]
}

NLU_SYSTEM_PROMPT = """You are a Semantic Parser for the CRMs Data Space.
Parse the user query into search filters.
You MUST output ONLY JSON conforming to the requested schema."""

NLG_SYSTEM_PROMPT = """You are a response synthesizer for the CRMs Data Space.
Synthesize database results into a structured natural language JSON response.
You MUST output ONLY JSON conforming to the requested schema."""

def process_chat_message(query: str, provider: str = "gemini") -> Dict[str, Any]:
    # Step 1: Semantic Parsing with schema enforcement
    raw_nlu = call_llm(
        system_prompt=NLU_SYSTEM_PROMPT,
        user_prompt=f"Parse the query: \"{query}\"",
        provider=provider,
        json_mode=True,
        response_schema=NLU_RESPONSE_SCHEMA
    )
    nlu_json = extract_json_block(raw_nlu)
    
    # Run through pipeline normalizer and validator
    normalizer = Normalizer()
    validator = Validator()
    query_builder = QueryBuilder()
    
    normalized = normalizer.normalize(nlu_json)
    validated = validator.validate(normalized)
    
    # Backward compatibility mappings
    validated["needs_report_context"] = validated.get("needs_rag", False)
    validated["needs_database_filtering"] = (validated.get("intent") != "generic_qa")
    validated["answer_mode"] = "structured_filters_and_rag" if validated.get("needs_rag") else "structured_filters"
    
    # Step 2: Query database
    solr_query = query_builder.build(validated)
    api_results = query_data_space_solr(solr_query["q"], solr_query["fq"])
    
    # Step 3: Synthesis with schema enforcement
    user_prompt = f"""
Consulta del Usuario: {query}
Resultados de base de datos ({len(api_results)} resultados):
{json.dumps(api_results, indent=2, ensure_ascii=False)}
"""
    
    raw_nlg = call_llm(
        system_prompt=NLG_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        provider=provider,
        json_mode=True,
        response_schema=NLG_RESPONSE_SCHEMA
    )
    nlg_json = extract_json_block(raw_nlg)
    
    # Convert structured response to natural response text for UI rendering
    resp_text = nlg_json.get("respuesta", "")
    key_findings = nlg_json.get("hallazgos_clave", [])
    if key_findings:
        resp_text += "\n\nHallazgos Clave:\n" + "\n".join(f"- {f}" for f in key_findings)
        
    return {
        "extracted_json": validated,
        "solr_query": solr_query,
        "api_results": api_results,
        "response_text": resp_text,
        "structured_response": nlg_json
    }
