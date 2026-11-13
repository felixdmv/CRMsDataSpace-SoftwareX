#!/usr/bin/env python3
"""
benchmark_rredondo.py
================================================================================
Comprehensive Evaluation Benchmark Suite for SoftwareX:
"A Modular NLU-Solr Architecture with Dynamic GIS Visual Synchronization 
 for Conversational Spatial Search"

Evaluates four fundamental architectural capabilities (v2.3.0 support):
1. Guardrails & Out-of-Domain Containment (crmDataSpace context enforcement & anti-hallucination)
2. Single-Turn Queries & Slot Filling (Canonical extraction, exclusions, technical specs)
3. Boolean Aggregation & Sum of Escombreras (Conjunction AND, Disjunction OR, Compound queries)
4. Conversational Memory & Dialogue State Tracking (DST: 'y también...', 'y además...', 'de esas...')

Supports execution across local HPC GPU clusters (NVIDIA A100/H100 via Slurm + Apptainer)
and deterministic offline CPU heuristics (Mock Baseline).
================================================================================
"""

import sys
import os
import time
import json
import argparse
import platform
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# Dynamically ensure code/ is on sys.path
EVAL_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = EVAL_DIR.parent
CODE_DIR = PROJECT_ROOT / "code"

if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

try:
    from agent import process_chat_message
    from llm_client import (
        load_local_model_weights,
        unload_all_local_models,
        get_model_state
    )
except ImportError as err:
    sys.stderr.write(f"[FATAL] Cannot import SoftwareX modules from {CODE_DIR}: {err}\n")
    sys.exit(1)

DEFAULT_BATTERY_PATH = EVAL_DIR / "test_battery_rredondo.json"
DEFAULT_RESULTS_DIR = EVAL_DIR / "results"

MODEL_METADATA = {
    "mock": {
        "name": "Deterministic Baseline (Mock)",
        "params": "Rule-based",
        "precision": "CPU Heuristics",
        "sovereignty": "100% On-Premises (Air-gapped)",
        "type": "cpu"
    },
    "llama": {
        "name": "Llama 3.2 3B Instruct",
        "params": "3.21B",
        "precision": "FP16",
        "sovereignty": "100% On-Premises (Private GPU)",
        "type": "gpu"
    },
    "phi3": {
        "name": "Phi-3 Mini 4K Instruct",
        "params": "3.82B",
        "precision": "FP16",
        "sovereignty": "100% On-Premises (Private GPU)",
        "type": "gpu"
    },
    "qwen": {
        "name": "Qwen 2.5 7B Instruct",
        "params": "7.61B",
        "precision": "FP16",
        "sovereignty": "100% On-Premises (Private GPU)",
        "type": "gpu"
    },
    "mistral": {
        "name": "Mistral 7B Instruct v0.2",
        "params": "7.24B",
        "precision": "FP16",
        "sovereignty": "100% On-Premises (Private GPU)",
        "type": "gpu"
    },
    "llama8b": {
        "name": "Llama 3.1 8B Instruct",
        "params": "8.03B",
        "precision": "FP16",
        "sovereignty": "100% On-Premises (Private GPU)",
        "type": "gpu"
    },
    "deepseek": {
        "name": "DeepSeek R1 Distill Qwen 7B",
        "params": "7.61B",
        "precision": "FP16",
        "sovereignty": "100% On-Premises (Private GPU)",
        "type": "gpu"
    }
}


def calculate_set_metrics(gold_list: List[str], pred_list: List[str]) -> Tuple[float, float, float, int, int, int]:
    """Computes precision, recall, f1, and raw TP, FP, FN counts for entity slot sets."""
    gold_set = set(gold_list)
    pred_set = set(pred_list)

    tp = len(gold_set.intersection(pred_set))
    fp = len(pred_set - gold_set)
    fn = len(gold_set - pred_set)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    return precision, recall, f1, tp, fp, fn


