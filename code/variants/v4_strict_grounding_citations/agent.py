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
from nlu_pipeline import NLUPipeline

GROUNDING_SYSTEM_PROMPT = """Responde única y exclusivamente utilizando la información proporcionada en el contexto de Solr.
Si la respuesta no se puede deducir de los datos provistos, responde EXACTAMENTE con:
{"error": "Información no disponible en el espacio de datos"}

Está terminantemente prohibido utilizar conocimiento externo o asumir datos.

Tu salida debe ser un objeto JSON estructurado con el siguiente formato:
{
  "respuesta": "La síntesis de la respuesta...",
  "fuentes": [
    {
      "doc_id": "nombre o ID del documento/sitio",
      "seccion": "provincia, región o sección del documento",
      "score_confianza": 0.95
    }
  ]
}
"""

def process_chat_message(query: str, provider: str = "openai") -> Dict[str, Any]:
    # 1. NLU Extraction
    pipeline = NLUPipeline(provider=provider)
    pipeline_res = pipeline.process(query)
    
    validated_json = pipeline_res["semantic_json"]
    solr_query = pipeline_res["solr_query"]
    
    # If generic_qa (greetings, off-topic), bypass Solr search and answer cordially
    if validated_json.get("intent") == "generic_qa":
        response_text = call_llm(
            "Responde al saludo de forma amigable y concisa.",
            query,
            provider=provider
        )
        return {
            "extracted_json": validated_json,
            "solr_query": solr_query,
            "api_results": [],
            "response_text": response_text
        }
        
    # 2. Query database (Solr context)
    api_results = query_data_space_solr(solr_query["q"], solr_query["fq"])
    
    # 3. Grounded Synthesis
    if provider == "rules":
        from variants.original.agent import generate_natural_response
        response_text = generate_natural_response(query, validated_json, api_results, provider="rules")
        return {
            "extracted_json": validated_json,
            "solr_query": solr_query,
            "api_results": api_results,
            "response_text": response_text
        }
        
    if not api_results:
        # Strict context failure: no results found
        error_json = {"error": "Información no disponible en el espacio de datos"}
        return {
            "extracted_json": validated_json,
            "solr_query": solr_query,
            "api_results": [],
            "response_text": "Información no disponible en el espacio de datos",
            "structured_response": error_json
        }
        
    user_prompt = f"""
Consulta del Usuario: {query}
Resultados del Espacio de Datos:
{json.dumps(api_results, indent=2, ensure_ascii=False)}

Genera la respuesta estructurada siguiendo las reglas de restricción estricta.
"""
    
    raw_nlg = call_llm(
        system_prompt=GROUNDING_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        provider=provider,
        json_mode=True
    )
    
    nlg_json = extract_json_block(raw_nlg)
    
    # Handle error block returned by the LLM
    if "error" in nlg_json:
        response_text = nlg_json["error"]
    else:
        # Build answer text with citations appended
        response_text = nlg_json.get("respuesta", "")
        sources = nlg_json.get("fuentes", [])
        if sources:
            response_text += "\n\nFuentes:"
            for src in sources:
                doc = src.get("doc_id", "Sin ID")
                sec = src.get("seccion")
                score = src.get("score_confianza", 1.0)
                sec_part = f", Sección: {sec}" if sec else ""
                response_text += f"\n- {doc}{sec_part} (Confianza: {score:.2f})"
                
    return {
        "extracted_json": validated_json,
        "solr_query": solr_query,
        "api_results": api_results,
        "response_text": response_text,
        "structured_response": nlg_json
    }
