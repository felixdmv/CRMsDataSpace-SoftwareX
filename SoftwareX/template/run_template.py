#!/usr/bin/env python3
"""
General-Purpose GIS Architecture Template Server:
Elsevier SoftwareX Demonstrator — Domain-Agnostic Conversational Spatial Search Sandbox.

Features:
- Zero external dependencies: Runs on standard Python 3.9+ (stdlib).
- 100% Offline Vector Map: Uses custom stylized cartographic GeoJSON (Land & Sea) with zero external tile server API keys.
- User-Driven Dynamic Schema: Users define custom filter dimensions, or select presets (Renewable Energy, Smart City, Custom).
- Procedural Spatial Generation: Points are only generated on demand when the user triggers population.
- Decoupled 4-Stage Architecture Pipeline:
    Stage 1: Dynamic Conversational NLU & Token Extraction
    Stage 2: Deterministic Schema Normalization & Validation
    Stage 3: Apache Solr-Style Boolean Query Builder ($q, fq$) & Live Facet Indexer
    Stage 4: Dynamic Cartographic Leaflet Synchronization
"""

import os
import sys
import json
import re
import random
import argparse
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from typing import Dict, Any, List, Optional, Tuple

TEMPLATE_DIR = Path(__file__).resolve().parent
DATA_FILE = TEMPLATE_DIR / "data" / "facilities.json"
CONFIG_FILE = TEMPLATE_DIR / "filters_config.json"
STATIC_DIR = TEMPLATE_DIR / "static"

# In-memory runtime state
_DATASET: List[Dict[str, Any]] = []
_CONFIG: Dict[str, Any] = {}

TERRITORY_AVALON: Dict[str, Any] = {
    "name": "Avalon Island",
    "description": "Archipelago island featuring 4 distinct biomes: Desert (Orange), Nature Reserve (Green), Metropolitan City (Grayish-Red), and Mountains (White), surrounded by a vibrant blue ocean.",
    "center": [20.0, 30.0],
    "zoom": 10.5,
    "zones": [
        {"name": "Metropolitan City District", "lat": 20.10, "lon": 30.12, "color": "#9b4d4d", "desc": "Civic harbor, commercial waterfront, and urban center (Grayish-Red)"},
        {"name": "Emerald Nature Reserve", "lat": 20.00, "lon": 29.75, "color": "#16a34a", "desc": "Lush river basin, temperate woodlands, and wildlife reserve (Green)"},
        {"name": "White Mountain Ridge", "lat": 20.02, "lon": 29.98, "color": "#f1f5f9", "desc": "Alpine peaks, rocky ridges, and snowcapped summits (White)"},
        {"name": "Avalon Desert Dunes", "lat": 19.84, "lon": 29.98, "color": "#ea580c", "desc": "Sun-drenched arid plains and coastal dunes (Orange)"},
        {"name": "Eastern Archipelago", "lat": 20.05, "lon": 30.34, "color": "#06b6d4", "desc": "Offshore maritime satellite islands"}
    ]
}

EMPTY_CONFIG: Dict[str, Any] = {
    "title": "General-Purpose GIS Architecture Template — Elsevier SoftwareX",
    "description": "Domain-Agnostic Conversational Spatial Search Sandbox. Select a domain preset to begin.",
    "active_preset": None,
    "territory": TERRITORY_AVALON,
    "filter_fields": []
}

ZONE_ALIASES: Dict[str, List[str]] = {
    "Metropolitan City District": ["metropolitan city district", "metropolitan city", "city district", "city", "metropolis", "urban", "harbor", "port", "ciudad metropolitana", "ciudad"],
    "Emerald Nature Reserve": ["emerald nature reserve", "nature reserve", "emerald park", "emerald reserve", "park", "reserve", "forest", "valley", "parque natural", "reserva", "esmeralda"],
    "White Mountain Ridge": ["white mountain ridge", "white mountains", "mountain ridge", "white peaks", "mountains", "peaks", "highlands", "alpine", "montanas", "picos"],
    "Avalon Desert Dunes": ["avalon desert dunes", "desert dunes", "avalon desert", "desert", "dunes", "arid", "south plains", "desierto", "dunas"],
    "Eastern Archipelago": ["eastern archipelago", "archipelago", "islands", "isles", "eastern isles", "satellite isles", "archipielago", "islas"]
}