# =============================================================================
# EVALUATION MODULE 1: OUT-OF-DOMAIN GUARDRAILS
# =============================================================================
def evaluate_guardrails(provider: str, test_cases: List[Dict[str, Any]], verbose: bool = False) -> Dict[str, Any]:
    print(f"\n--- [Suite 1] Evaluating Out-of-Domain Guardrails & Anti-Hallucination ({len(test_cases)} tests) ---")
    
    total = len(test_cases)
    passed = 0
    hallucinations = 0
    latencies = []
    failed_details = []

    for tc in test_cases:
        tc_id = tc["id"]
        q = tc["query"]
        sub_type = tc.get("sub_type", "general")
        expected_intent = tc.get("expected_intent", "generic_qa")
        expected_keywords = tc.get("expected_keywords", [])

        t0 = time.perf_counter()
        try:
            res = process_chat_message(q, provider=provider)
        except Exception as e:
            res = {"error": str(e), "num_found": -1, "response_text": ""}
        lat_ms = (time.perf_counter() - t0) * 1000.0
        latencies.append(lat_ms)

        num_found = res.get("num_found", 0)
        resp_text = (res.get("response_text") or "").lower()
        extracted_intent = res.get("extracted_json", {}).get("intent", "")

        # Guardrail checks:
        # 1. Zero records retrieved (no hallucinated / fabricated sites)
        is_zero_docs = (num_found == 0)
        if not is_zero_docs:
            hallucinations += 1

        # 2. Appropriate rejection notification present in response text
        domain_rejection_cues = [
            "fuera de ámbito", "fuera de cobertura", "no minero", "no forma parte",
            "no se ha ejecutado", "no corresponde", "out-of-scope", "outside",
            "not included", "geographical scope", "restricted to 12", "limitado exclusivamente",
            "país fuera de", "country outside"
        ]
        has_notice = any(cue in resp_text for cue in domain_rejection_cues)
        if not has_notice and tc.get("unsupported_country"):
            has_notice = tc["unsupported_country"].lower() in resp_text

        is_passed = is_zero_docs and has_notice

        if is_passed:
            passed += 1
            if verbose:
                print(f"  [PASS] {tc_id} ({sub_type}): '{q[:50]}...' -> 0 docs, notice verified ({lat_ms:.1f} ms)")
        else:
            reason = f"docs={num_found} (exp 0), has_notice={has_notice}, intent={extracted_intent}"
            failed_details.append(f"[{tc_id}] Q: '{q}' -> FAILED: {reason}")
            if verbose:
                print(f"  [FAIL] {tc_id}: {reason}")

    acc = (passed / total) * 100.0 if total > 0 else 0.0
    hallucination_rate = (hallucinations / total) * 100.0 if total > 0 else 0.0
    mean_lat = sum(latencies) / len(latencies) if latencies else 0.0

    print(f"  -> Suite 1 Result: {passed}/{total} Passed ({acc:.1f}%) | Hallucination Rate: {hallucination_rate:.1f}% | Mean Latency: {mean_lat:.1f} ms")

    return {
        "suite": "guardrails_ood",
        "total_tests": total,
        "passed_tests": passed,
        "accuracy": round(acc, 2),
        "hallucinations_detected": hallucinations,
        "hallucination_rate": round(hallucination_rate, 2),
        "mean_latency_ms": round(mean_lat, 1),
        "min_latency_ms": round(min(latencies), 1) if latencies else 0.0,
        "max_latency_ms": round(max(latencies), 1) if latencies else 0.0,
        "failures": failed_details
    }


# =============================================================================
# EVALUATION MODULE 2: SINGLE-TURN QUERIES & SLOT FILLING (v2.3.0)
# =============================================================================
def evaluate_single_turn(provider: str, test_cases: List[Dict[str, Any]], verbose: bool = False) -> Dict[str, Any]:
    print(f"\n--- [Suite 2] Evaluating Single-Turn Queries & Slot Filling ({len(test_cases)} tests) ---")

    total = len(test_cases)
    passed = 0
    slot_f1s = []
    latencies = []
    failed_details = []

    for tc in test_cases:
        tc_id = tc["id"]
        q = tc["query"]
        exp_filters = tc.get("expected_filters", {})
        exp_count = tc.get("expected_count")

        t0 = time.perf_counter()
        try:
            res = process_chat_message(q, provider=provider)
        except Exception as e:
            res = {"error": str(e), "num_found": -1, "filters": {}}
        lat_ms = (time.perf_counter() - t0) * 1000.0
        latencies.append(lat_ms)

        pred_filters = res.get("filters", {})
        pred_count = res.get("num_found", 0)

        # F1 metrics across slots (countries, commodities, facility types)
        c_p, c_r, c_f1, _, _, _ = calculate_set_metrics(exp_filters.get("countries", []), pred_filters.get("countries", []))
        m_p, m_r, m_f1, _, _, _ = calculate_set_metrics(exp_filters.get("commodities", []), pred_filters.get("commodities", []))
        f_p, f_r, f_f1, _, _, _ = calculate_set_metrics(exp_filters.get("storage_facility_types", []), pred_filters.get("storage_facility_types", []))

        macro_slot_f1 = (c_f1 + m_f1 + f_f1) / 3.0
        slot_f1s.append(macro_slot_f1)

        count_ok = True if exp_count is None else (pred_count == exp_count)
        slots_ok = macro_slot_f1 >= 0.8

        is_passed = count_ok and slots_ok

        if is_passed:
            passed += 1
            if verbose:
                print(f"  [PASS] {tc_id}: '{q[:40]}...' -> F1={macro_slot_f1:.2f}, cnt={pred_count} ({lat_ms:.1f} ms)")
        else:
            reason = f"slot_f1={macro_slot_f1:.2f}, count={pred_count} (exp {exp_count})"
            failed_details.append(f"[{tc_id}] Q: '{q}' -> FAILED: {reason}")
            if verbose:
                print(f"  [FAIL] {tc_id}: {reason}")

    acc = (passed / total) * 100.0 if total > 0 else 0.0
    mean_f1 = (sum(slot_f1s) / len(slot_f1s)) * 100.0 if slot_f1s else 0.0
    mean_lat = sum(latencies) / len(latencies) if latencies else 0.0

    print(f"  -> Suite 2 Result: {passed}/{total} Passed ({acc:.1f}%) | Mean Slot F1: {mean_f1:.1f}% | Mean Latency: {mean_lat:.1f} ms")

    return {
        "suite": "single_turn_queries",
        "total_tests": total,
        "passed_tests": passed,
        "accuracy": round(acc, 2),
        "mean_slot_f1": round(mean_f1, 2),
        "mean_latency_ms": round(mean_lat, 1),
        "min_latency_ms": round(min(latencies), 1) if latencies else 0.0,
        "max_latency_ms": round(max(latencies), 1) if latencies else 0.0,
        "failures": failed_details
    }


