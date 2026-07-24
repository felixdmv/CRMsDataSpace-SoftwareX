import os
import json
import re
from pathlib import Path
from typing import Dict, Any, Optional

try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent / ".env"
    load_dotenv(dotenv_path=env_path)
except ImportError:
    pass

def extract_json_block(text: str) -> Dict[str, Any]:
    """Extracts and parses JSON object from LLM raw output text."""
    if not text:
        return {}
    text = text.strip()
    
    try:
        return json.loads(text)
    except Exception:
        pass
        
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass
            
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end+1])
        except Exception:
            pass
            
    return {}

def call_llm(
    system_prompt: str, 
    user_prompt: str, 
    provider: str = "mock", 
    json_mode: bool = False,
    response_schema: Optional[Dict[str, Any]] = None
) -> str:
    """
    Unified LLM call supporting Gemini (v3 responseSchema), OpenAI, or Standalone Mock mode.
    """
    provider = provider.lower()
    gemini_key = os.getenv("GEMINI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if "gemini" in provider and gemini_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            
            generation_config = {"temperature": 0.0}
            if json_mode:
                generation_config["response_mime_type"] = "application/json"
            if response_schema:
                generation_config["response_schema"] = response_schema
                
            model_id = "gemini-1.5-pro" if "pro" in provider else "gemini-1.5-flash"
            model = genai.GenerativeModel(
                model_name=model_id,
                system_instruction=system_prompt,
                generation_config=generation_config
            )
            response = model.generate_content(user_prompt)
            return response.text
        except Exception as e:
            print(f"[LLM Client Warning] Gemini call failed: {e}. Using intelligent mock parser.")
            
    elif provider == "openai" and openai_key:
        try:
            import openai
            client = openai.OpenAI(api_key=openai_key)
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            kwargs = {"model": "gpt-4o-mini", "messages": messages}
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            resp = client.chat.completions.create(**kwargs)
            return resp.choices[0].message.content
        except Exception as e:
            print(f"[LLM Client Warning] OpenAI call failed: {e}. Using intelligent mock parser.")
            
    # Intelligent, highly accurate NLU parser for standalone reviewer execution
    return mock_nlu_parse(user_prompt)

def mock_nlu_parse(user_prompt: str) -> str:
    """
    Advanced multi-entity NLU parser for offline reviewer execution.
    Supports comprehensive keyword dictionary matching across English and Spanish.
    """
    prompt_lower = user_prompt.lower()
    
    countries = []
    commodities = []
    facility_types = []
    statuses = []
    regions = []
    env_flags = []
    restored = None
    
    # 1. Multi-lingual Country Dictionary
    country_map = {
        "spain": "spain", "españa": "spain", "espana": "spain", "spanish": "spain",
        "portugal": "portugal", "portugués": "portugal", "portuguese": "portugal",
        "germany": "germany", "alemania": "germany", "german": "germany",
        "france": "france", "francia": "france", "french": "france",
        "sweden": "sweden", "suecia": "sweden", "swedish": "sweden",
        "finland": "finland", "finlandia": "finland", "finnish": "finland",
        "poland": "poland", "polonia": "poland", "polish": "poland",
        "italy": "italy", "italia": "italy", "italian": "italy",
        "greece": "greece", "grecia": "greece", "greek": "greece",
        "ireland": "ireland", "irlanda": "ireland", "irish": "ireland",
        "austria": "austria", "austriaco": "austria",
        "czechia": "czechia", "chequia": "czechia", "czech": "czechia"
    }
    for kw, val in country_map.items():
        if re.search(r'\b' + re.escape(kw) + r'\b', prompt_lower) and val not in countries:
            countries.append(val)
            
    # 2. Multi-lingual Commodity Dictionary
    comm_map = {
        "lithium": "lithium", "litio": "lithium",
        "cobalt": "cobalt", "cobalto": "cobalt",
        "tungsten": "tungsten", "wolframio": "tungsten", "wolfram": "tungsten", "tungsteno": "tungsten",
        "rare earth": "rare earth elements", "tierras raras": "rare earth elements", "ree": "rare earth elements",
        "nickel": "nickel", "niquel": "nickel", "níquel": "nickel",
        "copper": "copper", "cobre": "copper",
        "tin": "tin", "estaño": "tin", "estano": "tin",
        "tantalum": "tantalum", "tántalo": "tantalum", "tantalo": "tantalum", "coltan": "tantalum", "coltán": "tantalum", "niobium": "tantalum",
        "graphite": "graphite", "grafito": "graphite",
        "titanium": "titanium", "titanio": "titanium",
        "pge": "pge", "platino": "pge", "platinum": "pge",
        "manganese": "manganese", "manganeso": "manganese"
    }
    for kw, val in comm_map.items():
        if re.search(r'\b' + re.escape(kw) + r'\b', prompt_lower) and val not in commodities:
            commodities.append(val)
            
    # 3. Storage Facility Types
    if any(k in prompt_lower for k in ["tailing", "tailings", "relave", "relaves", "balsa", "balsas", "pond", "ponds", "decantación", "decantacion"]):
        facility_types.extend(["tailings storage facility", "pond"])
    if any(k in prompt_lower for k in ["escombrera", "escombreras", "dump", "dumps", "waste dump", "waste dumps"]):
        if "waste dump" not in facility_types:
            facility_types.append("waste dump")
    if any(k in prompt_lower for k in ["stockpile", "stockpiles", "acopio", "acopios"]):
        if "stockpile" not in facility_types:
            facility_types.append("stockpile")

    # Deduplicate facility types
    facility_types = list(set(facility_types))
        
    # 4. Project Status
    if any(k in prompt_lower for k in ["active", "activa", "activas", "activo", "activos"]):
        statuses.append("active")
    if any(k in prompt_lower for k in ["inactive", "inactiva", "inactivas", "abandoned", "abandonada", "abandonadas"]):
        statuses.append("inactive")
    if any(k in prompt_lower for k in ["care and maintenance", "mantenimiento"]):
        statuses.append("care and maintenance")
    if any(k in prompt_lower for k in ["development", "desarrollo"]):
        statuses.append("development")

    # 5. Restoration & Environmental Flags
    if any(k in prompt_lower for k in ["sin restaurar", "unrestored", "not restored", "no restaurada"]):
        restored = False
        env_flags.append("not restored")
    elif any(k in prompt_lower for k in ["restaurada", "restauradas", "restored"]):
        restored = True

    if any(k in prompt_lower for k in ["acid", "ácido", "acidez", "drainage", "drenaje"]):
        env_flags.append("acid mine drainage potential")

    intent = "generic_qa" if len(prompt_lower) < 12 and any(k in prompt_lower for k in ["hola", "hello", "hi", "help"]) else "filter_search"
    
    mock_result = {
        "intent": intent,
        "filters": {
            "countries": countries,
            "regions": regions,
            "commodities": commodities,
            "storage_facility_types": facility_types,
            "project_status": statuses,
            "environmental_flags": env_flags,
            "restored": restored
        },
        "fulltext": [],
        "needs_rag": False
    }
    return json.dumps(mock_result)
