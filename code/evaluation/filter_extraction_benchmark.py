#!/usr/bin/env python3
"""
Benchmark structured filter extraction across OpenAI, Gemini, Anthropic, and xAI.

The script reads free-text queries from a CSV file, asks each selected model to
return a normalized JSON payload, and stores raw + parsed results for later
comparison with expert-provided gold filters.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT = ROOT / "templates" / "filter_queries.csv"
DEFAULT_OUTPUT_DIR = ROOT / "outputs" / "filter_extraction"


MODEL_SOURCES = {
    "openai": {
        "model": "gpt-5.5",
        "source": "https://developers.openai.com/api/docs/models",
        "checked_on": "2026-04-28",
        "note": "OpenAI docs recommend gpt-5.5 as the flagship model for complex reasoning and coding.",
    },
    "gemini": {
        "model": "gemini-2.0-flash",
        "source": "https://ai.google.dev/gemini-api/docs/models",
        "checked_on": "2026-04-28",
        "note": "Google lists Gemini 2.0 Flash (via gemini-2.0-flash) as a flagship, high-quota model.",
    },
    "anthropic": {
        "model": "claude-opus-4-7",
        "source": "https://platform.claude.com/docs/en/about-claude/models/overview",
        "checked_on": "2026-04-28",
        "note": "Anthropic recommends Claude Opus 4.7 for the most complex tasks.",
    },
    "xai": {
        "model": "grok-4.20-reasoning",
        "source": "https://docs.x.ai/overview",
        "checked_on": "2026-04-28",
        "note": "xAI documents Grok 4.20 as the newest flagship model in the API docs.",
    },
}


PROMPT_TEMPLATE = """You are extracting structured search filters for a mining and anthropogenic-resources data space.

Return ONLY valid JSON.
Do not wrap the JSON in markdown.
Do not add explanations outside the JSON.

The user may ask in Spanish or English.
Your job is to classify the request and extract only the filters that are explicit or strongly implied.

Use this schema exactly:
{{
  "intent": "filter_search" | "generic_qa" | "hybrid",
  "answer_mode": "structured_filters" | "rag_answer" | "structured_filters_and_rag",
  "rewritten_query": "short normalized rewrite in the same language as the user",
  "filters": {{
    "countries": ["..."],
    "regions": ["..."],
    "commodities": ["..."],
    "material_types": ["..."],
    "storage_facility_types": ["..."],
    "project_status": ["..."],
    "companies": ["..."],
    "site_names": ["..."],
    "unfc_e": ["..."],
    "unfc_f": ["..."],
    "unfc_g": ["..."],
    "environmental_flags": ["..."],
    "free_text_constraints": ["..."],
    "activity_types": ["..."],
    "mine_types": ["..."],
    "admin_statuses": ["..."],
    "mine_statuses": ["..."],
    "morphologies": ["..."],
    "restored": true | false | null,
    "restoration_types": ["..."],
    "site_contexts": ["..."]
  }},
  "ambiguities": ["..."],
  "needs_report_context": true,
  "needs_database_filtering": true
}}

Normalization rules:
- Countries and regions must be lowercase English canonical names when possible.
- Commodities must use singular English forms when possible, for example: nickel, copper, lithium, cobalt, tungsten, rare earth elements, coal.
- Material types should capture what is being searched for inside the storage body, for example: tailings, slag, waste rock, mine waste, sludge.
- Storage facility types should capture the physical asset, for example: tailings storage facility, waste dump, stockpile, pond.
- UNFC axes must use labels like E1, F2, G3.
- If the user is asking for a document-level question that requires reading a report, set needs_report_context=true.
- If the user is clearly asking to search structured records, set needs_database_filtering=true.
- If a field is absent, return an empty array or null (for restored).

Examples:

Example 1 (Conversational greeting / off-topic):
User: "hola buenas tardes, ¿quién eres y qué puedes hacer?"
JSON:
{{
  "intent": "generic_qa",
  "answer_mode": "rag_answer",
  "rewritten_query": "hola, quien eres y que puedes hacer",
  "filters": {{
    "countries": [],
    "regions": [],
    "commodities": [],
    "material_types": [],
    "storage_facility_types": [],
    "project_status": [],
    "companies": [],
    "site_names": [],
    "unfc_e": [],
    "unfc_f": [],
    "unfc_g": [],
    "environmental_flags": [],
    "free_text_constraints": [],
    "activity_types": [],
    "mine_types": [],
    "admin_statuses": [],
    "mine_statuses": [],
    "morphologies": [],
    "restored": null,
    "restoration_types": [],
    "site_contexts": []
  }},
  "ambiguities": [],
  "needs_report_context": false,
  "needs_database_filtering": false
}}