# =============================================================================
# EVALUATION MODULE 3: BOOLEAN AGGREGATION & SUM OF ESCOMBRERAS
# =============================================================================
def evaluate_boolean_sum(provider: str, test_cases: List[Dict[str, Any]], verbose: bool = False) -> Dict[str, Any]:
    print(f"\n--- [Suite 3] Evaluating Boolean Aggregation & Sum of Escombreras ({len(test_cases)} tests) ---")

    total = len(test_cases)
    passed = 0
    operator_correct = 0
    sum_matches = 0
    disambig_matches = 0
    disambig_total = 0
    latencies = []
    failed_details = []
    slot_f1s = []

    for tc in test_cases:
        tc_id = tc["id"]
        q = tc["query"]
        expected_op = tc.get("expected_operator", "OR")
        expected_count = tc.get("expected_count")
        expected_disambig = tc.get("expected_disambiguation", False)
        is_sum_query = tc.get("is_sum_query", False)

        t0 = time.perf_counter()
        try:
            res = process_chat_message(q, provider=provider)
        except Exception as e:
            res = {"error": str(e), "num_found": -1, "filters": {}}
        lat_ms = (time.perf_counter() - t0) * 1000.0
        latencies.append(lat_ms)

        filters = res.get("filters", {})
        pred_op = filters.get("commodity_operator", "OR")
        pred_count = res.get("num_found", 0)
        has_disambig = bool(res.get("disambiguation_options"))

        # 1. Operator match
        op_ok = (pred_op == expected_op)
        if op_ok:
            operator_correct += 1

        # 2. Count / Sum match
        count_ok = True
        if expected_count is not None:
            count_ok = (pred_count == expected_count)
            if is_sum_query and count_ok:
                sum_matches += 1

        # 3. Disambiguation check (for zero-result conjunctions)
        disambig_ok = True
        if expected_disambig:
            disambig_total += 1
            disambig_ok = has_disambig
            if disambig_ok:
                disambig_matches += 1

        # 4. Slot extraction F1
        exp_comms = set(tc.get("expected_commodities_or", []) + tc.get("expected_commodities_and", []))
        pred_comms = set(filters.get("commodities", []))
        _, _, comm_f1, _, _, _ = calculate_set_metrics(list(exp_comms), list(pred_comms))
        slot_f1s.append(comm_f1)

        is_passed = op_ok and count_ok and disambig_ok and (comm_f1 >= 0.8 if exp_comms else True)

        if is_passed:
            passed += 1
            if verbose:
                print(f"  [PASS] {tc_id}: '{q}' -> op={pred_op}, count={pred_count} (exp {expected_count}), lat={lat_ms:.1f} ms")
        else:
            reason = f"pred_op={pred_op} (exp {expected_op}), count={pred_count} (exp {expected_count}), disambig={has_disambig}"
            failed_details.append(f"[{tc_id}] Q: '{q}' -> FAILED: {reason}")
            if verbose:
                print(f"  [FAIL] {tc_id}: {reason}")

    op_acc = (operator_correct / total) * 100.0 if total > 0 else 0.0
    sum_queries_count = sum(1 for tc in test_cases if tc.get("is_sum_query"))
    sum_rate = (sum_matches / sum_queries_count) * 100.0 if sum_queries_count > 0 else 0.0
    pass_rate = (passed / total) * 100.0 if total > 0 else 0.0
    mean_slot_f1 = (sum(slot_f1s) / len(slot_f1s)) * 100.0 if slot_f1s else 0.0
    mean_lat = sum(latencies) / len(latencies) if latencies else 0.0

    print(f"  -> Suite 3 Result: {passed}/{total} Passed ({pass_rate:.1f}%) | Operator Acc: {op_acc:.1f}% | Sum Match Rate: {sum_rate:.1f}% | Mean Latency: {mean_lat:.1f} ms")

    return {
        "suite": "boolean_and_compound_logic",
        "total_tests": total,
        "passed_tests": passed,
        "pass_rate": round(pass_rate, 2),
        "operator_accuracy": round(op_acc, 2),
        "sum_queries_evaluated": sum_queries_count,
        "sum_matches": sum_matches,
        "sum_match_rate": round(sum_rate, 2),
        "mean_slot_f1": round(mean_slot_f1, 2),
        "disambiguation_evaluated": disambig_total,
        "disambiguation_accuracy": round((disambig_matches / disambig_total) * 100.0, 2) if disambig_total > 0 else 100.0,
        "mean_latency_ms": round(mean_lat, 1),
        "min_latency_ms": round(min(latencies), 1) if latencies else 0.0,
        "max_latency_ms": round(max(latencies), 1) if latencies else 0.0,
        "failures": failed_details
    }


