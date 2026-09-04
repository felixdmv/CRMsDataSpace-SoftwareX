import json
import os

DATASET_PATH = r"C:\Users\fdemiguel\OneDrive - Universidad de Burgos\Documentos\CRMsDataSpace\SoftwareX\code\data\synthetic_escombreras_europe.json"
INDEX_PATHS = [
    r"C:\Users\fdemiguel\OneDrive - Universidad de Burgos\Documentos\CRMsDataSpace\SoftwareX\code\static\index.html",
    r"C:\Users\fdemiguel\OneDrive - Universidad de Burgos\Documentos\CRMsDataSpace\geo-rag-explorer\index.html"
]

with open(DATASET_PATH, "r", encoding="utf-8") as f:
    raw_sites = json.load(f)

js_sites = []
for s in raw_sites:
    lat = s.get("latitude") or (float(s["location"].split(",")[0]) if s.get("location") else 40.0)
    lon = s.get("longitude") or (float(s["location"].split(",")[1]) if s.get("location") else 0.0)
    
    commodities = s.get("commodities", [])
    has_emerald = "lithium" in commodities or "cobalt" in commodities
    theme = "emerald" if has_emerald else "gold"
    
    status = s.get("project_status", "active")
    status_label = status.upper()
    status_color = "#10b981" if status == "active" else "#f59e0b"
    
    js_site = {
        "id": s.get("id"),
        "site_name": s.get("site_name"),
        "company": s.get("company", "EU Operator"),
        "country": s.get("country", "europe"),
        "country_name": s.get("country_name", "Europe"),
        "region": s.get("region_name", s.get("region", "Region")),
        "province": s.get("region_name", s.get("country_name", "EU")),
        "municipality": s.get("site_name"),
        "lat": lat,
        "lon": lon,
        "commodities": commodities,
        "commodities_label": s.get("commodities_label", ", ".join(commodities)),
        "facility_type": s.get("storage_facility_label", s.get("storage_facility_type", "Facility")),
        "material_type": s.get("material_type", "Tailings"),
        "project_status": status,
        "status_label": status_label,
        "status_color": status_color,
        "area_m2": f"{s.get('tonnage_mt', 10)} MT",
        "description": s.get("description", ""),
        "environmental_flags": s.get("environmental_flags", []),
        "unfc_code": s.get("unfc_code", "UNFC E1-F2-G1"),
        "color_theme": theme
    }
    js_sites.append(js_site)

js_block = """    // ==========================================
    // DATASET: 100 Synthetic European CRM Facilities
    // ==========================================
    let MINING_SITES = """ + json.dumps(js_sites, indent=6, ensure_ascii=False) + ";\n\n    let isTyping = false;"

for path in INDEX_PATHS:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    start_idx = content.find("// ==========================================\n    // MOCK DATA: Mining waste facilities in Spain")
    if start_idx == -1:
        start_idx = content.find("const MINING_SITES = [")
    
    end_idx = content.find("let isTyping = false;")
    
    if start_idx != -1 and end_idx != -1:
        new_content = content[:start_idx] + js_block + content[end_idx + len("let isTyping = false;")]
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Successfully replaced MINING_SITES in {path}")
    else:
        print(f"Indices not found in {path}: start_idx={start_idx}, end_idx={end_idx}")
