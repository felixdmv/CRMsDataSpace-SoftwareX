import json
import os
import unicodedata
from typing import Any, Dict, List

# Fake database of mining sites / waste facilities
MOCK_DATABASE = [
    {
        "id": "site_001",
        "site_name": "Riotinto Project",
        "country": "spain",
        "region": "andalucia",
        "lat": 37.69,
        "lon": -6.59,
        "commodities": ["copper", "silver", "gold"],
        "storage_facility_type": "tailings storage facility",
        "material_type": "tailings",
        "project_status": "active",
        "company": "Atalaya Mining",
        "unfc_e": "E1",
        "unfc_f": "F1",
        "unfc_g": "G1",
        "environmental_flags": [],
        "description": "Mina activa de cobre. Las balsas de estériles contienen trazas de metales preciosos."
    },
    {
        "id": "site_002",
        "site_name": "El Valle-Boinás",
        "country": "spain",
        "region": "asturias",
        "lat": 43.32,
        "lon": -6.32,
        "commodities": ["gold", "copper"],
        "storage_facility_type": "waste dump",
        "material_type": "waste rock",
        "project_status": "active",
        "company": "Orvana Minerals",
        "unfc_e": "E1",
        "unfc_f": "F2",
        "unfc_g": "G1",
        "environmental_flags": ["water contamination risk"],
        "description": "Mina de oro y cobre en el cinturón aurífero de Río Narcea. Escombreras con potencial de re-procesamiento."
    },
    {
        "id": "site_003",
        "site_name": "Los Santos",
        "country": "spain",
        "region": "castilla y leon",
        "lat": 40.55,
        "lon": -5.79,
        "commodities": ["tungsten"],
        "storage_facility_type": "waste dump",
        "material_type": "waste rock",
        "project_status": "care and maintenance",
        "company": "Almonty Industries",
        "unfc_e": "E2",
        "unfc_f": "F2",
        "unfc_g": "G2",
        "environmental_flags": [],
        "description": "Mina de wolframio (tungsteno) en Salamanca. Actualmente en mantenimiento, estudiando re-procesamiento de estériles."
    },
    {
        "id": "site_004",
        "site_name": "San Finx",
        "country": "spain",
        "region": "galicia",
        "lat": 42.75,
        "lon": -8.84,
        "commodities": ["tungsten", "tin"],
        "storage_facility_type": "pond",
        "material_type": "sludge",
        "project_status": "inactive",
        "company": "Valoriza Mineria",
        "unfc_e": "E3",
        "unfc_f": "F2",
        "unfc_g": "G3",
        "environmental_flags": ["acid mine drainage potential"],
        "description": "Antigua mina de wolframio y estaño. Hay balsas con potencial de re-procesamiento pero con retos ambientales."
    },
    {
        "id": "site_005",
        "site_name": "San José Valdeflórez",
        "country": "spain",
        "region": "extremadura",
        "lat": 39.46,
        "lon": -6.36,
        "commodities": ["lithium"],
        "storage_facility_type": "tailings storage facility",
        "material_type": "tailings",
        "project_status": "development",
        "company": "Infinity Lithium",
        "unfc_e": "E2",
        "unfc_f": "F1",
        "unfc_g": "G2",
        "environmental_flags": ["social opposition"],
        "description": "Gran proyecto de litio cerca de Cáceres. En fase de desarrollo, diseñado con almacenamiento subterráneo de relaves."
    }
]


def load_database() -> List[Dict[str, Any]]:
    warm_sites_path = os.path.join(os.path.dirname(__file__), "data", "warm_sites.json")
    combined = list(MOCK_DATABASE)
    if os.path.exists(warm_sites_path):
        with open(warm_sites_path, "r", encoding="utf-8") as handle:
            extra = json.load(handle)
            existing_ids = {s.get("id") for s in combined}
            for site in extra:
                if site.get("id") not in existing_ids:
                    combined.append(site)
    return combined


def values_match(site_values: Any, requested_values: List[str]) -> bool:
    if not requested_values:
        return True
    if site_values is None:
        return False
    if isinstance(site_values, (str, float, int, bool)):
        values = [str(site_values)]
    else:
        values = list(site_values)
    normalized_site_values = {normalize_lookup_value(value) for value in values if value is not None}
    normalized_requested = {normalize_lookup_value(value) for value in requested_values if value is not None}
    return bool(normalized_site_values.intersection(normalized_requested))


def normalize_lookup_value(value: Any) -> str:
    text = str(value).strip().lower()
    return "".join(
        char for char in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(char)
    )

