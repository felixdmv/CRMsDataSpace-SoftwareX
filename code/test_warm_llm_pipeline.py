#!/usr/bin/env python3
"""
Smoke test for the WARM/LLM prototype flow:

user question -> filter extraction -> WARM structured query -> answer.
"""
from __future__ import annotations

import json
from pathlib import Path

from chat_agent import process_chat_message
from export_warm_sites import DEFAULT_INPUT, DEFAULT_OUTPUT_DIR, export


QUERIES = [
    "Dime escombreras de carbon en Asturias",
    "Que escombreras tiene HUNOSA?",
    "Busca San Nicolas",
    "Hay escombreras sin restaurar con surgencias de agua?",
    "Dame informacion de Pumardongo",
]


def main() -> None:
    if DEFAULT_INPUT.exists():
        export(DEFAULT_INPUT, DEFAULT_OUTPUT_DIR)

    for query in QUERIES:
        result = process_chat_message(query, provider="rules")
        print("=" * 90)
        print(f"QUERY: {query}")
        print("\nFILTERS")
        print(json.dumps(result["extracted_json"]["filters"], ensure_ascii=False, indent=2))
        print(f"\nRESULTS: {len(result['api_results'])}")
        for site in result["api_results"]:
            print(f"- {site.get('id')} | {site.get('site_name')} | {site.get('municipality')} | {site.get('company')}")
        print("\nANSWER")
        print(result["response_text"])


if __name__ == "__main__":
    main()
