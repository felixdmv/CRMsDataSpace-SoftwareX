#!/usr/bin/env python3
"""
experiment_runner.py
Run a battery of QA queries against the local RAG pipeline for several HF models.
Creates an output folder per run with per-model result files.
"""
import argparse
import os
import sys
from pathlib import Path
from datetime import datetime
import time
import json
import gc

# Allow importing build_prompt from ask.py
sys.path.insert(0, os.path.dirname(__file__))
from ask import build_prompt
from search import Retriever


def sanitize(name: str) -> str:
    return name.replace('/', '_').replace(' ', '_')


def load_model_tokenizer(model_name: str):
    from transformers import AutoTokenizer, AutoModelForCausalLM, AutoModelForSeq2SeqLM
    import torch

    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    is_seq2seq = False
    try:
        model = AutoModelForCausalLM.from_pretrained(model_name, device_map="cpu", torch_dtype="auto", trust_remote_code=True)
        is_seq2seq = False
        print(f"[INFO] Loaded as causal LM: {model_name}")
    except Exception as e:
        print(f"[WARN] AutoModelForCausalLM load failed for {model_name}: {e}. Trying Seq2Seq class.")
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name, device_map="cpu", torch_dtype="auto", trust_remote_code=True)
        is_seq2seq = True
        print(f"[INFO] Loaded as Seq2Seq LM: {model_name}")

    model.eval()
    return model, tokenizer, is_seq2seq


def generate_with_model(model, tokenizer, is_seq2seq, prompt: str, gen_kwargs: dict):
    import torch
    # Tokenize (allow truncation but try to keep as much as possible)
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True)
    device = next(model.parameters()).device
    inputs = {k: v.to(device) for k, v in inputs.items()}

    # Filter allowed keys for generate
    allowed = {k: v for k, v in gen_kwargs.items() if k in (
        'max_new_tokens', 'min_length', 'num_beams', 'no_repeat_ngram_size', 'repetition_penalty',
        'length_penalty', 'early_stopping', 'do_sample', 'temperature', 'top_p', 'top_k'
    )}

    with torch.no_grad():
        outputs = model.generate(**inputs, **allowed)

    try:
        full_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    except Exception:
        full_text = tokenizer.decode(outputs, skip_special_tokens=True)

    # Remove prompt echo for causal models
    answer = full_text.strip()
    if not is_seq2seq:
        try:
            prompt_text = tokenizer.decode(inputs['input_ids'][0], skip_special_tokens=True)
            if full_text.startswith(prompt_text):
                answer = full_text[len(prompt_text):].strip()
        except Exception:
            pass

    return answer


def is_low_quality(text: str, tokenizer) -> bool:
    s = (text or "").strip()
    if not s:
        return True
    if len(s) < 30:
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
        threegrams = [' '.join(words[i:i+3]) for i in range(len(words)-2)]
        if threegrams:
            uniq_3 = len(set(threegrams)) / len(threegrams)
            if uniq_3 < 0.4:
                return True
    lines = [l.strip() for l in s.splitlines() if l.strip()]
    for l in lines:
        if lines.count(l) > 2:
            return True
    return False