# =============================================================================
# EVALUATION MODULE 4: CONVERSATIONAL MEMORY & DIALOGUE STATE TRACKING ("y también...")
# =============================================================================
def evaluate_conversational_memory(provider: str, episodes: List[Dict[str, Any]], verbose: bool = False) -> Dict[str, Any]:
    print(f"\n--- [Suite 4] Evaluating Conversational Memory & DST ({len(episodes)} episodes) ---")

    total_turns = sum(len(ep["turns"]) for ep in episodes)
    passed_turns = 0
    action_correct = 0
    exact_state_matches = 0
    perfect_episodes = 0
    
    y_tambien_turns = 0
    y_tambien_passed = 0

    latencies = []
    failed_details = []

    country_stats = [0, 0, 0]
    comm_stats = [0, 0, 0]
    fac_stats = [0, 0, 0]

    for ep in episodes:
        ep_id = ep["episode_id"]
        ep_title = ep.get("title", "")
        turns = ep["turns"]

        # Reset dialogue state for each episode
        conversation_history = []
        current_filters = {}
        ep_is_flawless = True

        for t in turns:
            turn_num = t["turn"]
            q = t["query"]
            exp_action = t["expected_action"]
            exp_filters = t.get("expected_filters", {})
            exp_count = t.get("expected_count")

            is_y_tambien = ("y también" in q.lower() or "y tambien" in q.lower() or "y además" in q.lower())
            if is_y_tambien:
                y_tambien_turns += 1

            t0 = time.perf_counter()
            try:
                res = process_chat_message(
                    query=q,
                    provider=provider,
                    conversation_history=conversation_history,
                    current_filters=current_filters
                )
            except Exception as e:
                res = {
                    "dialogue_action": "error",
                    "current_filters": current_filters,
                    "conversation_history": conversation_history,
                    "num_found": -1
                }
            lat_ms = (time.perf_counter() - t0) * 1000.0
            latencies.append(lat_ms)

            pred_action = res.get("dialogue_action", "new_search")
            pred_filters = res.get("current_filters", {})
            pred_count = res.get("num_found", 0)

            # Update conversational state for subsequent turn
            current_filters = pred_filters
            conversation_history = res.get("conversation_history", [])

            # 1. Action accuracy
            action_ok = (pred_action == exp_action)
            if action_ok:
                action_correct += 1
            else:
                ep_is_flawless = False

            # 2. Accumulated state match across slots
            c_p, c_r, c_f1, c_tp, c_fp, c_fn = calculate_set_metrics(exp_filters.get("countries", []), pred_filters.get("countries", []))
            country_stats[0] += c_tp; country_stats[1] += c_fp; country_stats[2] += c_fn
            c_ok = (set(exp_filters.get("countries", [])) == set(pred_filters.get("countries", [])))

            m_p, m_r, m_f1, m_tp, m_fp, m_fn = calculate_set_metrics(exp_filters.get("commodities", []), pred_filters.get("commodities", []))
            comm_stats[0] += m_tp; comm_stats[1] += m_fp; comm_stats[2] += m_fn
            m_ok = (set(exp_filters.get("commodities", [])) == set(pred_filters.get("commodities", [])))

            f_p, f_r, f_f1, f_tp, f_fp, f_fn = calculate_set_metrics(exp_filters.get("storage_facility_types", []), pred_filters.get("storage_facility_types", []))
            fac_stats[0] += f_tp; fac_stats[1] += f_fp; fac_stats[2] += f_fn
            f_ok = (set(exp_filters.get("storage_facility_types", [])) == set(pred_filters.get("storage_facility_types", [])))

            # 3. Count match
            count_ok = True
            if exp_count is not None:
                count_ok = (pred_count == exp_count)

            exact_match = c_ok and m_ok and f_ok
            if exact_match:
                exact_state_matches += 1

            turn_passed = action_ok and exact_match and count_ok
            if turn_passed:
                passed_turns += 1
                if is_y_tambien:
                    y_tambien_passed += 1
                if verbose:
                    print(f"  [PASS] {ep_id} Turn {turn_num}: '{q}' -> act={pred_action}, cnt={pred_count} ({lat_ms:.1f} ms)")
            else:
                ep_is_flawless = False
                reason = f"act={pred_action} (exp {exp_action}), cnt={pred_count} (exp {exp_count}), c_ok={c_ok}, m_ok={m_ok}, f_ok={f_ok}"
                failed_details.append(f"[{ep_id} T{turn_num}] '{q}' -> FAILED: {reason}")
                if verbose:
                    print(f"  [FAIL] {ep_id} T{turn_num}: {reason}")

        if ep_is_flawless:
            perfect_episodes += 1

    action_acc = (action_correct / total_turns) * 100.0 if total_turns > 0 else 0.0
    state_match_rate = (exact_state_matches / total_turns) * 100.0 if total_turns > 0 else 0.0
    turn_pass_rate = (passed_turns / total_turns) * 100.0 if total_turns > 0 else 0.0
    ep_success_rate = (perfect_episodes / len(episodes)) * 100.0 if episodes else 0.0
    y_tambien_rate = (y_tambien_passed / y_tambien_turns) * 100.0 if y_tambien_turns > 0 else 100.0
    mean_lat = sum(latencies) / len(latencies) if latencies else 0.0

    def compute_macro_f1(stats: List[int]) -> float:
        tp, fp, fn = stats
        p = tp / (tp + fp) if (tp + fp) > 0 else 1.0
        r = tp / (tp + fn) if (tp + fn) > 0 else 1.0
        f1 = (2 * p * r) / (p + r) if (p + r) > 0 else 0.0
        return round(f1 * 100.0, 2)

    cf1 = compute_macro_f1(country_stats)
    mf1 = compute_macro_f1(comm_stats)
    ff1 = compute_macro_f1(fac_stats)
    macro_dst_f1 = round((cf1 + mf1 + ff1) / 3.0, 2)

    print(f"  -> Suite 4 Result: {passed_turns}/{total_turns} Turns Passed ({turn_pass_rate:.1f}%) | Action Acc: {action_acc:.1f}% | Exact State Match: {state_match_rate:.1f}% | Episode Success: {ep_success_rate:.1f}% | 'y también' Acc: {y_tambien_rate:.1f}%")

    return {
        "suite": "conversational_memory",
        "total_episodes": len(episodes),
        "total_turns": total_turns,
        "passed_turns": passed_turns,
        "turn_pass_rate": round(turn_pass_rate, 2),
        "action_accuracy": round(action_acc, 2),
        "exact_state_match_rate": round(state_match_rate, 2),
        "episode_success_rate": round(ep_success_rate, 2),
        "y_tambien_turns_evaluated": y_tambien_turns,
        "y_tambien_accuracy": round(y_tambien_rate, 2),
        "country_f1": cf1,
        "commodity_f1": mf1,
        "facility_f1": ff1,
        "macro_dst_f1": macro_dst_f1,
        "mean_latency_ms": round(mean_lat, 1),
        "min_latency_ms": round(min(latencies), 1) if latencies else 0.0,
        "max_latency_ms": round(max(latencies), 1) if latencies else 0.0,
        "failures": failed_details
    }


