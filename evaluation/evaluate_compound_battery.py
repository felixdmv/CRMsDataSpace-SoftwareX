#!/usr/bin/env python3
"""
SoftwareX Evaluation Suite:
Extensive Benchmark Battery for Conjunctions (AND), Disjunctions (OR),
Complex Compound Boolean Queries, and Zero-Result Disambiguation Fallbacks.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List

# Ensure code/ is in python path
ROOT_DIR = Path(__file__).resolve().parents[2]
CODE_DIR = ROOT_DIR / "code"
TEMPLATE_DIR = ROOT_DIR / "template"

sys.path.insert(0, str(CODE_DIR))
sys.path.insert(0, str(TEMPLATE_DIR))

from agent import process_chat_message
import run_template

BENCHMARK_FILE = Path(__file__).resolve().parent / "test_battery_compound_conjunction_disjunction.json"


def evaluate_compound_battery(provider="mock") -> Dict[str, Any]:
    with open(BENCHMARK_FILE, "r", encoding="utf-8") as f:
        tests = json.load(f)

    print("=" * 80)
    print(f"  CRMsDataSpace & GIS Template: Compound Boolean & Operator Evaluation")
    print(f"  Benchmark File: {BENCHMARK_FILE.name} ({len(tests)} test cases)")
    print(f"  Execution Provider: {provider.upper()}")
    print("=" * 80)

    category_stats = {
        "pure_conjunction": {"total": 0, "operator_match": 0, "slots_f1": []},
        "pure_disjunction": {"total": 0, "operator_match": 0, "slots_f1": []},
        "complex_compound": {"total": 0, "operator_match": 0, "slots_f1": []},
        "zero_result_disambiguation": {"total": 0, "disambig_matched": 0, "zero_results_detected": 0},
        "conversational_disambiguation_followup": {"total": 0, "resolved": 0},
        "template_compound_preset": {"total": 0, "passed": 0}
    }

    passed_count = 0
    failed_details = []

    for tc in tests:
        tc_id = tc["id"]
        cat = tc["category"]
        query = tc["query"]
        expected_op = tc.get("expected_operator")
        expected_and = set(tc.get("expected_commodities_and", []))
        expected_or = set(tc.get("expected_commodities_or", []))
        expected_disambig = tc.get("expected_disambiguation", False)

        category_stats[cat]["total"] += 1

        # Handle Template Preset Tests
        if cat == "template_compound_preset":
            preset_name = tc.get("preset", "energy")
            cfg = run_template.PRESETS[preset_name]
            field_name = "energy_type" if preset_name == "energy" else "facility_type"
            parsed = run_template.parse_conversational_query(query, cfg)
            f_state = parsed.get("filters", {}).get(field_name, {})

            if expected_op == "AND":
                is_correct = len(f_state.get("and", [])) >= 2
            else:
                is_correct = len(f_state.get("or", [])) >= 2

            if is_correct:
                category_stats[cat]["passed"] += 1
                passed_count += 1
            else:
                failed_details.append(f"[{tc_id}] Template '{preset_name}' parse failed for query: '{query}'")
            continue

        # Handle Conversational Follow-Up Tests
        if cat == "conversational_disambiguation_followup":
            prior_q = tc.get("prior_query", "escombreras en españa con litio y estaño")
            # First turn: trigger 0-result ambiguity
            res_t1 = process_chat_message(prior_q, provider=provider)
            history = [
                {"role": "user", "content": prior_q},
                {"role": "assistant", "content": res_t1.get("response_text", ""), "active_filters": res_t1.get("filters", {})}
            ]
            # Second turn: user resolves ambiguity
            res_t2 = process_chat_message(query, provider=provider, conversation_history=history, current_filters=res_t1.get("filters", {}))
            nlu_t2 = res_t2.get("extracted_json", {})
            pred_op = nlu_t2.get("filters", {}).get("commodity_operator", "OR")

            if pred_op == expected_op:
                category_stats[cat]["resolved"] += 1
                passed_count += 1
            else:
                failed_details.append(f"[{tc_id}] Follow-up failed: query='{query}', expected={expected_op}, got={pred_op}")
            continue

        # Standard CRMs Chat Query
        res = process_chat_message(query, provider=provider)
        nlu = res.get("extracted_json", {})
        filters = nlu.get("filters", {})
        pred_op = filters.get("commodity_operator", "OR")
        pred_and = set(filters.get("commodities_and", []))
        pred_or = set(filters.get("commodities_or", []))
        disambig_triggered = bool(res.get("disambiguation_options"))
        matched_sites_count = len(res.get("docs", []))

        # Check Category Metrics
        if cat in ["pure_conjunction", "pure_disjunction", "complex_compound"]:
            op_match = (pred_op == expected_op)
            if op_match:
                category_stats[cat]["operator_match"] += 1

            # Slots F1 for AND & OR sets
            all_expected = expected_and | expected_or
            all_pred = pred_and | pred_or
            tp = len(all_expected & all_pred)
            fp = len(all_pred - all_expected)
            fn = len(all_expected - all_pred)
            prec = tp / (tp + fp) if (tp + fp) > 0 else 1.0
            rec = tp / (tp + fn) if (tp + fn) > 0 else 1.0
            f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
            category_stats[cat]["slots_f1"].append(f1)

            if op_match and f1 >= 0.8:
                passed_count += 1
            else:
                failed_details.append(f"[{tc_id}] Op/Slot mismatch: query='{query}' -> pred_op={pred_op} (exp {expected_op}), f1={f1:.2f}")

        elif cat == "zero_result_disambiguation":
            if matched_sites_count == 0:
                category_stats[cat]["zero_results_detected"] += 1
            if disambig_triggered == expected_disambig:
                category_stats[cat]["disambig_matched"] += 1
                passed_count += 1
            else:
                failed_details.append(f"[{tc_id}] Disambiguation mismatch: query='{query}', triggered={disambig_triggered}, exp={expected_disambig}")

    total_tests = len(tests)
    pass_rate = (passed_count / total_tests) * 100.0

    print("\nRESULTS BREAKDOWN BY CATEGORY:")
    print("-" * 80)
    for c_name, stats in category_stats.items():
        tot = stats["total"]
        if "operator_match" in stats:
            op_acc = (stats["operator_match"] / tot) * 100.0 if tot > 0 else 0.0
            mean_f1 = (sum(stats["slots_f1"]) / len(stats["slots_f1"])) * 100.0 if stats["slots_f1"] else 0.0
            print(f"  • {c_name.replace('_', ' ').title():<36} | Tests: {tot:>2} | Operator Acc: {op_acc:>5.1f}% | Mean Slots F1: {mean_f1:>5.1f}%")
        elif "disambig_matched" in stats:
            d_acc = (stats["disambig_matched"] / tot) * 100.0 if tot > 0 else 0.0
            print(f"  • {c_name.replace('_', ' ').title():<36} | Tests: {tot:>2} | Disambiguation Trigger Acc: {d_acc:>5.1f}%")
        elif "resolved" in stats:
            r_acc = (stats["resolved"] / tot) * 100.0 if tot > 0 else 0.0
            print(f"  • {c_name.replace('_', ' ').title():<36} | Tests: {tot:>2} | Disambiguation Resolution: {r_acc:>5.1f}%")
        elif "passed" in stats:
            p_acc = (stats["passed"] / tot) * 100.0 if tot > 0 else 0.0
            print(f"  • {c_name.replace('_', ' ').title():<36} | Tests: {tot:>2} | Preset Compound Parse Acc: {p_acc:>5.1f}%")

    print("=" * 80)
    print(f"OVERALL BENCHMARK PASS RATE: {passed_count}/{total_tests} ({pass_rate:.1f}%)")
    print("=" * 80)

    if failed_details:
        print(f"\nFailed Test Details ({len(failed_details)}):")
        for fail in failed_details:
            print(f"  - {fail}")

    return {
        "total": total_tests,
        "passed": passed_count,
        "pass_rate": pass_rate,
        "category_stats": category_stats
    }


if __name__ == "__main__":
    report = evaluate_compound_battery()
    sys.exit(0 if report["pass_rate"] >= 95.0 else 1)
