import os
import json
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

# Load .env variables
def load_dotenv(dotenv_path: Path) -> None:
    if not dotenv_path.exists():
        return
    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]
        if key and key not in os.environ:
            os.environ[key] = value

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

def http_post_json(url: str, headers: dict, payload: dict, timeout: int = 120) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={**headers, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} calling {url}: {detail}") from exc

def call_openai(system_prompt: str, user_prompt: str, model: str = None, json_mode: bool = False) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment.")
    
    model = model or os.getenv("OPENAI_MODEL", "gpt-4o")
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.0
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
        
    response = http_post_json(
        "https://api.openai.com/v1/chat/completions",
        {"Authorization": f"Bearer {api_key}"},
        payload,
    )
    return response["choices"][0]["message"]["content"]

def call_gemini(system_prompt: str, user_prompt: str, model: str = None, json_mode: bool = False, response_schema: Optional[dict] = None) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment.")
        
    model = model or os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{urllib.parse.quote(model)}:generateContent?key={urllib.parse.quote(api_key)}"
    
    payload = {
        "system_instruction": {
            "parts": [{"text": system_prompt}]
        },
        "contents": [
            {"parts": [{"text": user_prompt}]}
        ],
        "generationConfig": {
            "temperature": 0.0
        }
    }
    
    if json_mode:
        payload["generationConfig"]["responseMimeType"] = "application/json"
        if response_schema:
            payload["generationConfig"]["responseSchema"] = response_schema
            
    response = http_post_json(url, {}, payload)
    try:
        return response["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise RuntimeError(f"Error parsing Gemini response: {json.dumps(response)}")

# Global cache for loaded local GPU models and tokenizers
LOCAL_MODELS_CACHE = {}
LOCAL_TOKENIZERS_CACHE = {}

MODEL_REPO_MAP = {
    "qwen": "Qwen/Qwen2.5-7B-Instruct",
    "qwen2.5": "Qwen/Qwen2.5-7B-Instruct",
    "qwen-7b": "Qwen/Qwen2.5-7B-Instruct",
    "llama": "unsloth/Llama-3.2-3B-Instruct",
    "llama3": "unsloth/Llama-3.2-3B-Instruct",
    "llama-3.2": "unsloth/Llama-3.2-3B-Instruct",
    "gemma": "google/gemma-2-2b-it",
    "gemma2": "google/gemma-2-2b-it",
    "deepseek": "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
    "phi3": "microsoft/Phi-3-mini-4k-instruct",
    "local": "microsoft/Phi-3-mini-4k-instruct"
}

def call_local_gpu_model(system_prompt: str, user_prompt: str, provider: str = "qwen", json_mode: bool = False) -> str:
    """
    Executes local inference on available CUDA GPUs using Hugging Face Transformers.
    """
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    
    prov = provider.lower().strip()
    repo_id = MODEL_REPO_MAP.get(prov, prov)
    
    cache_dir = Path.home() / ".cache" / "huggingface"
    cache_dir.mkdir(parents=True, exist_ok=True)
    os.environ["HF_HOME"] = str(cache_dir)
    
    if repo_id not in LOCAL_MODELS_CACHE:
        print(f"[LLM Client] Loading local model '{repo_id}' onto GPU (CUDA)...")
        use_cuda = torch.cuda.is_available()
        dtype = torch.float16 if use_cuda else torch.float32
        
        tokenizer = AutoTokenizer.from_pretrained(repo_id, cache_dir=str(cache_dir), trust_remote_code=True)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            
        model = AutoModelForCausalLM.from_pretrained(
            repo_id,
            cache_dir=str(cache_dir),
            dtype=dtype,
            device_map="auto" if use_cuda else None,
            trust_remote_code=True
        )
        if not use_cuda:
            model = model.to("cpu")
            
        LOCAL_MODELS_CACHE[repo_id] = model
        LOCAL_TOKENIZERS_CACHE[repo_id] = tokenizer
        print(f"[LLM Client] Model '{repo_id}' successfully loaded into GPU VRAM.")
        
    model = LOCAL_MODELS_CACHE[repo_id]
    tokenizer = LOCAL_TOKENIZERS_CACHE[repo_id]
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})
    
    try:
        prompt_text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    except Exception:
        prompt_text = f"System: {system_prompt}\nUser: {user_prompt}\nAssistant:"
        
    inputs = tokenizer(prompt_text, return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=600,
            temperature=0.1,
            do_sample=False,
            pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id
        )
        
    generated_tokens = outputs[0][inputs.input_ids.shape[1]:]
    response_text = tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()
    return response_text

def call_llm(system_prompt: str, user_prompt: str, provider: str = "gemini", json_mode: bool = False, response_schema: Optional[dict] = None) -> str:
    """
    Unified caller for LLMs. Supports 'openai', 'gemini', and local GPU models ('qwen', 'llama', 'gemma', 'deepseek', 'phi3', 'local').
    """
    prov = provider.lower().strip()
    
    openai_key = os.getenv("OPENAI_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    
    if prov in ("openai", "gpt", "gpt-4o") and openai_key:
        return call_openai(system_prompt, user_prompt, json_mode=json_mode)
    elif prov in ("gemini", "gemini-2.0-flash") and gemini_key:
        return call_gemini(system_prompt, user_prompt, json_mode=json_mode, response_schema=response_schema)
    elif prov in MODEL_REPO_MAP or "/" in prov:
        return call_local_gpu_model(system_prompt, user_prompt, provider=prov, json_mode=json_mode)
    
    # Fallback cascade
    if gemini_key:
        return call_gemini(system_prompt, user_prompt, json_mode=json_mode, response_schema=response_schema)
    elif openai_key:
        return call_openai(system_prompt, user_prompt, json_mode=json_mode)
    else:
        return call_local_gpu_model(system_prompt, user_prompt, provider="qwen", json_mode=json_mode)

def extract_json_block(text: str) -> dict:
    raw = (text or "").strip()
    if raw.startswith("```"):
        import re
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        import re
        match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))