# =============================================================================
# LATEX TABLE GENERATOR (FOR SOFTWAREX MANUSCRIPT INTEGRATION)
# =============================================================================
def generate_latex_table(results_dict: Dict[str, Any]) -> str:
    prov = results_dict.get("provider", "mock")
    meta = MODEL_METADATA.get(prov, {})
    m_name = meta.get("name", prov.upper())
    s1 = results_dict.get("suite_1_guardrails", {})
    st = results_dict.get("suite_single_turn", {})
    s2 = results_dict.get("suite_2_boolean_sum", {})
    s3 = results_dict.get("suite_3_conversational_memory", {})

    template = r"""% Auto-generated LaTeX summary for SoftwareX evaluation_rredondo
\begin{table}[htbp]
\centering
\small
\caption{Empirical Evaluation of @MODEL_NAME@ on evaluation\_rredondo Test Battery across Guardrails, Single-Turn Slot Filling, Boolean Summation, and Conversational DST.}
\label{tab:evaluation_rredondo_@PROV@}
\begin{tabularx}{\linewidth}{>{\raggedright\arraybackslash}X>{\centering\arraybackslash}p{2.0cm}>{\centering\arraybackslash}p{2.0cm}>{\centering\arraybackslash}p{2.2cm}>{\centering\arraybackslash}p{2.2cm}}
\toprule
\textbf{Benchmark Suite} & \textbf{Test Units} & \textbf{Pass Rate (\%)} & \textbf{Key Metric} & \textbf{Mean Latency} \\
\midrule
1. Out-of-Domain Guardrails & @S1_TOTAL@ queries & @S1_PASS@\% & Rejection: @S1_PASS@\% & @S1_LAT@ ms \\
2. Single-Turn Slot Filling & @ST_TOTAL@ queries & @ST_PASS@\% & Slot F1: @ST_F1@\% & @ST_LAT@ ms \\
3. Boolean Sum (AND/OR) & @S2_TOTAL@ queries & @S2_PASS@\% & Sum Match: @S2_SUM@\% & @S2_LAT@ ms \\
4. Conversational Memory & @S3_TOTAL@ turns & @S3_PASS@\% & 'Y también': @S3_YT@\% & @S3_LAT@ ms \\
\midrule
\textbf{Overall Macro Score} & \textbf{@TOT_UNITS@ units} & \textbf{@OVERALL@\%} & Macro F1: @MACRO_F1@\% & \textbf{@OVERALL_LAT@ ms} \\
\bottomrule
\end{tabularx}
\end{table}
"""
    tex = (template
           .replace("@MODEL_NAME@", str(m_name))
           .replace("@PROV@", str(prov))
           .replace("@S1_TOTAL@", str(s1.get('total_tests', 0)))
           .replace("@S1_PASS@", f"{s1.get('accuracy', 0.0):.1f}")
           .replace("@S1_LAT@", f"{s1.get('mean_latency_ms', 0.0):.1f}")
           .replace("@ST_TOTAL@", str(st.get('total_tests', 0)))
           .replace("@ST_PASS@", f"{st.get('accuracy', 0.0):.1f}")
           .replace("@ST_F1@", f"{st.get('mean_slot_f1', 0.0):.1f}")
           .replace("@ST_LAT@", f"{st.get('mean_latency_ms', 0.0):.1f}")
           .replace("@S2_TOTAL@", str(s2.get('total_tests', 0)))
           .replace("@S2_PASS@", f"{s2.get('pass_rate', 0.0):.1f}")
           .replace("@S2_SUM@", f"{s2.get('sum_match_rate', 0.0):.1f}")
           .replace("@S2_LAT@", f"{s2.get('mean_latency_ms', 0.0):.1f}")
           .replace("@S3_TOTAL@", str(s3.get('total_turns', 0)))
           .replace("@S3_PASS@", f"{s3.get('turn_pass_rate', 0.0):.1f}")
           .replace("@S3_YT@", f"{s3.get('y_tambien_accuracy', 0.0):.1f}")
           .replace("@S3_LAT@", f"{s3.get('mean_latency_ms', 0.0):.1f}")
           .replace("@TOT_UNITS@", str(results_dict.get('total_evaluated_units', 0)))
           .replace("@OVERALL@", f"{results_dict.get('overall_score', 0.0):.1f}")
           .replace("@MACRO_F1@", f"{s3.get('macro_dst_f1', 0.0):.1f}")
           .replace("@OVERALL_LAT@", f"{results_dict.get('mean_overall_latency_ms', 0.0):.1f}")
    )
    return tex