Example 2 (Complex spatial and multi-mineral search):
User: "Busca balsas de decantación con wolframio y estaño en Galicia cerca de San Finx"
JSON:
{{
  "intent": "filter_search",
  "answer_mode": "structured_filters",
  "rewritten_query": "balsas de decantacion con tungsten y tin en galicia cerca de san finx",
  "filters": {{
    "countries": ["spain"],
    "regions": ["galicia"],
    "commodities": ["tungsten", "tin"],
    "material_types": ["tailings", "sludge"],
    "storage_facility_types": ["pond", "tailings storage facility"],
    "project_status": [],
    "companies": [],
    "site_names": ["San Finx"],
    "unfc_e": [],
    "unfc_f": [],
    "unfc_g": [],
    "environmental_flags": [],
    "free_text_constraints": ["cerca de san finx"],
    "activity_types": [],
    "mine_types": [],
    "admin_statuses": [],
    "mine_statuses": [],
    "morphologies": [],
    "restored": null,
    "restoration_types": [],
    "site_contexts": []
  }},
  "ambiguities": ["'balsas de decantación' maps to pond and tailings storage facility"],
  "needs_report_context": false,
  "needs_database_filtering": true
}}

Example 3 (Company name and active status filter):
User: "Proyectos activos de cobalto o cobre gestionados por Atalaya Mining"
JSON:
{{
  "intent": "filter_search",
  "answer_mode": "structured_filters",
  "rewritten_query": "proyectos activos de cobalt o copper de atalaya mining",
  "filters": {{
    "countries": ["spain"],
    "regions": [],
    "commodities": ["cobalt", "copper"],
    "material_types": [],
    "storage_facility_types": [],
    "project_status": ["active"],
    "companies": ["atalaya mining"],
    "site_names": [],
    "unfc_e": [],
    "unfc_f": [],
    "unfc_g": [],
    "environmental_flags": [],
    "free_text_constraints": [],
    "activity_types": [],
    "mine_types": [],
    "admin_statuses": [],
    "mine_statuses": [],
    "morphologies": [],
    "restored": null,
    "restoration_types": [],
    "site_contexts": []
  }},
  "ambiguities": [],
  "needs_report_context": false,
  "needs_database_filtering": true
}}

Example 4 (Document-level report analysis / Hybrid):
User: "¿Qué dice el informe técnico de Penouta sobre la estabilidad física de la balsa B?"
JSON:
{{
  "intent": "hybrid",
  "answer_mode": "structured_filters_and_rag",
  "rewritten_query": "estabilidad fisica de la balsa b en informe tecnico de penouta",
  "filters": {{
    "countries": ["spain"],
    "regions": ["galicia"],
    "commodities": [],
    "material_types": [],
    "storage_facility_types": ["pond", "tailings storage facility"],
    "project_status": [],
    "companies": [],
    "site_names": ["Mina de Penouta"],
    "unfc_e": [],
    "unfc_f": [],
    "unfc_g": [],
    "environmental_flags": ["stability"],
    "free_text_constraints": ["estabilidad balsa b"],
    "activity_types": [],
    "mine_types": [],
    "admin_statuses": [],
    "mine_statuses": [],
    "morphologies": [],
    "restored": null,
    "restoration_types": [],
    "site_contexts": []
  }},
  "ambiguities": ["stability is mapped to environmental_flags"],
  "needs_report_context": true,
  "needs_database_filtering": true
}}

