#!/usr/bin/env python3
"""
download_all_models_fast.py
Downloads models for the CRMs Data Space GPU benchmark:
1. Llama 3.2 3B Instruct (unsloth/Llama-3.2-3B-Instruct)
2. Qwen 2.5 7B Instruct (Qwen/Qwen2.5-7B-Instruct)
3. Gemma 2 2B IT (google/gemma-2-2b-it)
4. Phi-3 Mini 4K Instruct (microsoft/Phi-3-mini-4k-instruct)
"""
import os
import sys
import time
from pathlib import Path
from huggingface_hub import snapshot_download

MODELS = [
    ("llama", "unsloth/Llama-3.2-3B-Instruct"),
    ("qwen", "Qwen/Qwen2.5-7B-Instruct"),
    ("gemma", "google/gemma-2-2b-it"),
    ("phi3", "microsoft/Phi-3-mini-4k-instruct"),
    ("deepseek", "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B")
]

def main():
    print("=" * 80)
    print(" DOWNLOADING LLM BENCHMARK MODELS FOR SLURM GPU CLUSTER")
    print("=" * 80)
    
    for alias, repo_id in MODELS:
        print(f"\n>>> Downloading [{alias.upper()}]: {repo_id}")
        t0 = time.time()
        try:
            cache_dir = str(Path.home() / ".cache" / "huggingface")
            path = snapshot_download(repo_id=repo_id, cache_dir=cache_dir)
            elapsed = time.time() - t0
            print(f" [SUCCESS] [{alias.upper()}] ready at: {path} ({elapsed:.2f}s)")
        except Exception as e:
            print(f" [ERROR] [{alias.upper()}] Failed: {e}")
            
    print("\n" + "=" * 80)
    print(" ALL DOWNLOADS COMPLETED!")
    print("=" * 80)

if __name__ == "__main__":
    main()
