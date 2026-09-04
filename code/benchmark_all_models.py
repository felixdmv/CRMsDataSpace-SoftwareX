#!/usr/bin/env python3
"""
benchmark_all_models.py
Batería de Pruebas Comparativa Multimodelo en Cluster GPU (Slurm / NVIDIA A100).
Compara el rendimiento end-to-end de:
1. Reglas (WARM Baseline)
2. Qwen 2.5 7B Instruct (GPU)
3. Llama 3.2 3B Instruct (GPU)
4. Gemma 2 2B IT (GPU)
5. DeepSeek R1 Distill Qwen 7B (GPU)
6. Phi-3 Mini 4K Instruct (GPU)
7. Gemini 2.0 Flash (API)
8. OpenAI GPT-4o (API)

Genera métricas de:
- Precisión de respuesta NLG (Score %)
- Cobertura de activos/sitios mineros (Accuracy %)
- Cobertura de palabras clave (Accuracy %)
- Ausencia de alucinaciones (Database Grounding %)
- Tiempo de ejecución / Latencia media por consulta (s)
- Tasa de éxito global (Pass Rate %)
- Tabla resumen comparativa en formato Markdown y LaTeX para publicación académica.
"""
from __future__ import annotations

import os
import sys
import time
import json
import argparse
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "common"))

from chat_agent import process_chat_message
from evaluate_nlg_quality import TEST_CASES, evaluate_response

ALL_PROVIDERS = [
    "rules",
    "qwen",
    "llama",
    "gemma",
    "deepseek",
    "phi3",
    "gemini",
    "openai"
]

PROVIDER_LABELS = {
    "rules": "Reglas / WARM (Baseline)",
    "qwen": "Qwen 2.5 7B (Local GPU)",
    "llama": "Llama 3.2 3B (Local GPU)",
    "gemma": "Gemma 2 2B (Local GPU)",
    "deepseek": "DeepSeek R1 7B (Local GPU)",
    "phi3": "Phi-3 Mini (Local GPU)",
    "gemini": "Gemini 2.0 Flash (Cloud API)",
    "openai": "GPT-4o (Cloud API)"
}

