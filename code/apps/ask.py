#!/usr/bin/env python3
"""
ask.py
CLI to ask a question against the FAISS index. Usage:
  python code/ask.py "What materials are present in the waste facility?"

Prints question, answer, and the source fragments used.
"""
import os
import sys
import argparse
import textwrap

sys.path.insert(0, os.path.dirname(__file__))
from search import Retriever

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def find_local_model(models_dir: str = None):
    models_dir = models_dir or os.path.join(ROOT, 'models')
    if not os.path.exists(models_dir):
        return None
    for root, _, files in os.walk(models_dir):
        for f in files:
            if f.endswith('.gguf') or f.endswith('.ggml') or f.endswith('.safetensors') or f.endswith('.bin'):
                return os.path.join(root, f)
    return None


def generate_answer(prompt: str, gen_kwargs: dict | None = None) -> str:
    model_name = os.environ.get("HF_MODEL", "microsoft/phi-3-mini-4k-instruct")
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        import torch
    except Exception as e:
        print(f"[ERROR] transformers or torch not available: {e}")
        return "I don't know"

    gen_kwargs = gen_kwargs or {}
    # Defaults (can be overridden by gen_kwargs)
    defaults = dict(
        max_new_tokens=gen_kwargs.get("max_new_tokens", 512),
        min_length=gen_kwargs.get("min_length", 60),
        num_beams=gen_kwargs.get("num_beams", 4),
        no_repeat_ngram_size=gen_kwargs.get("no_repeat_ngram_size", 3),
        repetition_penalty=gen_kwargs.get("repetition_penalty", 1.2),
        length_penalty=gen_kwargs.get("length_penalty", 1.0),
        early_stopping=gen_kwargs.get("early_stopping", True),
        do_sample=gen_kwargs.get("do_sample", False),
        temperature=gen_kwargs.get("temperature", 0.0),
        top_p=gen_kwargs.get("top_p", 0.92),
        top_k=gen_kwargs.get("top_k", 50),
    )
    # merge defaults with provided gen_kwargs
    merged_gen_kwargs = {**defaults, **gen_kwargs}

    try:
        print(f"[INFO] Loading model {model_name} on CPU (device_map='cpu', torch_dtype='auto')")
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=False)

        # Format prompt using chat template (pass list of messages)
        formatted = prompt
        try:
            if hasattr(tokenizer, "apply_chat_template"):
                try:
                    template_out = tokenizer.apply_chat_template([{"role": "user", "content": prompt}])
                    if isinstance(template_out, str):
                        formatted = template_out
                    elif isinstance(template_out, dict):
                        for key in ("text", "input_text", "prompt"):
                            if key in template_out and isinstance(template_out[key], str):
                                formatted = template_out[key]
                                break
                        else:
                            if "input_ids" in template_out:
                                try:
                                    formatted = tokenizer.decode(template_out["input_ids"], skip_special_tokens=True)
                                except Exception:
                                    formatted = prompt
                            else:
                                formatted = str(template_out)
                except Exception:
                    formatted = prompt
        except Exception:
            formatted = prompt

        use_gpu = os.environ.get("USE_GPU") == "1"
        device_map = "auto" if use_gpu else "cpu"
        
        quant_kwargs = {}
        if use_gpu:
            try:
                from transformers import BitsAndBytesConfig
                quant_kwargs["quantization_config"] = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4"
                )
                print("[INFO] Using 4-bit quantization with bitsandbytes for GPU")
            except ImportError:
                print("[WARN] bitsandbytes not found. Loading without quantization.")

        # Try loading a causal LM; if it fails, try seq2seq (T5-like)
        model = None
        is_seq2seq = False
        try:
            model = AutoModelForCausalLM.from_pretrained(
                model_name, 
                device_map=device_map, 
                torch_dtype="auto", 
                trust_remote_code=False,
                **quant_kwargs
            )
            print(f"[INFO] Loaded as causal LM: {model_name} on {device_map}")
        except Exception as e_causal:
            print(f"[WARN] AutoModelForCausalLM load failed: {e_causal}. Trying Seq2Seq model class.")
            try:
                from transformers import AutoModelForSeq2SeqLM

                model = AutoModelForSeq2SeqLM.from_pretrained(
                    model_name, 
                    device_map=device_map, 
                    torch_dtype="auto", 
                    trust_remote_code=False,
                    **quant_kwargs
                )
                is_seq2seq = True
                print(f"[INFO] Loaded as Seq2Seq LM: {model_name} on {device_map}")
            except Exception as e_seq:
                print(f"[ERROR] Failed to load model as causal or seq2seq: {e_seq}")
                return "I don't know"

        # Tokenize the formatted prompt
        inputs = tokenizer(formatted, return_tensors="pt")
        # ensure tensors on same device as model (CPU)
        device = next(model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}

        # Prepare final kwargs for .generate(): remove keys not accepted by model.generate()
        allowed_kwargs = {k: v for k, v in merged_gen_kwargs.items()}

        # Generate tokens
        with torch.no_grad():
            outputs = model.generate(**inputs, **allowed_kwargs)

        # Decode generated sequence. For seq2seq models the output typically contains only the answer.
        try:
            full_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        except Exception as e:
            print(f"[WARN] tokenizer.decode(outputs[0]) failed: {e}; trying tokenizer.decode(outputs)")
            try:
                full_text = tokenizer.decode(outputs, skip_special_tokens=True)
            except Exception as e2:
                print(f"[ERROR] decoding failed: {e2}")
                return "I don't know"

        # For causal models, remove the prompt text from the beginning to get a clean answer.
        answer = full_text.strip()
        if not is_seq2seq:
            try:
                prompt_text = tokenizer.decode(inputs["input_ids"][0], skip_special_tokens=True)
                if full_text.startswith(prompt_text):
                    answer = full_text[len(prompt_text):].strip()
                elif full_text.startswith(formatted):
                    answer = full_text[len(formatted):].strip()
            except Exception:
                pass

        # Post-process: detect low-quality answers and replace with "I don't know"
        def is_low_quality(text: str) -> bool:
            s = (text or "").strip()
            if not s:
                return True
            # Basic length check
            if len(s) < int(merged_gen_kwargs.get("min_length", 60) * 0.5):
                return True
            try:
                toks = tokenizer.encode(s, add_special_tokens=False)
                uniq_ratio = len(set(toks)) / max(1, len(toks))
                if uniq_ratio < 0.45:
                    return True
            except Exception:
                pass
            words = s.split()
            if len(words) >= 6:
                threegrams = [" ".join(words[i:i+3]) for i in range(len(words) - 2)]
                if threegrams:
                    uniq_3 = len(set(threegrams)) / len(threegrams)
                    if uniq_3 < 0.4:
                        return True
            # repeated-line detector
            lines = [l.strip() for l in s.splitlines() if l.strip()]
            for l in lines:
                if lines.count(l) > 2:
                    return True
            return False

        if is_low_quality(answer):
            return "I don't know"

        return answer if answer else "I don't know"
    except Exception as e:
        print(f"[ERROR] model generation failed: {e}")
        return "I don't know"


