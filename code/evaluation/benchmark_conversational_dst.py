#!/usr/bin/env python3
"""
benchmark_conversational_dst.py
Comprehensive Evaluation Benchmark for Multi-Turn Conversational Dialogue State Tracking (DST):
Compares Rule-based Deterministic Baseline (Mock), Llama 3.2 3B, Phi-3 Mini 4K, Qwen 2.5 7B,
and DeepSeek R1 7B across 25 multi-turn dialogue episodes (102 sequential conversational turns).

Evaluates:
- Turn Dialogue Action Classification Accuracy (new_search, expand, refine, remove, reset)
- Field-level F1-scores for accumulated state tracking across conversation history
  (countries, commodities, storage_facility_types, project_status, restored)
- Cumulative State Exact Match Rate (% of turns where the active filter state is 100% correct)
- Episode Completion Rate (% of entire dialogue episodes executed with zero state drift)
- Turn inference latency (ms) and GPU VRAM memory footprint (GB)
- Generates LaTeX table for the SoftwareX manuscript
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
    get_model_state
)

BENCHMARK_FILE = Path(__file__).resolve().parent / "test_battery_conversational_dst.json"
RESULTS_JSON = Path(__file__).resolve().parent / "benchmark_dst_results.json"
RESULTS_TXT = Path(__file__).resolve().parent / "benchmark_dst_summary.txt"

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

def calculate_set_metrics(gold_list: List[str], pred_list: List[str]) -> Tuple[float, float, float, int, int, int]:
    gold_set = set(gold_list)
    pred_set = set(pred_list)
    
    tp = len(gold_set.intersection(pred_set))
    fp = len(pred_set - gold_set)
    fn = len(gold_set - pred_set)
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    return precision, recall, f1, tp, fp, fn

def run_conversational_benchmark(provider: str, episodes: List[Dict[str, Any]]) -> Dict[str, Any]:
    print(f"\n{'='*75}")
    print(f"  EVALUATING DST BENCHMARK: {provider.upper()} ({MODEL_METADATA[provider]['name']})")
    print(f"{'='*75}")

    vram_used_gb = 0.0
    if provider != "mock":
        print(f"[Benchmark] Loading weights for '{provider}' into GPU VRAM...")
        success = load_local_model_weights(provider)
        if not success:
            print(f"[ERROR] Failed to load model '{provider}'. Running in CPU fallback mode.")
        state = get_model_state()
        vram_used_gb = state.get("vram_gb", 0.0)
        print(f"[Benchmark] Status: {state.get('status')} | VRAM: {vram_used_gb} GB.")

    # Warm-up run
    print("[Benchmark] Executing warm-up turn...")
    try:
        process_chat_message("Muestra litio en España", provider=provider)
    except Exception as e:
        print(f"[Warning] Warm-up failed: {e}")

    total_turns = sum(len(ep["turns"]) for ep in episodes)
    latencies_ms = []
    
    action_correct = 0
    exact_state_matches = 0
    episodes_fully_correct = 0

    country_stats = [0, 0, 0]
    comm_stats = [0, 0, 0]
    fac_stats = [0, 0, 0]
    status_stats = [0, 0, 0]
    restored_matches = 0

    action_breakdown = {
        "new_search": {"total": 0, "correct": 0},
        "expand": {"total": 0, "correct": 0},
        "refine": {"total": 0, "correct": 0},
        "remove": {"total": 0, "correct": 0},
        "reset": {"total": 0, "correct": 0}
    }

    processed_turns = 0

    for ep_idx, ep in enumerate(episodes, 1):
        ep_id = ep["episode_id"]
        ep_title = ep.get("title", "")
        turns = ep["turns"]
        
        # Reset conversation state for new dialogue episode
        current_filters = {}
        conversation_history = []
        ep_perfect = True

        for t in turns:
            processed_turns += 1
            turn_num = t["turn"]
            q = t["query"]
            exp_action = t["expected_action"]
            exp_filters = t["expected_accumulated_filters"]

            if exp_action in action_breakdown:
                action_breakdown[exp_action]["total"] += 1

            start_time = time.perf_counter()
            try:
                res = process_chat_message(
                    query=q,
                    provider=provider,
                    conversation_history=conversation_history,
                    current_filters=current_filters
                )
            except Exception as err:
                print(f"  [Error] Episode {ep_id} Turn {turn_num} failed: {err}")
                res = {
                    "dialogue_action": "new_search",
                    "current_filters": current_filters,
                    "conversation_history": conversation_history
                }
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            latencies_ms.append(latency_ms)

            pred_action = res.get("dialogue_action", "new_search")
            pred_filters = res.get("current_filters", {})
            current_filters = pred_filters
            conversation_history = res.get("conversation_history", [])

            # 1. Action accuracy
            if pred_action == exp_action:
                action_correct += 1
                if exp_action in action_breakdown:
                    action_breakdown[exp_action]["correct"] += 1
            else:
                ep_perfect = False

            # 2. Field metrics on accumulated state
            p, r, f1, tp, fp, fn = calculate_set_metrics(exp_filters.get("countries", []), pred_filters.get("countries", []))
            country_stats[0] += tp; country_stats[1] += fp; country_stats[2] += fn
            c_match = (set(exp_filters.get("countries", [])) == set(pred_filters.get("countries", [])))

            p, r, f1, tp, fp, fn = calculate_set_metrics(exp_filters.get("commodities", []), pred_filters.get("commodities", []))
            comm_stats[0] += tp; comm_stats[1] += fp; comm_stats[2] += fn
            m_match = (set(exp_filters.get("commodities", [])) == set(pred_filters.get("commodities", [])))

            p, r, f1, tp, fp, fn = calculate_set_metrics(exp_filters.get("storage_facility_types", []), pred_filters.get("storage_facility_types", []))
            fac_stats[0] += tp; fac_stats[1] += fp; fac_stats[2] += fn
            f_match = (set(exp_filters.get("storage_facility_types", [])) == set(pred_filters.get("storage_facility_types", [])))

            p, r, f1, tp, fp, fn = calculate_set_metrics(exp_filters.get("project_status", []), pred_filters.get("project_status", []))
            status_stats[0] += tp; status_stats[1] += fp; status_stats[2] += fn
            s_match = (set(exp_filters.get("project_status", [])) == set(pred_filters.get("project_status", [])))

            r_match = (exp_filters.get("restored") == pred_filters.get("restored"))
            if r_match:
                restored_matches += 1

            turn_exact = c_match and m_match and f_match and s_match and r_match
            if turn_exact:
                exact_state_matches += 1
            else:
                ep_perfect = False

        if ep_perfect:
            episodes_fully_correct += 1

        if ep_idx % 5 == 0 or ep_idx == len(episodes):
            print(f"  Processed {ep_idx}/{len(episodes)} episodes ({processed_turns}/{total_turns} turns) | Current Lat.: {latency_ms:.1f} ms")

    # Global computations
    action_accuracy = (action_correct / total_turns) * 100.0
    exact_match_rate = (exact_state_matches / total_turns) * 100.0
    episode_success_rate = (episodes_fully_correct / len(episodes)) * 100.0
    restored_accuracy = (restored_matches / total_turns) * 100.0

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

    # Evict model if loaded
    if provider != "mock":
        unload_all_local_models()

    action_rates = {}
    for act, data in action_breakdown.items():
        tot = data["total"]
        cor = data["correct"]
        action_rates[act] = round((cor / tot) * 100.0, 1) if tot > 0 else 0.0

    result_entry = {
        "provider": provider,
        "model_name": MODEL_METADATA[provider]["name"],
        "parameters": MODEL_METADATA[provider]["params"],
        "precision": MODEL_METADATA[provider]["precision"],
        "sovereignty": MODEL_METADATA[provider]["sovereignty"],
        "vram_gb": vram_used_gb,
        "total_episodes": len(episodes),
        "total_turns": total_turns,
        "mean_latency_ms": mean_latency,
        "min_latency_ms": min_latency,
        "max_latency_ms": max_latency,
        "action_accuracy": round(action_accuracy, 2),
        "exact_state_match_rate": round(exact_match_rate, 2),
        "episode_success_rate": round(episode_success_rate, 2),
        "macro_f1": macro_f1,
        "country_f1": cf1,
        "commodity_f1": mf1,
        "facility_f1": ff1,
        "status_f1": sf1,
        "restored_accuracy": round(restored_accuracy, 2),
        "action_breakdown": action_rates,
        "details": {
            "country": {"p": cp, "r": cr, "f1": cf1},
            "commodity": {"p": mp, "r": mr, "f1": mf1},
            "facility": {"p": fp, "r": fr, "f1": ff1},
            "status": {"p": sp, "r": sr, "f1": sf1}
        }
    }

    print(f"\n[Done {provider.upper()}] Action Acc: {action_accuracy:.1f}% | State Exact Match: {exact_match_rate:.1f}% | Macro F1: {macro_f1}% | Mean Latency: {mean_latency} ms")
    return result_entry

def generate_latex_dst_table(results: List[Dict[str, Any]]) -> str:
    """Generates an academic publication-ready LaTeX table for SoftwareX."""
    lines = [
        r"\begin{table*}[t!]",
        r"\centering",
        r"\small",
        r"\caption{Empirical evaluation of multi-turn Conversational Dialogue State Tracking (DST) across 25 dialogue episodes (102 sequential conversational turns) on the NVIDIA A100 testbed.}",
        r"\label{tab:dst_benchmark}",
        r"\resizebox{\textwidth}{!}{",
        r"\begin{tabular}{lcccccccc}",
        r"\hline",
        r"\textbf{Inference Model} & \textbf{Parameters} & \textbf{VRAM (GB)} & \textbf{Action Acc. (\%)} & \textbf{State Country F1 (\%)} & \textbf{State CRM F1 (\%)} & \textbf{Macro State F1 (\%)} & \textbf{State Exact Match (\%)} & \textbf{Mean Turn Lat. (ms)} \\",
        r"\hline"
    ]
    for r in results:
        vram_str = f"{r['vram_gb']:.1f}" if r['vram_gb'] > 0 else "0.0 (RAM)"
        lines.append(
            f"{r['model_name']} & {r['parameters']} & {vram_str} & {r['action_accuracy']:.1f} & "
            f"{r['country_f1']:.1f} & {r['commodity_f1']:.1f} & "
            f"\\textbf{{{r['macro_f1']:.1f}}} & {r['exact_state_match_rate']:.1f} & {r['mean_latency_ms']:.1f} \\\\"
        )
    lines.extend([
        r"\hline",
        r"\multicolumn{9}{l}{\footnotesize Evaluated on 102 sequential turns spanning 5 dialogue actions: \texttt{new\_search}, \texttt{expand} (OR), \texttt{refine} (AND), \texttt{remove}, and \texttt{reset}.} \\",
        r"\end{tabular}",
        r"}",
        r"\end{table*}"
    ])
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="SoftwareX Conversational DST Benchmark")
    parser.add_argument("--models", nargs="+", default=["mock", "llama", "phi3", "qwen", "deepseek"],
                        help="List of model keys to benchmark: mock, llama, phi3, qwen, deepseek")
    args = parser.parse_args()

    with open(BENCHMARK_FILE, "r", encoding="utf-8") as f:
        episodes = json.load(f)

    total_turns = sum(len(ep["turns"]) for ep in episodes)
    print(f"\n{'='*75}")
    print(f"  SOFTWAREX - MULTI-TURN CONVERSATIONAL DST BENCHMARK")
    print(f"  Episodes: {len(episodes)} | Total Conversational Turns: {total_turns}")
    print(f"  Models: {', '.join(args.models)}")
    print(f"{'='*75}\n")

    existing_map = {}
    if RESULTS_JSON.exists():
        try:
            with open(RESULTS_JSON, "r", encoding="utf-8") as f:
                old_list = json.load(f)
                for item in old_list:
                    existing_map[item.get("provider")] = item
        except Exception:
            pass

    for model_key in args.models:
        if model_key not in MODEL_METADATA:
            print(f"[Warning] Unknown model key '{model_key}'. Skipping.")
            continue
        entry = run_conversational_benchmark(model_key, episodes)
        if entry:
            existing_map[entry["provider"]] = entry

    order = ["mock", "llama", "phi3", "qwen", "deepseek"]
    benchmark_results = []
    for k in order:
        if k in existing_map:
            benchmark_results.append(existing_map[k])
    for k, v in existing_map.items():
        if k not in order:
            benchmark_results.append(v)

    with open(RESULTS_JSON, "w", encoding="utf-8") as f:
        json.dump(benchmark_results, f, indent=2, ensure_ascii=False)
    print(f"\n[Saved] Detailed DST metrics saved to: {RESULTS_JSON}")

    latex_table = generate_latex_dst_table(benchmark_results)

    summary_lines = [
        "="*95,
        "  SOFTWAREX CONVERSATIONAL DST BENCHMARK SUMMARY (102 TURNS, 25 EPISODES)",
        "="*95,
        f"{'Model':<30} | {'Action Acc':<11} | {'Country F1':<11} | {'CRM F1':<10} | {'Macro F1':<10} | {'Exact Match':<12} | {'Lat. (ms)':<10}",
        "-"*95
    ]
    for r in benchmark_results:
        summary_lines.append(
            f"{r['model_name']:<30} | {r['action_accuracy']:<10.1f}% | {r['country_f1']:<10.1f}% | {r['commodity_f1']:<9.1f}% | {r['macro_f1']:<9.1f}% | {r['exact_state_match_rate']:<11.1f}% | {r['mean_latency_ms']:<10.1f}"
        )
    summary_lines.append("="*95)
    summary_lines.append("\nLATEX TABLE OUTPUT FOR MANUSCRIPT:\n")
    summary_lines.append(latex_table)

    summary_text = "\n".join(summary_lines)
    print("\n" + summary_text)

    with open(RESULTS_TXT, "w", encoding="utf-8") as f:
        f.write(summary_text)
    print(f"[Saved] Summary text report saved to: {RESULTS_TXT}")

if __name__ == "__main__":
    main()