# Built-in Domain Presets (1-Click Switching)
PRESETS: Dict[str, Dict[str, Any]] = {
    "energy": {
        "title": "Avalon Island — Renewable Energy & Power Grid",
        "description": "Exploration of utility-scale renewable generation, storage assets, and grid compliance.",
        "active_preset": "energy",
        "territory": TERRITORY_AVALON,
        "filter_fields": [
            {
                "key": "energy_type",
                "label": "Generation Technology",
                "type": "multiselect",
                "options": [
                    "Solar Photovoltaic",
                    "Onshore Wind",
                    "Offshore Wind",
                    "Hydroelectric Dam",
                    "Battery Storage (BESS)",
                    "Geothermal Plant"
                ],
                "colors": {
                    "Solar Photovoltaic": "#f59e0b",
                    "Onshore Wind": "#06b6d4",
                    "Offshore Wind": "#38bdf8",
                    "Hydroelectric Dam": "#3b82f6",
                    "Battery Storage (BESS)": "#8b5cf6",
                    "Geothermal Plant": "#10b981"
                },
                "synonyms": {
                    "solar photovoltaic": ["solar", "photovoltaic", "pv", "solar farm", "solar plant", "sun"],
                    "onshore wind": ["onshore wind", "wind turbines", "wind farm", "wind", "turbines"],
                    "offshore wind": ["offshore wind", "marine wind", "sea wind", "coastal wind"],
                    "hydroelectric dam": ["hydro", "hydroelectric", "dam", "reservoir", "water power"],
                    "battery storage (bess)": ["battery", "storage", "bess", "battery storage", "energy storage"],
                    "geothermal plant": ["geothermal", "thermal power", "geo", "hot springs"]
                }
            },
            {
                "key": "status",
                "label": "Operational Status",
                "type": "select",
                "options": [
                    "Operational",
                    "Under Construction",
                    "Permitting & Planned",
                    "Decommissioned"
                ],
                "colors": {
                    "Operational": "#10b981",
                    "Under Construction": "#f59e0b",
                    "Permitting & Planned": "#3b82f6",
                    "Decommissioned": "#64748b"
                },
                "synonyms": {
                    "operational": ["operational", "active", "online", "running", "producing", "commissioned"],
                    "under construction": ["under construction", "construction", "building", "in progress"],
                    "permitting & planned": ["planned", "projected", "permitting", "proposed", "pipeline"],
                    "decommissioned": ["decommissioned", "retired", "closed", "offline", "shut down"]
                }
            },
            {
                "key": "capacity_tier",
                "label": "Capacity Scale",
                "type": "select",
                "options": [
                    "Utility Scale (> 100 MW)",
                    "Medium Scale (20-100 MW)",
                    "Distributed (< 20 MW)"
                ],
                "colors": {
                    "Utility Scale (> 100 MW)": "#ec4899",
                    "Medium Scale (20-100 MW)": "#f97316",
                    "Distributed (< 20 MW)": "#14b8a6"
                },
                "synonyms": {
                    "utility scale (> 100 mw)": ["utility scale", "large scale", "major", "over 100", "> 100", "high capacity"],
                    "medium scale (20-100 mw)": ["medium scale", "mid scale", "20-100", "medium"],
                    "distributed (< 20 mw)": ["distributed", "small scale", "local", "under 20", "< 20", "micro"]
                }
            },
            {
                "key": "esg_rating",
                "label": "ESG Compliance Grade",
                "type": "select",
                "options": [
                    "Grade A (Exemplary)",
                    "Grade B (Compliant)",
                    "Grade C (Under Review)"
                ],
                "colors": {
                    "Grade A (Exemplary)": "#10b981",
                    "Grade B (Compliant)": "#f59e0b",
                    "Grade C (Under Review)": "#ef4444"
                },
                "synonyms": {
                    "grade a (exemplary)": ["grade a", "esg a", "top esg", "exemplary", "tier a", "a"],
                    "grade b (compliant)": ["grade b", "esg b", "compliant", "tier b", "b"],
                    "grade c (under review)": ["grade c", "esg c", "under review", "tier c", "c"]
                }
            }
        ]
    },
    "smartcity": {
        "title": "Avalon Metropolitan Area — Smart City & Public Services",
        "description": "Urban planning dashboard monitoring municipal facilities, response priorities, and transit hubs.",
        "active_preset": "smartcity",
        "territory": TERRITORY_AVALON,
        "filter_fields": [
            {
                "key": "facility_type",
                "label": "Municipal Infrastructure",
                "type": "multiselect",
                "options": [
                    "General Hospital",
                    "Public School",
                    "Metro Transit Hub",
                    "Urban Green Park",
                    "Police Station",
                    "Fire & Rescue"
                ],
                "colors": {
                    "General Hospital": "#ef4444",
                    "Public School": "#f59e0b",
                    "Metro Transit Hub": "#3b82f6",
                    "Urban Green Park": "#10b981",
                    "Police Station": "#8b5cf6",
                    "Fire & Rescue": "#f97316"
                },
                "synonyms": {
                    "general hospital": ["hospital", "clinic", "health", "medical center", "emergency room", "care"],
                    "public school": ["school", "education", "college", "academy", "high school"],
                    "metro transit hub": ["metro", "transit", "station", "bus", "transport hub", "subway", "train"],
                    "urban green park": ["park", "green space", "garden", "urban park", "recreation"],
                    "police station": ["police", "patrol", "precinct", "law enforcement", "station"],
                    "fire & rescue": ["fire", "fire station", "rescue", "emergency services"]
                }
            },
            {
                "key": "status",
                "label": "Operational Status",
                "type": "select",
                "options": [
                    "Operational",
                    "Under Maintenance",
                    "Capital Project / Planned"
                ],
                "colors": {
                    "Operational": "#10b981",
                    "Under Maintenance": "#f59e0b",
                    "Capital Project / Planned": "#3b82f6"
                },
                "synonyms": {
                    "operational": ["operational", "active", "open", "in service", "functioning"],
                    "under maintenance": ["maintenance", "repairs", "renovation", "closed temporarily"],
                    "capital project / planned": ["planned", "projected", "in development", "pipeline", "scheduled"]
                }
            },
            {
                "key": "priority",
                "label": "Response Priority",
                "type": "select",
                "options": [
                    "Critical Tier 1",
                    "Standard Tier 2",
                    "Secondary Tier 3"
                ],
                "colors": {
                    "Critical Tier 1": "#ef4444",
                    "Standard Tier 2": "#3b82f6",
                    "Secondary Tier 3": "#64748b"
                },
                "synonyms": {
                    "critical tier 1": ["critical", "tier 1", "urgent", "priority", "essential"],
                    "standard tier 2": ["standard", "tier 2", "normal", "routine"],
                    "secondary tier 3": ["secondary", "tier 3", "low priority", "optional"]
                }
            }
        ]
    },
    "custom": {
        "title": "Avalon Republic — Custom Blank Canvas",
        "description": "Start completely from scratch by designing your own filter attributes and category values.",
        "active_preset": "custom",
        "territory": TERRITORY_AVALON,
        "filter_fields": []
    }
}