def build_prompt(question: str, sources: list, detailed: bool = False) -> str:
    # Build an instruct-friendly prompt: clear system role, numbered sources, and strict instruction
    system = (
        "SYSTEM: You are an expert technical assistant. Use ONLY the numbered SOURCE snippets below to answer the question. "
        "Do NOT invent facts. If the evidence is insufficient, reply exactly: I don't know."
    )

    ctx_lines = []
    for i, s in enumerate(sources, start=1):
        header = f"[{i}] {s['pdf']} | page {s['page']} | chunk {s['chunk_id']} | score {s['score']:.4f}"
        ctx_lines.append(header)
        # keep source text short (avoid huge context blocks)
        ctx_lines.append(s['text'])

    context = "\n".join(ctx_lines)

    instructions = (
        "INSTRUCTIONS:\n- Write a natural, consolidated answer (2–6 sentences).\n"
        "- After the answer, include a single line 'Sources:' listing the source IDs used (e.g. [1], [2]).\n"
        "- Do NOT invent facts. If you cannot answer from the sources, reply exactly: I don't know.\n"
    )

    prompt = f"{system}\n\nSOURCES:\n{context}\n\nQUESTION: {question}\n\n{instructions}\nAnswer:"
    if detailed:
        prompt += "\n\n(Provide an enumerated list of findings and cite sources for each point.)"
    return prompt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('question', help='Question to ask (quote it)')
    parser.add_argument('--k', type=int, default=3, help='Number of chunks to retrieve')
    parser.add_argument('--threshold', type=float, default=0.15, help='Minimum similarity threshold to attempt answering')
    parser.add_argument('--max-tokens', type=int, default=512, help='Maximum tokens to generate from the LLM')
    parser.add_argument('--detailed', action='store_true', help='Request a detailed, enumerated answer with source citations')
    # Generation parameters exposed for quick tuning
    parser.add_argument('--num-beams', type=int, default=4, help='Beam size for generation')
    parser.add_argument('--no-repeat-ngram-size', type=int, default=3, help='no_repeat_ngram_size for generation')
    parser.add_argument('--repetition-penalty', type=float, default=1.2, help='repetition_penalty for generation')
    parser.add_argument('--min-length', type=int, default=60, help='Minimum generated token length (heuristic)')
    parser.add_argument('--do-sample', action='store_true', help='Enable sampling instead of beam search')
    parser.add_argument('--temperature', type=float, default=0.0, help='Sampling temperature')
    parser.add_argument('--top-p', type=float, default=0.92, help='top_p for sampling')
    parser.add_argument('--top-k', type=int, default=50, help='top_k for sampling')
    parser.add_argument('--length-penalty', type=float, default=1.0, help='length_penalty for beams')
    parser.add_argument('-cpu', action='store_true', help='Force CPU execution')
    parser.add_argument('-gpu', action='store_true', help='Enable GPU execution')
    args = parser.parse_args()

    if args.gpu:
        os.environ["USE_GPU"] = "1"
    else:
        os.environ["USE_GPU"] = "0"

    question = args.question
    print(f"Question: {question}\n")

    try:
        retriever = Retriever()
    except Exception as e:
        print(f"[ERROR] Retriever initialization failed: {e}")
        print("Run build_index.py first to create the index.")
        sys.exit(1)

    results = retriever.search(question, k=args.k)
    if not results:
        print("Answer:\nI don't know")
        return

    print("Retrieved chunks:")
    for i, r in enumerate(results, start=1):
        snippet = r['text'].replace('\n', ' ')[:300]
        print(f"{i}. {r['pdf']} page {r['page']} chunk {r['chunk_id']} score={r['score']:.4f}")
        print(f"   {snippet}...\n")

    max_score = max(r['score'] for r in results)
    if max_score < args.threshold:
        print("Answer:\nI don't know")
        return

    prompt = build_prompt(question, results, detailed=args.detailed)

    gen_kwargs = dict(
        max_new_tokens=args.max_tokens,
        min_length=args.min_length,
        num_beams=args.num_beams,
        no_repeat_ngram_size=args.no_repeat_ngram_size,
        repetition_penalty=args.repetition_penalty,
        length_penalty=args.length_penalty,
        early_stopping=True,
        do_sample=args.do_sample,
        temperature=args.temperature,
        top_p=args.top_p,
        top_k=args.top_k,
    )

    answer = generate_answer(prompt, gen_kwargs=gen_kwargs)

    print("Answer:")
    print(textwrap.fill(answer, width=100))

    print("\nSources used:")
    for i, r in enumerate(results, start=1):
        print(f"[SOURCE {i}] {r['pdf']} page {r['page']} chunk {r['chunk_id']} (score={r['score']:.4f})")
        print(r['text'])
        print('-' * 60)


if __name__ == '__main__':
    main()
