#!/usr/bin/env python3
"""
General-Purpose GIS Architecture Template Server:
Elsevier SoftwareX Demonstrator — Domain-Agnostic Conversational Spatial Search.

Features:
- Zero external dependencies: Runs on standard Python 3.9+ (http.server, json, re, urllib).
- 4-Stage Architecture Pipeline:
    Stage 1: Conversational Input & Intent Parsing
    Stage 2: Deterministic Thesaurus Normalizer & Schema Validator
    Stage 3: Apache Solr-Style Boolean Filter Builder & Live Facet Indexer
    Stage 4: Dynamic GIS UI Synchronization (Leaflet.js Badges & Pulsing Rings)
- Real-time Filter & Schema Studio: Live editing of filter definitions and thesaurus synonyms.
"""

import os
import sys
import json
import re
import argparse
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from typing import Dict, Any, List, Optional

TEMPLATE_DIR = Path(__file__).resolve().parent
DATA_FILE = TEMPLATE_DIR / "data" / "facilities.json"
CONFIG_FILE = TEMPLATE_DIR / "filters_config.json"
STATIC_DIR = TEMPLATE_DIR / "static"

# Cache and in-memory state
_DATASET: List[Dict[str, Any]] = []
_CONFIG: Dict[str, Any] = {}

def load_dataset() -> List[Dict[str, Any]]:
    global _DATASET
    if not _DATASET:
        if DATA_FILE.exists():
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                _DATASET = json.load(f)
        else:
            _DATASET = []
    return _DATASET

def load_config() -> Dict[str, Any]:
    global _CONFIG
    if not _CONFIG:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                _CONFIG = json.load(f)
        else:
            _CONFIG = {"filter_fields": []}
    return _CONFIG

def save_config(new_config: Dict[str, Any]) -> None:
    global _CONFIG
    _CONFIG = new_config
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(new_config, f, indent=2, ensure_ascii=False)

def reset_to_defaults() -> None:
    global _DATASET, _CONFIG
    _DATASET = []
    _CONFIG = {}
    load_dataset()
    load_config()


# ==============================================================================
# STAGE 1 & 2: CONVERSATIONAL NLU PARSER, NORMALIZER & SCHEMA VALIDATOR
# ==============================================================================

