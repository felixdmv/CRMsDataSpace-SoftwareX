import os
import sys
from pathlib import Path
from typing import Dict, Any

# Ensure all subdirectories are in sys.path so imports work seamlessly
ROOT = Path(__file__).resolve().parent
sys.path.extend([
    str(ROOT),
    str(ROOT / "common"),
    str(ROOT / "variants"),
    str(ROOT / "apps"),
    str(ROOT / "evaluation"),
    str(ROOT / "utils"),
    str(ROOT / "experiments")
])

# Import default fallback (original)
try:
    from variants.original.agent import process_chat_message as original_process
except ImportError:
    original_process = None

def get_active_variant_name() -> str:
    """
    Returns the active architectural variant from environment variable,
    defaulting to 'v4_strict_grounding_citations'.
    """
    # Load .env explicitly if not loaded
    from llm_client import load_dotenv
    load_dotenv(ROOT / ".env")
    
    variant = os.getenv("CRMS_ARCH_VARIANT", "v4_strict_grounding_citations").strip().lower()
    # Normalize aliases
    if variant in ("original", "base"):
        return "original"
    elif variant in ("v1", "v1_intent", "v1_intent_classification"):
        return "v1_intent_classification"
    elif variant in ("v2", "v2_hybrid", "v2_hybrid_search_rerank"):
        return "v2_hybrid_search_rerank"
    elif variant in ("v3", "v3_schema", "v3_json_schema"):
        return "v3_json_schema"
    elif variant in ("v4", "v4_grounding", "v4_strict_grounding_citations"):
        return "v4_strict_grounding_citations"
    return "v4_strict_grounding_citations"

def process_chat_message(query: str, provider: str = "openai") -> Dict[str, Any]:
    """
    Routes chat message processing to the active architectural variant.
    """
    variant_name = get_active_variant_name()
    print(f"[INFO] Routing query to active variant: '{variant_name}' using provider '{provider}'")
    
    try:
        if variant_name == "original":
            if original_process:
                return original_process(query, provider=provider)
            else:
                raise ImportError("Original agent not found.")
                
        elif variant_name == "v1_intent_classification":
            from variants.v1_intent_classification.agent import process_chat_message as v1_process
            return v1_process(query, provider=provider)
            
        elif variant_name == "v2_hybrid_search_rerank":
            from variants.v2_hybrid_search_rerank.agent import process_chat_message as v2_process
            return v2_process(query, provider=provider)
            
        elif variant_name == "v3_json_schema":
            from variants.v3_json_schema.agent import process_chat_message as v3_process
            return v3_process(query, provider=provider)
            
        elif variant_name == "v4_strict_grounding_citations":
            from variants.v4_strict_grounding_citations.agent import process_chat_message as v4_process
            return v4_process(query, provider=provider)
            
    except Exception as e:
        print(f"[ERROR] Active variant '{variant_name}' failed: {e}. Falling back to rules-based processing.")
        # Fallback to original rules-based parser if LLM fails
        if original_process:
            return original_process(query, provider="rules")
            
    # Basic fallback if everything fails
    return {
        "extracted_json": {"filters": {}, "intent": "error"},
        "solr_query": {"q": "*:*", "fq": []},
        "api_results": [],
        "response_text": f"Error al procesar la consulta con la variante '{variant_name}'. Por favor, compruebe la configuración."
    }

if __name__ == "__main__":
    # Command-line testing
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("query", nargs="?", default="Dime escombreras de cobre en España")
    parser.add_argument("--provider", default="gemini")
    parser.add_argument("--variant", default=None)
    args = parser.parse_args()
    
    if args.variant:
        os.environ["CRMS_ARCH_VARIANT"] = args.variant
        
    print(f"Active Architecture Variant: {get_active_variant_name()}")
    res = process_chat_message(args.query, provider=args.provider)
    print("\nResponse Text:")
    print(res.get("response_text"))
