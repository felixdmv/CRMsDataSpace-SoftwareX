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

SYSTEM_PROMPT = """You are a deterministical Semantic Parser for the CRMs Data Space (critical raw materials database).
Your sole task is to translate the user query into a clean, structured JSON search query using a closed schema.

The allowed database filter fields are:
- countries: list of lowercase English countries (e.g., ["spain", "portugal"])
- regions: list of lowercase English regions (e.g., ["galicia", "asturias", "andalucia", "castilla y leon", "extremadura"])
- commodities: list of lowercase English commodities (e.g., ["copper", "gold", "silver", "tungsten", "lithium", "tin", "cobalt", "zinc", "nickel"])
- storage_facility_types: list of lowercase English asset types: ["tailings storage facility", "waste dump", "stockpile", "pond"]
- material_types: list of lowercase English contents: ["tailings", "slag", "waste rock", "sludge"]
- project_status: list of lowercase status: ["active", "inactive", "care and maintenance", "development"]
- companies: list of lowercase managed companies (e.g., ["atalaya mining", "almonty industries", "orvana minerals", "infinity lithium", "valoriza mineria", "hunosa"])
- site_names: list of site names (e.g., ["Riotinto Project", "El Valle-Boinás", "Los Santos", "San Finx", "San José Valdeflórez", "Mina de Penouta"])
- environmental_flags: list of flags: ["water emergence", "not restored", "acid mine drainage potential", "social opposition"]
- restored: true | false | null (boolean representing restored status)
- unfc_e, unfc_f, unfc_g: list of UNFC codes (e.g., ["E1", "E2"], ["F1", "F2"], ["G1", "G2"])
- free_text_constraints: list of text search strings

You must classify the query's INTENT as one of:
- "filter_search": for database queries searching for sites, deposits, or facilities.
- "generic_qa": for greetings, off-topic, or queries asking who you are.
- "hybrid": for queries requesting technical document search (RAG) on reports/papers/PDFs.

Your output must be ONLY a valid JSON object matching the examples below. Do not output markdown code blocks or explanations.

--- FEW-SHOT EXAMPLES ---

Example 1 (Basic query):
User: "Dime escombreras de cobre en España"
JSON:
{
  "intent": "filter_search",
  "filters": {
    "countries": ["spain"],
    "storage_facility_types": ["waste dump"],
    "commodities": ["copper"]
  },
  "fulltext": [],
  "needs_rag": false
}

Example 2 (Complex filters & negation):
User: "Balsas de decantación con wolframio y estaño en Galicia pero que no sea en Pontevedra cerca de San Finx"
JSON:
{
  "intent": "filter_search",
  "filters": {
    "regions": ["galicia"],
    "storage_facility_types": ["pond", "tailings storage facility"],
    "commodities": ["tungsten", "tin"],
    "site_names": ["San Finx"],
    "free_text_constraints": ["cerca de san finx"]
  },
  "negated_filters": {
    "regions": ["pontevedra"]
  },
  "fulltext": [],
  "needs_rag": false
}

Example 3 (Environmental flag):
User: "Balsas sin restaurar en Andalucía con surgencias de agua"
JSON:
{
  "intent": "filter_search",
  "filters": {
    "regions": ["andalucia"],
    "storage_facility_types": ["pond", "tailings storage facility"],
    "restored": false,
    "environmental_flags": ["water emergence", "not restored"]
  },
  "fulltext": [],
  "needs_rag": false
}

Example 4 (Hybrid RAG query):
User: "¿Qué dice el informe sobre la estabilidad física de la balsa B de Penouta?"
JSON:
{
  "intent": "hybrid",
  "filters": {
    "storage_facility_types": ["pond", "tailings storage facility"],
    "site_names": ["Mina de Penouta"]
  },
  "fulltext": ["estabilidad física de la balsa b"],
  "needs_rag": true
}

Example 5 (Conversational greeting):
User: "Hola buenas tardes, ¿cómo estás y en qué puedes ayudarme?"
JSON:
{
  "intent": "generic_qa",
  "filters": {},
  "fulltext": [],
  "needs_rag": false
}
"""

def generate_natural_response(query: str, filters: Dict[str, Any], api_results: list, provider: str) -> str:
    system_prompt = (
        "Eres el agente inteligente del 'CRMs Data Space' (Espacio de Datos de Materias Críticas de la UE).\n"
        "Tu tarea es responder al usuario en lenguaje natural en base a los resultados de búsqueda proporcionados en JSON.\n"
        "Describe las minas o balsas encontradas, indicando su localización, compañía y minerales de interés. Sé conciso y claro en castellano."
    )
    user_prompt = f"""
Consulta Original: {query}
Resultados de base de datos ({len(api_results)} resultados):
{json.dumps(api_results, indent=2, ensure_ascii=False)}

Por favor, redacta una respuesta profesional al usuario. Si no hay resultados, indícalo amablemente.
"""
    return call_llm(system_prompt, user_prompt, provider=provider)

def process_chat_message(query: str, provider: str = "openai") -> Dict[str, Any]:
    # 1. Ask LLM to parse using strict few-shot prompt
    raw_response = call_llm(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=f"User Query: \"{query}\"\nJSON Output:",
        provider=provider,
        json_mode=True
    )
    
    # 2. Parse and normalize
    raw_json = extract_json_block(raw_response)
    
    # Run through pipeline normalizer and validator to guarantee output contracts
    normalizer = Normalizer()
    validator = Validator()
    query_builder = QueryBuilder()
    
    normalized = normalizer.normalize(raw_json)
    validated = validator.validate(normalized)
    
    # Backward compatibility mappings
    validated["needs_report_context"] = validated.get("needs_rag", False)
    validated["needs_database_filtering"] = (validated.get("intent") != "generic_qa")
    validated["answer_mode"] = "structured_filters_and_rag" if validated.get("needs_rag") else "structured_filters"
    
    # 3. Build Solr parameters
    solr_query = query_builder.build(validated)
    
    # 4. Search
    api_results = query_data_space_solr(solr_query["q"], solr_query["fq"])
    
    # 5. Synthesize NLG response
    if validated["intent"] == "generic_qa":
        # Pure conversational response without querying database results
        response_text = call_llm(
            "Responde al saludo o pregunta del usuario amablemente en castellano como el asistente del CRMs Data Space.",
            query,
            provider=provider
        )
    else:
        response_text = generate_natural_response(query, validated, api_results, provider)
        
    return {
        "extracted_json": validated,
        "solr_query": solr_query,
        "api_results": api_results,
        "response_text": response_text
    }

if __name__ == "__main__":
    q = "Dime escombreras de wolframio activas en Salamanca"
    print(f"Query: {q}")
    res = process_chat_message(q, provider="gemini")
    print(json.dumps(res, indent=2, ensure_ascii=False))
