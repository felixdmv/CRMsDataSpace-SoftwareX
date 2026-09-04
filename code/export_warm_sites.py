#!/usr/bin/env python3
"""
Export the SATEC WARM proposal workbook into JSON files usable by the LLM prototype.

Outputs:
- code/data/warm_sites.json: normalized site records for structured filtering.
- code/data/warm_field_mapping.json: IGME/source field to WARM mapping.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
DEFAULT_INPUT = PROJECT_ROOT / "BBDD_propuesta_LLM_WARM.xlsx"
DEFAULT_OUTPUT_DIR = ROOT / "data"

COUNTRY_BY_CODE = {
    "ES": "spain",
}

SPANISH_TO_ENGLISH_COMMODITIES = {
    "hulla": "coal",
    "carbon": "coal",
    "carbón": "coal",
}

SPANISH_TO_ENGLISH_FACILITY = {
    "escombrera": "waste dump",
    "balsa": "pond",
}

SPANISH_TO_ENGLISH_MATERIAL = {
    "pizarras": "slates",
    "pizarra": "slate",
}


def clean_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.date().isoformat()
    if isinstance(value, str):
        text = re.sub(r"\s+", " ", value.strip())
        return text or None
    return value


def normalize_text(value: Any) -> str:
    cleaned = clean_value(value)
    return str(cleaned).strip().lower() if cleaned is not None else ""


def mapped_list(row: dict[str, Any], fields: list[str], mapping: dict[str, str]) -> list[str]:
    values: list[str] = []
    for field in fields:
        raw = normalize_text(row.get(field))
        if not raw:
            continue
        values.append(mapping.get(raw, raw))
    return sorted(set(values))


def site_aliases(row: dict[str, Any]) -> list[str]:
    values = [
        row.get("local_name"),
        row.get("locality"),
        row.get("municipality"),
    ]
    aliases = [str(clean_value(value)) for value in values if clean_value(value)]

    joined = " ".join(alias.lower() for alias in aliases)
    if "nicolasa" in joined or "nicolás" in joined or "nicolas" in joined:
        aliases.extend(["San Nicolás", "San Nicolas", "Nicolasa", "Arroyo de la Nicolasa"])
    if "pumardongo" in joined or "aguilar" in joined:
        aliases.extend(["Pumardongo", "Aguilar - Pumardongo"])
    if "figaredo" in joined or "casona" in joined:
        aliases.extend(["Figaredo", "La Casona"])
    return sorted(set(aliases))


def environmental_flags(row: dict[str, Any]) -> list[str]:
    observations = normalize_text(row.get("observations"))
    flags = []
    if "surgencias de agua" in observations or "water" in observations:
        flags.append("water emergence")
    if "sin restaurar" in normalize_text(row.get("rest_type")) or row.get("restored") is False:
        flags.append("not restored")
    return flags


def normalize_site(row: dict[str, Any]) -> dict[str, Any]:
    country_code = str(clean_value(row.get("country_code")) or "").upper()
    country = COUNTRY_BY_CODE.get(country_code, country_code.lower())

    site_name = clean_value(row.get("local_name")) or clean_value(row.get("locality")) or clean_value(row.get("id_site"))
    commodities = mapped_list(row, ["exp_subs_1", "exp_subs_2", "exp_subs_3"], SPANISH_TO_ENGLISH_COMMODITIES)
    material_types = mapped_list(row, ["debris_lit_1", "debris_lit_2", "debris_lit_3"], SPANISH_TO_ENGLISH_MATERIAL)
    facility_type = SPANISH_TO_ENGLISH_FACILITY.get(normalize_text(row.get("dep_type")), normalize_text(row.get("dep_type")))

    return {
        "id": clean_value(row.get("id_site")) or clean_value(row.get("id")),
        "source_record_id": clean_value(row.get("id")),
        "site_name": site_name,
        "aliases": site_aliases(row),
        "country": country,
        "country_code": country_code,
        "region": normalize_text(row.get("nuts3_label")),
        "nuts3_code": clean_value(row.get("nuts3_code")),
        "province": clean_value(row.get("province")),
        "municipality": clean_value(row.get("municipality")),
        "locality": clean_value(row.get("locality")),
        "utm_x": clean_value(row.get("utm_x")),
        "utm_y": clean_value(row.get("utm_y")),
        "utm_zone": clean_value(row.get("utm")),
        "altitude_m": clean_value(row.get("alt")),
        "commodities": commodities,
        "raw_exploited_substances": [clean_value(row.get(f)) for f in ["exp_subs_1", "exp_subs_2", "exp_subs_3"] if clean_value(row.get(f))],
        "material_types": material_types,
        "storage_facility_type": facility_type,
        "activity_type": clean_value(row.get("act_type")),
        "mine_type": clean_value(row.get("expl_type")),
        "company": clean_value(row.get("company")),
        "admin_status": clean_value(row.get("admin_status")),
        "mine_status": clean_value(row.get("mine_status")),
        "morphology": clean_value(row.get("morphology")),
        "area_m2": clean_value(row.get("area")),
        "restored": clean_value(row.get("restored")),
        "restoration_type": clean_value(row.get("rest_type")),
        "linked_facilities": clean_value(row.get("linked_fac")),
        "site_context": clean_value(row.get("site_context")),
        "environmental_flags": environmental_flags(row),
        "observations": clean_value(row.get("observations")),
        "source": clean_value(row.get("source")),
        "raw": {key: clean_value(value) for key, value in row.items()},
    }


def export(workbook_path: Path, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    table = pd.read_excel(workbook_path, sheet_name="tabla")
    metadata = pd.read_excel(workbook_path, sheet_name="metadatos")

    sites = [normalize_site(row) for row in table.to_dict(orient="records")]
    mapping = []
    for row in metadata.to_dict(orient="records"):
        field = clean_value(row.get("CAMPO"))
        if not field:
            continue
        mapping.append(
            {
                "source_field": field,
                "description": clean_value(row.get("DESCRIPCIÓN")),
                "warm_mapping": clean_value(row.get("WARM")),
            }
        )

    sites_path = output_dir / "warm_sites.json"
    mapping_path = output_dir / "warm_field_mapping.json"
    sites_path.write_text(json.dumps(sites, ensure_ascii=False, indent=2), encoding="utf-8")
    mapping_path.write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")
    return sites_path, mapping_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    sites_path, mapping_path = export(args.input, args.output_dir)
    print(f"Exported sites: {sites_path}")
    print(f"Exported field mapping: {mapping_path}")


if __name__ == "__main__":
    main()
