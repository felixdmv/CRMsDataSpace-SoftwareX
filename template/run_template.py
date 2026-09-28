#!/usr/bin/env python3
"""
General-Purpose GIS Architecture Template Server:
Elsevier SoftwareX Demonstrator — Domain-Agnostic Conversational Spatial Search.

Features:
- Zero external dependencies: Runs on Python 3.9+ standard library.
- Dynamic Sandbox: Users create their own custom filters and categories freely.
- Procedural Point Generator: Distributes random points with dynamic attributes across the geographic zone.
- Decoupled 4-Stage Architecture Pipeline:
    Stage 1: Dynamic Conversational NLU & Token Extraction
    Stage 2: Deterministic Schema Validation & Normalization
    Stage 3: Apache Solr-Style Boolean Filter Builder & Live Facet Indexer
    Stage 4: Leaflet Cartographic Dynamic Synchronization
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

# Built-in Presets for 1-click domain switching
PRESETS: Dict[str, Dict[str, Any]] = {
    "adventure": {
        "title": "Archipiélago Avalon — Aventura y Rol",
        "description": "Exploración de santuarios, castillos y enclaves insulares.",
        "active_preset": "adventure",
        "territory": {
            "name": "Archipiélago Avalon",
            "description": "Territorio insular con costas escarpadas, valles y cordilleras.",
            "center": [28.28, -16.48],
            "zoom": 10.5,
            "zones": [
                {"name": "Costa Norte", "lat": 28.44, "lon": -16.42, "color": "#06b6d4", "desc": "Litoral con acantilados y puertos pesqueros"},
                {"name": "Tierras Altas", "lat": 28.30, "lon": -16.52, "color": "#8b5cf6", "desc": "Mesetas y macizos montañosos centrales"},
                {"name": "Bahía Sur", "lat": 28.17, "lon": -16.62, "color": "#f59e0b", "desc": "Aguas calmas, playas y ensenadas abrigadas"},
                {"name": "Valle Esmeralda", "lat": 28.32, "lon": -16.70, "color": "#10b981", "desc": "Cuenca fértil con densa vegetación y manantiales"},
                {"name": "Sector Oriental", "lat": 28.26, "lon": -16.25, "color": "#ec4899", "desc": "Archipiélago de islotes rocosos y arrecifes"}
            ]
        },
        "filter_fields": [
            {
                "key": "tipo",
                "label": "Tipo de Lugar",
                "type": "multiselect",
                "options": ["Castillo", "Mina abandonada", "Templo místico", "Puerto pirata", "Refugio"],
                "colors": {
                    "Castillo": "#3b82f6",
                    "Mina abandonada": "#f59e0b",
                    "Templo místico": "#8b5cf6",
                    "Puerto pirata": "#06b6d4",
                    "Refugio": "#10b981"
                },
                "synonyms": {
                    "castillo": ["castillo", "castillos", "fortaleza", "torre", "castle", "castles", "fortress"],
                    "mina abandonada": ["mina", "minas", "mina abandonada", "cantera", "mine", "mines"],
                    "templo místico": ["templo", "templos", "santuario", "templo mistico", "shrine", "temple", "temples"],
                    "puerto pirata": ["puerto", "puertos", "muelle", "embarcadero", "port", "harbor"],
                    "refugio": ["refugio", "refugios", "albergue", "campamento", "shelter", "refuge", "camp"]
                }
            },
            {
                "key": "faccion",
                "label": "Facción Dominante",
                "type": "select",
                "options": ["Guardianes", "Mercaderes", "Exploradores", "Rebeldes"],
                "colors": {
                    "Guardianes": "#3b82f6",
                    "Mercaderes": "#10b981",
                    "Exploradores": "#f59e0b",
                    "Rebeldes": "#ef4444"
                },
                "synonyms": {
                    "guardianes": ["guardianes", "guardian", "guardianes del reino", "guardians"],
                    "mercaderes": ["mercaderes", "mercader", "comerciantes", "merchants", "traders"],
                    "exploradores": ["exploradores", "explorador", "rastreadores", "explorers", "scouts"],
                    "rebeldes": ["rebeldes", "rebelde", "insurgentes", "rebels"]
                }
            },
            {
                "key": "peligro",
                "label": "Nivel de Peligro",
                "type": "select",
                "options": ["Seguro", "Moderado", "Peligroso", "Crítico"],
                "colors": {
                    "Seguro": "#10b981",
                    "Moderado": "#f59e0b",
                    "Peligroso": "#f97316",
                    "Crítico": "#ef4444"
                },
                "synonyms": {
                    "seguro": ["seguro", "segura", "tranquilo", "pacifico", "safe", "secure"],
                    "moderado": ["moderado", "medio", "alerta", "moderate"],
                    "peligroso": ["peligroso", "alto peligro", "amenaza", "dangerous", "perilous"],
                    "crítico": ["critico", "crítico", "extremo", "mortal", "critical", "extreme"]
                }
            }
        ]
    },
    "smartcity": {
        "title": "Distrito Metropolitano Nova — Smart City",
        "description": "Gestión de infraestructuras públicas, servicios urbanos y movilidad.",
        "active_preset": "smartcity",
        "territory": {
            "name": "Distrito Metropolitano Nova",
            "description": "Área urbana y metropolitana dividida en 5 sectores de servicio.",
            "center": [28.28, -16.48],
            "zoom": 10.5,
            "zones": [
                {"name": "Sector Norte", "lat": 28.44, "lon": -16.42, "color": "#06b6d4", "desc": "Distrito financiero y campus universitario"},
                {"name": "Sector Central", "lat": 28.30, "lon": -16.52, "color": "#8b5cf6", "desc": "Casco histórico y eje administrativo"},
                {"name": "Sector Sur", "lat": 28.17, "lon": -16.62, "color": "#f59e0b", "desc": "Área residencial y corredor comercial costero"},
                {"name": "Sector Oeste", "lat": 28.32, "lon": -16.70, "color": "#10b981", "desc": "Parque tecnológico y pulmón verde metropolitano"},
                {"name": "Sector Este", "lat": 28.26, "lon": -16.25, "color": "#ec4899", "desc": "Polígono logístico e intermodal portuario"}
            ]
        },
        "filter_fields": [
            {
                "key": "equipamiento",
                "label": "Tipo de Equipamiento",
                "type": "multiselect",
                "options": ["Hospital", "Parque Verde", "Estación de Metro", "Escuela Pública", "Comisaría"],
                "colors": {
                    "Hospital": "#ef4444",
                    "Parque Verde": "#10b981",
                    "Estación de Metro": "#3b82f6",
                    "Escuela Pública": "#f59e0b",
                    "Comisaría": "#8b5cf6"
                },
                "synonyms": {
                    "hospital": ["hospital", "hospitales", "clinica", "salud", "sanitario"],
                    "parque verde": ["parque", "parques", "jardin", "area verde", "zona verde"],
                    "estación de metro": ["metro", "estacion", "transporte", "parada", "intercambiador"],
                    "escuela pública": ["escuela", "colegio", "instituto", "educacion"],
                    "comisaría": ["comisaria", "comisaría", "policia", "seguridad"]
                }
            },
            {
                "key": "estado",
                "label": "Estado del Servicio",
                "type": "select",
                "options": ["Operativo", "En Mantenimiento", "Planificado"],
                "colors": {
                    "Operativo": "#10b981",
                    "En Mantenimiento": "#f59e0b",
                    "Planificado": "#3b82f6"
                },
                "synonyms": {
                    "operativo": ["operativo", "activo", "abierto", "funcionando"],
                    "en mantenimiento": ["mantenimiento", "obras", "reparacion", "cerrado temporalmente"],
                    "planificado": ["planificado", "proyecto", "futuro", "en construccion"]
                }
            },
            {
                "key": "prioridad",
                "label": "Nivel de Prioridad",
                "type": "select",
                "options": ["Urgente", "Normal", "Baja"],
                "colors": {
                    "Urgente": "#ef4444",
                    "Normal": "#3b82f6",
                    "Baja": "#64748b"
                },
                "synonyms": {
                    "urgente": ["urgente", "alta", "prioritario", "critico"],
                    "normal": ["normal", "estandar", "media"],
                    "baja": ["baja", "secundaria", "opcional"]
                }
            }
        ]
    },
    "infrastructure": {
        "title": "Cuenca Energética Avalon — Infraestructura",
        "description": "Monitorización de activos energéticos, red eléctrica y calificaciones ESG.",
        "active_preset": "infrastructure",
        "territory": {
            "name": "Cuenca Energética Avalon",
            "description": "Red de generación distribuida insular en 5 nodos de evacuación.",
            "center": [28.28, -16.48],
            "zoom": 10.5,
            "zones": [
                {"name": "Costa Norte", "lat": 28.44, "lon": -16.42, "color": "#06b6d4", "desc": "Corredor eólico marítimo"},
                {"name": "Tierras Altas", "lat": 28.30, "lon": -16.52, "color": "#8b5cf6", "desc": "Saltos hidroeléctricos y bombeo"},
                {"name": "Bahía Sur", "lat": 28.17, "lon": -16.62, "color": "#f59e0b", "desc": "Plantas fotovoltaicas de gran escala"},
                {"name": "Valle Esmeralda", "lat": 28.32, "lon": -16.70, "color": "#10b981", "desc": "Instalaciones de biomasa y microrredes"},
                {"name": "Sector Oriental", "lat": 28.26, "lon": -16.25, "color": "#ec4899", "desc": "Complejo de baterías y almacenamiento"}
            ]
        },
        "filter_fields": [
            {
                "key": "tecnologia",
                "label": "Tecnología de Generación",
                "type": "multiselect",
                "options": ["Parque Solar", "Parque Eólico", "Presa Hidroeléctrica", "Batería BESS"],
                "colors": {
                    "Parque Solar": "#f59e0b",
                    "Parque Eólico": "#06b6d4",
                    "Presa Hidroeléctrica": "#3b82f6",
                    "Batería BESS": "#8b5cf6"
                },
                "synonyms": {
                    "parque solar": ["solar", "fotovoltaica", "pv", "paneles solares"],
                    "parque eólico": ["eolica", "eólica", "aerogeneradores", "viento", "wind"],
                    "presa hidroeléctrica": ["hidro", "hidroelectrica", "presa", "embalse", "hydro"],
                    "batería bess": ["bateria", "batería", "almacenamiento", "bess", "battery"]
                }
            },
            {
                "key": "estado_red",
                "label": "Conexión a Red",
                "type": "select",
                "options": ["Sincronizada", "Aislada / Isla", "En Pruebas"],
                "colors": {
                    "Sincronizada": "#10b981",
                    "Aislada / Isla": "#f59e0b",
                    "En Pruebas": "#3b82f6"
                },
                "synonyms": {
                    "sincronizada": ["sincronizada", "conectada", "en servicio", "activa"],
                    "aislada / isla": ["aislada", "isla", "autonoma", "desconectada"],
                    "en pruebas": ["pruebas", "comisionado", "testing"]
                }
            },
            {
                "key": "esg",
                "label": "Calificación ESG",
                "type": "select",
                "options": ["Clase A", "Clase B", "Clase C"],
                "colors": {
                    "Clase A": "#10b981",
                    "Clase B": "#f59e0b",
                    "Clase C": "#ef4444"
                },
                "synonyms": {
                    "clase a": ["clase a", "grado a", "a", "excelente"],
                    "clase b": ["clase b", "grado b", "b", "medio"],
                    "clase c": ["clase c", "grado c", "c", "bajo"]
                }
            }
        ]
    },
    "empty": {
        "title": "Territorio Abierto — Plantilla en Blanco",
        "description": "Crea tus propios filtros desde cero usando el panel interactivo.",
        "active_preset": "empty",
        "territory": {
            "name": "Archipiélago Avalon",
            "description": "Territorio libre para definir tus propios filtros y categorías.",
            "center": [28.28, -16.48],
            "zoom": 10.5,
            "zones": [
                {"name": "Costa Norte", "lat": 28.44, "lon": -16.42, "color": "#06b6d4", "desc": "Sector Septentrional"},
                {"name": "Tierras Altas", "lat": 28.30, "lon": -16.52, "color": "#8b5cf6", "desc": "Macizo Central"},
                {"name": "Bahía Sur", "lat": 28.17, "lon": -16.62, "color": "#f59e0b", "desc": "Sector Meridional"},
                {"name": "Valle Esmeralda", "lat": 28.32, "lon": -16.70, "color": "#10b981", "desc": "Sector Occidental"},
                {"name": "Sector Oriental", "lat": 28.26, "lon": -16.25, "color": "#ec4899", "desc": "Sector Oriental"}
            ]
        },
        "filter_fields": []
    }
}

COLOR_PALETTE = [
    "#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899",
    "#06b6d4", "#f97316", "#14b8a6", "#6366f1", "#84cc16"
]

def strip_accents(text: str) -> str:
    accents = {'á':'a', 'é':'e', 'í':'i', 'ó':'o', 'ú':'u', 'ü':'u', 'ñ':'n'}
    for k, v in accents.items():
        text = text.replace(k, v)
    return text

def get_word_variants(word: str) -> List[str]:
    w = word.strip().lower()
    variants = {w, strip_accents(w)}
    if w.endswith('es'):
        variants.add(w[:-2])
        variants.add(strip_accents(w[:-2]))
    elif w.endswith('s'):
        variants.add(w[:-1])
        variants.add(strip_accents(w[:-1]))
    else:
        variants.add(w + 's')
        variants.add(w + 'es')
        variants.add(strip_accents(w + 's'))
    return [v for v in variants if len(v) >= 3]


# ==============================================================================
# PROCEDURAL OBJECT & DATASET GENERATOR
# ==============================================================================

def generate_procedural_points(count: int, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Procedurally generates spatial points distributed across the geographic zone
    using random combinations of the active user-defined filter dimensions.
    """
    territory = config.get("territory", {})
    zones = territory.get("zones", [
        {"name": "Costa Norte", "lat": 28.44, "lon": -16.42},
        {"name": "Tierras Altas", "lat": 28.30, "lon": -16.52},
        {"name": "Bahía Sur", "lat": 28.17, "lon": -16.62},
        {"name": "Valle Esmeralda", "lat": 28.32, "lon": -16.70},
        {"name": "Sector Oriental", "lat": 28.26, "lon": -16.25}
    ])
    filter_fields = config.get("filter_fields", [])

    points: List[Dict[str, Any]] = []

    for i in range(1, count + 1):
        zone = random.choice(zones)
        # Jitter coordinates inside zone landmass
        lat = round(zone["lat"] + random.uniform(-0.045, 0.045), 5)
        lon = round(zone["lon"] + random.uniform(-0.055, 0.055), 5)

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
        first_val = props.get(first_field["key"]) if first_field else "Punto"
        if isinstance(first_val, list):
            first_val = first_val[0]

        name = f"{first_val} de {zone['name']} #{i:02d}"

        # Generate descriptive sentence reflecting all assigned properties
        desc_parts = [f"{f.get('label', f.get('key'))}: {props.get(f.get('key'))}" for f in filter_fields if f.get("key") in props]
        if desc_parts:
            description = f"Ubicado en {zone['name']}. Atributos: {'; '.join(desc_parts)}."
        else:
            description = f"Punto georreferenciado en {zone['name']}."

        point = {
            "id": f"OBJ-{i:03d}",
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
        if not _DATASET:
            cfg = load_config()
            _DATASET = generate_procedural_points(40, cfg)
            save_dataset(_DATASET)
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
            _CONFIG = PRESETS["adventure"]
            save_config(_CONFIG)
    return _CONFIG

def save_config(new_config: Dict[str, Any]) -> None:
    global _CONFIG
    _CONFIG = new_config
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(new_config, f, indent=2, ensure_ascii=False)


# ==============================================================================
# STAGE 1 & 2: DYNAMIC CONVERSATIONAL NLU & SCHEMA NORMALIZER
# ==============================================================================

def parse_conversational_query(query: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Translates raw conversational user input into a validated filter dictionary
    based on the current dynamic filter dimensions, options, synonyms, and territory zones.
    """
    q_lower = query.lower()
    q_norm = strip_accents(q_lower)
    extracted_filters: Dict[str, Any] = {}
    matched_tokens: List[str] = []

    # Greeting / Help intent patterns
    greeting_patterns = [r'\bhola\b', r'\bhello\b', r'\bhi\b', r'\bbuenos d[ií]as\b', r'\bbuenas\b']
    help_patterns = [r'ayuda\b', r'help\b', r'c[oó]mo funciona', r'qu[eé] puedes hacer', r'qu[eé] es esto']
    is_greeting = any(re.search(pat, q_lower) for pat in greeting_patterns)
    is_help = any(re.search(pat, q_lower) for pat in help_patterns)

    # 1. Check territory zones
    zones = config.get("territory", {}).get("zones", [])
    for z in zones:
        z_name = z["name"]
        z_norm = strip_accents(z_name.lower())
        pattern = r'\b' + re.escape(z_norm) + r'\b'
        if re.search(pattern, q_norm):
            extracted_filters["zone"] = z_name
            matched_tokens.append(z_name)
            break

    # 2. Check each dynamic filter field defined by user
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
                    # Find actual option casing
                    matched_opt = next((opt for opt in options if strip_accents(opt.lower()) == strip_accents(canon_opt.lower())), canon_opt)
                    if matched_opt not in field_matches:
                        field_matches.append(matched_opt)
                    matched_tokens.append(syn)
                    break

        # Check options directly with morphological plural/accent variants
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
        if any(w in q_lower for w in ["todo", "todos", "todas", "all", "dataset", "mostrar todo", "show all"]):
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

    # Compute live Solr facets for all user filter fields + zone
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
    Synthesizes a grounded natural language response explaining the spatial query results.
    """
    num_found = results.get("num_found", 0)
    total = results.get("total_dataset", len(load_dataset()))
    docs = results.get("matched_docs", [])
    territory_name = config.get("territory", {}).get("name", "la región")

    if intent == "generic_qa" and not filters:
        filter_count = len(config.get("filter_fields", []))
        return (
            f"👋 **Bienvenido a la Plantilla GIS de Propósito General (SoftwareX).**\n\n"
            f"Este entorno experimental demuestra cómo la **arquitectura desacoplada de 4 etapas (NLU $\\to$ Solr $\\to$ GIS)** "
            f"funciona sobre **cualquier dominio cartográfico**, adaptándose en tiempo real a los filtros que tú crees.\n\n"
            f"### 🚀 Flujo Interactivo de la Plantilla:\n"
            f"1. **Paso 1: Define tus filtros**: Crea dimensiones personalizadas o carga un preset (Aventura, Smart City, Energía).\n"
            f"2. **Paso 2: Genera puntos aleatorios**: Haz clic en *\"🎲 Generar Puntos en el Mapa\"* para poblar **{territory_name}** con objetos combinando tus filtros.\n"
            f"3. **Paso 3: Busca de forma conversacional**: Escribe consultas libres como *\"castillos con peligro crítico\"* o usa los filtros manuales.\n"
            f"4. **Inspecciona las 4 etapas**: Observa en el panel inferior la tokenización NLU, la consulta booleana Solr ($fq$) y la sincronización dinámica en Leaflet."
        )

    if num_found == 0:
        return (
            f"🔍 **Sin coincidencias para los criterios activos:**\n"
            f"Ningún punto en **{territory_name}** cumple simultáneamente todas las restricciones seleccionadas.\n\n"
            f"💡 *Sugerencia: Haz clic en una etiqueta de filtro para relajarla o prueba a buscar otra categoría.*"
        )

    # Summarize matched items by first filter and by zone
    fields = config.get("filter_fields", [])
    primary_field = fields[0]["key"] if fields else "zone"
    field_label = fields[0].get("label", primary_field) if fields else "Zona"

    summary: Dict[str, int] = {}
    zone_summary: Dict[str, int] = {}
    for d in docs:
        val = d.get(primary_field)
        if isinstance(val, list):
            val = ", ".join(val)
        summary[str(val)] = summary.get(str(val), 0) + 1
        z = d.get("zone", "Territorio")
        zone_summary[z] = zone_summary.get(z, 0) + 1

    summary_str = ", ".join([f"{k} ({v})" for k, v in summary.items()])
    zones_str = ", ".join([f"{k} ({v})" for k, v in zone_summary.items()])
    featured = docs[0]

    pct = round(num_found / total * 100, 1) if total else 100
    narrative = (
        f"✅ **Se han identificado {num_found} de {total} objetos ({pct}%) en {territory_name}:**\n\n"
        f"- 📌 **Desglose por {field_label}**: {summary_str}.\n"
        f"- 🗺️ **Sectores biogeográficos**: {zones_str}.\n"
        f"- 🌟 **Punto destacado**: **{featured.get('name')}** (Zona: *{featured.get('zone')}*).\n\n"
        f"*(Los marcadores coincidentes se han resaltado en Leaflet con anillos de pulso luminosos y etiquetas sincronizadas).* "
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
            label = "Sector / Zona"
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

        # API: Return available presets list
        elif self.path == "/api/presets":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            presets_summary = [
                {"id": k, "title": v.get("title"), "description": v.get("description"), "fields_count": len(v.get("filter_fields", []))}
                for k, v in PRESETS.items()
            ]
            self.wfile.write(json.dumps(presets_summary, ensure_ascii=False).encode("utf-8"))
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

        # API: Add new user-defined filter field
        elif self.path == "/api/add_filter":
            try:
                payload = json.loads(post_data)
                label = payload.get("label", "").strip()
                if not label:
                    raise ValueError("El nombre del filtro no puede estar vacío.")

                raw_key = payload.get("key") or label.lower()
                key = re.sub(r'[^a-zA-Z0-9_]', '_', strip_accents(raw_key.lower()))

                options = [opt.strip() for opt in payload.get("options", []) if opt.strip()]
                if not options:
                    options = ["Opción A", "Opción B", "Opción C"]

                colors = {}
                for idx, opt in enumerate(options):
                    colors[opt] = COLOR_PALETTE[idx % len(COLOR_PALETTE)]

                cfg = load_config()
                # Check if field key exists; update or append
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

                # Assign random values for this new property to current points if any
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

        # API: Delete user-defined filter field
        elif self.path == "/api/delete_filter":
            try:
                payload = json.loads(post_data)
                key = payload.get("key", "").strip()
                cfg = load_config()
                cfg["filter_fields"] = [f for f in cfg.get("filter_fields", []) if f["key"] != key]
                save_config(cfg)

                # Clean up property in dataset
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
                    raise ValueError("La opción no puede estar vacía.")

                cfg = load_config()
                field = next((f for f in cfg.get("filter_fields", []) if f["key"] == key), None)
                if not field:
                    raise ValueError(f"Filtro con clave '{key}' no encontrado.")

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

        # API: Load preset (adventure, smartcity, infrastructure, empty)
        elif self.path == "/api/preset":
            try:
                payload = json.loads(post_data)
                preset_id = payload.get("preset", "adventure")
                count = int(payload.get("count", 40))
                if preset_id not in PRESETS:
                    raise ValueError(f"Preset desconocido: {preset_id}")

                new_cfg = json.loads(json.dumps(PRESETS[preset_id]))
                save_config(new_cfg)

                new_points = generate_procedural_points(count, new_cfg)
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

        # API: Reset to factory defaults
        elif self.path == "/api/reset":
            try:
                new_cfg = json.loads(json.dumps(PRESETS["adventure"]))
                save_config(new_cfg)
                new_points = generate_procedural_points(40, new_cfg)
                save_dataset(new_points)

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "reset_successful",
                    "config": new_cfg,
                    "points": new_points
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
    print(" 🛠️  Domain-Agnostic Conversational Spatial Search & Procedural Sandbox")
    print("=" * 76)
    print(f" [*] HTTP Server active on: http://{host}:{port}/")
    print(f" [*] Local access URL:     http://localhost:{port}/")
    print(f" [*] Active territory:     {load_config().get('territory', {}).get('name')}")
    print(f" [*] Dataset objects:      {len(load_dataset())} points distributed")
    print(f" [*] Active filter fields: {len(load_config().get('filter_fields', []))} dimensions")
    print(f" [*] Zero external dependencies. Press Ctrl+C to terminate.")
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
