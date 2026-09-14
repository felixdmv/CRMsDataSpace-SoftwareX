"""
Search Engine Client & Apache Solr Connector for SoftwareX:
Supports production Apache Solr / SolrCloud clusters via HTTP REST API (SOLR_URL)
with automatic fallback to the zero-setup standalone synthetic dataset (synthetic_escombreras_europe.json).
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

DATA_FILE = Path(__file__).resolve().parent / "data" / "synthetic_escombreras_europe.json"

_DATASET_CACHE: List[Dict[str, Any]] = []

def load_dataset() -> List[Dict[str, Any]]:
    global _DATASET_CACHE
    if not _DATASET_CACHE:
        if DATA_FILE.exists():
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                _DATASET_CACHE = json.load(f)
        else:
            print(f"[Warning] Dataset file not found at {DATA_FILE}")
            _DATASET_CACHE = []
    return _DATASET_CACHE

def query_solr_cloud(solr_base_url: str, q: str = "*:*", fq: List[str] = None) -> Optional[Dict[str, Any]]:
    """
    Executes search query directly against an Apache Solr / SolrCloud collection via HTTP REST API (/select).
    Retrieves matching document records, Solr scores, and multi-dimensional facets.
    """
    if fq is None:
        fq = []

    base = solr_base_url.rstrip("/")
    collection = os.getenv("SOLR_COLLECTION", "").strip()
    if collection and not base.endswith(collection):
        base = f"{base}/{collection}"

    select_url = base if base.endswith("/select") else f"{base}/select"
    timeout = float(os.getenv("SOLR_TIMEOUT", "5.0"))
    rows = int(os.getenv("SOLR_ROWS", "1000"))

    # Solr REST parameters
    params = [
        ("q", q if q else "*:*"),
        ("wt", "json"),
        ("rows", str(rows)),
        ("facet", "true"),
        ("facet.field", "country"),
        ("facet.field", "commodities"),
        ("facet.field", "storage_facility_type"),
        ("facet.field", "project_status"),
    ]
    for rule in fq:
        params.append(("fq", rule))

    try:
        try:
            import requests
            resp = requests.get(select_url, params=params, timeout=timeout)
            if resp.status_code != 200:
                print(f"[SolrCloud] Warning: Server returned status {resp.status_code}: {resp.text[:180]}")
                return None
            data = resp.json()
        except ImportError:
            import urllib.request
            import urllib.parse
            query_string = urllib.parse.urlencode(params)
            req = urllib.request.Request(f"{select_url}?{query_string}")
            with urllib.request.urlopen(req, timeout=timeout) as response:
                data = json.loads(response.read().decode("utf-8"))

        response_block = data.get("response", {})
        docs = response_block.get("docs", [])
        num_found = response_block.get("numFound", len(docs))

        # Format Solr facet fields [val1, cnt1, val2, cnt2, ...] into mapping
        raw_facets = data.get("facet_counts", {}).get("facet_fields", {})
        parsed_facets = {
            "country": {},
            "commodities": {},
            "facility_type": {},
            "status": {}
        }
        for field, raw_list in raw_facets.items():
            norm_key = "facility_type" if "facility" in field.lower() else ("status" if "status" in field.lower() else field.lower())
            field_dict = {}
            if isinstance(raw_list, list):
                for i in range(0, len(raw_list), 2):
                    if i + 1 < len(raw_list):
                        field_dict[str(raw_list[i])] = raw_list[i + 1]
            elif isinstance(raw_list, dict):
                field_dict = raw_list
            parsed_facets[norm_key] = field_dict

        # Ensure docs have consistent score and id attributes
        for d in docs:
            if "score" not in d:
                d["score"] = 0.98 if fq else 0.85

        return {
            "numFound": num_found,
            "totalDatasetSize": num_found,
            "docs": docs,
            "facets": parsed_facets,
            "engine": "solr_cloud"
        }
    except Exception as e:
        print(f"[SolrCloud] Connection to '{select_url}' failed ({e}). Falling back to standalone mock engine.")
        return None

def query_data_space_solr(q: str = "*:*", fq: List[str] = None) -> Dict[str, Any]:
    """
    Retrieves spatial CRM records from Apache Solr (SolrCloud / Standalone) if SOLR_URL is configured,
    or from the local zero-setup synthetic European CRM dataset (Standalone Mock Mode).
    """
    solr_url = os.getenv("SOLR_URL", "").strip()
    if solr_url:
        cloud_res = query_solr_cloud(solr_url, q=q, fq=fq)
        if cloud_res is not None:
            return cloud_res

    dataset = load_dataset()
    if fq is None:
        fq = []

    # Parse filter queries (fq)
    filter_rules = {}
    for rule in fq:
        if ":" in rule:
            field, raw_vals = rule.split(":", 1)
            raw_vals = raw_vals.strip("()")
            # split OR values
            vals = [v.strip().strip('"').lower() for v in raw_vals.split(" OR ")]
            filter_rules[field.lower()] = vals

    matched_sites = []

    for site in dataset:
        matches = True

        # Check country filter
        if "country" in filter_rules:
            site_c = site.get("country", "").lower()
            if site_c not in filter_rules["country"]:
                matches = False

        # Check region filter
        if "region" in filter_rules and matches:
            site_r = site.get("region", "").lower()
            if site_r not in filter_rules["region"]:
                matches = False

        # Check commodities filter
        if "commodities" in filter_rules and matches:
            site_comms = [c.lower() for c in site.get("commodities", [])]
            target_comms = filter_rules["commodities"]
            if not any(tc in site_comms for tc in target_comms):
                matches = False

        # Check storage facility type
        if "storage_facility_type" in filter_rules and matches:
            site_st = site.get("storage_facility_type", "").lower()
            target_st = filter_rules["storage_facility_type"]
            if not any(ts in site_st for ts in target_st):
                matches = False

        # Check project status
        if "project_status" in filter_rules and matches:
            site_ps = site.get("project_status", "").lower()
            if site_ps not in filter_rules["project_status"]:
                matches = False

        # Check restored
        if "restored" in filter_rules and matches:
            target_rest = filter_rules["restored"][0] == "true"
            if site.get("restored") != target_rest:
                matches = False

        if matches:
            site_copy = dict(site)
            site_copy["score"] = 0.98 if len(fq) > 0 else 0.85
            matched_sites.append(site_copy)

    # Fallback to core filters (country & commodity) if combined filters yield 0 sites
    if len(matched_sites) == 0 and len(fq) > 1:
        for site in dataset:
            core_match = True
            if "country" in filter_rules:
                if site.get("country", "").lower() not in filter_rules["country"]:
                    core_match = False
            if "commodities" in filter_rules and core_match:
                site_comms = [c.lower() for c in site.get("commodities", [])]
                if not any(tc in site_comms for tc in filter_rules["commodities"]):
                    core_match = False
            if core_match:
                site_copy = dict(site)
                site_copy["score"] = 0.75
                matched_sites.append(site_copy)

    # Compute Solr Facets
    facet_countries = {}
    facet_commodities = {}
    facet_facility_types = {}
    facet_statuses = {}

    for s in matched_sites:
        c = s.get("country_name", s.get("country", ""))
        facet_countries[c] = facet_countries.get(c, 0) + 1

        for cm in s.get("commodities", []):
            facet_commodities[cm] = facet_commodities.get(cm, 0) + 1

        ft = s.get("storage_facility_label", s.get("storage_facility_type", ""))
        facet_facility_types[ft] = facet_facility_types.get(ft, 0) + 1

        st = s.get("project_status", "")
        facet_statuses[st] = facet_statuses.get(st, 0) + 1

    return {
        "numFound": len(matched_sites),
        "totalDatasetSize": len(dataset),
        "docs": matched_sites,
        "facets": {
            "country": facet_countries,
            "commodities": facet_commodities,
            "facility_type": facet_facility_types,
            "status": facet_statuses
        },
        "engine": "standalone_mock"
    }
