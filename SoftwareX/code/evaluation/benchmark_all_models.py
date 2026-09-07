"""
Comprehensive Evaluation Benchmark across Local GPU Models and Baseline:
Compares Mock Baseline, Llama 3.2 3B, Phi-3 Mini 4K, Qwen 2.5 7B, and DeepSeek R1 7B
on NVIDIA A100-PCIE-40GB GPU across the 100-query test battery.
Measures latency (ms), GPU VRAM memory footprint (GB), intent accuracy,
field-level F1-scores, and overall filter match rate.
"""

import sys
import os
import time
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Add code/ to sys.path
CODE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE_DIR))

from agent import process_chat_message
from llm_client import (
    load_local_model_weights, 
    unload_all_local_models, 
    get_model_state,
    MODEL_REPO_MAP
)

BENCHMARK_FILE = Path(__file__).resolve().parent / "test_battery_100.json"
RESULTS_JSON = Path(__file__).resolve().parent / "benchmark_complete_results.json"
RESULTS_TXT = Path(__file__).resolve().parent / "benchmark_all_models_summary.txt"

MODEL_METADATA = {
    "mock": {
        "name": "Deterministic Baseline (Mock)",
        "params": "Rule-based",
        "precision": "CPU Heuristics",
        "sovereignty": "100% On-Premises (Air-gapped)"
    },
    "llama": {
        "name": "Llama 3.2 3B Instruct",
        "params": "3.21B",
        "precision": "FP16",
        "sovereignty": "100% On-Premises (Private GPU)"
    },
    "phi3": {
        "name": "Phi-3 Mini 4K Instruct",
        "params": "3.82B",
        "precision": "FP16",
        "sovereignty": "100% On-Premises (Private GPU)"
    },
    "qwen": {
        "name": "Qwen 2.5 7B Instruct",
        "params": "7.61B",
        "precision": "FP16",
        "sovereignty": "100% On-Premises (Private GPU)"
    },
    "deepseek": {
        "name": "DeepSeek R1 Distill Qwen 7B",
        "params": "7.61B",
        "precision": "FP16",
        "sovereignty": "100% On-Premises (Private GPU)"
    }
}

def calculate_metrics(gold_list: List[str], pred_list: List[str]) -> Tuple[float, float, float, int, int, int]:
    gold_set = set(gold_list)
    pred_set = set(pred_list)
    
    tp = len(gold_set.intersection(pred_set))
    fp = len(pred_set - gold_set)
    fn = len(gold_set - pred_set)
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    return precision, recall, f1, tp, fp, fn