def run_benchmark_for_provider(provider: str, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    print(f"\n{'='*75}")
    print(f" EJECUTANDO BATERÍA DE PRUEBAS PARA: {PROVIDER_LABELS.get(provider, provider).upper()}")
    print(f"{'='*75}")
    
    results = []
    total_score = 0.0
    passed_cases = 0
    total_time = 0.0
    site_acc_total = 0.0
    kw_acc_total = 0.0
    hallucination_count = 0
    
    for tc in test_cases:
        tc_id = tc["id"]
        query = tc["query"]
        print(f"  Consulta [{tc_id}]: '{query}'")
        
        t0 = time.time()
        try:
            res = process_chat_message(query, provider=provider)
            elapsed = time.time() - t0
            
            response_text = res.get("response_text", "")
            api_results = res.get("api_results", [])
            
            metrics = evaluate_response(
                response_text,
                api_results,
                tc["expected_sites"],
                tc["expected_keywords"]
            )
            
            tc_score = metrics["score"]
            total_score += tc_score
            total_time += elapsed
            site_acc_total += metrics["site_accuracy"]
            kw_acc_total += metrics["keyword_accuracy"]
            
            if metrics["has_hallucinations"]:
                hallucination_count += 1
                
            if metrics["status"] == "PASS":
                passed_cases += 1
                status_str = "PASS"
            else:
                status_str = "FAIL"
                
            results.append({
                "id": tc_id,
                "query": query,
                "elapsed_seconds": round(elapsed, 3),
                "score": tc_score,
                "status": status_str,
                "site_accuracy": metrics["site_accuracy"],
                "keyword_accuracy": metrics["keyword_accuracy"],
                "has_hallucinations": metrics["has_hallucinations"],
                "matched_sites": metrics["matched_sites"],
                "missing_sites": metrics["missing_sites"],
                "response_text": response_text
            })
            
            print(f"    -> {elapsed:.2f}s | Score: {tc_score*100:.0f}% | Status: [{status_str}]")
            
        except Exception as e:
            elapsed = time.time() - t0
            print(f"    -> ERROR: {e}")
            results.append({
                "id": tc_id,
                "query": query,
                "error": str(e),
                "status": "ERROR",
                "score": 0.0,
                "elapsed_seconds": round(elapsed, 3),
                "site_accuracy": 0.0,
                "keyword_accuracy": 0.0,
                "has_hallucinations": False,
                "matched_sites": [],
                "missing_sites": tc["expected_sites"],
                "response_text": f"Error: {e}"
            })
            
    n = len(test_cases)
    avg_score = round(total_score / n, 4) if n > 0 else 0.0
    avg_time = round(total_time / n, 3) if n > 0 else 0.0
    pass_rate = round(passed_cases / n, 4) if n > 0 else 0.0
    avg_site_acc = round(site_acc_total / n, 4) if n > 0 else 0.0
    avg_kw_acc = round(kw_acc_total / n, 4) if n > 0 else 0.0
    
    return {
        "provider": provider,
        "provider_label": PROVIDER_LABELS.get(provider, provider),
        "total_test_cases": n,
        "passed_cases": passed_cases,
        "pass_rate": pass_rate,
        "average_score": avg_score,
        "average_site_accuracy": avg_site_acc,
        "average_keyword_accuracy": avg_kw_acc,
        "hallucination_rate": round(hallucination_count / n, 4) if n > 0 else 0.0,
        "average_latency_seconds": avg_time,
        "total_time_seconds": round(total_time, 2),
        "detailed_results": results
    }

def print_summary_tables(all_summary: Dict[str, Dict[str, Any]]) -> str:
    lines = []
    lines.append("\n" + "="*110)
    lines.append(" TABLA COMPARATIVA MULTIMODELO - RESULTADOS DEL BENCHMARK EN CLUSTER GPU")
    lines.append("="*110)
    lines.append(f"| {'Modelo / Proveedor':<30} | {'Score (%)':<10} | {'Exito (PASS)':<13} | {'Sitios Acc.':<12} | {'KW Acc.':<10} | {'Alucin. (%)':<12} | {'Latencia (s)':<12} |")
    lines.append(f"|{'-'*32}|{'-'*12}|{'-'*15}|{'-'*14}|{'-'*12}|{'-'*14}|{'-'*14}|")
    
    for prov, data in all_summary.items():
        label = data["provider_label"]
        score_pct = f"{data['average_score']*100:.1f}%"
        pass_pct = f"{data['pass_rate']*100:.1f}% ({data['passed_cases']}/{data['total_test_cases']})"
        site_acc = f"{data['average_site_accuracy']*100:.1f}%"
        kw_acc = f"{data['average_keyword_accuracy']*100:.1f}%"
        halluc_pct = f"{data['hallucination_rate']*100:.1f}%"
        lat = f"{data['average_latency_seconds']:.2f}s"
        
        lines.append(f"| {label:<30} | {score_pct:<10} | {pass_pct:<13} | {site_acc:<12} | {kw_acc:<10} | {halluc_pct:<12} | {lat:<12} |")
        
    lines.append(f"|{'-'*32}|{'-'*12}|{'-'*15}|{'-'*14}|{'-'*12}|{'-'*14}|{'-'*14}|")
    lines.append("="*110)
    
    # LaTeX Table output for paper insertion
    latex_lines = []
    latex_lines.append("\n% --- TABLA LATEX PARA EL ARTÍCULO CIENTÍFICO ---")
    latex_lines.append("\\begin{table}[htbp]")
    latex_lines.append("\\centering")
    latex_lines.append("\\caption{Comparative Performance of Baseline and LLMs for Critical Raw Materials Data Space Queries.}")
    latex_lines.append("\\label{tab:crms_llm_benchmark}")
    latex_lines.append("\\begin{tabular}{lcccccc}")
    latex_lines.append("\\toprule")
    latex_lines.append("\\textbf{Model / Provider} & \\textbf{Score (\\%)} & \\textbf{Pass Rate} & \\textbf{Site Acc.} & \\textbf{KW Acc.} & \\textbf{Halluc. (\\%)} & \\textbf{Avg Latency (s)} \\\\")
    latex_lines.append("\\midrule")
    
    for prov, data in all_summary.items():
        label = data["provider_label"]
        score = f"{data['average_score']*100:.1f}"
        pass_r = f"{data['pass_rate']*100:.1f}\\%"
        site_a = f"{data['average_site_accuracy']*100:.1f}\\%"
        kw_a = f"{data['average_keyword_accuracy']*100:.1f}\\%"
        halluc = f"{data['hallucination_rate']*100:.1f}\\%"
        lat = f"{data['average_latency_seconds']:.2f}"
        latex_lines.append(f"{label} & {score}\\% & {pass_r} & {site_a} & {kw_a} & {halluc} & {lat}s \\\\")
        
    latex_lines.append("\\bottomrule")
    latex_lines.append("\\end{tabular}")
    latex_lines.append("\\end{table}")
    
    full_report = "\n".join(lines) + "\n" + "\n".join(latex_lines)
    return full_report

def main():
    parser = argparse.ArgumentParser(description="Ejecutor del Benchmark Multimodelo en Cluster GPU")
    parser.add_argument(
        "--models",
        nargs="+",
        default=ALL_PROVIDERS,
        choices=ALL_PROVIDERS,
        help="Lista de modelos a evaluar en el benchmark"
    )
    args = parser.parse_args()
    
    out_dir = ROOT / "outputs" / "benchmark_reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = int(time.time())
    report_file = out_dir / f"benchmark_all_models_{timestamp}.json"
    summary_txt_file = out_dir / f"benchmark_summary_{timestamp}.txt"
    
    print("=" * 90)
    print(" BATERÍA DE PRUEBAS COMPLETA MULTIMODELO - CRMs Data Space")
    print(f" Modelos seleccionados: {args.models}")
    print(f" Número de consultas por modelo: {len(TEST_CASES)}")
    print("=" * 90)
    
    all_summary = {}
    
    for prov in args.models:
        summary_data = run_benchmark_for_provider(prov, TEST_CASES)
        all_summary[prov] = summary_data
        
    # Write full JSON benchmark report
    benchmark_payload = {
        "timestamp": timestamp,
        "models_evaluated": args.models,
        "total_test_cases": len(TEST_CASES),
        "summary": all_summary
    }
    
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(benchmark_payload, f, indent=2, ensure_ascii=False)
        
    # Generate human readable report and LaTeX tables
    readable_tables = print_summary_tables(all_summary)
    print(readable_tables)
    
    with open(summary_txt_file, "w", encoding="utf-8") as f:
        f.write(readable_tables)
        
    print(f"\n[OK] Informe JSON guardado en: {report_file}")
    print(f"[OK] Resumen TXT/LaTeX guardado en: {summary_txt_file}")

if __name__ == "__main__":
    main()