User query:
{query}
"""


COUNTRY_ALIASES = {
    "espana": "spain",
    "españa": "spain",
    "spain": "spain",
    "portugal": "portugal",
    "france": "france",
    "francia": "france",
    "europa": "europe",
    "europe": "europe",
}

COMMODITY_ALIASES = {
    "hulla": "coal",
    "carbon": "coal",
    "carbón": "coal",
    "coal": "coal",
    "niquel": "nickel",
    "níquel": "nickel",
    "nickel": "nickel",
    "cobre": "copper",
    "copper": "copper",
    "litio": "lithium",
    "lithium": "lithium",
    "cobalto": "cobalt",
    "cobalt": "cobalt",
    "wolframio": "tungsten",
    "tungsteno": "tungsten",
    "tungsten": "tungsten",
    "tierras raras": "rare earth elements",
    "rare earths": "rare earth elements",
    "rare earth elements": "rare earth elements",
}

FACILITY_TYPE_ALIASES = {
    "escombrera": "waste dump",
    "escombreras": "waste dump",
    "escombrera minera": "waste dump",
    "escombrera de mina": "waste dump",
    "dump": "waste dump",
    "spoil heap": "waste dump",
    "waste dump": "waste dump",
    "tailings": "tailings storage facility",
    "tailings storage facility": "tailings storage facility",
    "tsf": "tailings storage facility",
    "balsa": "pond",
    "balsas": "pond",
    "pond": "pond",
    "stockpile": "stockpile",
    "acopio": "stockpile",
}

REGION_ALIASES = {
    "asturias": "asturias",
    "principado de asturias": "asturias",
}


@dataclass(frozen=True)
class Provider:
    name: str
    model: str
    env_var: str


PROVIDERS = {
    "openai": Provider("openai", MODEL_SOURCES["openai"]["model"], "OPENAI_API_KEY"),
    "gemini": Provider("gemini", MODEL_SOURCES["gemini"]["model"], "GEMINI_API_KEY"),
    "anthropic": Provider("anthropic", MODEL_SOURCES["anthropic"]["model"], "ANTHROPIC_API_KEY"),
    "xai": Provider("xai", MODEL_SOURCES["xai"]["model"], "XAI_API_KEY"),
}


def load_dotenv(dotenv_path: Path) -> None:
    if not dotenv_path.exists():
        return
    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]
        if key and key not in os.environ:
            os.environ[key] = value


def split_pipe_values(raw: str) -> list[str]:
    if not raw:
        return []
    return [normalize_scalar(part) for part in raw.split("|") if normalize_scalar(part)]


def normalize_scalar(value: str) -> str:
    text = re.sub(r"\s+", " ", (value or "").strip().lower())
    text = "".join(
        char for char in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(char)
    )
    return text


def normalize_country(value: str) -> str:
    return COUNTRY_ALIASES.get(normalize_scalar(value), normalize_scalar(value))


def normalize_commodity(value: str) -> str:
    return COMMODITY_ALIASES.get(normalize_scalar(value), normalize_scalar(value))


def normalize_facility_type(value: str) -> str:
    return FACILITY_TYPE_ALIASES.get(normalize_scalar(value), normalize_scalar(value))


def normalize_region(value: str) -> str:
    return REGION_ALIASES.get(normalize_scalar(value), normalize_scalar(value))


def normalize_prediction(payload: dict[str, Any]) -> dict[str, Any]:
    filters = payload.setdefault("filters", {})
    fields = {
        "countries": normalize_country,
        "regions": normalize_region,
        "commodities": normalize_commodity,
        "material_types": normalize_scalar,
        "storage_facility_types": normalize_facility_type,
        "project_status": normalize_scalar,
        "companies": normalize_scalar,
        "site_names": normalize_scalar,
        "unfc_e": lambda x: normalize_scalar(x).upper(),
        "unfc_f": lambda x: normalize_scalar(x).upper(),
        "unfc_g": lambda x: normalize_scalar(x).upper(),
        "environmental_flags": normalize_scalar,
        "free_text_constraints": normalize_scalar,
        "activity_types": normalize_scalar,
        "mine_types": normalize_scalar,
        "admin_statuses": normalize_scalar,
        "mine_statuses": normalize_scalar,
        "morphologies": normalize_scalar,
        "restoration_types": normalize_scalar,
        "site_contexts": normalize_scalar,
    }
    for field, fn in fields.items():
        raw_values = filters.get(field, [])
        if not isinstance(raw_values, list):
            raw_values = [raw_values] if raw_values else []
        cleaned = []
        for item in raw_values:
            value = fn(str(item))
            if value and value not in cleaned:
                cleaned.append(value)
        filters[field] = cleaned

    restored_val = filters.get("restored")
    if restored_val is not None:
        if isinstance(restored_val, list):
            if len(restored_val) > 0:
                restored_val = restored_val[0]
            else:
                restored_val = None
        if restored_val is not None:
            if isinstance(restored_val, str):
                restored_val = restored_val.strip().lower() in ("true", "1", "yes")
            else:
                restored_val = bool(restored_val)
        filters["restored"] = restored_val

    payload["intent"] = normalize_scalar(str(payload.get("intent", ""))) or "generic_qa"
    payload["answer_mode"] = normalize_scalar(str(payload.get("answer_mode", ""))) or "rag_answer"
    payload["rewritten_query"] = str(payload.get("rewritten_query", "")).strip()
    payload["ambiguities"] = [str(x).strip() for x in payload.get("ambiguities", []) if str(x).strip()]
    payload["needs_report_context"] = bool(payload.get("needs_report_context", False))
    payload["needs_database_filtering"] = bool(payload.get("needs_database_filtering", False))
    return payload


def extract_json_block(text: str) -> dict[str, Any]:
    raw = (text or "").strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def http_post_json(url: str, headers: dict[str, str], payload: dict[str, Any], timeout: int = 120) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={**headers, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} calling {url}: {detail}") from exc


def call_openai_like(base_url: str, api_key: str, model: str, prompt: str) -> tuple[str, dict[str, Any]]:
    payload = {
        "model": model,
        "input": [
            {"role": "system", "content": "Return only valid JSON."},
            {"role": "user", "content": prompt},
        ],
    }
    response = http_post_json(
        f"{base_url}/responses",
        {"Authorization": f"Bearer {api_key}"},
        payload,
    )
    text = response.get("output_text", "")
    if not text:
        text_fragments = []
        for item in response.get("output", []):
            for content in item.get("content", []):
                if content.get("type") in {"output_text", "text"} and content.get("text"):
                    text_fragments.append(content["text"])
        text = "\n".join(text_fragments).strip()
    return text, response


def call_openai(api_key: str, model: str, prompt: str) -> tuple[str, dict[str, Any]]:
    return call_openai_like("https://api.openai.com/v1", api_key, model, prompt)


def call_xai(api_key: str, model: str, prompt: str) -> tuple[str, dict[str, Any]]:
    return call_openai_like("https://api.x.ai/v1", api_key, model, prompt)


def call_anthropic(api_key: str, model: str, prompt: str) -> tuple[str, dict[str, Any]]:
    payload = {
        "model": model,
        "max_tokens": 1200,
        "messages": [{"role": "user", "content": prompt}],
    }
    response = http_post_json(
        "https://api.anthropic.com/v1/messages",
        {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        payload,
    )
    chunks = []
    for item in response.get("content", []):
        if item.get("type") == "text" and item.get("text"):
            chunks.append(item["text"])
    return "\n".join(chunks).strip(), response


def call_gemini(api_key: str, model: str, prompt: str) -> tuple[str, dict[str, Any]]:
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{urllib.parse.quote(model)}:generateContent?key={urllib.parse.quote(api_key)}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0,
            "maxOutputTokens": 2048
        },
    }
    response = http_post_json(url, {}, payload)
    text_parts = []
    for candidate in response.get("candidates", []):
        content = candidate.get("content", {})
        for part in content.get("parts", []):
            if part.get("text"):
                text_parts.append(part["text"])
    return "\n".join(text_parts).strip(), response


def call_provider(provider: Provider, query: str) -> tuple[dict[str, Any], str, dict[str, Any]]:
    api_key = os.getenv(provider.env_var)
    if not api_key:
        raise RuntimeError(f"Missing environment variable {provider.env_var}")
    prompt = PROMPT_TEMPLATE.format(query=query.strip())
    if provider.name == "openai":
        text, raw = call_openai(api_key, provider.model, prompt)
    elif provider.name == "gemini":
        text, raw = call_gemini(api_key, provider.model, prompt)
    elif provider.name == "anthropic":
        text, raw = call_anthropic(api_key, provider.model, prompt)
    elif provider.name == "xai":
        text, raw = call_xai(api_key, provider.model, prompt)
    else:
        raise ValueError(f"Unsupported provider: {provider.name}")
    parsed = normalize_prediction(extract_json_block(text))
    return parsed, text, raw


def load_queries(path: Path, limit: int | None = None) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    if limit is not None:
        rows = rows[:limit]
    return rows


def build_expected(row: dict[str, str]) -> dict[str, list[str] | str]:
    return {
        "intent": normalize_scalar(row.get("expected_intent", "")),
        "countries": [normalize_country(x) for x in split_pipe_values(row.get("expected_countries", ""))],
        "regions": split_pipe_values(row.get("expected_regions", "")),
        "commodities": [normalize_commodity(x) for x in split_pipe_values(row.get("expected_commodities", ""))],
        "material_types": split_pipe_values(row.get("expected_material_types", "")),
        "storage_facility_types": [normalize_facility_type(x) for x in split_pipe_values(row.get("expected_storage_facility_types", ""))],
        "project_status": split_pipe_values(row.get("expected_project_status", "")),
        "unfc_e": [x.upper() for x in split_pipe_values(row.get("expected_unfc_e", ""))],
        "unfc_f": [x.upper() for x in split_pipe_values(row.get("expected_unfc_f", ""))],
        "unfc_g": [x.upper() for x in split_pipe_values(row.get("expected_unfc_g", ""))],
        "environmental_flags": split_pipe_values(row.get("expected_environmental_flags", "")),
        "free_text_constraints": split_pipe_values(row.get("expected_free_text_constraints", "")),
    }


def evaluate_prediction(expected: dict[str, Any], predicted: dict[str, Any]) -> dict[str, Any]:
    pred_filters = predicted.get("filters", {})
    field_names = [
        "countries",
        "regions",
        "commodities",
        "material_types",
        "storage_facility_types",
        "project_status",
        "unfc_e",
        "unfc_f",
        "unfc_g",
        "environmental_flags",
        "free_text_constraints",
    ]
    scores: dict[str, Any] = {}
    exact_all = True
    for field in field_names:
        exp = sorted(expected.get(field, []))
        pred = sorted(pred_filters.get(field, []))
        exact = exp == pred
        scores[f"{field}_exact"] = exact
        exact_all = exact_all and exact
    intent_exact = expected.get("intent", "") == predicted.get("intent", "")
    scores["intent_exact"] = intent_exact
    scores["overall_exact"] = exact_all and intent_exact
    return scores


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_summary_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    keys = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def run(provider_names: list[str], input_file: Path, output_dir: Path, limit: int | None, sleep_seconds: float) -> Path:
    rows = load_queries(input_file, limit=limit)
    run_dir = output_dir / datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=True)

    meta = {
        "created_at": datetime.now().isoformat(),
        "input_file": str(input_file),
        "providers": {name: MODEL_SOURCES[name] for name in provider_names},
        "rows": len(rows),
    }
    (run_dir / "run_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    summary_rows: list[dict[str, Any]] = []
    for provider_name in provider_names:
        provider = PROVIDERS[provider_name]
        provider_rows = []
        for row in rows:
            query = row.get("user_query", "").strip()
            record: dict[str, Any] = {
                "provider": provider_name,
                "model": provider.model,
                "query_id": row.get("query_id", ""),
                "user_query": query,
            }
            try:
                parsed, raw_text, raw_response = call_provider(provider, query)
                expected = build_expected(row)
                evaluation = evaluate_prediction(expected, parsed)
                record.update(
                    {
                        "status": "ok",
                        "parsed": parsed,
                        "raw_text": raw_text,
                        "raw_response": raw_response,
                        "expected": expected,
                        "evaluation": evaluation,
                    }
                )
                summary_rows.append(
                    {
                        "provider": provider_name,
                        "model": provider.model,
                        "query_id": row.get("query_id", ""),
                        "intent_exact": evaluation["intent_exact"],
                        "overall_exact": evaluation["overall_exact"],
                        "countries_exact": evaluation["countries_exact"],
                        "regions_exact": evaluation["regions_exact"],
                        "commodities_exact": evaluation["commodities_exact"],
                        "material_types_exact": evaluation["material_types_exact"],
                        "storage_facility_types_exact": evaluation["storage_facility_types_exact"],
                        "project_status_exact": evaluation["project_status_exact"],
                        "unfc_e_exact": evaluation["unfc_e_exact"],
                        "unfc_f_exact": evaluation["unfc_f_exact"],
                        "unfc_g_exact": evaluation["unfc_g_exact"],
                    }
                )
            except Exception as exc:
                record.update({"status": "error", "error": str(exc)})
                summary_rows.append(
                    {
                        "provider": provider_name,
                        "model": provider.model,
                        "query_id": row.get("query_id", ""),
                        "intent_exact": False,
                        "overall_exact": False,
                        "countries_exact": False,
                        "regions_exact": False,
                        "commodities_exact": False,
                        "material_types_exact": False,
                        "storage_facility_types_exact": False,
                        "project_status_exact": False,
                        "unfc_e_exact": False,
                        "unfc_f_exact": False,
                        "unfc_g_exact": False,
                    }
                )
            provider_rows.append(record)
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)
        write_jsonl(run_dir / f"{provider_name}.jsonl", provider_rows)

    write_summary_csv(run_dir / "summary.csv", summary_rows)
    return run_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--providers",
        default="openai,gemini,anthropic,xai",
        help="Comma-separated providers: openai, gemini, anthropic, xai",
    )
    parser.add_argument("--input-file", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--sleep-seconds", type=float, default=0.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    load_dotenv(ROOT / ".env")
    provider_names = [name.strip() for name in args.providers.split(",") if name.strip()]
    invalid = [name for name in provider_names if name not in PROVIDERS]
    if invalid:
        print(f"Unsupported providers: {', '.join(invalid)}", file=sys.stderr)
        sys.exit(2)
    if not args.input_file.exists():
        print(f"Input file not found: {args.input_file}", file=sys.stderr)
        sys.exit(2)
    run_dir = run(provider_names, args.input_file, args.output_dir, args.limit, args.sleep_seconds)
    print(f"Results written to: {run_dir}")


if __name__ == "__main__":
    main()