def query_data_space_solr(q: str, fq: List[str]) -> List[Dict[str, Any]]:
    """
    Simulates querying Apache Solr using 'q' (main free-text query) and 'fq' (filter queries).
    """
    database = load_database()
    filtered = []

    # 1. Filter by fq (filter queries)
    for site in database:
        match_all = True
        for filter_str in fq:
            is_negated = filter_str.startswith("-")
            clean_filter = filter_str[1:] if is_negated else filter_str
            
            if ":" not in clean_filter:
                continue
            key, val_part = clean_filter.split(":", 1)
            key = key.strip()
            val_part = val_part.strip()
            
            # Extract values from val_part
            # e.g. "value" or (value1 OR value2) or true/false
            if val_part.startswith("(") and val_part.endswith(")"):
                inner = val_part[1:-1]
                raw_vals = [v.strip() for v in inner.split(" OR ")]
                vals = [v[1:-1] if v.startswith('"') and v.endswith('"') else v for v in raw_vals]
            else:
                vals = [val_part[1:-1] if val_part.startswith('"') and val_part.endswith('"') else val_part]
                
            # Map Solr filter query keys to database fields
            if key == "regions":
                site_val = [site.get("region"), site.get("province")]
            elif key == "countries":
                site_val = site.get("country")
            elif key == "storage_facility_types":
                site_val = site.get("storage_facility_type")
            elif key == "material_types":
                site_val = site.get("material_type") or site.get("material_types")
            elif key == "companies":
                site_val = site.get("company")
            elif key == "site_names":
                site_val = [site.get("site_name")] + site.get("aliases", [])
            else:
                site_val = site.get(key)
            
            # Special handling for restored (boolean)
            if key == "restored":
                target_bool = vals[0].lower() == "true"
                site_bool = bool(site_val) if site_val is not None else False
                has_match = site_bool == target_bool
            else:
                # site_val could be a list (like commodities) or a single value (like country)
                if isinstance(site_val, list):
                    site_set = {normalize_lookup_value(s) for s in site_val}
                else:
                    site_set = {normalize_lookup_value(site_val)} if site_val is not None else set()
                
                req_set = {normalize_lookup_value(v) for v in vals}
                has_match = bool(site_set.intersection(req_set))
                
            if is_negated:
                if has_match:
                    match_all = False
                    break
            else:
                if not has_match:
                    match_all = False
                    break
                    
        if match_all:
            filtered.append(site)
            
    # 2. Filter by q (main search query)
    if not q or q == "*:*":
        return filtered
        
    # Standard text search check: terms must match site text fields
    # Strip enclosing quotes for simple match if present
    clean_q = q
    if clean_q.startswith('"') and clean_q.endswith('"'):
        clean_q = clean_q[1:-1]
        
    q_words = [normalize_lookup_value(w) for w in clean_q.split() if w.strip()]
    if not q_words:
        return filtered
        
    final_results = []
    for site in filtered:
        # Build text representation of site
        text_block = " ".join([
            str(site.get("site_name", "")),
            str(site.get("description", "")),
            " ".join(site.get("commodities", [])),
            str(site.get("region", "")),
            str(site.get("country", "")),
            str(site.get("company", ""))
        ])
        norm_block = normalize_lookup_value(text_block)
        
        # Check if any query word matches (OR behavior)
        if any(word in norm_block for word in q_words):
            final_results.append(site)
            
    return final_results


def query_data_space(filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Mock function to simulate querying a database with extracted filters.
    """
    results = []
    
    # We will do a simple exact/partial match for the mock API.
    # If a filter is provided (non-empty list), the site must match at least one element of the filter array.
    
    for site in load_database():
        match = True
        
        if filters.get("countries"):
            if not values_match(site.get("country"), filters["countries"]):
                match = False
                
        if filters.get("commodities"):
            # If site has ANY of the requested commodities, we consider it a match
            site_comms = set(site.get("commodities", []))
            req_comms = set(filters["commodities"])
            if not site_comms.intersection(req_comms):
                match = False
                
        if filters.get("storage_facility_types"):
            if not values_match(site.get("storage_facility_type"), filters["storage_facility_types"]):
                match = False
                
        if filters.get("material_types"):
            if not values_match(site.get("material_type") or site.get("material_types"), filters["material_types"]):
                match = False
                
        if filters.get("regions"):
            if not values_match([site.get("region"), site.get("province")], filters["regions"]):
                match = False

        if filters.get("companies"):
            if not values_match(site.get("company"), filters["companies"]):
                match = False

        if filters.get("site_names"):
            names = [site.get("site_name")] + site.get("aliases", [])
            if not values_match(names, filters["site_names"]):
                match = False
                
        if filters.get("unfc_e"):
            if not values_match(site.get("unfc_e"), filters["unfc_e"]):
                match = False
                
        if filters.get("unfc_f"):
            if not values_match(site.get("unfc_f"), filters["unfc_f"]):
                match = False

        if filters.get("unfc_g"):
            if not values_match(site.get("unfc_g"), filters["unfc_g"]):
                match = False

        if filters.get("activity_types"):
            if not values_match(site.get("activity_type"), filters["activity_types"]):
                match = False

        if filters.get("mine_types"):
            if not values_match(site.get("mine_type"), filters["mine_types"]):
                match = False

        if filters.get("admin_statuses"):
            if not values_match(site.get("admin_status"), filters["admin_statuses"]):
                match = False

        if filters.get("mine_statuses"):
            if not values_match(site.get("mine_status"), filters["mine_statuses"]):
                match = False

        if filters.get("morphologies"):
            if not values_match(site.get("morphology"), filters["morphologies"]):
                match = False

        if "restored" in filters and filters["restored"] is not None:
            # filters["restored"] can be a boolean or a list containing boolean(s)
            val = filters["restored"]
            target_bool = val[0] if isinstance(val, list) and len(val) > 0 else val
            if site.get("restored") != target_bool:
                match = False

        if filters.get("restoration_types"):
            if not values_match(site.get("restoration_type"), filters["restoration_types"]):
                match = False

        if filters.get("site_contexts"):
            if not values_match(site.get("site_context"), filters["site_contexts"]):
                match = False

        if match:
            results.append(site)
            
    return results

if __name__ == "__main__":
    # Test the mock API
    test_filters = {"countries": ["spain"], "commodities": ["nickel"]}
    print(f"Testing filters: {test_filters}")
    res = query_data_space(test_filters)
    print(json.dumps(res, indent=2))
