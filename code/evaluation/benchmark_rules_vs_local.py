#!/usr/bin/env python3
"""
benchmark_rules_vs_local.py
Script comparativo de rendimiento: Reglas (WARM) vs. LLM Local (Phi-3).
Ejecuta las mismas preguntas sobre ambos enfoques midiendo tiempos y calidad de respuestas.
"""
from __future__ import annotations

import os
import sys
import time
import json
from pathlib import Path
from typing import Any, Dict, List

# Asegurar importes desde el directorio de código
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from chat_agent import process_chat_message
from evaluate_nlg_quality import TEST_CASES, evaluate_response

def main() -> None:
    print("=" * 80)
    print(" BENCHMARK COMPARATIVO: REGLAS (WARM) VS. LLM LOCAL (PHI-3)")
    print("=" * 80)
    print(f"Número de preguntas a evaluar: {len(TEST_CASES)}")
    print("NOTA: Si es la primera vez que usas el proveedor 'local', Hugging Face")
    print("descargará el modelo Phi-3-mini (~7.6 GB). Esto tardará unos minutos.")
    print("=" * 80)
    
    # Confirmación de ejecución del modo local
    input("\nPresiona ENTER para comenzar el benchmark...")
    
    results = {
        "rules": [],
        "local": []
    }
    
    summary = {
        "rules": {"passed": 0, "total_time": 0.0, "total_score": 0.0},
        "local": {"passed": 0, "total_time": 0.0, "total_score": 0.0}
    }
    
    providers = ["rules", "local"]
    
    for provider in providers:
        print(f"\n>>> Evaluando paradigma: {provider.upper()}...")
        
        # Si es local, avisar de la carga inicial
        if provider == "local":
            print("Cargando modelo local en memoria (puede demorar al inicio)...")
            
        for tc in TEST_CASES:
            print(f"  Procesando consulta [{tc['id']}]: '{tc['query']}'")
            t0 = time.time()
            try:
                # Ejecutar consulta
                res = process_chat_message(tc["query"], provider=provider)
                elapsed = time.time() - t0
                
                response_text = res.get("response_text", "")
                api_results = res.get("api_results", [])
                
                # Evaluar calidad de la respuesta redactada
                metrics = evaluate_response(
                    response_text,
                    api_results,
                    tc["expected_sites"],
                    tc["expected_keywords"]
                )
                
                metrics_score = metrics["score"]
                summary[provider]["total_time"] += elapsed
                summary[provider]["total_score"] += metrics_score
                if metrics["status"] == "PASS":
                    summary[provider]["passed"] += 1
                    
                results[provider].append({
                    "id": tc["id"],
                    "query": tc["query"],
                    "elapsed_seconds": round(elapsed, 3),
                    "score": metrics_score,
                    "status": metrics["status"],
                    "response_text": response_text
                })
                print(f"    -> Completado en {elapsed:.3f}s | Score: {metrics_score*100:.0f}% | {metrics['status']}")
                
            except Exception as e:
                print(f"    -> ERROR: {e}")
                results[provider].append({
                    "id": tc["id"],
                    "query": tc["query"],
                    "error": str(e),
                    "status": "ERROR",
                    "score": 0.0,
                    "elapsed_seconds": 0.0
                })
                
    # Calcular promedios
    n_cases = len(TEST_CASES)
    for prov in providers:
        summary[prov]["avg_time"] = round(summary[prov]["total_time"] / n_cases, 3) if n_cases else 0.0
        summary[prov]["avg_score"] = round(summary[prov]["total_score"] / n_cases, 4) if n_cases else 0.0
        summary[prov]["success_rate"] = round(summary[prov]["passed"] / n_cases, 4) if n_cases else 0.0

    # Guardar reporte detallado en archivo
    out_dir = ROOT / "outputs" / "nlg_evaluation"
    out_dir.mkdir(parents=True, exist_ok=True)
    report_file = out_dir / f"comparison_benchmark_{int(time.time())}.json"
    
    report_data = {
        "timestamp": time.time(),
        "summary": summary,
        "detailed_results": results
    }
    
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)

    # Imprimir Tabla Comparativa
    print("\n" + "=" * 90)
    print(" INFORME COMPARATIVO DE RENDIMIENTO")
    print("=" * 90)
    print(f"| {'Consulta (ID)':<15} | {'Rules Time (s)':<16} | {'Local Time (s)':<16} | {'Rules Score':<12} | {'Local Score':<12} |")
    print(f"|{'-'*17}|{'-'*18}|{'-'*18}|{'-'*14}|{'-'*14}|")
    
    for i in range(n_cases):
        r_res = results["rules"][i]
        l_res = results["local"][i]
        q_id = r_res["id"]
        
        r_time = f"{r_res['elapsed_seconds']:.3f}s"
        l_time = f"{l_res['elapsed_seconds']:.3f}s" if l_res['status'] != "ERROR" else "ERROR"
        r_score = f"{r_res['score']*100:.0f}%"
        l_score = f"{l_res['score']*100:.0f}%" if l_res['status'] != "ERROR" else "0%"
        
        print(f"| {q_id:<15} | {r_time:<16} | {l_time:<16} | {r_score:<12} | {l_score:<12} |")
        
    print(f"|{'-'*17}|{'-'*18}|{'-'*18}|{'-'*14}|{'-'*14}|")
    print(f"| {'PROMEDIOS/TOTAL':<15} | {summary['rules']['avg_time']:<15}s | {summary['local']['avg_time']:<15}s | {summary['rules']['avg_score']*100:.1f}% | {summary['local']['avg_score']*100:.1f}% |")
    print(f"| {'Tasa Éxito (PASS)':<15} | {summary['rules']['success_rate']*100:.1f}% ({summary['rules']['passed']}/{n_cases}) | {summary['local']['success_rate']*100:.1f}% ({summary['local']['passed']}/{n_cases}) |")
    print("=" * 90)
    print(f"Informe detallado guardado en: {report_file.name}")
    print("=" * 90)

if __name__ == "__main__":
    main()
