#!/usr/bin/env python3
"""
build_index.py
Build a FAISS index from PDFs under ../pdfs/ using sentence-transformers embeddings.
Outputs `code/index.faiss` and `code/index_meta.json`.
"""
import os
import sys
import json
import argparse
from typing import List
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PDFS_DIR = os.path.join(ROOT, "pdfs")
INDEX_PATH_DEFAULT = os.path.join(os.path.dirname(__file__), "index.faiss")
META_PATH_DEFAULT = os.path.join(os.path.dirname(__file__), "index_meta.json")

# allow importing local module
sys.path.insert(0, os.path.dirname(__file__))
from extract_text import list_pdfs, extract_text_from_pdf


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
    if not text:
        return []
    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + chunk_size, n)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == n:
            break
        start = max(end - overlap, start + 1)
    return chunks


def build_index(pdfs: List[str], index_path: str, meta_path: str, chunk_size: int = 500, overlap: int = 100, embed_model_name: str = "BAAI/bge-small-en"):
    try:
        from sentence_transformers import SentenceTransformer
    except Exception as e:
        raise RuntimeError("sentence-transformers is required. Install with 'pip install sentence-transformers'") from e
    try:
        import faiss
    except Exception as e:
        raise RuntimeError("faiss-cpu is required. Install with 'pip install faiss-cpu'") from e

    all_chunks = []
    meta = []
    for pdf in pdfs:
        print(f"[INFO] processing {pdf}")
        pages_text, ocr_used = extract_text_from_pdf(pdf)
        print(f"[INFO] pages={len(pages_text)} ocr_used={ocr_used}")
        for page_idx, page_text in enumerate(pages_text, start=1):
            page_chunks = chunk_text(page_text, chunk_size, overlap)
            for ci, chunk in enumerate(page_chunks):
                meta.append({
                    "pdf": os.path.relpath(pdf),
                    "page": page_idx,
                    "chunk_id": ci,
                    "text": chunk,
                })
                all_chunks.append(chunk)

    if not all_chunks:
        print("[WARN] No chunks extracted. Exiting.")
        return

    print(f"[INFO] total chunks: {len(all_chunks)}")
    # load embedding model
    try:
        model = SentenceTransformer(embed_model_name, device="cpu")
    except Exception as e:
        print(f"[WARN] Could not load {embed_model_name}: {e}. Falling back to 'all-MiniLM-L6-v2'")
        model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")

    embeddings = model.encode(all_chunks, show_progress_bar=True, batch_size=32, convert_to_numpy=True)
    # normalize for cosine similarity
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    embeddings = embeddings / np.maximum(norms, 1e-12)

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings.astype("float32"))

    os.makedirs(os.path.dirname(index_path), exist_ok=True)
    faiss.write_index(index, index_path)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"[INFO] index saved to {index_path}")
    print(f"[INFO] meta saved to {meta_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdfs", nargs="*", help="PDF files to index (default: ../pdfs/*)")
    parser.add_argument("--index", default=INDEX_PATH_DEFAULT)
    parser.add_argument("--meta", default=META_PATH_DEFAULT)
    parser.add_argument("--chunk_size", type=int, default=500)
    parser.add_argument("--overlap", type=int, default=100)
    args = parser.parse_args()
    pdfs = args.pdfs if args.pdfs else list_pdfs()
    if not pdfs:
        print("[WARN] No PDFs to process.")
        sys.exit(1)
    build_index(pdfs, args.index, args.meta, chunk_size=args.chunk_size, overlap=args.overlap)