# =============================================================================
# MAIN BENCHMARK ORCHESTRATOR
# =============================================================================
def main():
    parser = argparse.ArgumentParser(description="evaluation_rredondo: SoftwareX Conversational Spatial Search Benchmark Runner")
    parser.add_argument("--provider", "-p", default="mock", choices=list(MODEL_METADATA.keys()),
                        help="Execution model provider (default: mock CPU baseline)")
    parser.add_argument("--suite", "-s", default="all", choices=["all", "guardrails_ood", "single_turn_queries", "boolean_sum", "boolean_and_compound_logic", "conversational_memory"],
                        help="Target test suite to run (default: all)")
    parser.add_argument("--test-file", default=str(DEFAULT_BATTERY_PATH),
                        help="Path to JSON test battery file")
    parser.add_argument("--output-dir", "-o", default=str(DEFAULT_RESULTS_DIR),
                        help="Directory to save JSON, TXT, and LaTeX outputs")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Print verbose turn logs")
    args = parser.parse_args()

    test_file = Path(args.test_file)
    if not test_file.exists():
        sys.stderr.write(f"[ERROR] Test battery not found at {test_file}.\n")
        sys.exit(1)

    with open(test_file, "r", encoding="utf-8") as f:
        battery_data = json.load(f)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    provider = args.provider
    meta = MODEL_METADATA[provider]

    print("=" * 80)
    print(f"  SOFTWAREX EVALUATION SUITE: evaluation_rredondo")
    print(f"  Provider:         {provider.upper()} ({meta['name']})")
    print(f"  Parameters:       {meta['params']} | Precision: {meta['precision']}")
    print(f"  Sovereignty:      {meta['sovereignty']}")
    print(f"  Host Machine:     {platform.node()} ({platform.system()} {platform.machine()})")
    print(f"  Test Battery:     {test_file.name}")
    print(f"  Timestamp:        {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # GPU telemetry and weight loading
    vram_used_gb = 0.0
    if provider != "mock":
        print(f"\n[Cluster GPU] Allocating tensor memory and loading weights for '{provider}'...")
        success = load_local_model_weights(provider)
        if not success:
            print(f"[Warning] Failed to allocate GPU weights for '{provider}'. Falling back to CPU heuristic execution.")
        state = get_model_state()
        vram_used_gb = state.get("vram_gb", 0.0)
        print(f"[Cluster GPU] Status: {state.get('status')} | VRAM Allocated: {vram_used_gb} GB")

    # Warm-up turn
    print("[Warm-up] Initializing query pipeline with test prompt...")
    try:
        process_chat_message("Muestra escombreras de litio en España", provider=provider)
    except Exception as e:
        print(f"[Warning] Warm-up encountered: {e}")

    results_payload = {
        "benchmark_suite": "evaluation_rredondo",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "host": platform.node(),
        "provider": provider,
        "model_metadata": meta,
        "vram_allocated_gb": vram_used_gb,
        "suites_run": []
    }

    all_latencies = []
    total_units = 0
    passed_units = 0

    # 1. Guardrails OOD Suite
    if args.suite in ["all", "guardrails_ood"]:
        res_ood = evaluate_guardrails(provider, battery_data.get("guardrails_ood", []), verbose=args.verbose)
        results_payload["suite_1_guardrails"] = res_ood
        results_payload["suites_run"].append("guardrails_ood")
        total_units += res_ood["total_tests"]
        passed_units += res_ood["passed_tests"]
        all_latencies.append(res_ood["mean_latency_ms"])

    # 2. Single-Turn Queries Suite (v2.3.0)
    if args.suite in ["all", "single_turn_queries"]:
        res_st = evaluate_single_turn(provider, battery_data.get("single_turn_queries", []), verbose=args.verbose)
        results_payload["suite_single_turn"] = res_st
        results_payload["suites_run"].append("single_turn_queries")
        total_units += res_st["total_tests"]
        passed_units += res_st["passed_tests"]
        all_latencies.append(res_st["mean_latency_ms"])

    # 3. Boolean Aggregation & Sum Suite (Dual key support for v1.0 and v2.3)
    if args.suite in ["all", "boolean_sum", "boolean_and_compound_logic"]:
        bool_cases = battery_data.get("boolean_and_compound_logic") or battery_data.get("boolean_sum_and_or", [])
        res_bool = evaluate_boolean_sum(provider, bool_cases, verbose=args.verbose)
        results_payload["suite_2_boolean_sum"] = res_bool
        results_payload["suites_run"].append("boolean_and_compound_logic")
        total_units += res_bool["total_tests"]
        passed_units += res_bool["passed_tests"]
        all_latencies.append(res_bool["mean_latency_ms"])

    # 4. Conversational Memory & DST Suite
    if args.suite in ["all", "conversational_memory"]:
        res_dst = evaluate_conversational_memory(provider, battery_data.get("conversational_memory", []), verbose=args.verbose)
        results_payload["suite_3_conversational_memory"] = res_dst
        results_payload["suites_run"].append("conversational_memory")
        total_units += res_dst["total_turns"]
        passed_units += res_dst["passed_turns"]
        all_latencies.append(res_dst["mean_latency_ms"])

    # Overall consolidated statistics
    overall_score = (passed_units / total_units) * 100.0 if total_units > 0 else 0.0
    mean_overall_lat = sum(all_latencies) / len(all_latencies) if all_latencies else 0.0

    results_payload["total_evaluated_units"] = total_units
    results_payload["passed_units"] = passed_units
    results_payload["overall_score"] = round(overall_score, 2)
    results_payload["mean_overall_latency_ms"] = round(mean_overall_lat, 1)

    # Save JSON results
    json_path = out_dir / f"results_rredondo_{provider}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results_payload, f, indent=2, ensure_ascii=False)

    # Save LaTeX table
    tex_path = out_dir / f"table_rredondo_{provider}.tex"
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(generate_latex_table(results_payload))

    # Print human-readable summary
    summary_path = out_dir / f"summary_rredondo_{provider}.txt"
    summary_lines = [
        "=" * 80,
        f"  EVALUATION_RREDONDO BENCHMARK SUMMARY REPORT",
        "=" * 80,
        f"  Model Provider:        {provider.upper()} ({meta['name']})",
        f"  Architecture/Params:   {meta['params']} ({meta['precision']})",
        f"  Execution Node:        {platform.node()}",
        f"  VRAM Memory Footprint: {vram_used_gb} GB",
        f"  Timestamp:             {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "-" * 80,
        f"  1. Out-of-Domain Guardrails & Anti-Hallucination:",
        f"     • Queries Evaluated:    {results_payload.get('suite_1_guardrails', {}).get('total_tests', 'N/A')}",
        f"     • Rejection Accuracy:   {results_payload.get('suite_1_guardrails', {}).get('accuracy', 'N/A')}%",
        f"     • Hallucination Rate:   {results_payload.get('suite_1_guardrails', {}).get('hallucination_rate', 'N/A')}% (0.0% is optimal)",
        f"     • Mean Latency:         {results_payload.get('suite_1_guardrails', {}).get('mean_latency_ms', 'N/A')} ms",
        "-" * 80,
        f"  2. Single-Turn Queries & Slot Filling:",
        f"     • Queries Evaluated:    {results_payload.get('suite_single_turn', {}).get('total_tests', 'N/A')}",
        f"     • Accuracy Rate:        {results_payload.get('suite_single_turn', {}).get('accuracy', 'N/A')}%",
        f"     • Mean Slot F1:         {results_payload.get('suite_single_turn', {}).get('mean_slot_f1', 'N/A')}%",
        f"     • Mean Latency:         {results_payload.get('suite_single_turn', {}).get('mean_latency_ms', 'N/A')} ms",
        "-" * 80,
        f"  3. Boolean Aggregation & Sum of Escombreras:",
        f"     • Queries Evaluated:    {results_payload.get('suite_2_boolean_sum', {}).get('total_tests', 'N/A')}",
        f"     • Pass Rate:            {results_payload.get('suite_2_boolean_sum', {}).get('pass_rate', 'N/A')}%",
        f"     • Operator Accuracy:    {results_payload.get('suite_2_boolean_sum', {}).get('operator_accuracy', 'N/A')}% (AND/OR/COMPOUND)",
        f"     • Sum Match Rate:       {results_payload.get('suite_2_boolean_sum', {}).get('sum_match_rate', 'N/A')}% (Disjunctive site count match)",
        f"     • Mean Slot F1:         {results_payload.get('suite_2_boolean_sum', {}).get('mean_slot_f1', 'N/A')}%",
        f"     • Mean Latency:         {results_payload.get('suite_2_boolean_sum', {}).get('mean_latency_ms', 'N/A')} ms",
        "-" * 80,
        f"  4. Conversational Memory & Dialogue State Tracking (DST):",
        f"     • Episodes / Turns:     {results_payload.get('suite_3_conversational_memory', {}).get('total_episodes', 'N/A')} episodes / {results_payload.get('suite_3_conversational_memory', {}).get('total_turns', 'N/A')} turns",
        f"     • Turn Pass Rate:       {results_payload.get('suite_3_conversational_memory', {}).get('turn_pass_rate', 'N/A')}%",
        f"     • Action Accuracy:      {results_payload.get('suite_3_conversational_memory', {}).get('action_accuracy', 'N/A')}%",
        f"     • Exact State Match:    {results_payload.get('suite_3_conversational_memory', {}).get('exact_state_match_rate', 'N/A')}%",
        f"     • Episode Success Rate: {results_payload.get('suite_3_conversational_memory', {}).get('episode_success_rate', 'N/A')}% (100% flawless dialogue)",
        f"     • 'y también' Acc:      {results_payload.get('suite_3_conversational_memory', {}).get('y_tambien_accuracy', 'N/A')}%",
        f"     • Macro DST F1:         {results_payload.get('suite_3_conversational_memory', {}).get('macro_dst_f1', 'N/A')}%",
        f"     • Mean Latency:         {results_payload.get('suite_3_conversational_memory', {}).get('mean_latency_ms', 'N/A')} ms",
        "=" * 80,
        f"  OVERALL BENCHMARK SCORE:   {passed_units}/{total_units} ({overall_score:.1f}%)",
        f"  CONSOLIDATED MEAN LATENCY: {mean_overall_lat:.1f} ms",
        "=" * 80,
        f"  Artifacts Saved:",
        f"   - JSON Results: {json_path}",
        f"   - LaTeX Table:  {tex_path}",
        f"   - Text Summary: {summary_path}",
        "=" * 80
    ]
    summary_text = "\n".join(summary_lines)
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(summary_text + "\n")

    print("\n" + summary_text)

    # Free GPU VRAM on exit if model was loaded
    if provider != "mock":
        print("\n[Cluster GPU] Reclaiming VRAM allocations...")
        unload_all_local_models()

    sys.exit(0 if overall_score >= 90.0 else 1)


if __name__ == "__main__":
    main()
