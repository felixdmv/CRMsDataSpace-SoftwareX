import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List

# Adjust paths to import common modules
ROOT = Path(__file__).resolve().parents[3]
CODE_DIR = ROOT / "code"
sys.path.extend([str(CODE_DIR), str(CODE_DIR / "common")])

from llm_client import call_llm, extract_json_block
from mock_api import query_data_space_solr
from search import Retriever
from nlu_pipeline import NLUPipeline

def rerank_and_curate_context(query: str, raw_chunks: List[Dict[str, Any]], threshold: float = 0.20, max_chunks: int = 3) -> List[Dict[str, Any]]:
    """
    Reranks and curates retrieved document chunks.
    Filters out noise (chunks with similarity score below threshold)
    and retains only the top max_chunks with the highest information density.
    """
    # Filter by similarity score threshold
    filtered_chunks = [chunk for chunk in raw_chunks if chunk.get("score", 0.0) >= threshold]
    
    # Sort by score descending (Rerank)
    sorted_chunks = sorted(filtered_chunks, key=lambda x: x.get("score", 0.0), reverse=True)
    
    # Select top K highest-density fragments
    return sorted_chunks[:max_chunks]

def process_chat_message(query: str, provider: str = "openai") -> Dict[str, Any]:
    # 1. Run standard NLU pipeline to extract intent and filters
    pipeline = NLUPipeline(provider=provider)
    pipeline_res = pipeline.process(query)
    
    validated_json = pipeline_res["semantic_json"]
    solr_query = pipeline_res["solr_query"]
    
    # 2. Database query (Solr)
    api_results = query_data_space_solr(solr_query["q"], solr_query["fq"])
    
    # 3. Vector search / RAG retrieval if needed (Hybrid Search)
    curated_chunks = []
    if validated_json.get("needs_rag", False) or "estabilidad" in query.lower() or "informe" in query.lower():
        try:
            retriever = Retriever()
            # Perform vector search on the PDF index
            raw_chunks = retriever.search(query, k=10)
            
            # Curation & Reranking: filter out noise and sort
            curated_chunks = rerank_and_curate_context(query, raw_chunks, threshold=0.15, max_chunks=3)
        except Exception as e:
            print(f"[WARN] Vector retrieval failed: {e}. Index might not be built.")
            
    # 4. Generate final narrative response combining database results and curated document snippets
    system_prompt = (
        "Eres el agente inteligente del 'CRMs Data Space' (Espacio de Datos de Materias Críticas de la UE).\n"
        "Tu tarea es responder al usuario en lenguaje natural en castellano basándote en la información estructurada de la base de datos "
        "y los fragmentos de informes técnicos (RAG) proporcionados. No te inventes ningún dato. "
        "Resume la información de manera profesional y resalta los hallazgos clave."
    )
    
    context_data = {
        "database_results": api_results,
        "technical_document_snippets": [
            {
                "pdf": c.get("pdf"),
                "page": c.get("page"),
                "text": c.get("text"),
                "score": c.get("score")
            } for c in curated_chunks
        ]
    }
    
    user_prompt = f"""
Consulta del Usuario: {query}
Filtros Aplicados: {json.dumps(validated_json.get('filters', {}), ensure_ascii=False)}

INFORMACIÓN RECUPERADA (HÍBRIDA):
{json.dumps(context_data, indent=2, ensure_ascii=False)}

Por favor, redacta una respuesta coherente y estructurada al usuario en base a estos datos.
"""
    response_text = call_llm(system_prompt, user_prompt, provider=provider)
    
    # Format return dictionary to match web application requirements
    # Add mapped/found chunks to api_results/evidences so it renders in the UI
    res = {
        "extracted_json": validated_json,
        "solr_query": solr_query,
        "api_results": api_results,
        "response_text": response_text
    }
    
    if curated_chunks:
        # Map curated chunks as evidences for UI rendering
        res["evidences"] = [
            {
                "title": chunk.get("pdf", "Documento.pdf"),
                "page": chunk.get("page", 1),
                "score": chunk.get("score", 0.0),
                "entities": [f"Score: {chunk.get('score', 0.0):.2f}"],
                "snippet": chunk.get("text", "")
            } for chunk in curated_chunks
        ]
        
    return res