def parse_conversational_query(query: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Translates raw natural language user text into a structured, validated filter dictionary
    based on the declarative synonyms defined in filters_config.json.
    """
    q_lower = query.lower()
    fields = config.get("filter_fields", [])
    extracted_filters: Dict[str, Any] = {}
    matched_tokens: List[str] = []

    # Check for greeting or onboarding intent
    greeting_patterns = [
        r'\bhola\b', r'\bhello\b', r'\bhi\b', r'\bhey\b', 
        r'\bbuenos d[ií]as\b', r'\bbuenas tardes\b', r'\bbuenas\b',
        r'\bgood morning\b', r'\bgood afternoon\b'
    ]
    help_patterns = [
        r'ayuda\b', r'help\b', r'como funciona', r'c[oó]mo funciona',
        r'qu[eé] puedes hacer', r'what can you do', r'que es esto', r'qu[eé] es esto'
    ]
    is_greeting = any(re.search(pat, q_lower) for pat in greeting_patterns)
    is_help = any(re.search(pat, q_lower) for pat in help_patterns)

    # 1. Parse each field defined in the declarative schema
    for field in fields:
        f_key = field.get("key")
        f_type = field.get("type")
        synonyms = field.get("synonyms", {})
        options = field.get("options", [])

        if f_type in ["multiselect", "select"]:
            field_matches = []
            # Check synonyms mapping
            for canon_val, syn_list in synonyms.items():
                for syn in syn_list:
                    pattern = r'\b' + re.escape(syn.lower()) + r'\b'
                    if re.search(pattern, q_lower):
                        # Match with case of options if possible
                        matched_option = next((opt for opt in options if opt.lower() == canon_val.lower()), canon_val.title())
                        if matched_option not in field_matches:
                            field_matches.append(matched_option)
                        matched_tokens.append(syn)
                        break

            # If no synonyms matched, check literal options directly
            if not field_matches:
                for opt in options:
                    pattern = r'\b' + re.escape(opt.lower()) + r'\b'
                    if re.search(pattern, q_lower):
                        if opt not in field_matches:
                            field_matches.append(opt)
                        matched_tokens.append(opt)

            if field_matches:
                extracted_filters[f_key] = field_matches if f_type == "multiselect" else field_matches[0]

        elif f_type == "range":
            # Extract numeric range comparisons: e.g. "> 100", "over 50", "capacity > 200", "más de 100", "< 50"
            range_filter = {}
            # Min comparison: > 100, over 100, mayor que 100, mas de 100
            min_match = re.search(r'(?:>|over|greater than|above|m[aá]s de|mayor(?: que)?)\s*(\d+(?:\.\d+)?)', q_lower)
            if min_match:
                range_filter["min"] = float(min_match.group(1))
                matched_tokens.append(min_match.group(0))

            # Max comparison: < 50, under 50, less than 50, menor que 50, menos de 50
            max_match = re.search(r'(?:<|under|less than|below|menos de|menor(?: que)?)\s*(\d+(?:\.\d+)?)', q_lower)
            if max_match:
                range_filter["max"] = float(max_match.group(1))
                matched_tokens.append(max_match.group(0))

            # Between comparison: between X and Y, entre X e Y
            between_match = re.search(r'(?:between|entre)\s*(\d+(?:\.\d+)?)\s*(?:and|y|a)\s*(\d+(?:\.\d+)?)', q_lower)
            if between_match:
                range_filter["min"] = float(between_match.group(1))
                range_filter["max"] = float(between_match.group(2))
                matched_tokens.append(between_match.group(0))

            if range_filter:
                extracted_filters[f_key] = range_filter

    # Determine intent
    if (is_greeting or is_help) and not extracted_filters:
        intent = "generic_qa"
    elif extracted_filters:
        intent = "filter_search"
    else:
        # Check if user asked for all/everything
        if any(w in q_lower for w in ["all", "todos", "todas", "everything", "dataset"]):
            intent = "filter_search"
        else:
            intent = "generic_qa"

    return {
        "intent": intent,
        "filters": extracted_filters,
        "matched_tokens": matched_tokens
    }


# ==============================================================================
# STAGE 3: APACHE SOLR BOOLEAN QUERY BUILDER & SPATIAL FILTERING ENGINE
# ==============================================================================

def build_solr_query(filters: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Constructs Apache Solr search query parameters (q, fq) from structured filters.
    """
    q = "*:*"
    fq_list: List[str] = []

    fields_dict = {f["key"]: f for f in config.get("filter_fields", [])}

    for f_key, f_val in filters.items():
        if not f_val:
            continue
        field_def = fields_dict.get(f_key, {})
        f_type = field_def.get("type", "multiselect")

        if f_type == "multiselect":
            if isinstance(f_val, list) and f_val:
                clauses = [f'"{v}"' for v in f_val]
                fq_list.append(f"{f_key}:({' OR '.join(clauses)})")
            elif isinstance(f_val, str):
                fq_list.append(f'{f_key}:"{f_val}"')

        elif f_type == "select":
            val_str = f_val if isinstance(f_val, str) else str(f_val)
            fq_list.append(f'{f_key}:"{val_str}"')

        elif f_type == "range":
            if isinstance(f_val, dict):
                min_v = f_val.get("min", "*")
                max_v = f_val.get("max", "*")
                fq_list.append(f"{f_key}:[{min_v} TO {max_v}]")

    return {
        "q": q,
        "fq": fq_list,
        "solr_url_preview": f"/solr/select?q={q}" + "".join([f"&fq={rule}" for rule in fq_list])
    }

def execute_spatial_filtering(filters: Dict[str, Any], dataset: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Applies the Solr filter rules to the in-memory dataset, generating live facet distributions.
    """
    fields_dict = {f["key"]: f for f in config.get("filter_fields", [])}
    matched_sites = []

    for site in dataset:
        matches = True

        for f_key, f_val in filters.items():
            if not f_val:
                continue
            field_def = fields_dict.get(f_key, {})
            f_type = field_def.get("type", "multiselect")
            site_val = site.get(f_key)

            if f_type == "multiselect":
                target_vals = [v.lower() for v in (f_val if isinstance(f_val, list) else [f_val])]
                if isinstance(site_val, list):
                    site_vals_lower = [str(x).lower() for x in site_val]
                    if not any(tv in site_vals_lower for tv in target_vals):
                        matches = False
                        break
                else:
                    if str(site_val).lower() not in target_vals:
                        matches = False
                        break

            elif f_type == "select":
                target_str = str(f_val).lower()
                if str(site_val).lower() != target_str:
                    matches = False
                    break

            elif f_type == "range":
                if isinstance(f_val, dict) and site_val is not None:
                    try:
                        num_val = float(site_val)
                        if "min" in f_val and num_val < float(f_val["min"]):
                            matches = False
                            break
                        if "max" in f_val and num_val > float(f_val["max"]):
                            matches = False
                            break
                    except (ValueError, TypeError):
                        matches = False
                        break

        if matches:
            site_copy = dict(site)
            site_copy["score"] = 0.98 if filters else 0.85
            matched_sites.append(site_copy)

    # Compute dynamic Solr facet counts across the matched results
    facets: Dict[str, Dict[str, int]] = {}
    for f in config.get("filter_fields", []):
        if f.get("type") in ["multiselect", "select"]:
            f_key = f["key"]
            facets[f_key] = {}
            for opt in f.get("options", []):
                facets[f_key][opt] = 0

            for doc in matched_sites:
                val = doc.get(f_key)
                if isinstance(val, list):
                    for item in val:
                        norm_item = next((opt for opt in f.get("options", []) if opt.lower() == str(item).lower()), str(item))
                        facets[f_key][norm_item] = facets[f_key].get(norm_item, 0) + 1
                elif val is not None:
                    norm_val = next((opt for opt in f.get("options", []) if opt.lower() == str(val).lower()), str(val))
                    facets[f_key][norm_val] = facets[f_key].get(norm_val, 0) + 1

    return {
        "matched_docs": matched_sites,
        "matched_ids": [d["id"] for d in matched_sites],
        "num_found": len(matched_sites),
        "total_dataset": len(dataset),
        "facets": facets
    }


# ==============================================================================
# STAGE 4: GIS VISUAL SYNCHRONIZATION & NARRATIVE RESPONSE SYNTHESIS
# ==============================================================================

def generate_natural_narrative(
    query: str,
    intent: str,
    filters: Dict[str, Any],
    results: Dict[str, Any],
    config: Dict[str, Any]
) -> str:
    """
    Synthesizes natural language narrative response with grounding evidence.
    """
    q_lower = query.lower()
    is_spanish = any(w in q_lower for w in ["hola", "buen", "ayuda", "como", "cuantos", "filtrar", "solar", "eolica", "escombrera", "balsa", "en ", "de "])
    num_found = results.get("num_found", 0)
    total = results.get("total_dataset", len(load_dataset()))
    docs = results.get("matched_docs", [])

    if intent == "generic_qa" and not filters:
        if is_spanish:
            return (
                "👋 **Bienvenido a la Plantilla de Arquitectura GIS de Propósito General (SoftwareX).**\n\n"
                "Este entorno interactivo permite comprobar la **reutilización y generalidad del framework desacoplado** (NLU $\\to$ Solr $\\to$ GIS) "
                "más allá del caso de estudio minero europeo.\n\n"
                "### 🎯 ¿Qué puedes probar en esta plantilla?\n"
                "1. **Búsqueda conversacional**: Escribe consultas como *\"Instalaciones solares y eólicas en España con más de 50 MW\"* o *\"Almacenamiento en construcción\"*.\n"
                "2. **Filtros manuales**: Modifica las casillas y deslizadores del panel lateral para observar la sincronización cartográfica en tiempo real.\n"
                "3. **Estudio de Esquema y Filtros (Reviewer Tinkering)**: En la pestaña *\"🛠️ Filtros y Esquema\"*, añade nuevos campos o sinónimos al vuelo y observa cómo el motor NLU los adopta inmediatamente.\n"
                "4. **Traza de 4 etapas**: Inspecciona en el panel inferior cómo la consulta se convierte en reglas Solr booleanas y facetas calculadas.\n"
            )
        else:
            return (
                "👋 **Welcome to the General-Purpose GIS Architecture Template Sandbox (SoftwareX).**\n\n"
                "This sandbox demonstrates the **modularity, generality, and domain-independence** of the 4-stage decoupled architecture (NLU $\\to$ Solr $\\to$ GIS) "
                "beyond the European Critical Raw Materials demonstrator.\n\n"
                "### 🎯 Features you can evaluate:\n"
                "1. **Conversational Spatial Search**: Try queries like *\"Solar and wind facilities in Spain over 50 MW\"* or *\"Operational storage in United States\"*.\n"
                "2. **Manual Filter Controls**: Use the interactive pills and sliders on the sidebar to filter facilities with real-time Leaflet synchronization.\n"
                "3. **Schema & Filter Studio (Tinkering)**: Open the *\"🛠️ Schema & Filters Studio\"* tab to create new custom filter fields or edit synonyms live.\n"
                "4. **4-Stage Pipeline Trace**: Inspect the bottom drawer to examine NLU parsing, Boolean Solr query construction, and GIS pulse rings.\n"
            )

    if num_found == 0:
        if is_spanish:
            return (
                f"🔍 **Sin coincidencias para los criterios indicados:**\n"
                f"No se ha encontrado ninguna instalación que cumpla simultáneamente todos los filtros activos.\n\n"
                f"💡 *Sugerencia: Prueba a relajar alguno de los filtros en el panel lateral o amplía el rango de capacidad.*"
            )
        else:
            return (
                f"🔍 **No matching facilities found:**\n"
                f"No spatial points in the current dataset satisfy all active filter criteria.\n\n"
                f"💡 *Suggestion: Try relaxing one of the filter fields or broadening the capacity range.*"
            )

    # Summarize findings
    cat_summary = {}
    country_summary = {}
    for d in docs:
        c = d.get("category", "General")
        cat_summary[c] = cat_summary.get(c, 0) + 1
        ctry = d.get("country", "Global")
        country_summary[ctry] = country_summary.get(ctry, 0) + 1

    cats_str = ", ".join([f"{k} ({v})" for k, v in cat_summary.items()])
    countries_str = ", ".join([f"{k} ({v})" for k, v in country_summary.items()])

    top_facility = docs[0]

    if is_spanish:
        narrative = (
            f"✅ **Se han identificado {num_found} de {total} instalaciones ({round(num_found/total*100, 1)}% del repositorio)** "
            f"que satisfacen los criterios de búsqueda:\n\n"
            f"- 📌 **Distribución por tipología**: {cats_str}.\n"
            f"- 🌍 **Países representados**: {countries_str}.\n"
            f"- 🌟 **Instalación destacada**: **{top_facility.get('name')}** ({top_facility.get('country')}, {top_facility.get('capacity_mw')} MW, Estado: *{top_facility.get('status')}*).\n\n"
            f"*(Los marcadores coincidentes se han resaltado en el mapa con anillos de pulso luminosos y etiquetas activas).* "
        )
    else:
        narrative = (
            f"✅ **Identified {num_found} of {total} facilities ({round(num_found/total*100, 1)}% of dataset)** "
            f"matching your spatial criteria:\n\n"
            f"- 📌 **Category breakdown**: {cats_str}.\n"
            f"- 🌍 **Geographic distribution**: {countries_str}.\n"
            f"- 🌟 **Featured facility**: **{top_facility.get('name')}** ({top_facility.get('country')}, {top_facility.get('capacity_mw')} MW, Status: *{top_facility.get('status')}*).\n\n"
            f"*(Matching facilities are highlighted on the Leaflet map with pulsing rings and active filter badges).* "
        )

    return narrative


# ==============================================================================
# PIPELINE ORCHESTRATOR
# ==============================================================================

def process_query_pipeline(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes the complete 4-stage pipeline for a given user query or manual filter set.
    """
    dataset = load_dataset()
    config = load_config()

    query = payload.get("query", "").strip()
    manual_filters = payload.get("manual_filters")

    # If manual filters are explicitly provided, use them; otherwise parse conversational text
    if manual_filters is not None and isinstance(manual_filters, dict):
        validated_filters = manual_filters
        intent = "filter_search"
        matched_tokens = list(manual_filters.keys())
    elif query:
        parsed = parse_conversational_query(query, config)
        validated_filters = parsed["filters"]
        intent = parsed["intent"]
        matched_tokens = parsed["matched_tokens"]
    else:
        validated_filters = {}
        intent = "generic_qa"
        matched_tokens = []

    # Stage 3: Solr query construction & spatial execution
    solr_query = build_solr_query(validated_filters, config)
    filtering_results = execute_spatial_filtering(validated_filters, dataset, config)

    # Active filter badges for GIS map
    active_badges = []
    fields_dict = {f["key"]: f for f in config.get("filter_fields", [])}
    for k, v in validated_filters.items():
        if not v:
            continue
        f_def = fields_dict.get(k, {})
        label = f_def.get("label", k.title())
        f_type = f_def.get("type", "multiselect")

        if f_type == "range" and isinstance(v, dict):
            min_str = f">= {v['min']} MW" if "min" in v else ""
            max_str = f"<= {v['max']} MW" if "max" in v else ""
            val_str = " & ".join(filter(None, [min_str, max_str]))
            active_badges.append({"key": k, "label": label, "values": [val_str]})
        elif isinstance(v, list):
            active_badges.append({"key": k, "label": label, "values": v})
        else:
            active_badges.append({"key": k, "label": label, "values": [str(v)]})

    # Stage 4: Narrative synthesis
    narrative = generate_natural_narrative(query, intent, validated_filters, filtering_results, config)

    return {
        "query": query,
        "intent": intent,
        "matched_tokens": matched_tokens,
        "filters": validated_filters,
        "solr_query": solr_query,
        "solr_facets": filtering_results["facets"],
        "num_found": filtering_results["num_found"],
        "total_dataset": filtering_results["total_dataset"],
        "matched_ids": filtering_results["matched_ids"],
        "active_map_filters": active_badges,
        "docs": filtering_results["matched_docs"],
        "narrative": narrative,
        "response_text": narrative
    }


# ==============================================================================
# HTTP WEB SERVER & REST API HANDLER
# ==============================================================================

class GenericGISHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        # API: Return all facilities
        if self.path in ["/api/sites", "/api/facilities", "/api/data"]:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            data = load_dataset()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            return

        # API: Return active schema & filter configuration
        elif self.path in ["/api/config", "/api/schema", "/api/filters_config"]:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            cfg = load_config()
            self.wfile.write(json.dumps(cfg, ensure_ascii=False).encode("utf-8"))
            return

        # API: Health check
        elif self.path == "/api/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            resp = {"status": "ok", "app": "General GIS Template Sandbox", "facilities": len(load_dataset())}
            self.wfile.write(json.dumps(resp).encode("utf-8"))
            return

        return super().do_GET()

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"

        # API: Conversational query or manual filter query
        if self.path in ["/api/chat", "/api/query"]:
            try:
                payload = json.loads(post_data) if post_data else {}
                result = process_query_pipeline(payload)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        # API: Live update schema & filters configuration (Reviewer Tinkering Studio)
        elif self.path in ["/api/config", "/api/schema", "/api/filters_config"]:
            try:
                new_cfg = json.loads(post_data)
                save_config(new_cfg)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "saved", "config": new_cfg}, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        # API: Reset to factory defaults
        elif self.path == "/api/reset":
            try:
                reset_to_defaults()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "reset_successful"}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()


def run_server(port: int = 8085, host: str = "0.0.0.0"):
    # Ensure static directory exists
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    load_dataset()
    load_config()

    server = ThreadingHTTPServer((host, port), GenericGISHandler)
    print("=" * 76)
    print(" 🌍 Elsevier SoftwareX — General-Purpose GIS Architecture Template")
    print(" 🛠️  Domain-Agnostic Conversational Spatial Search & Live Filter Studio")
    print("=" * 76)
    print(f" [*] HTTP Server active on: http://{host}:{port}/")
    print(f" [*] Local access URL:     http://localhost:{port}/")
    print(f" [*] Facilities dataset:   {len(load_dataset())} points loaded ({DATA_FILE})")
    print(f" [*] Filter configuration: {CONFIG_FILE}")
    print(f" [*] Zero external dependencies required. Press Ctrl+C to terminate.")
    print("=" * 76)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[!] Shutting down General-Purpose GIS Template server gracefully.")
        server.shutdown()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="General-Purpose GIS Architecture Template Server")
    parser.add_argument("--port", type=int, default=8085, help="Port to listen on (default: 8085)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host interface to bind (default: 0.0.0.0)")
    args = parser.parse_args()

    run_server(port=args.port, host=args.host)