def run_model_benchmark(provider: str, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    print(f"\n{'='*70}")
    print(f"  EVALUATING MODEL: {provider.upper()} ({MODEL_METADATA[provider]['name']})")
    print(f"{'='*70}")

    vram_used_gb = 0.0
    if provider != "mock":
        print(f"[Benchmark] Loading weights for '{provider}' into GPU VRAM...")
        success = load_local_model_weights(provider)
        if not success:
            print(f"[ERROR] Failed to load model '{provider}'. Skipping.")
            return {}
        state = get_model_state()
        vram_used_gb = state.get("vram_gb", 0.0)
        print(f"[Benchmark] Weights loaded successfully. Allocated VRAM: {vram_used_gb} GB.")

    # Warm-up run
    print("[Benchmark] Executing warm-up query...")
    try:
        process_chat_message("Muestra litio en Espana", provider=provider)
    except Exception as e:
        print(f"[Warning] Warm-up failed: {e}")

    latencies_ms = []
    intent_correct = 0
    exact_matches = 0
    
    country_stats = [0, 0, 0]
    comm_stats = [0, 0, 0]
    fac_stats = [0, 0, 0]
    status_stats = [0, 0, 0]

    for idx, tc in enumerate(test_cases, 1):
        q = tc["query"]
        expected_intent = tc["expected_intent"]
        expected_filters = tc.get("expected_filters", {})

        start_time = time.perf_counter()
        try:
            res = process_chat_message(q, provider=provider)
        except Exception as err:
            print(f"  [Error] Query {idx} failed: {err}")
            res = {"extracted_json": {"intent": "filter_search", "filters": {}}}
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        latencies_ms.append(latency_ms)

        nlu = res.get("extracted_json", {})
        pred_intent = nlu.get("intent", "filter_search")
        pred_filters = nlu.get("filters", {})

        # Intent
        if pred_intent == expected_intent:
            intent_correct += 1

        # Country
        p, r, f1, tp, fp, fn = calculate_metrics(expected_filters.get("countries", []), pred_filters.get("countries", []))
        country_stats[0] += tp; country_stats[1] += fp; country_stats[2] += fn
        c_match = (set(expected_filters.get("countries", [])) == set(pred_filters.get("countries", [])))

        # Commodity
        p, r, f1, tp, fp, fn = calculate_metrics(expected_filters.get("commodities", []), pred_filters.get("commodities", []))
        comm_stats[0] += tp; comm_stats[1] += fp; comm_stats[2] += fn
        m_match = (set(expected_filters.get("commodities", [])) == set(pred_filters.get("commodities", [])))

        # Facility
        p, r, f1, tp, fp, fn = calculate_metrics(expected_filters.get("storage_facility_types", []), pred_filters.get("storage_facility_types", []))
        fac_stats[0] += tp; fac_stats[1] += fp; fac_stats[2] += fn
        f_match = (set(expected_filters.get("storage_facility_types", [])) == set(pred_filters.get("storage_facility_types", [])))

        # Status
        p, r, f1, tp, fp, fn = calculate_metrics(expected_filters.get("project_status", []), pred_filters.get("project_status", []))
        status_stats[0] += tp; status_stats[1] += fp; status_stats[2] += fn
        s_match = (set(expected_filters.get("project_status", [])) == set(pred_filters.get("project_status", [])))

        if c_match and m_match and f_match and s_match:
            exact_matches += 1

        if idx % 25 == 0 or idx == len(test_cases):
            print(f"  Processed {idx}/{len(test_cases)} queries | Current Latency: {latency_ms:.1f} ms")

    total = len(test_cases)
    intent_acc = (intent_correct / total) * 100.0
    exact_match_rate = (exact_matches / total) * 100.0

    def compute_macro(stats):
        tp, fp, fn = stats
        p = tp / (tp + fp) if (tp + fp) > 0 else 1.0
        r = tp / (tp + fn) if (tp + fn) > 0 else 1.0
        f1 = (2 * p * r) / (p + r) if (p + r) > 0 else 0.0
        return round(p * 100.0, 2), round(r * 100.0, 2), round(f1 * 100.0, 2)

    cp, cr, cf1 = compute_macro(country_stats)
    mp, mr, mf1 = compute_macro(comm_stats)
    fp, fr, ff1 = compute_macro(fac_stats)
    sp, sr, sf1 = compute_macro(status_stats)
    macro_f1 = round((cf1 + mf1 + ff1 + sf1) / 4.0, 2)

    mean_latency = round(sum(latencies_ms) / len(latencies_ms), 1)
    min_latency = round(min(latencies_ms), 1)
    max_latency = round(max(latencies_ms), 1)

    # Evict model from GPU memory to keep clean state
    if provider != "mock":
        unload_all_local_models()

    result_entry = {
        "provider": provider,
        "model_name": MODEL_METADATA[provider]["name"],
        "parameters": MODEL_METADATA[provider]["params"],
        "precision": MODEL_METADATA[provider]["precision"],
        "sovereignty": MODEL_METADATA[provider]["sovereignty"],
        "vram_gb": vram_used_gb,
        "mean_latency_ms": mean_latency,
        "min_latency_ms": min_latency,
        "max_latency_ms": max_latency,
        "intent_accuracy": round(intent_acc, 2),
        "exact_match_rate": round(exact_match_rate, 2),
        "macro_f1": macro_f1,
        "country_f1": cf1,
        "commodity_f1": mf1,
        "facility_f1": ff1,
        "status_f1": sf1,
        "details": {
            "country": {"p": cp, "r": cr, "f1": cf1},
            "commodity": {"p": mp, "r": mr, "f1": mf1},
            "facility": {"p": fp, "r": fr, "f1": ff1},
            "status": {"p": sp, "r": sr, "f1": sf1}
        }
    }

    print(f"[Done {provider.upper()}] Mean Latency: {mean_latency} ms | Macro F1: {macro_f1}% | Exact Match: {exact_match_rate}% | VRAM: {vram_used_gb} GB")
    return result_entry

def generate_latex_table(results: List[Dict[str, Any]]) -> str:
    """Generates an academic publication-ready LaTeX table for SoftwareX."""
    lines = [
        r"\begin{table*}[t!]",
        r"\centering",
        r"\small",
        r"\caption{Comprehensive empirical evaluation across local GPU LLMs and baseline on the NVIDIA A100-PCIE-40GB testbed over the 100-query benchmark battery.}",
        r"\label{tab:gpu_models_benchmark}",
        r"\resizebox{\textwidth}{!}{",
        r"\begin{tabular}{lcccccccc}",
        r"\hline",
        r"\textbf{Inference Model} & \textbf{Parameters} & \textbf{VRAM (GB)} & \textbf{Mean Lat. (ms)} & \textbf{Intent Acc. (\%)} & \textbf{Country F1 (\%)} & \textbf{CRM Metal F1 (\%)} & \textbf{Macro F1 (\%)} & \textbf{Data Sovereignty} \\",
        r"\hline"
    ]
    for r in results:
        vram_str = f"{r['vram_gb']:.1f}" if r['vram_gb'] > 0 else "0.0 (RAM)"
        lines.append(
            f"{r['model_name']} & {r['parameters']} & {vram_str} & {r['mean_latency_ms']:.1f} & "
            f"{r['intent_accuracy']:.1f} & {r['country_f1']:.1f} & {r['commodity_f1']:.1f} & "
            f"\\textbf{{{r['macro_f1']:.1f}}} & {r['sovereignty']} \\\\"
        )
    lines.extend([
        r"\hline",
        r"\multicolumn{9}{l}{\footnotesize Evaluated under greedy decoding ($T = 0.0$) on dual Intel Xeon CPUs and $1\times$ NVIDIA A100-PCIE-40GB GPU with CUDA 12 and FP16 precision.} \\",
        r"\end{tabular}",
        r"}",
        r"\end{table*}"
    ])
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="SoftwareX LLM Model Evaluation Benchmark")
    parser.add_argument("--models", nargs="+", default=["mock", "llama", "phi3", "qwen", "deepseek"],
                        help="List of model keys to benchmark: mock, llama, phi3, qwen, deepseek")
    parser.add_argument("--num_queries", type=int, default=100,
                        help="Number of queries to evaluate from test_battery_100.json (default: 100)")
    args = parser.parse_args()

    with open(BENCHMARK_FILE, "r", encoding="utf-8") as f:
        all_tests = json.load(f)
    test_cases = all_tests[:args.num_queries]

    print(f"\n{'='*70}")
    print(f"  SOFTWAREX CRMsDataSpace - COMPREHENSIVE LLM BENCHMARK")
    print(f"  Hardware: NVIDIA A100-PCIE-40GB (Slurm Cluster)")
    print(f"  Test Battery Size: {len(test_cases)} queries")
    print(f"  Models to Evaluate: {', '.join(args.models)}")
    print(f"{'='*70}\n")

    benchmark_results = []
    for model_key in args.models:
        if model_key not in MODEL_METADATA:
            print(f"[Warning] Unknown model key '{model_key}'. Skipping.")
            continue
        entry = run_model_benchmark(model_key, test_cases)
        if entry:
            benchmark_results.append(entry)

    # Save complete JSON
    with open(RESULTS_JSON, "w", encoding="utf-8") as f:
        json.dump(benchmark_results, f, indent=2, ensure_ascii=False)
    print(f"\n[Saved] Detailed JSON metrics saved to: {RESULTS_JSON}")

    # Generate LaTeX Table
    latex_table = generate_latex_table(benchmark_results)
    
    # Text summary
    summary_lines = [
        "="*80,
        "  SOFTWAREX BENCHMARK SUMMARY (NVIDIA A100 GPU + LOCAL MODELS)",
        "="*80,
        f"{'Model':<30} | {'Params':<8} | {'VRAM (GB)':<10} | {'Lat. (ms)':<10} | {'Macro F1':<10} | {'Exact Match':<12}",
        "-"*80
    ]
    for r in benchmark_results:
        summary_lines.append(
            f"{r['model_name']:<30} | {r['parameters']:<8} | {r['vram_gb']:<10.1f} | {r['mean_latency_ms']:<10.1f} | {r['macro_f1']:<10.1f}% | {r['exact_match_rate']:<12.1f}%"
        )
    summary_lines.append("="*80)
    summary_lines.append("\nLATEX TABLE OUTPUT FOR MANUSCRIPT:\n")
    summary_lines.append(latex_table)

    summary_text = "\n".join(summary_lines)
    print("\n" + summary_text)

    with open(RESULTS_TXT, "w", encoding="utf-8") as f:
        f.write(summary_text)
    print(f"[Saved] Text report saved to: {RESULTS_TXT}")

if __name__ == "__main__":
    main()
