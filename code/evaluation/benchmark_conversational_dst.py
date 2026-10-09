#!/usr/bin/env python3
"""
benchmark_conversational_dst.py
Evaluates Dialogue State Tracking (DST) and accumulated filter extraction accuracy
across multi-turn conversational dialogue episodes on the NVIDIA A100 testbed.

Specifically evaluates expected filter accuracy across test categories:
- search: Initial spatial searches with natural language, periphrasis, and synonyms
- expansion: Additive disjunction (OR) using natural conversational phrasing
- refinement: Progressive conjunction (AND) with complex constraints
- removal: Subtractive exclusion with diverse natural phrasing
- context: Anaphoric, elliptical, and cross-turn conversational continuity
- reset: Natural conversational resets
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
    "llama8b": {
        "name": "Llama 3.1 8B Instruct",
        "params": "8.03B",
        "precision": "FP16",
        "sovereignty": "100% On-Premises (Private GPU)"
    },
    "mistral": {
        "name": "Mistral 7B Instruct v0.2",
        "params": "7.24B",
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

CATEGORIES = ["search", "expansion", "refinement", "removal", "context", "reset"]

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

def compute_macro_f1(stats: List[int]) -> float:
    tp, fp, fn = stats
    p = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    r = tp / (tp + fn) if (tp + fn) > 0 else 1.0
    f1 = (2 * p * r) / (p + r) if (p + r) > 0 else 0.0
    return round(f1 * 100.0, 1)

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

    category_stats = {
        cat: {
            "total": 0,
            "exact": 0,
            "country": [0, 0, 0],
            "comm": [0, 0, 0],
            "fac": [0, 0, 0],
            "status": [0, 0, 0],
            "restored_matches": 0
        }
        for cat in CATEGORIES
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
            cat = t.get("test_category", "search")
            if cat not in category_stats:
                category_stats[cat] = {
                    "total": 0, "exact": 0, "country": [0, 0, 0],
                    "comm": [0, 0, 0], "fac": [0, 0, 0], "status": [0, 0, 0], "restored_matches": 0
                }
            category_stats[cat]["total"] += 1

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
            category_stats[cat]["country"][0] += tp; category_stats[cat]["country"][1] += fp; category_stats[cat]["country"][2] += fn
            c_match = (set(exp_filters.get("countries", [])) == set(pred_filters.get("countries", [])))

            p, r, f1, tp, fp, fn = calculate_set_metrics(exp_filters.get("commodities", []), pred_filters.get("commodities", []))
            comm_stats[0] += tp; comm_stats[1] += fp; comm_stats[2] += fn
            category_stats[cat]["comm"][0] += tp; category_stats[cat]["comm"][1] += fp; category_stats[cat]["comm"][2] += fn
            m_match = (set(exp_filters.get("commodities", [])) == set(pred_filters.get("commodities", [])))

            p, r, f1, tp, fp, fn = calculate_set_metrics(exp_filters.get("storage_facility_types", []), pred_filters.get("storage_facility_types", []))
            fac_stats[0] += tp; fac_stats[1] += fp; fac_stats[2] += fn
            category_stats[cat]["fac"][0] += tp; category_stats[cat]["fac"][1] += fp; category_stats[cat]["fac"][2] += fn
            f_match = (set(exp_filters.get("storage_facility_types", [])) == set(pred_filters.get("storage_facility_types", [])))

            p, r, f1, tp, fp, fn = calculate_set_metrics(exp_filters.get("project_status", []), pred_filters.get("project_status", []))
            status_stats[0] += tp; status_stats[1] += fp; status_stats[2] += fn
            category_stats[cat]["status"][0] += tp; category_stats[cat]["status"][1] += fp; category_stats[cat]["status"][2] += fn
            s_match = (set(exp_filters.get("project_status", [])) == set(pred_filters.get("project_status", [])))

            r_match = (exp_filters.get("restored") == pred_filters.get("restored"))
            if r_match:
                restored_matches += 1
                category_stats[cat]["restored_matches"] += 1

            exp_op = exp_filters.get("commodity_operator", "OR")
            pred_op = pred_filters.get("commodity_operator", "OR")
            op_match = (len(exp_filters.get("commodities", [])) <= 1) or (exp_op == pred_op)

            turn_exact = c_match and m_match and f_match and s_match and r_match and op_match
            if turn_exact:
                exact_state_matches += 1
                category_stats[cat]["exact"] += 1
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

    # Category breakdown computations
    cat_results = {}
    for cat_name, c_data in category_stats.items():
        tot = c_data["total"]
        ex = c_data["exact"]
        ex_rate = round((ex / tot) * 100.0, 1) if tot > 0 else 0.0
        c_f1 = compute_macro_f1(c_data["country"])
        m_f1 = compute_macro_f1(c_data["comm"])
        f_f1 = compute_macro_f1(c_data["fac"])
        s_f1 = compute_macro_f1(c_data["status"])
        c_macro = round((c_f1 + m_f1 + f_f1 + s_f1) / 4.0, 1)
        cat_results[cat_name] = {
            "total_turns": tot,
            "exact_matches": ex,
            "exact_match_rate": ex_rate,
            "macro_f1": c_macro
        }

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
        "category_metrics": cat_results,
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
    """
    Generates an academic publication-ready LaTeX table for SoftwareX
    strictly focusing on expected filter precision/accuracy across test categories.
    """
    lines = [
        r"\begin{table*}[t!]",
        r"\centering",
        r"\small",
        r"\caption{Empirical evaluation of expected filter accuracy (Macro F1 / Exact Match) across conversational test categories (132 sequential turns, 30 dialogue episodes) on the NVIDIA A100 testbed.}",
        r"\label{tab:dst_benchmark}",
        r"\resizebox{\textwidth}{!}{",
        r"\begin{tabular}{lccccccc}",
        r"\hline",
        r"\textbf{Inference Model} & \textbf{Search (\%)} & \textbf{Expansion (\%)} & \textbf{Refinement (\%)} & \textbf{Removal (\%)} & \textbf{Context (\%)} & \textbf{Reset (\%)} & \textbf{Global Macro F1 (\%)} \\",
        r"\hline"
    ]
    for r in results:
        cm = r.get("category_metrics", {})
        s_f1 = cm.get("search", {}).get("macro_f1", 0.0)
        e_f1 = cm.get("expansion", {}).get("macro_f1", 0.0)
        ref_f1 = cm.get("refinement", {}).get("macro_f1", 0.0)
        rem_f1 = cm.get("removal", {}).get("macro_f1", 0.0)
        ctx_f1 = cm.get("context", {}).get("macro_f1", 0.0)
        rst_f1 = cm.get("reset", {}).get("exact_match_rate", 0.0)
        glob_f1 = r.get("macro_f1", 0.0)

        lines.append(
            f"{r['model_name']} & {s_f1:.1f} & {e_f1:.1f} & {ref_f1:.1f} & "
            f"{rem_f1:.1f} & {ctx_f1:.1f} & {rst_f1:.1f} & \\textbf{{{glob_f1:.1f}}} \\\\"
        )
    lines.extend([
        r"\hline",
        r"\multicolumn{8}{l}{\footnotesize Filter accuracy measured as Macro F1 on accumulated expected filters across 6 test categories: Initial Search (31 turns), Expansion (19 turns), Refinement (30 turns), Removal (28 turns), Contextual Anaphora (14 turns), and Reset (10 turns).} \\",
        r"\end{tabular}",
        r"}",
        r"\end{table*}"
    ])
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="SoftwareX Conversational DST Benchmark")
    parser.add_argument("--models", nargs="+", default=["mock", "phi3", "mistral", "llama8b", "qwen"],
                        help="List of model keys to benchmark: mock, phi3, mistral, llama8b, qwen")
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

    order = ["mock", "phi3", "mistral", "llama8b", "qwen"]
    benchmark_results = []
    for k in order:
        if k in existing_map:
            benchmark_results.append(existing_map[k])

    with open(RESULTS_JSON, "w", encoding="utf-8") as f:
        json.dump(benchmark_results, f, indent=2, ensure_ascii=False)
    print(f"\n[Saved] Detailed DST metrics saved to: {RESULTS_JSON}")

    latex_table = generate_latex_dst_table(benchmark_results)

    summary_lines = [
        "="*105,
        f"  SOFTWAREX CONVERSATIONAL DST BENCHMARK (132 TURNS, 30 EPISODES) - FILTER ACCURACY ACROSS TEST TYPES",
        "="*105,
        f"{'Model':<30} | {'Search':<8} | {'Expand':<8} | {'Refine':<8} | {'Remove':<8} | {'Context':<8} | {'Reset':<8} | {'Global F1':<10}",
        "-"*105
    ]
    for r in benchmark_results:
        cm = r.get("category_metrics", {})
        s_f1 = cm.get("search", {}).get("macro_f1", 0.0)
        e_f1 = cm.get("expansion", {}).get("macro_f1", 0.0)
        ref_f1 = cm.get("refinement", {}).get("macro_f1", 0.0)
        rem_f1 = cm.get("removal", {}).get("macro_f1", 0.0)
        ctx_f1 = cm.get("context", {}).get("macro_f1", 0.0)
        rst_f1 = cm.get("reset", {}).get("exact_match_rate", 0.0)
        glob_f1 = r.get("macro_f1", 0.0)
        summary_lines.append(
            f"{r['model_name']:<30} | {s_f1:<7.1f}% | {e_f1:<7.1f}% | {ref_f1:<7.1f}% | {rem_f1:<7.1f}% | {ctx_f1:<7.1f}% | {rst_f1:<7.1f}% | {glob_f1:<9.1f}%"
        )
    summary_lines.append("="*105)
    summary_lines.append("\nLATEX TABLE OUTPUT FOR MANUSCRIPT:\n")
    summary_lines.append(latex_table)

    summary_text = "\n".join(summary_lines)
    print("\n" + summary_text)

    with open(RESULTS_TXT, "w", encoding="utf-8") as f:
        f.write(summary_text)
    print(f"[Saved] Summary text report saved to: {RESULTS_TXT}")

if __name__ == "__main__":
    main()
