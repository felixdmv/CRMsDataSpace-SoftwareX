"""
SoftwareX Agent Orchestrator:
Combines Few-Shot prompting (v1) with JSON Schema validation (v3)
to drive Apache Solr filtering and GIS visualization on 100 European CRM sites.
"""

import json
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

def generate_natural_response(query: str, validated_nlu: Dict[str, Any], solr_results: Dict[str, Any], provider: str) -> str:
    """Generates a professional natural language summary of search results."""
    num_found = solr_results.get("numFound", 0)
    docs = solr_results.get("docs", [])
    
    if num_found == 0:
        return f"No synthetic European tailings or mining sites were found matching your criteria ({json.dumps(validated_nlu.get('filters', {}))}). Try broadening the country or commodity filters."

    # Sample top 3 sites for summary
    top_sites = docs[:3]
    summary_items = []
    for s in top_sites:
        summary_items.append(f"- **{s['site_name']}** ({s['country_name']}): {s['storage_facility_label']} with {s['commodities_label']}. Status: *{s['project_status']}*.")
        
    sites_text = "\n".join(summary_items)
    
    system_prompt = (
        "You are the intelligent assistant for the European Critical Raw Materials (CRMs) Data Space.\n"
        "Synthesize search results for scientific reviewers in clear, concise language."
    )
    user_prompt = f"""
User Query: "{query}"
Extracted Filters: {json.dumps(validated_nlu.get('filters', {}))}
Matched Sites ({num_found} total in dataset):
{sites_text}

Provide a concise, scientific summary of findings in English or Spanish according to query language.
"""
    # Direct fast fallback narrative generation for instant responsive UI
    narrative = f"Located **{num_found} synthetic European CRM facilities** matching your query filters.\n\n"
    narrative += "**Key Matching Sites:**\n" + sites_text
    if num_found > 3:
        narrative += f"\n\n*...and {num_found - 3} additional facilities visualised on the map.*"
    return narrative

def process_chat_message(query: str, provider: str = "mock") -> Dict[str, Any]:
    """
    Main entry point for processing chat queries in SoftwareX application.
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
    
    # 3. Solr query construction & execution
    solr_query = query_builder.build(validated)
    solr_results = query_data_space_solr(solr_query["q"], solr_query["fq"])
    
    matched_docs = solr_results.get("docs", [])
    matched_ids = [d["id"] for d in matched_docs]
    
    # 4. Extract active filter badges for visual GIS map display
    active_map_filters = []
    filters = validated.get("filters", {})
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

    # 5. Generate natural language answer
    if validated["intent"] == "generic_qa" and not active_map_filters:
        response_text = "Welcome to the European CRMs Data Space Explorer. You can ask queries like: 'Show active lithium tailings in Spain and Finland' or 'Find tungsten dumps in Germany'."
        matched_ids = [d["id"] for d in load_dataset()] # Show all 100 on generic QA
    else:
        response_text = generate_natural_response(query, validated, solr_results, provider)
        
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
