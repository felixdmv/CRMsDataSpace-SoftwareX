#!/usr/bin/env python3
"""
search.py
Load FAISS index and metadata and provide a simple retriever interface.
"""
import os
import sys
import json
import argparse
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from sentence_transformers import SentenceTransformer

INDEX_PATH_DEFAULT = os.path.join(os.path.dirname(__file__), "index.faiss")
META_PATH_DEFAULT = os.path.join(os.path.dirname(__file__), "index_meta.json")
EMBED_MODEL = "BAAI/bge-small-en"
EMBEDS_PATH = os.path.join(os.path.dirname(__file__), "index_meta_embs.npy")


class Retriever:
    def __init__(self, index_path: str = INDEX_PATH_DEFAULT, meta_path: str = META_PATH_DEFAULT, embed_model: str = EMBED_MODEL):
        # Try to use FAISS if available; otherwise fallback to in-memory numpy search
        try:
            import faiss
            self._faiss = faiss
        except Exception:
            self._faiss = None

        if not os.path.exists(meta_path):
            raise FileNotFoundError("Meta not found. Run build_index.py first.")

        with open(meta_path, "r", encoding="utf-8") as f:
            self.meta = json.load(f)

        use_gpu = os.environ.get("USE_GPU") == "1"
        device = "cuda" if use_gpu else "cpu"

        try:
            self.embedder = SentenceTransformer(embed_model, device=device)
        except Exception as e:
            print(f"[WARN] Could not load {embed_model}: {e}. Falling back to all-MiniLM-L6-v2")
            self.embedder = SentenceTransformer("all-MiniLM-L6-v2", device=device)

        # If faiss is available and index exists, load it; otherwise precompute embeddings for in-memory search
        if self._faiss is not None and os.path.exists(index_path):
            try:
                self.index = self._faiss.read_index(index_path)
                self.use_faiss = True
            except Exception:
                self.index = None
                self.use_faiss = False
        else:
            self.index = None
            self.use_faiss = False

        if not self.use_faiss:
            # Try to load precomputed embeddings to speed up queries; otherwise precompute and save them.
            if os.path.exists(EMBEDS_PATH):
                try:
                    self._meta_embs = np.load(EMBEDS_PATH)
                    print(f"[INFO] Loaded precomputed embeddings from {EMBEDS_PATH}")
                except Exception as e:
                    print(f"[WARN] Failed to load precomputed embeddings: {e}")
                    self._meta_embs = None
            else:
                # Precompute embeddings for all chunks (may take time), then save to disk
                texts = [m.get("text", "") for m in self.meta]
                if texts:
                    print(f"[INFO] Precomputing embeddings for {len(texts)} chunks (this may take several minutes)...")
                    embs = self.embedder.encode(texts, show_progress_bar=True, convert_to_numpy=True)
                    norms = np.linalg.norm(embs, axis=1, keepdims=True)
                    embs = embs / np.maximum(norms, 1e-12)
                    try:
                        np.save(EMBEDS_PATH, embs)
                        print(f"[INFO] Saved embeddings to {EMBEDS_PATH}")
                    except Exception as e:
                        print(f"[WARN] Could not save embeddings: {e}")
                    self._meta_embs = embs
                else:
                    self._meta_embs = None

    def search(self, query: str, k: int = 3):
        q_emb = self.embedder.encode(query, convert_to_numpy=True)
        q_emb = q_emb / np.maximum(np.linalg.norm(q_emb), 1e-12)

        results = []
        if self.use_faiss and self.index is not None:
            D, I = self.index.search(np.array([q_emb]).astype("float32"), k)
            for score, idx in zip(D[0].tolist(), I[0].tolist()):
                if idx < 0:
                    continue
                item = self.meta[idx].copy()
                item["score"] = float(score)
                results.append(item)
            return results

        # Fallback: find candidate chunks by simple token matching, then embed only candidates
        import re
        tokens = set(re.findall(r"\w+", query.lower()))
        candidates = []
        for i, m in enumerate(self.meta):
            text_l = m.get("text", "").lower()
            if any(t in text_l for t in tokens):
                candidates.append(i)

        # If no token matches, fallback to a small sample of the corpus
        if not candidates:
            n = len(self.meta)
            if n == 0:
                return []
            sample_n = min(500, n)
            candidates = list(range(sample_n))

        # limit number of candidates to avoid heavy encoding
        max_cands = 500
        if len(candidates) > max_cands:
            candidates = candidates[:max_cands]

        cand_texts = [self.meta[i].get("text", "") for i in candidates]
        embs = self.embedder.encode(cand_texts, show_progress_bar=False, convert_to_numpy=True)
        norms = np.linalg.norm(embs, axis=1, keepdims=True)
        embs = embs / np.maximum(norms, 1e-12)

        q_vec = q_emb.reshape(-1)
        scores = (embs @ q_vec).squeeze()
        if scores.ndim == 0:
            scores = np.array([float(scores)])

        idxs = np.argsort(-scores)[:k]
        for idx in idxs.tolist():
            meta_idx = candidates[idx]
            item = self.meta[meta_idx].copy()
            item["score"] = float(scores[idx])
            results.append(item)
        return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("query", help="Query string to search")
    parser.add_argument("--k", type=int, default=3)
    args = parser.parse_args()
    r = Retriever()
    res = r.search(args.query, k=args.k)
    print(f"[INFO] Query: {args.query}")
    for i, item in enumerate(res, start=1):
        print(f"--- Rank {i} | score={item['score']:.4f} | {item['pdf']} page {item['page']} chunk {item['chunk_id']} ---")
        print(item['text'][:400].replace("\n", " "))
        print()
