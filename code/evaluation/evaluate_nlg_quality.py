#!/usr/bin/env python3
"""
evaluate_nlg_quality.py
Script para evaluar automáticamente la calidad de las respuestas del LLM/Agente (NLG)
en la Tarea 1. Compara las respuestas generadas con los activos esperados y palabras clave.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import unicodedata
from pathlib import Path
from typing import Any, Dict, List

# Asegurar que podemos importar desde el directorio de código
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from chat_agent import process_chat_message

# Casos de prueba de oro (Gold Test Cases)
TEST_CASES = [
    {
        "id": "TC_001",
        "query": "Dime escombreras de carbón en Asturias",
        "expected_sites": ["Arroyo de la Nicolasa", "Aguilar - Pumardongo", "La Casona"],
        "expected_keywords": ["carbón", "asturias", "hunosa"]
    },
    {
        "id": "TC_002",
        "query": "Qué escombreras tiene HUNOSA?",
        "expected_sites": ["Arroyo de la Nicolasa", "Aguilar - Pumardongo", "La Casona"],
        "expected_keywords": ["hunosa"]
    },
    {
        "id": "TC_003",
        "query": "Busca el proyecto San Nicolás",
        "expected_sites": ["Arroyo de la Nicolasa"],
        "expected_keywords": ["nicolás"]
    },
    {
        "id": "TC_004",
        "query": "Hay escombreras sin restaurar con surgencias de agua?",
        "expected_sites": ["Arroyo de la Nicolasa", "Aguilar - Pumardongo", "La Casona"],
        "expected_keywords": ["agua", "surgencia", "restaurar"]
    },
    {
        "id": "TC_005",
        "query": "Dime escombreras de cobre en Andalucía",
        "expected_sites": ["Riotinto Project"],
        "expected_keywords": ["cobre", "andalucía", "atalaya"]
    },
    {
        "id": "TC_006",
        "query": "Busca escombreras de wolframio en Castilla y León",
        "expected_sites": ["Los Santos"],
        "expected_keywords": ["wolframio", "tungsteno", "salamanca"]
    },
    {
        "id": "TC_007",
        "query": "Hay proyectos de litio en Extremadura?",
        "expected_sites": ["San José Valdeflórez"],
        "expected_keywords": ["litio", "cáceres"]
    }
]


def clean_text(text: str) -> str:
    """Normaliza texto eliminando acentos y convirtiendo a minúsculas."""
    if not text:
        return ""
    t = text.lower().strip()
    return "".join(
        c for c in unicodedata.normalize("NFD", t)
        if unicodedata.category(c) != "Mn"
    )


def evaluate_response(
    response_text: str,
    api_results: List[Dict[str, Any]],
    expected_sites: List[str],
    expected_keywords: List[str]
) -> Dict[str, Any]:
    """Calcula métricas de precisión y cobertura para una respuesta individual."""
    norm_response = clean_text(response_text)
    
    # 1. Evaluar aciertos de activos/sitios (Mención de escombreras esperadas)
    matched_sites = []
    missing_sites = []
    for site in expected_sites:
        if clean_text(site) in norm_response:
            matched_sites.append(site)
        else:
            # Comprobar si algún alias del sitio fue mencionado
            # Buscamos en la base de datos de resultados el alias correspondiente
            found_alias = False
            for res in api_results:
                if clean_text(res.get("site_name", "")) == clean_text(site):
                    for alias in res.get("aliases", []):
                        if clean_text(alias) in norm_response:
                            matched_sites.append(f"{site} (vía alias '{alias}')")
                            found_alias = True
                            break
                if found_alias:
                    break
            if not found_alias:
                missing_sites.append(site)
                
    site_accuracy = len(matched_sites) / len(expected_sites) if expected_sites else 1.0
    
    # 2. Evaluar presencia de palabras clave (Keywords)
    matched_keywords = []
    missing_keywords = []
    for kw in expected_keywords:
        if clean_text(kw) in norm_response:
            matched_keywords.append(kw)
        else:
            missing_keywords.append(kw)
            
    kw_accuracy = len(matched_keywords) / len(expected_keywords) if expected_keywords else 1.0
    
    # 3. Métrica general (F-Score simplificado de calidad de respuesta)
    overall_score = (site_accuracy * 0.6) + (kw_accuracy * 0.4)
    
    # 4. Alucinación de base de datos
    # Comprobamos si el LLM menciona sitios de la base de datos que NO estaban en los resultados de la API
    mentioned_hallucinated_sites = []
    # Cargamos la base completa para comparar nombres
    from mock_api import load_database
    all_known_sites = load_database()
    result_ids = {s.get("id") for s in api_results}
    
    for site in all_known_sites:
        if site.get("id") not in result_ids:
            name = site.get("site_name", "")
            if name and clean_text(name) in norm_response:
                # El LLM menciona un sitio que no devolvió la base de datos para esta consulta
                mentioned_hallucinated_sites.append(name)
                
    has_hallucinations = len(mentioned_hallucinated_sites) > 0

    return {
        "site_accuracy": site_accuracy,
        "matched_sites": matched_sites,
        "missing_sites": missing_sites,
        "keyword_accuracy": kw_accuracy,
        "matched_keywords": matched_keywords,
        "missing_keywords": missing_keywords,
        "hallucinated_sites": mentioned_hallucinated_sites,
        "has_hallucinations": has_hallucinations,
        "score": round(overall_score, 2),
        "status": "PASS" if overall_score >= 0.8 and not has_hallucinations else "FAIL"
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluacion automatica de calidad de respuesta (NLG)")
    parser.add_argument(
        "--provider",
        type=str,
        default="rules",
        choices=["rules", "local", "openai", "gemini"],
        help="Proveedor del LLM para ejecutar las consultas"
    )
    args = parser.parse_args()
    
    output_dir = ROOT / "outputs" / "nlg_evaluation"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"metrics_{args.provider}_{int(time.time())}.json"
    
    print("=" * 80)
    print(f" INICIANDO EVALUACION AUTOMATICA DE CALIDAD DE RESPUESTA (NLG)")
    print(f" Proveedor: {args.provider.upper()}")
    print(f" Casos de prueba: {len(TEST_CASES)}")
    print("=" * 80)
    
    evaluation_results = []
    total_score = 0.0
    passed_cases = 0
    total_time = 0.0
    
    for tc in TEST_CASES:
        print(f"\n[{tc['id']}] Consulta: '{tc['query']}'")
        t0 = time.time()
        
        try:
            # Ejecutar el pipeline completo del agente
            result = process_chat_message(tc["query"], provider=args.provider)
            elapsed = time.time() - t0
            total_time += elapsed
            
            response_text = result.get("response_text", "")
            api_results = result.get("api_results", [])
            
            # Evaluar calidad de la respuesta redactada
            metrics = evaluate_response(
                response_text,
                api_results,
                tc["expected_sites"],
                tc["expected_keywords"]
            )
            
            tc_score = metrics["score"]
            total_score += tc_score
            if metrics["status"] == "PASS":
                passed_cases += 1
                status_str = "[PASS]"
            else:
                status_str = "[FAIL]"
                
            print(f"  Tiempo: {elapsed:.2f}s | Score: {tc_score * 100:.0f}% | Estado: {status_str}")
            print(f"  Sitios encontrados: {metrics['matched_sites']}")
            if metrics["missing_sites"]:
                print(f"  [AVISO] Sitios faltantes: {metrics['missing_sites']}")
            if metrics["hallucinated_sites"]:
                print(f"  [ALUCINACION] (sitios no devueltos por la DB pero mencionados): {metrics['hallucinated_sites']}")
                
            evaluation_results.append({
                "id": tc["id"],
                "query": tc["query"],
                "response_text": response_text,
                "api_results_count": len(api_results),
                "evaluation": metrics,
                "elapsed_seconds": round(elapsed, 2)
            })
            
        except Exception as e:
            print(f"  [ERROR] al ejecutar el caso de prueba: {e}")
            evaluation_results.append({
                "id": tc["id"],
                "query": tc["query"],
                "error": str(e),
                "status": "ERROR"
            })
            
    # Estadisticas globales
    avg_score = total_score / len(TEST_CASES) if TEST_CASES else 0.0
    success_rate = passed_cases / len(TEST_CASES) if TEST_CASES else 0.0
    
    summary_report = {
        "provider": args.provider,
        "timestamp": time.time(),
        "total_test_cases": len(TEST_CASES),
        "passed_test_cases": passed_cases,
        "success_rate": round(success_rate, 4),
        "average_score": round(avg_score, 4),
        "average_time_seconds": round(total_time / len(TEST_CASES), 2) if TEST_CASES else 0.0,
        "results": evaluation_results
    }
    
    # Escribir fichero de metricas profesional
    with open(output_file, "w", encoding="utf-8") as handle:
        json.dump(summary_report, handle, indent=2, ensure_ascii=False)
        
    print("\n" + "=" * 80)
    print(" INFORME GLOBAL DE METRICAS NLG")
    print("=" * 80)
    print(f" Fichero guardado en: {output_file.name}")
    print(f" Tasa de exito (PASS): {success_rate * 100:.1f}% ({passed_cases}/{len(TEST_CASES)})")
    print(f" Puntuacion media de calidad: {avg_score * 100:.1f}%")
    print(f" Tiempo medio por consulta: {summary_report['average_time_seconds']:.2f}s")
    print("=" * 80)


if __name__ == "__main__":
    main()