DEFAULT_QUESTIONS = [
    "What materials are present in the waste facility?",
    "List all waste materials placed into the TSF and short descriptions.",
    "Describe how sludge from the water treatment plant is managed and its potential impacts.",
    "Which documents define reporting standards for mineral resources and reserves?",
    "According to 2023LUGTechnicalReport.pdf, what is the operating philosophy for the TSF?",
    "Summarize the monitoring instrumentation used for the TSF.",
    "What is the sludge production rate and solids content specified for the WTP?",
    "What is the total storage capacity of the TSF reported in the technical report?",
    "What is the recommended minimum depth of the operating decant pond?",
    "What is the monitoring frequency for tailings beach surveying and pond bathymetry?",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--models', type=str, default=None, help='Comma-separated list of HF model ids to test')
    parser.add_argument('--outdir', type=str, default=None, help='Output directory base (will create dated subfolder)')
    parser.add_argument('--k', type=int, default=6, help='Top-k retrieval')
    parser.add_argument('--max-tokens', type=int, default=512)
    parser.add_argument('--num-beams', type=int, default=4)
    parser.add_argument('--no-repeat-ngram-size', type=int, default=3)
    parser.add_argument('--repetition-penalty', type=float, default=1.2)
    parser.add_argument('--min-length', type=int, default=60)
    parser.add_argument('--do-sample', action='store_true')
    parser.add_argument('--temperature', type=float, default=0.0)
    parser.add_argument('--top-p', type=float, default=0.92)
    parser.add_argument('--top-k', type=int, default=50)
    parser.add_argument('--detailed', action='store_true')
    parser.add_argument('--questions-file', type=str, default=None, help='Optional file with one question per line')
    args = parser.parse_args()

    run_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    base_out = Path(args.outdir) if args.outdir else Path(__file__).resolve().parent / 'experiments'
    run_out = base_out / run_time
    run_out.mkdir(parents=True, exist_ok=True)

    # load questions
    if args.questions_file and Path(args.questions_file).exists():
        with open(args.questions_file, 'r', encoding='utf-8') as f:
            questions = [l.strip() for l in f if l.strip()]
    else:
        questions = DEFAULT_QUESTIONS

    models = []
    if args.models:
        models = [m.strip() for m in args.models.split(',') if m.strip()]
    else:
        # default battery (small collection)
        models = [
            'google/flan-t5-large',
            'EleutherAI/gpt-neo-1.3B',
        ]

    print(f"Run out: {run_out}")
    print(f"Models: {models}")
    print(f"Questions: {len(questions)}")

    # init retriever once
    try:
        retriever = Retriever()
    except Exception as e:
        print(f"[ERROR] Retriever init failed: {e}")
        sys.exit(1)

    for model_name in models:
        safe = sanitize(model_name)
        model_out = run_out / safe
        model_out.mkdir(parents=True, exist_ok=True)
        results_file = model_out / 'results.txt'
        meta_file = model_out / 'meta.json'

        with open(results_file, 'w', encoding='utf-8') as rf, open(meta_file, 'w', encoding='utf-8') as mf:
            mf.write(json.dumps({'model': model_name, 'started': datetime.now().isoformat(), 'questions': len(questions)}, indent=2))

        try:
            model, tokenizer, is_seq2seq = load_model_tokenizer(model_name)
        except Exception as e:
            with open(results_file, 'a', encoding='utf-8') as rf:
                rf.write(f"[ERROR] Failed to load model {model_name}: {e}\n")
            continue

        gen_kwargs = dict(
            max_new_tokens=args.max_tokens,
            min_length=args.min_length,
            num_beams=args.num_beams,
            no_repeat_ngram_size=args.no_repeat_ngram_size,
            repetition_penalty=args.repetition_penalty,
            length_penalty=args.num_beams and 1.0 or 1.0,
            early_stopping=True,
            do_sample=args.do_sample,
            temperature=args.temperature,
            top_p=args.top_p,
            top_k=args.top_k,
        )

        # per-model loop
        for i, q in enumerate(questions, 1):
            print(f"[{model_name}] Question {i}/{len(questions)}")
            out_path = model_out / f'q{i:02d}.txt'
            t0 = time.time()
            try:
                results = retriever.search(q, k=args.k)
            except Exception as e:
                results = []
                with open(out_path, 'w', encoding='utf-8') as f:
                    f.write(f"[ERROR] Retriever search failed: {e}\n")
                continue

            if not results:
                with open(out_path, 'w', encoding='utf-8') as f:
                    f.write('Answer:\nI don\'t know\n')
                continue

            prompt = build_prompt(q, results, detailed=args.detailed)

            try:
                answer = generate_with_model(model, tokenizer, is_seq2seq, prompt, gen_kwargs)
            except Exception as e:
                answer = f"I don't know"
                with open(out_path, 'w', encoding='utf-8') as f:
                    f.write(f"[ERROR] generation failed: {e}\nI don't know\n")
                continue

            # post-process quality
            try:
                if is_low_quality(answer, tokenizer):
                    answer = "I don't know"
            except Exception:
                pass

            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(f"Question: {q}\n\n")
                f.write("Answer:\n")
                f.write(answer + '\n\n')
                f.write("Sources used:\n")
                for j, r in enumerate(results, 1):
                    f.write(f"[SOURCE {j}] {r['pdf']} page {r['page']} chunk {r['chunk_id']} (score={r['score']:.4f})\n")
                    f.write(r['text'] + '\n')
                    f.write('-'*60 + '\n')

            t1 = time.time()
            print(f"[{model_name}] done q{i} in {t1-t0:.1f}s -> {out_path}")

        # write finished meta
        with open(meta_file, 'w', encoding='utf-8') as mf:
            mf.write(json.dumps({'model': model_name, 'finished': datetime.now().isoformat(), 'questions': len(questions)}, indent=2))

        # unload model to free memory
        try:
            del model
            del tokenizer
            gc.collect()
            time.sleep(2)
        except Exception:
            pass

    print(f"All models processed. Results in {run_out}")


if __name__ == '__main__':
    main()
