#!/usr/bin/env python3
"""
Downloads unsloth/Meta-Llama-3.1-8B-Instruct completely into the HF cache.
"""
import time
from huggingface_hub import snapshot_download

def main():
    repo_id = "unsloth/Meta-Llama-3.1-8B-Instruct"
    print(f"=== Starting full download of {repo_id} ===")
    t0 = time.time()
    
    path = snapshot_download(
        repo_id=repo_id,
        ignore_patterns=["*.pt", "*.bin", "*.onnx", "*.msgpack"],
        max_workers=4
    )
    
    dt = time.time() - t0
    print(f"\n[Success] {repo_id} fully downloaded in {dt:.1f}s ({dt/60:.2f} min)")
    print(f"Cached at: {path}")

if __name__ == "__main__":
    main()