COLOR_PALETTE = [
    "#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899",
    "#06b6d4", "#f97316", "#14b8a6", "#6366f1", "#84cc16"
]

def strip_accents(text: str) -> str:
    accents = {'á':'a', 'é':'e', 'í':'i', 'ó':'o', 'ú':'u', 'ñ':'n'}
    for k, v in accents.items():
        text = text.replace(k, v)
    return text

def get_word_variants(word: str) -> List[str]:
    w = word.strip().lower()
    variants = {w, strip_accents(w)}
    if w.endswith('es'):
        variants.add(w[:-2])
    elif w.endswith('s'):
        variants.add(w[:-1])
    else:
        variants.add(w + 's')
        variants.add(w + 'es')
    return [v for v in variants if len(v) >= 3]


# ==============================================================================
# PROCEDURAL OBJECT & DATASET GENERATOR
# ==============================================================================

def generate_procedural_points(count: int, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Procedurally generates spatial facilities placed strictly within the landmass
    zones using random combinations of current active filter dimensions.
    """
    territory = config.get("territory", {})
    zones = territory.get("zones", [
        {"name": "North Coast", "lat": 20.17, "lon": 30.00},
        {"name": "Central Highlands", "lat": 20.02, "lon": 29.98},
        {"name": "South Bay", "lat": 19.84, "lon": 29.94},
        {"name": "Emerald Valley", "lat": 20.00, "lon": 29.75},
        {"name": "Eastern Archipelago", "lat": 20.05, "lon": 30.34}
    ])
    filter_fields = config.get("filter_fields", [])

    points: List[Dict[str, Any]] = []

    for i in range(1, count + 1):
        zone = random.choice(zones)
        # Jitter coordinates inside the land bounds of this specific zone
        lat = round(zone["lat"] + random.uniform(-0.035, 0.035), 5)
        lon = round(zone["lon"] + random.uniform(-0.045, 0.045), 5)

        props: Dict[str, Any] = {}
        for f in filter_fields:
            key = f.get("key")
            opts = f.get("options", [])
            f_type = f.get("type", "select")
            if opts:
                if f_type == "multiselect" and random.random() < 0.25 and len(opts) > 1:
                    props[key] = random.sample(opts, k=min(2, len(opts)))
                else:
                    props[key] = random.choice(opts)

        first_field = filter_fields[0] if filter_fields else None
        first_val = props.get(first_field["key"]) if first_field else "Facility"
        if isinstance(first_val, list):
            first_val = first_val[0]

        name = f"{first_val} - {zone['name']} #{i:02d}"

        # Generate descriptive sentence reflecting assigned attributes
        desc_parts = [f"{f.get('label', f.get('key'))}: {props.get(f.get('key'))}" for f in filter_fields if f.get("key") in props]
        if desc_parts:
            description = f"Located in {zone['name']}. Key attributes: {'; '.join(desc_parts)}."
        else:
            description = f"Spatial asset georeferenced in {zone['name']}."

        point = {
            "id": f"FAC-{i:03d}",
            "name": name,
            "latitude": lat,
            "longitude": lon,
            "zone": zone["name"],
            "description": description,
            **props
        }
        points.append(point)

    return points


def load_dataset() -> List[Dict[str, Any]]:
    global _DATASET
    if not _DATASET:
        if DATA_FILE.exists():
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    _DATASET = json.load(f)
            except Exception:
                _DATASET = []
        else:
            _DATASET = []
    return _DATASET

def save_dataset(dataset: List[Dict[str, Any]]) -> None:
    global _DATASET
    _DATASET = dataset
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

def load_config() -> Dict[str, Any]:
    global _CONFIG
    if not _CONFIG:
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    _CONFIG = json.load(f)
            except Exception:
                _CONFIG = {}
        if not _CONFIG:
            _CONFIG = json.loads(json.dumps(EMPTY_CONFIG))
            save_config(_CONFIG)
    return _CONFIG

def save_config(new_config: Dict[str, Any]) -> None:
    global _CONFIG
    _CONFIG = new_config
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(new_config, f, indent=2, ensure_ascii=False)


# ==============================================================================
# STAGE 1 & 2: DYNAMIC CONVERSATIONAL NLU & DETERMINISTIC NORMALIZER
# ==============================================================================

def parse_conversational_query(query: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Translates raw conversational natural language into a validated filter dictionary
    based on the current dynamic filter dimensions, options, synonyms, and territory zones.
    """
    q_lower = query.lower()
    q_norm = strip_accents(q_lower)
    extracted_filters: Dict[str, Any] = {}
    matched_tokens: List[str] = []

    # Greeting / Help intent patterns
    greeting_patterns = [r'\bhello\b', r'\bhi\b', r'\bhey\b', r'\bgood morning\b', r'\bgreetings\b', r'\bhola\b', r'\bbuenos dias\b', r'\bayuda\b']
    help_patterns = [r'\bhelp\b', r'how (?:does it|to) work', r'what can you do', r'what is this', r'como funciona']
    is_greeting = any(re.search(pat, q_lower) for pat in greeting_patterns)
    is_help = any(re.search(pat, q_lower) for pat in help_patterns)

    # 1. Match territory zones (including bilingual aliases)
    zones = config.get("territory", {}).get("zones", [])
    for z in zones:
        z_name = z["name"]
        alias_list = ZONE_ALIASES.get(z_name, []) + [z_name]
        matched_zone = False
        for alias in alias_list:
            a_norm = strip_accents(alias.lower())
            pattern = r'\b' + re.escape(a_norm) + r'\b'
            if re.search(pattern, q_norm):
                extracted_filters["zone"] = z_name
                matched_tokens.append(alias)
                matched_zone = True
                break
        if matched_zone:
            break

    # 2. Match each dynamic filter field defined by user
    filter_fields = config.get("filter_fields", [])
    for field in filter_fields:
        f_key = field.get("key")
        f_type = field.get("type", "select")
        options = field.get("options", [])
        synonyms = field.get("synonyms", {})

        field_matches: List[str] = []

        # Check explicit synonyms mapping
        for canon_opt, syn_list in synonyms.items():
            for syn in syn_list:
                s_norm = strip_accents(syn.lower())
                pattern = r'\b' + re.escape(s_norm) + r'\b'
                if re.search(pattern, q_norm):
                    matched_opt = next((opt for opt in options if strip_accents(opt.lower()) == strip_accents(canon_opt.lower())), canon_opt)
                    if matched_opt not in field_matches:
                        field_matches.append(matched_opt)
                    matched_tokens.append(syn)
                    break

        # Check literal option words and morphological variants
        for opt in options:
            if opt in field_matches:
                continue
            words = opt.split()
            matched = False
            for word in words:
                for variant in get_word_variants(word):
                    pattern = r'\b' + re.escape(variant) + r'\b'
                    if re.search(pattern, q_norm):
                        field_matches.append(opt)
                        matched_tokens.append(word)
                        matched = True
                        break
                if matched:
                    break

        if field_matches:
            if f_type == "multiselect" or len(field_matches) > 1:
                extracted_filters[f_key] = field_matches
            else:
                extracted_filters[f_key] = field_matches[0]

    # Intent determination
    if (is_greeting or is_help) and not extracted_filters:
        intent = "generic_qa"
    elif extracted_filters:
        intent = "filter_search"
    else:
        if any(w in q_lower for w in ["all", "everything", "dataset", "show all", "list all"]):
            intent = "filter_search"
        else:
            intent = "generic_qa"

    return {
        "intent": intent,
        "filters": extracted_filters,
        "matched_tokens": list(set(matched_tokens))
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

    for f_key, f_val in filters.items():
        if not f_val:
            continue
        if isinstance(f_val, list):
            clauses = [f'"{v}"' for v in f_val]
            fq_list.append(f"{f_key}:({' OR '.join(clauses)})")
        else:
            fq_list.append(f'{f_key}:"{f_val}"')

    solr_url_preview = f"/solr/select?q={q}" + "".join([f"&fq={rule}" for rule in fq_list])

    return {
        "q": q,
        "fq": fq_list,
        "solr_url_preview": solr_url_preview
    }


def execute_spatial_filtering(filters: Dict[str, Any], dataset: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes Solr boolean filter rules over the in-memory dataset,
    computing dynamic multidimensional facet distributions.
    """
    matched_sites = []

    for site in dataset:
        matches = True
        for f_key, f_val in filters.items():
            if not f_val:
                continue
            site_val = site.get(f_key)
            if site_val is None:
                matches = False
                break

            target_vals = [strip_accents(str(v).lower()) for v in (f_val if isinstance(f_val, list) else [f_val])]

            if isinstance(site_val, list):
                site_vals_norm = [strip_accents(str(x).lower()) for x in site_val]
                if not any(tv in site_vals_norm for tv in target_vals):
                    matches = False
                    break
            else:
                site_val_norm = strip_accents(str(site_val).lower())
                if site_val_norm not in target_vals:
                    matches = False
                    break

        if matches:
            site_copy = dict(site)
            site_copy["score"] = 0.98 if filters else 0.85
            matched_sites.append(site_copy)

    # Compute live Solr facets for all user filter fields + territory zones
    facets: Dict[str, Dict[str, int]] = {}

    # 1. Territory Zones Facets
    zones = config.get("territory", {}).get("zones", [])
    facets["zone"] = {z["name"]: 0 for z in zones}
    for doc in matched_sites:
        z = doc.get("zone")
        if z and z in facets["zone"]:
            facets["zone"][z] += 1

    # 2. Dynamic Filter Fields Facets
    for f in config.get("filter_fields", []):
        f_key = f["key"]
        options = f.get("options", [])
        facets[f_key] = {opt: 0 for opt in options}

        for doc in matched_sites:
            val = doc.get(f_key)
            if isinstance(val, list):
                for item in val:
                    norm_item = next((opt for opt in options if opt.lower() == str(item).lower()), str(item))
                    facets[f_key][norm_item] = facets[f_key].get(norm_item, 0) + 1
            elif val is not None:
                norm_val = next((opt for opt in options if opt.lower() == str(val).lower()), str(val))
                facets[f_key][norm_val] = facets[f_key].get(norm_val, 0) + 1

    return {
        "matched_docs": matched_sites,
        "matched_ids": [d["id"] for d in matched_sites],
        "num_found": len(matched_sites),
        "total_dataset": len(dataset),
        "facets": facets
    }


# ==============================================================================
# STAGE 4: GROUNDED NARRATIVE SYNTHESIS
# ==============================================================================

def generate_natural_narrative(
    query: str,
    intent: str,
    filters: Dict[str, Any],
    results: Dict[str, Any],
    config: Dict[str, Any]
) -> str:
    """
    Synthesizes a grounded natural language response in English explaining spatial query results.
    """
    num_found = results.get("num_found", 0)
    total = results.get("total_dataset", len(load_dataset()))
    docs = results.get("matched_docs", [])
    territory_name = config.get("territory", {}).get("name", "the territory")

    if not config.get("active_preset"):
        return (
            f"### 👋 Welcome to the Decoupled GIS Architecture Sandbox\n\n"
            f"Currently, **no domain is selected**.\n\n"
            f"#### 🚀 Getting Started:\n"
            f"1. **Select a domain** on the left panel (*⚡ Renewable Energy*, *🏙️ Smart City*, or *✨ Custom*).\n"
            f"2. The **domain filters** will activate in the right-hand panel next to the interactive map.\n"
            f"3. Click **🎲 Generate Points** to scatter facilities across the 4 island biomes: **Desert (Orange)**, **Nature Reserve (Green)**, **City (Grayish-Red)**, and **Mountains (White)**, surrounded by the blue ocean.\n"
            f"4. Perform **conversational searches** or interact with facet pills to synchronize the cartographic map."
        )

    if total == 0:
        return (
            f"👋 **Welcome to the General-Purpose GIS Architecture Template (SoftwareX).**\n\n"
            f"The map of **{territory_name}** currently has **0 spatial points**.\n\n"
            f"### 🚀 Getting Started (3-Step Walkthrough):\n"
            f"1. **Step 1 — Review Filters**: Filters are available in the right panel.\n"
            f"2. **Step 2 — Populate the Map**: Choose the number of points and click *\"🎲 Generate Points\"*. The procedural generator will scatter objects across {territory_name} combining your active filters.\n"
            f"3. **Step 3 — Conversational Spatial Search**: Query the map using conversational phrases (e.g. *\"solar and wind with grade a\"*, *\"nature reserve\"*) to see the 4-stage pipeline synchronize Leaflet with pulsing rings."
        )

    if intent == "generic_qa" and not filters:
        filter_count = len(config.get("filter_fields", []))
        return (
            f"👋 **{territory_name} GIS Sandbox Ready ({total} facilities loaded).**\n\n"
            f"This environment demonstrates how our decoupled 4-stage architecture (**Conversational NLU $\\to$ Solr Boolean Builder $\\to$ Leaflet GIS Visual Sync**) "
            f"adapts dynamically to any geospatial domain without code modifications.\n\n"
            f"### 💡 Things you can try right now:\n"
            f"- **Conversational Search**: Type queries such as *\"Solar farms with Grade A rating\"* or *\"Facilities in North Coast\"*.\n"
            f"- **Manual Facet Pills**: Click any badge on the sidebar to toggle Solr filter rules.\n"
            f"- **Inspector Drawer**: Expand the bottom panel to inspect NLU tokens, validated JSON schema, Solr `$fq` rules, and cartographic sync."
        )

    if num_found == 0:
        return (
            f"🔍 **No spatial facilities matched your active criteria:**\n"
            f"No objects in **{territory_name}** satisfy all active filter rules simultaneously.\n\n"
            f"💡 *Suggestion: Click on an active filter badge to relax criteria or try searching for another technology/sector.*"
        )

    fields = config.get("filter_fields", [])
    primary_field = fields[0]["key"] if fields else "zone"
    field_label = fields[0].get("label", primary_field) if fields else "Zone"

    summary: Dict[str, int] = {}
    zone_summary: Dict[str, int] = {}
    for d in docs:
        val = d.get(primary_field)
        if isinstance(val, list):
            val = ", ".join(val)
        summary[str(val)] = summary.get(str(val), 0) + 1
        z = d.get("zone", "Territory")
        zone_summary[z] = zone_summary.get(z, 0) + 1

    summary_str = ", ".join([f"{k} ({v})" for k, v in summary.items()])
    zones_str = ", ".join([f"{k} ({v})" for k, v in zone_summary.items()])
    featured = docs[0]

    pct = round(num_found / total * 100, 1) if total else 100
    narrative = (
        f"✅ **Identified {num_found} of {total} facilities ({pct}%) in {territory_name}:**\n\n"
        f"- 📌 **Breakdown by {field_label}**: {summary_str}.\n"
        f"- 🗺️ **Geographic Sectors**: {zones_str}.\n"
        f"- 🌟 **Featured Facility**: **{featured.get('name')}** (Sector: *{featured.get('zone')}*).\n\n"
        f"*(Matching facilities are highlighted on the offline vector map with pulsing radar rings and active filter tags).* "
    )
    return narrative


# ==============================================================================
# PIPELINE ORCHESTRATOR
# ==============================================================================

def process_query_pipeline(payload: Dict[str, Any]) -> Dict[str, Any]:
    dataset = load_dataset()
    config = load_config()

    query = payload.get("query", "").strip()
    manual_filters = payload.get("manual_filters")

    if manual_filters is not None and isinstance(manual_filters, dict):
        validated_filters = {k: v for k, v in manual_filters.items() if v}
        intent = "filter_search"
        matched_tokens = list(validated_filters.keys())
    elif query:
        parsed = parse_conversational_query(query, config)
        validated_filters = parsed["filters"]
        intent = parsed["intent"]
        matched_tokens = parsed["matched_tokens"]
    else:
        validated_filters = {}
        intent = "generic_qa"
        matched_tokens = []

    solr_query = build_solr_query(validated_filters, config)
    filtering_results = execute_spatial_filtering(validated_filters, dataset, config)

    # Active filter badges for UI map header
    active_badges = []
    fields_dict = {f["key"]: f for f in config.get("filter_fields", [])}
    for k, v in validated_filters.items():
        if not v:
            continue
        if k == "zone":
            label = "Geographic Sector"
        else:
            f_def = fields_dict.get(k, {})
            label = f_def.get("label", k.title())

        vals = v if isinstance(v, list) else [str(v)]
        active_badges.append({"key": k, "label": label, "values": vals})

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
        # API: Return all facilities / points
        if self.path in ["/api/facilities", "/api/points", "/api/sites", "/api/data"]:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            data = load_dataset()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            return

        # API: Return active configuration
        elif self.path in ["/api/config", "/api/schema", "/api/filters_config"]:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            cfg = load_config()
            self.wfile.write(json.dumps(cfg, ensure_ascii=False).encode("utf-8"))
            return

        # API: Return territory GeoJSON vector map (Land & Sea)
        elif self.path == "/api/territory_geojson":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            geo_file = STATIC_DIR / "territory.geojson"
            if geo_file.exists():
                with open(geo_file, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.wfile.write(b'{"type":"FeatureCollection","features":[]}')
            return

        # API: Health check
        elif self.path == "/api/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            resp = {
                "status": "ok",
                "app": "General GIS Template Sandbox",
                "points_count": len(load_dataset()),
                "filters_count": len(load_config().get("filter_fields", []))
            }
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

        # API: Generate procedural random points across the territory
        elif self.path == "/api/generate_points":
            try:
                payload = json.loads(post_data) if post_data else {}
                count = int(payload.get("count", 40))
                count = max(10, min(150, count))
                cfg = load_config()
                new_points = generate_procedural_points(count, cfg)
                save_dataset(new_points)

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "success",
                    "count": len(new_points),
                    "points": new_points
                }, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        # API: Clear all points from the map
        elif self.path == "/api/clear_points":
            try:
                save_dataset([])
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success", "count": 0}, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        # API: Add new user-defined filter field
        elif self.path == "/api/add_filter":
            try:
                payload = json.loads(post_data)
                label = payload.get("label", "").strip()
                if not label:
                    raise ValueError("Filter name cannot be empty.")

                raw_key = payload.get("key") or label.lower()
                key = re.sub(r'[^a-zA-Z0-9_]', '_', strip_accents(raw_key.lower()))

                options = [opt.strip() for opt in payload.get("options", []) if opt.strip()]
                if not options:
                    options = ["Option A", "Option B", "Option C"]

                colors = {}
                for idx, opt in enumerate(options):
                    colors[opt] = COLOR_PALETTE[idx % len(COLOR_PALETTE)]

                cfg = load_config()
                existing = next((f for f in cfg.get("filter_fields", []) if f["key"] == key), None)
                field_entry = {
                    "key": key,
                    "label": label,
                    "type": payload.get("type", "select"),
                    "options": options,
                    "colors": colors,
                    "synonyms": {}
                }

                if existing:
                    existing.update(field_entry)
                else:
                    cfg.setdefault("filter_fields", []).append(field_entry)

                save_config(cfg)

                # Populate property on existing points if any
                dataset = load_dataset()
                for pt in dataset:
                    if key not in pt or not pt[key]:
                        pt[key] = random.choice(options)
                save_dataset(dataset)

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success", "field": field_entry, "config": cfg}, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        # API: Delete filter field
        elif self.path == "/api/delete_filter":
            try:
                payload = json.loads(post_data)
                key = payload.get("key", "").strip()
                cfg = load_config()
                cfg["filter_fields"] = [f for f in cfg.get("filter_fields", []) if f["key"] != key]
                save_config(cfg)

                dataset = load_dataset()
                for pt in dataset:
                    pt.pop(key, None)
                save_dataset(dataset)

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success", "config": cfg}, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        # API: Add an option to an existing filter field
        elif self.path == "/api/add_option":
            try:
                payload = json.loads(post_data)
                key = payload.get("key")
                option = payload.get("option", "").strip()
                if not option:
                    raise ValueError("Option value cannot be empty.")

                cfg = load_config()
                field = next((f for f in cfg.get("filter_fields", []) if f["key"] == key), None)
                if not field:
                    raise ValueError(f"Filter with key '{key}' not found.")

                if option not in field["options"]:
                    field["options"].append(option)
                    if "colors" not in field:
                        field["colors"] = {}
                    field["colors"][option] = COLOR_PALETTE[len(field["options"]) % len(COLOR_PALETTE)]
                    save_config(cfg)

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success", "field": field}, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        # API: Switch Preset (energy, smartcity, custom) without auto-generating points
        elif self.path == "/api/preset":
            try:
                payload = json.loads(post_data)
                preset_id = payload.get("preset", "energy")
                generate = payload.get("generate", False)
                count = int(payload.get("count", 40))

                if preset_id not in PRESETS:
                    raise ValueError(f"Unknown preset: {preset_id}")

                new_cfg = json.loads(json.dumps(PRESETS[preset_id]))
                save_config(new_cfg)

                if generate:
                    new_points = generate_procedural_points(count, new_cfg)
                    save_dataset(new_points)
                else:
                    new_points = []
                    save_dataset(new_points)

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "success",
                    "preset": preset_id,
                    "config": new_cfg,
                    "points": new_points
                }, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        # API: Save raw configuration
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

        # API: Reset to factory defaults (empty map and no domain selected)
        elif self.path == "/api/reset":
            try:
                new_cfg = json.loads(json.dumps(EMPTY_CONFIG))
                save_config(new_cfg)
                save_dataset([])

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "reset_successful",
                    "config": new_cfg,
                    "points": []
                }, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()


def run_server(port: int = 8085, host: str = "0.0.0.0"):
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    load_config()
    load_dataset()

    server = ThreadingHTTPServer((host, port), GenericGISHandler)
    print("=" * 76)
    print(" 🌍 Elsevier SoftwareX — General-Purpose GIS Architecture Template")
    print(" 🛠️  Domain-Agnostic Conversational Spatial Search Sandbox (100% Offline)")
    print("=" * 76)
    print(f" [*] HTTP Server active on: http://{host}:{port}/")
    print(f" [*] Local access URL:     http://localhost:{port}/")
    print(f" [*] Active territory:     {load_config().get('territory', {}).get('name')}")
    print(f" [*] Dataset objects:      {len(load_dataset())} points (On-demand population)")
    print(f" [*] Active filter fields: {len(load_config().get('filter_fields', []))} dimensions")
    print(f" [*] Map tiles engine:     Custom Vector GeoJSON (No external API keys)")
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
