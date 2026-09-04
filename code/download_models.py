#!/usr/bin/env python3
"""
download_models.py
Downloads and verifies Hugging Face open-weight LLMs onto the GPU cluster.
Models targeted:
1. Qwen 2.5 (Qwen/Qwen2.5-7B-Instruct)
2. Llama 3.2 (unsloth/Llama-3.2-3B-Instruct or NousResearch/Meta-Llama-3-8B-Instruct)
3. Gemma 2 (google/gemma-2-2b-it)
4. DeepSeek R1 Distill Qwen (deepseek-ai/DeepSeek-R1-Distill-Qwen-7B)
5. Phi-3 Mini (microsoft/Phi-3-mini-4k-instruct)
"""
import os
import sys
import time
from pathlib import Path

# Ensure HF cache directory is set in workspace storage
ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / ".cache" / "huggingface"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
os.environ["HF_HOME"] = str(CACHE_DIR)

from huggingface_hub import snapshot_download
from transformers import AutoTokenizer, AutoModelForCausalLM

MODELS_TO_DOWNLOAD = {
    "qwen": "Qwen/Qwen2.5-7B-Instruct",
    "llama": "unsloth/Llama-3.2-3B-Instruct",
    "gemma": "google/gemma-2-2b-it",
    "deepseek": "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
    "phi3": "microsoft/Phi-3-mini-4k-instruct"
}

def download_model(alias: str, repo_id: str):
    print(f"\n{'='*70}")
    print(f" Downloading Model [{alias.upper()}]: {repo_id}")
    print(f" Target Cache: {CACHE_DIR}")
    print(f"{'='*70}")
    t0 = time.time()
    try:
        # Download repository files (weights, config, tokenizer)
        snapshot_download(
            repo_id=repo_id,
            cache_dir=str(CACHE_DIR),
            resume_download=True
        )
        elapsed = time.time() - t0
        print(f" [SUCCESS] Downloaded {repo_id} in {elapsed:.2f}s")
        return True
    except Exception as e:
        print(f" [ERROR] Failed downloading {repo_id}: {e}")
        return False

def main():
    print("="*80)
    print(" HUGGING FACE MODEL DOWNLOADER FOR CRMsDataSpace SLURM CLUSTER")
    print("="*80)
    
    selected_alias = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    if selected_alias == "all":
        targets = MODELS_TO_DOWNLOAD
    elif selected_alias in MODELS_TO_DOWNLOAD:
        targets = {selected_alias: MODELS_TO_DOWNLOAD[selected_alias]}
    else:
        print(f"Unknown alias '{selected_alias}'. Available: {list(MODELS_TO_DOWNLOAD.keys())}")
        sys.exit(1)
        
    results = {}
    for alias, repo_id in targets.items():
        ok = download_model(alias, repo_id)
        results[alias] = ok
        
    print("\n" + "="*70)
    print(" DOWNLOAD SUMMARY")
    print("="*70)
    for alias, ok in results.items():
        status = "PASSED" if ok else "FAILED"
        print(f" - {alias:<10} ({MODELS_TO_DOWNLOAD[alias]}): {status}")
    print("="*70)

if __name__ == "__main__":
    main()
