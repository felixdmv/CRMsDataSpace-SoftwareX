"""
Evaluation Script for SoftwareX 100-Test Case Benchmark:
Evaluates NLU Intent Classification, Country Extraction, Commodity Extraction,
Facility Type Extraction, and Status Extraction F1-Scores.
"""

import sys
import json
from pathlib import Path

# Add code/ to sys.path
CODE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE_DIR))

from agent import process_chat_message

BENCHMARK_FILE = Path(__file__).resolve().parent / "test_battery_100.json"

def calculate_metrics(gold_list, pred_list):
    gold_set = set(gold_list)
    pred_set = set(pred_list)
    
    tp = len(gold_set.intersection(pred_set))
    fp = len(pred_set - gold_set)
    fn = len(gold_set - pred_set)
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    return precision, recall, f1, tp, fp, fn

def run_evaluation(provider="mock"):
    with open(BENCHMARK_FILE, "r", encoding="utf-8") as f:
        test_cases = json.load(f)
        
    print(f"Starting evaluation over {len(test_cases)} test cases using provider='{provider}'...\n")
    
    intent_correct = 0
    country_stats = [0, 0, 0] # TP, FP, FN
    comm_stats = [0, 0, 0]
    fac_stats = [0, 0, 0]
    status_stats = [0, 0, 0]
    
    results_detail = []

    for tc in test_cases:
        q = tc["query"]
        expected_intent = tc["expected_intent"]
        expected_filters = tc.get("expected_filters", {})
        
        # Run agent NLU pipeline
        res = process_chat_message(q, provider=provider)
        nlu = res["extracted_json"]
        
        pred_intent = nlu.get("intent", "filter_search")
        pred_filters = nlu.get("filters", {})
        
        if pred_intent == expected_intent:
            intent_correct += 1
            
        # Country metrics
        p, r, f1, tp, fp, fn = calculate_metrics(expected_filters.get("countries", []), pred_filters.get("countries", []))
        country_stats[0] += tp; country_stats[1] += fp; country_stats[2] += fn
        
        # Commodity metrics
        p, r, f1, tp, fp, fn = calculate_metrics(expected_filters.get("commodities", []), pred_filters.get("commodities", []))
        comm_stats[0] += tp; comm_stats[1] += fp; comm_stats[2] += fn
        
        # Facility metrics
        p, r, f1, tp, fp, fn = calculate_metrics(expected_filters.get("storage_facility_types", []), pred_filters.get("storage_facility_types", []))
        fac_stats[0] += tp; fac_stats[1] += fp; fac_stats[2] += fn
        
        # Status metrics
        p, r, f1, tp, fp, fn = calculate_metrics(expected_filters.get("project_status", []), pred_filters.get("project_status", []))
        status_stats[0] += tp; status_stats[1] += fp; status_stats[2] += fn

    total = len(test_cases)
    intent_acc = (intent_correct / total) * 100.0

    def compute_macro(stats):
        tp, fp, fn = stats
        p = tp / (tp + fp) if (tp + fp) > 0 else 1.0
        r = tp / (tp + fn) if (tp + fn) > 0 else 1.0
        f1 = (2 * p * r) / (p + r) if (p + r) > 0 else 0.0
        return p * 100.0, r * 100.0, f1 * 100.0

    cp, cr, cf1 = compute_macro(country_stats)
    mp, mr, mf1 = compute_macro(comm_stats)
    fp, fr, ff1 = compute_macro(fac_stats)
    sp, sr, sf1 = compute_macro(status_stats)

    report = f"""
========================================================================
  SOFTWAREX BENCHMARK EVALUATION REPORT (100 TEST CASES)
========================================================================
Provider Evaluated: {provider.upper()}
Total Test Queries: {total}

1. INTENT CLASSIFICATION ACCURACY:
   - Intent Accuracy: {intent_acc:.2f}% ({intent_correct}/{total})

2. FIELD EXTRACTION METRICS (PRECISION / RECALL / F1-SCORE):
   - Countries:         Precision: {cp:.2f}% | Recall: {cr:.2f}% | F1-Score: {cf1:.2f}%
   - Commodities (CRMs): Precision: {mp:.2f}% | Recall: {mr:.2f}% | F1-Score: {mf1:.2f}%
   - Facility Types:    Precision: {fp:.2f}% | Recall: {fr:.2f}% | F1-Score: {ff1:.2f}%
   - Project Status:    Precision: {sp:.2f}% | Recall: {sr:.2f}% | F1-Score: {sf1:.2f}%

OVERALL AVERAGE F1-SCORE: {((cf1 + mf1 + ff1 + sf1) / 4):.2f}%
========================================================================
"""
    print(report)
    
    out_summary = Path(__file__).resolve().parent / "benchmark_results_summary.txt"
    with open(out_summary, "w", encoding="utf-8") as f:
        f.write(report)
    return report

if __name__ == "__main__":
    run_evaluation(provider="mock")
