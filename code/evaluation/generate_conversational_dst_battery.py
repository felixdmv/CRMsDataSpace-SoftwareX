#!/usr/bin/env python3
"""
generate_conversational_dst_battery.py
Generates an extensive, publication-grade benchmark battery of 25 multi-turn
dialogue episodes (100 total conversational turns) for Dialogue State Tracking (DST)
and multi-criteria spatial search in CRMsDataSpace.

Covers:
1. Spatial grounding (European capitals/cities -> countries)
2. Additive Disjunction (expand / OR)
3. Progressive Conjunction (refine / AND)
4. Subtractive Attribute Exclusion (remove)
5. Explicit Dialogue Reset (reset)
6. Multilingual & colloquial phrasing (Spanish, English, mixed terms)
7. Out-of-scope geographic boundaries handled within conversation flow
"""

import json
from pathlib import Path

OUTPUT_FILE = Path(__file__).resolve().parent / "test_battery_conversational_dst.json"

episodes = [
    # Episode 1: The Canonical Multi-Turn Exploration (Paris -> Berlin -> Lithium/Cobalt -> Remove Cobalt -> Reset)
    {
        "episode_id": "EP-01",
        "title": "Canonical 5-Turn Sequential Exploration and Reset",
        "turns": [
            {
                "turn": 1,
                "query": "Dime escombreras cerca de París",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["france"],
                    "commodities": [],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "query": "Y además las que estén cerca de Berlín",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["france", "germany"],
                    "commodities": [],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "query": "De esas, solo las que contengan litio y cobalto",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["france", "germany"],
                    "commodities": ["lithium", "cobalt"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "query": "Ahora quita las de cobalto",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["france", "germany"],
                    "commodities": ["lithium"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 5,
                "query": "Reiniciar búsqueda",
                "expected_action": "reset",
                "expected_accumulated_filters": {
                    "countries": [],
                    "commodities": [],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            }
        ]
    },

    # Episode 2: Iberian Cross-Border Corridor (Lisbon -> Madrid -> Tungsten -> Active only)
    {
        "episode_id": "EP-02",
        "title": "Iberian Cross-Border Corridor Refinement",
        "turns": [
            {
                "turn": 1,
                "query": "Balsas de relaves cerca de Lisboa",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["portugal"],
                    "commodities": [],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "query": "Y también añade las instalaciones en Madrid",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["portugal", "spain"],
                    "commodities": [],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "query": "De esas solo las que tengan wolframio o estaño",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["portugal", "spain"],
                    "commodities": ["tungsten", "tin"],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "query": "Filtra únicamente las operativas o activas",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["portugal", "spain"],
                    "commodities": ["tungsten", "tin"],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": ["active"],
                    "restored": None
                }
            }
        ]
    },

    # Episode 3: Nordic Critical Raw Materials Audit (Stockholm -> Helsinki -> REE -> Unrestored)
    {
        "episode_id": "EP-03",
        "title": "Nordic Critical Raw Materials & Environmental Audit",
        "turns": [
            {
                "turn": 1,
                "query": "Show active waste facilities around Stockholm",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["sweden"],
                    "commodities": [],
                    "storage_facility_types": [],
                    "project_status": ["active"],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "query": "Include also facilities in Helsinki",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["sweden", "finland"],
                    "commodities": [],
                    "storage_facility_types": [],
                    "project_status": ["active"],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "query": "From these, only those with rare earth elements or nickel",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["sweden", "finland"],
                    "commodities": ["rare earth elements", "nickel"],
                    "storage_facility_types": [],
                    "project_status": ["active"],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "query": "Narrow down to unrestored facilities",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["sweden", "finland"],
                    "commodities": ["rare earth elements", "nickel"],
                    "storage_facility_types": [],
                    "project_status": ["active"],
                    "restored": False
                }
            }
        ]
    },

    # Episode 4: Central European Mining Exploration (Warsaw -> Prague -> Copper -> Remove Poland)
    {
        "episode_id": "EP-04",
        "title": "Central European Corridor & Subtractive Country Removal",
        "turns": [
            {
                "turn": 1,
                "query": "Escombreras en Polonia",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["poland"],
                    "commodities": [],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "query": "Y además las de Chequia",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["poland", "czechia"],
                    "commodities": [],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "query": "De esas solo las que tengan cobre",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["poland", "czechia"],
                    "commodities": ["copper"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "query": "Quita las de Polonia",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["czechia"],
                    "commodities": ["copper"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            }
        ]
    },

    # Episode 5: Alpine Exploration & Reset (Vienna -> Rome -> Graphite -> Clear)
    {
        "episode_id": "EP-05",
        "title": "Alpine Exploration and Immediate Clear",
        "turns": [
            {
                "turn": 1,
                "query": "Tailings ponds in Austria",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["austria"],
                    "commodities": [],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "query": "Add also sites near Rome",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["austria", "italy"],
                    "commodities": [],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "query": "Just the ones with graphite",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["austria", "italy"],
                    "commodities": ["graphite"],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "query": "Clear all filters",
                "expected_action": "reset",
                "expected_accumulated_filters": {
                    "countries": [],
                    "commodities": [],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            }
        ]
    },

    # Episode 6: Commodity Expansion & Subsequent Refinement (Lithium -> Add Cobalt -> Add Nickel -> Only Active)
    {
        "episode_id": "EP-06",
        "title": "Commodity Expansion with Status Refinement",
        "turns": [
            {
                "turn": 1,
                "query": "Instalaciones con litio en España",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["spain"],
                    "commodities": ["lithium"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "query": "Y además añade cobalto",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["spain"],
                    "commodities": ["lithium", "cobalt"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "query": "Y también níquel",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["spain"],
                    "commodities": ["lithium", "cobalt", "nickel"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "query": "De esas solo las que estén en estado activo",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["spain"],
                    "commodities": ["lithium", "cobalt", "nickel"],
                    "storage_facility_types": [],
                    "project_status": ["active"],
                    "restored": None
                }
            }
        ]
    },

    # Episode 7: Subtractive Commodity Cleanup (Lithium + Cobalt + Nickel -> Remove Lithium -> Remove Nickel)
    {
        "episode_id": "EP-07",
        "title": "Sequential Subtractive Commodity Removal",
        "turns": [
            {
                "turn": 1,
                "query": "Depósitos con litio, cobalto y níquel en Finlandia",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["finland"],
                    "commodities": ["lithium", "cobalt", "nickel"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "query": "Elimina el litio",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["finland"],
                    "commodities": ["cobalt", "nickel"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "query": "Descarta el níquel",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["finland"],
                    "commodities": ["cobalt"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "query": "Y además las de Suecia",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["finland", "sweden"],
                    "commodities": ["cobalt"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            }
        ]
    },

    # Episode 8: Geographic Grounding with Capital Cities (Dublin -> Athens -> Titanium -> Waste Dumps)
    {
        "episode_id": "EP-08",
        "title": "Geographic City Grounding across Island and Mediterranean",
        "turns": [
            {
                "turn": 1,
                "query": "Dumps near Dublin",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["ireland"],
                    "commodities": [],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "query": "And also sites around Athens",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["ireland", "greece"],
                    "commodities": [],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "query": "Only those containing titanium",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["ireland", "greece"],
                    "commodities": ["titanium"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "query": "Start over with a new search",
                "expected_action": "reset",
                "expected_accumulated_filters": {
                    "countries": [],
                    "commodities": [],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            }
        ]
    },

    # Episode 9: Multi-Turn Chemical Notation & Facility Type Switch (W in Germany -> Add Sn -> Tailings only -> Inactive only)
    {
        "episode_id": "EP-09",
        "title": "Chemical Notation with Facility Type Narrowing",
        "turns": [
            {
                "turn": 1,
                "query": "Muestra instalaciones con W en Alemania",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["germany"],
                    "commodities": ["tungsten"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "query": "Y además con Sn",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["germany"],
                    "commodities": ["tungsten", "tin"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "query": "De esas solo balsas de decantación",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["germany"],
                    "commodities": ["tungsten", "tin"],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "query": "Únicamente las inactivas",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["germany"],
                    "commodities": ["tungsten", "tin"],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": ["inactive"],
                    "restored": None
                }
            }
        ]
    },

    # Episode 10: Environmental Risk & Restoration Tracking
    {
        "episode_id": "EP-10",
        "title": "Environmental Risk and Restoration State Tracking",
        "turns": [
            {
                "turn": 1,
                "query": "Escombreras de cobre en España",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["spain"],
                    "commodities": ["copper"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "query": "Y además en Portugal",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["spain", "portugal"],
                    "commodities": ["copper"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "query": "Filtra por las no restauradas",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["spain", "portugal"],
                    "commodities": ["copper"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": False
                }
            },
            {
                "turn": 4,
                "query": "Borrar filtros y reset",
                "expected_action": "reset",
                "expected_accumulated_filters": {
                    "countries": [],
                    "commodities": [],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            }
        ]
    },

    # Episode 11: Regional Geographic Expansion (Southern Europe -> Add France -> Refine Manganese)
    {
        "episode_id": "EP-11",
        "title": "Macro-Regional Entity Resolution and Incremental Narrowing",
        "turns": [
            {
                "turn": 1,
                "query": "Instalaciones en el sur de Europa",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["spain", "portugal", "italy", "greece"],
                    "commodities": [],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "query": "Y también Francia",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["spain", "portugal", "italy", "greece", "france"],
                    "commodities": [],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "query": "De esas solo las que tengan manganeso",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["spain", "portugal", "italy", "greece", "france"],
                    "commodities": ["manganese"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "query": "Quita Grecia e Italia",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["spain", "portugal", "france"],
                    "commodities": ["manganese"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            }
        ]
    },

    # Episode 12: Nordic Regional Entities (Nordic countries -> Refine Platinum -> Add Tantalum)
    {
        "episode_id": "EP-12",
        "title": "Nordic Regional Expansion and Critical Metal Combination",
        "turns": [
            {
                "turn": 1,
                "query": "Tailings facilities in Nordic countries",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["sweden", "finland"],
                    "commodities": [],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "query": "Of those, only with platinum or PGE",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["sweden", "finland"],
                    "commodities": ["pge"],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "query": "And also add tantalum",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["sweden", "finland"],
                    "commodities": ["pge", "tantalum"],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "query": "Only active ones",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["sweden", "finland"],
                    "commodities": ["pge", "tantalum"],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": ["active"],
                    "restored": None
                }
            }
        ]
    },

    # Episode 13: Colloquial Code-Switching Dialogue
    {
        "episode_id": "EP-13",
        "title": "Colloquial Code-Switching Dialogue",
        "turns": [
            {
                "turn": 1,
                "query": "Find waste dumps in Spain with coltan",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["spain"],
                    "commodities": ["tantalum"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "query": "Y además en Portugal",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["spain", "portugal"],
                    "commodities": ["tantalum"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "query": "Just the active ones",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["spain", "portugal"],
                    "commodities": ["tantalum"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": ["active"],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "query": "Olvida todo",
                "expected_action": "reset",
                "expected_accumulated_filters": {
                    "countries": [],
                    "commodities": [],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            }
        ]
    },

    # Episode 14: Industrial Cluster Tracking (Munich -> Lyon -> Kiruna)
    {
        "episode_id": "EP-14",
        "title": "Industrial City Cluster Expansion and Commodity Narrowing",
        "turns": [
            {
                "turn": 1,
                "query": "Escombreras cerca de Munich",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["germany"],
                    "commodities": [],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "query": "Y también las de Lyon",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["germany", "france"],
                    "commodities": [],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "query": "Y suma Kiruna",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["germany", "france", "sweden"],
                    "commodities": [],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "query": "De esas solo con tierras raras",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["germany", "france", "sweden"],
                    "commodities": ["rare earth elements"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            }
        ]
    },

    # Episode 15: Out-of-Scope Geographic Handling within Conversation
    {
        "episode_id": "EP-15",
        "title": "Out-of-Scope Geographic Boundary Dialogue Handling",
        "turns": [
            {
                "turn": 1,
                "query": "Dime escombreras de litio en España",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["spain"],
                    "commodities": ["lithium"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "query": "Y además las que estén en Chile",
                "expected_action": "expand",
                # Chile is outside European data space; active filter should preserve Spain without breaking
                "expected_accumulated_filters": {
                    "countries": ["spain"],
                    "commodities": ["lithium"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "query": "Y también Portugal",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["spain", "portugal"],
                    "commodities": ["lithium"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "query": "De esas solo las activas",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["spain", "portugal"],
                    "commodities": ["lithium"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": ["active"],
                    "restored": None
                }
            }
        ]
    },

    # Episode 16: Stockpile & Waste Facility Typology Refinement
    {
        "episode_id": "EP-16",
        "title": "Storage Facility Typology Transformation",
        "turns": [
            {
                "turn": 1,
                "query": "Instalaciones con titanio en Italia",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["italy"],
                    "commodities": ["titanium"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "query": "Y también en Grecia",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["italy", "greece"],
                    "commodities": ["titanium"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "query": "Filtra por acopios o stockpiles",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["italy", "greece"],
                    "commodities": ["titanium"],
                    "storage_facility_types": ["stockpile"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "query": "Quita Grecia",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["italy"],
                    "commodities": ["titanium"],
                    "storage_facility_types": ["stockpile"],
                    "project_status": [],
                    "restored": None
                }
            }
        ]
    },

    # Episode 17: Multi-Turn Environmental Remediation Status
    {
        "episode_id": "EP-17",
        "title": "Restoration State Inversion and Re-filtering",
        "turns": [
            {
                "turn": 1,
                "query": "Balsas de relave en Portugal",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["portugal"],
                    "commodities": [],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "query": "De esas solo las que estén restauradas",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["portugal"],
                    "commodities": [],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": True
                }
            },
            {
                "turn": 3,
                "query": "Y además añade España",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["portugal", "spain"],
                    "commodities": [],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": True
                }
            },
            {
                "turn": 4,
                "query": "Reiniciar",
                "expected_action": "reset",
                "expected_accumulated_filters": {
                    "countries": [],
                    "commodities": [],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            }
        ]
    },

    # Episode 18: Polish-German Border Mining Corridor
    {
        "episode_id": "EP-18",
        "title": "German-Polish Border Mining Basin",
        "turns": [
            {
                "turn": 1,
                "query": "Depósitos en Katowice",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["poland"],
                    "commodities": [],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "query": "Y además los de Frankfurt",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["poland", "germany"],
                    "commodities": [],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "query": "De esos solo con cobre y zinc o estaño",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["poland", "germany"],
                    "commodities": ["copper", "tin"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "query": "Elimina Alemania",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["poland"],
                    "commodities": ["copper", "tin"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            }
        ]
    },

    # Episode 19: Rare Metals Multi-Step Expansion
    {
        "episode_id": "EP-19",
        "title": "Strategic Raw Materials Multi-Step Expansion",
        "turns": [
            {
                "turn": 1,
                "query": "Muestra instalaciones de galio o tántalo en España",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["spain"],
                    "commodities": ["tantalum"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "query": "Y además en Irlanda",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["spain", "ireland"],
                    "commodities": ["tantalum"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "query": "Suma también Austria",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["spain", "ireland", "austria"],
                    "commodities": ["tantalum"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "query": "De esas solo escombreras activas",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["spain", "ireland", "austria"],
                    "commodities": ["tantalum"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": ["active"],
                    "restored": None
                }
            }
        ]
    },

    # Episode 20: Iberian Regional Expansion with City Grounding
    {
        "episode_id": "EP-20",
        "title": "Iberian Municipal Grounding and Progressive Subtraction",
        "turns": [
            {
                "turn": 1,
                "query": "Balsas de decantación en Ourense",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["spain"],
                    "commodities": [],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "query": "Y además las de Porto",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["spain", "portugal"],
                    "commodities": [],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "query": "De esas solo con litio",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["spain", "portugal"],
                    "commodities": ["lithium"],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "query": "Quita las de España",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["portugal"],
                    "commodities": ["lithium"],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": None
                }
            }
        ]
    },

    # Episode 21: French-German Industrial Corridor
    {
        "episode_id": "EP-21",
        "title": "French-German Industrial Corridor and Material Refinement",
        "turns": [
            {
                "turn": 1,
                "query": "Waste dumps in France",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["france"],
                    "commodities": [],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "query": "And also Germany",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["france", "germany"],
                    "commodities": [],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "query": "Only those with tungsten",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["france", "germany"],
                    "commodities": ["tungsten"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "query": "Empezar de nuevo",
                "expected_action": "reset",
                "expected_accumulated_filters": {
                    "countries": [],
                    "commodities": [],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            }
        ]
    },

    # Episode 22: Finnish-Swedish Arctic Mining
    {
        "episode_id": "EP-22",
        "title": "Arctic Mining Sector Exploration and Status Narrowing",
        "turns": [
            {
                "turn": 1,
                "query": "Instalaciones activas en Finlandia",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["finland"],
                    "commodities": [],
                    "storage_facility_types": [],
                    "project_status": ["active"],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "query": "Y además en Suecia",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["finland", "sweden"],
                    "commodities": [],
                    "storage_facility_types": [],
                    "project_status": ["active"],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "query": "De esas solo escombreras con níquel",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["finland", "sweden"],
                    "commodities": ["nickel"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": ["active"],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "query": "Quita las de Suecia",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["finland"],
                    "commodities": ["nickel"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": ["active"],
                    "restored": None
                }
            }
        ]
    },

    # Episode 23: Czech-Austrian Cross-Border Corridor
    {
        "episode_id": "EP-23",
        "title": "Czech-Austrian Corridor with Multi-Commodity Narrowing",
        "turns": [
            {
                "turn": 1,
                "query": "Balsas de relaves en Praga",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["czechia"],
                    "commodities": [],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "query": "Y también las de Viena",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["czechia", "austria"],
                    "commodities": [],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "query": "De esas solo con manganeso",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["czechia", "austria"],
                    "commodities": ["manganese"],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "query": "Limpiar filtros",
                "expected_action": "reset",
                "expected_accumulated_filters": {
                    "countries": [],
                    "commodities": [],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            }
        ]
    },

    # Episode 24: Italian Mediterranean Exploration
    {
        "episode_id": "EP-24",
        "title": "Italian Mediterranean Exploration and Commodity Removal",
        "turns": [
            {
                "turn": 1,
                "query": "Tailings ponds in Italy with titanium and graphite",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["italy"],
                    "commodities": ["titanium", "graphite"],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "query": "And also sites in Greece",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["italy", "greece"],
                    "commodities": ["titanium", "graphite"],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "query": "Remove graphite",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["italy", "greece"],
                    "commodities": ["titanium"],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "query": "Only unrestored",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["italy", "greece"],
                    "commodities": ["titanium"],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": False
                }
            }
        ]
    },

    # Episode 25: Comprehensive 5-Turn Full Cycle
    {
        "episode_id": "EP-25",
        "title": "Comprehensive 5-Turn End-to-End Exploration Cycle",
        "turns": [
            {
                "turn": 1,
                "query": "Dime escombreras en Huelva",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["spain"],
                    "commodities": [],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "query": "Y además añade las instalaciones en Francia",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["spain", "france"],
                    "commodities": [],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "query": "De esas solo con cobre",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["spain", "france"],
                    "commodities": ["copper"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "query": "Quita las de España",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["france"],
                    "commodities": ["copper"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 5,
                "query": "Reiniciar",
                "expected_action": "reset",
                "expected_accumulated_filters": {
                    "countries": [],
                    "commodities": [],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            }
        ]
    }
]

def main():
    total_turns = sum(len(ep["turns"]) for ep in episodes)
    print(f"Generating Conversational DST Benchmark Battery:")
    print(f"- Total Episodes: {len(episodes)}")
    print(f"- Total Conversational Turns: {total_turns}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(episodes, f, indent=2, ensure_ascii=False)

    print(f"Successfully saved test battery to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
