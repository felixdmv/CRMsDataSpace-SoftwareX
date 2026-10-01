#!/usr/bin/env python3
"""
generate_conversational_dst_battery.py
Generates an extensive, realistic, publication-grade benchmark battery of 25 multi-turn
dialogue episodes (110 total conversational turns) for Dialogue State Tracking (DST)
and multi-criteria spatial search in CRMsDataSpace.

Specifically tagged by test categories to evaluate:
- "search": Initial spatial search with natural linguistic variation, periphrasis, asset & metal synonyms
- "expansion": Additive disjunction (OR) using natural conversational phrasing without rigid triggers
- "refinement": Progressive conjunction (AND) with complex constraints and natural periphrasis
- "removal": Subtractive exclusion with diverse natural verbs (prescinde, saca, descarta, deja fuera)
- "context": Anaphoric, elliptical, and conversational continuity (país vecino, lo mismo en..., de las anteriores...)
- "reset": Natural conversational resets (empecemos de cero, limpia el mapa, vuelve al catálogo)
"""

import json
from pathlib import Path

OUTPUT_FILE = Path(__file__).resolve().parent / "test_battery_conversational_dst.json"

episodes = [
    # Episode 1: Iberian Corridor with Natural Synonyms & Colloquial Phrasing
    {
        "episode_id": "EP-01",
        "title": "Iberian Corridor with Natural Synonyms and Non-Formulaic Phrasing",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Quiero ver las presas de residuos mineros en la península ibérica",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["spain", "portugal"],
                    "commodities": [],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "test_category": "expansion",
                "query": "Incluye también los yacimientos del país galo",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["spain", "portugal", "france"],
                    "commodities": [],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "refinement",
                "query": "Quédate únicamente con aquellas que sigan extrayendo a día de hoy",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["spain", "portugal", "france"],
                    "commodities": [],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": ["active"],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "test_category": "refinement",
                "query": "Acota a las que contengan litio o cobalto",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["spain", "portugal", "france"],
                    "commodities": ["lithium", "cobalt"],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": ["active"],
                    "restored": None
                }
            },
            {
                "turn": 5,
                "test_category": "removal",
                "query": "Prescinde de las explotaciones de cobalto",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["spain", "portugal", "france"],
                    "commodities": ["lithium"],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": ["active"],
                    "restored": None
                }
            },
            {
                "turn": 6,
                "test_category": "reset",
                "query": "Empecemos de cero",
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

    # Episode 2: Central European Corridor with Natural Constraints
    {
        "episode_id": "EP-02",
        "title": "Central European Corridor with Negative Status Constraints",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Muestra acúmulos de estériles y escorias en territorio germano",
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
                "test_category": "expansion",
                "query": "Suma también las instalaciones de la República Checa",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["germany", "czechia"],
                    "commodities": [],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "refinement",
                "query": "Filtra aquellas donde el terreno continúe sin rehabilitar",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["germany", "czechia"],
                    "commodities": [],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": False
                }
            },
            {
                "turn": 4,
                "test_category": "refinement",
                "query": "Me interesan solo las que alberguen wolframio",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["germany", "czechia"],
                    "commodities": ["tungsten"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": False
                }
            },
            {
                "turn": 5,
                "test_category": "removal",
                "query": "Olvídate de las de Chequia",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["germany"],
                    "commodities": ["tungsten"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": False
                }
            }
        ]
    },

    # Episode 3: Nordic Critical Raw Materials Audit
    {
        "episode_id": "EP-03",
        "title": "Nordic Critical Raw Materials & Environmental Audit",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Localiza balsas de decantación activas en Suecia",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["sweden"],
                    "commodities": [],
                    "storage_facility_types": ["pond"],
                    "project_status": ["active"],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "test_category": "expansion",
                "query": "Incorpora las instalaciones de Finlandia a la visualización",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["sweden", "finland"],
                    "commodities": [],
                    "storage_facility_types": ["pond"],
                    "project_status": ["active"],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "refinement",
                "query": "De todas esas, quédate solo con las que tengan tierras raras o níquel",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["sweden", "finland"],
                    "commodities": ["rare earth elements", "nickel"],
                    "storage_facility_types": ["pond"],
                    "project_status": ["active"],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "test_category": "removal",
                "query": "Saca las que están en Suecia",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["finland"],
                    "commodities": ["rare earth elements", "nickel"],
                    "storage_facility_types": ["pond"],
                    "project_status": ["active"],
                    "restored": None
                }
            }
        ]
    },

    # Episode 4: Contextual Anaphora & Cross-Border Shift
    {
        "episode_id": "EP-04",
        "title": "Contextual Anaphora and Cross-Border Neighbor Query",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Busca escombreras de litio en España",
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
                "test_category": "context",
                "query": "¿Y qué tenemos en el país vecino pero con wolframio?",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["spain", "portugal"],
                    "commodities": ["lithium", "tungsten"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "refinement",
                "query": "Conserva únicamente las que sigan operativas hoy",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["spain", "portugal"],
                    "commodities": ["lithium", "tungsten"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": ["active"],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "test_category": "removal",
                "query": "Descarta España de la selección",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["portugal"],
                    "commodities": ["lithium", "tungsten"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": ["active"],
                    "restored": None
                }
            }
        ]
    },

    # Episode 5: Mediterranean Corridor Exploration
    {
        "episode_id": "EP-05",
        "title": "Mediterranean Corridor Exploration and Facility Filtering",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Depósitos mineros en territorio heleno",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["greece"],
                    "commodities": [],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "test_category": "expansion",
                "query": "Agrega también lo que tengamos registrado en Italia",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["greece", "italy"],
                    "commodities": [],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "refinement",
                "query": "Conserva solo las balsas de lodos y relaves",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["greece", "italy"],
                    "commodities": [],
                    "storage_facility_types": ["pond", "tailings storage facility"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "test_category": "refinement",
                "query": "Filtra las que contengan titanio",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["greece", "italy"],
                    "commodities": ["titanium"],
                    "storage_facility_types": ["pond", "tailings storage facility"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 5,
                "test_category": "reset",
                "query": "Limpia la vista del mapa",
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

    # Episode 6: Alpine Corridor with Acid Mine Drainage Focus
    {
        "episode_id": "EP-06",
        "title": "Alpine Corridor with Environmental Acid Risk",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Instalaciones en Austria con manganeso",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["austria"],
                    "commodities": ["manganese"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "test_category": "expansion",
                "query": "Incorpora las escombreras de Alemania",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["austria", "germany"],
                    "commodities": ["manganese"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "expansion",
                "query": "Suma también minerales de wolframio",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["austria", "germany"],
                    "commodities": ["manganese", "tungsten"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "test_category": "removal",
                "query": "Prescinde del manganeso",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["austria", "germany"],
                    "commodities": ["tungsten"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            }
        ]
    },

    # Episode 7: Elliptical Entity Transfer Across Jurisdictions
    {
        "episode_id": "EP-07",
        "title": "Elliptical Entity Transfer Across Jurisdictions",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Escombreras de litio en Francia",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["france"],
                    "commodities": ["lithium"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "test_category": "context",
                "query": "Aplica exactamente los mismos criterios para Alemania",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["france", "germany"],
                    "commodities": ["lithium"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "expansion",
                "query": "Añade además cobalto",
                "expected_action": "expand",
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
                "test_category": "refinement",
                "query": "Quédate únicamente con las que continúen en fase de explotación",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["france", "germany"],
                    "commodities": ["lithium", "cobalt"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": ["active"],
                    "restored": None
                }
            },
            {
                "turn": 5,
                "test_category": "removal",
                "query": "Pasa de las instalaciones francesas",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["germany"],
                    "commodities": ["lithium", "cobalt"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": ["active"],
                    "restored": None
                }
            }
        ]
    },

    # Episode 8: Multi-Commodity Progressive Filtering in Italy & Greece
    {
        "episode_id": "EP-08",
        "title": "Multi-Commodity Refinement and Subtraction",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Yacimientos con titanio y grafito en Italia",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["italy"],
                    "commodities": ["titanium", "graphite"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "test_category": "expansion",
                "query": "Suma también las ubicaciones en territorio heleno",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["italy", "greece"],
                    "commodities": ["titanium", "graphite"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "removal",
                "query": "El grafito ya no me interesa, déjalo fuera",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["italy", "greece"],
                    "commodities": ["titanium"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "test_category": "refinement",
                "query": "Acota a las que no se hayan restaurado todavía",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["italy", "greece"],
                    "commodities": ["titanium"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": False
                }
            }
        ]
    },

    # Episode 9: Polish-Czech Copper & Tin Exploration
    {
        "episode_id": "EP-09",
        "title": "Polish-Czech Copper Exploration and Reset",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Escombreras de estériles en Polonia",
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
                "test_category": "expansion",
                "query": "Incorpora las instalaciones de Chequia",
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
                "test_category": "refinement",
                "query": "Quédate únicamente con las que contengan cobre",
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
                "test_category": "removal",
                "query": "Saca las instalaciones polacas de los filtros",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["czechia"],
                    "commodities": ["copper"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 5,
                "test_category": "reset",
                "query": "Vuelve a mostrar todo el catálogo europeo",
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

    # Episode 10: English Exploration with Regional Concepts
    {
        "episode_id": "EP-10",
        "title": "English Spatial Search with Regional Concepts",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Locate operational tailings storage facilities in the Iberian peninsula",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["spain", "portugal"],
                    "commodities": [],
                    "storage_facility_types": ["tailings storage facility"],
                    "project_status": ["active"],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "test_category": "expansion",
                "query": "Include also mining waste sites across France",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["spain", "portugal", "france"],
                    "commodities": [],
                    "storage_facility_types": ["tailings storage facility"],
                    "project_status": ["active"],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "refinement",
                "query": "Filter down to those containing lithium or cobalt",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["spain", "portugal", "france"],
                    "commodities": ["lithium", "cobalt"],
                    "storage_facility_types": ["tailings storage facility"],
                    "project_status": ["active"],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "test_category": "removal",
                "query": "Drop facilities located in Spain",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["portugal", "france"],
                    "commodities": ["lithium", "cobalt"],
                    "storage_facility_types": ["tailings storage facility"],
                    "project_status": ["active"],
                    "restored": None
                }
            },
            {
                "turn": 5,
                "test_category": "reset",
                "query": "Reset all active search filters",
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

    # Episode 11: English Neighboring Entity Context
    {
        "episode_id": "EP-11",
        "title": "English Elliptical Context and Neighbor Shift",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Show tungsten waste dumps in Germany",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["germany"],
                    "commodities": ["tungsten"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "test_category": "context",
                "query": "What about in the neighboring Czech Republic?",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["germany", "czechia"],
                    "commodities": ["tungsten"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "refinement",
                "query": "Keep solely unrestored sites",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["germany", "czechia"],
                    "commodities": ["tungsten"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": False
                }
            },
            {
                "turn": 4,
                "test_category": "removal",
                "query": "Get rid of the German deposits",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["czechia"],
                    "commodities": ["tungsten"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": False
                }
            }
        ]
    },

    # Episode 12: English Multi-Element Exclusion
    {
        "episode_id": "EP-12",
        "title": "English Multi-Element Exclusion and Status Refinement",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Find facilities with titanium and graphite in Italy",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["italy"],
                    "commodities": ["titanium", "graphite"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "test_category": "expansion",
                "query": "Also bring in locations in Greece",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["italy", "greece"],
                    "commodities": ["titanium", "graphite"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "removal",
                "query": "Exclude graphite from the results",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["italy", "greece"],
                    "commodities": ["titanium"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "test_category": "refinement",
                "query": "Restrict to active commercial operations",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["italy", "greece"],
                    "commodities": ["titanium"],
                    "storage_facility_types": [],
                    "project_status": ["active"],
                    "restored": None
                }
            }
        ]
    },

    # Episode 13: Atlantic Corridor (Ireland and Spain)
    {
        "episode_id": "EP-13",
        "title": "Atlantic Corridor Exploration",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Balsas de relaves en Irlanda",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["ireland"],
                    "commodities": [],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "test_category": "expansion",
                "query": "Incorpora las instalaciones mineras de España",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["ireland", "spain"],
                    "commodities": [],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "refinement",
                "query": "Quédate únicamente con aquellas que sigan operando hoy",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["ireland", "spain"],
                    "commodities": [],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": ["active"],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "test_category": "removal",
                "query": "Descarta los depósitos de Irlanda",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["spain"],
                    "commodities": [],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": ["active"],
                    "restored": None
                }
            }
        ]
    },

    # Episode 14: Nordic Battery Minerals Supply Chain
    {
        "episode_id": "EP-14",
        "title": "Nordic Battery Minerals Supply Chain",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Yacimientos con litio y níquel en Finlandia",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["finland"],
                    "commodities": ["lithium", "nickel"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "test_category": "expansion",
                "query": "Agrega también las explotaciones de Suecia",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["finland", "sweden"],
                    "commodities": ["lithium", "nickel"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "refinement",
                "query": "Restringe la consulta a balsas de relaves",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["finland", "sweden"],
                    "commodities": ["lithium", "nickel"],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "test_category": "removal",
                "query": "Prescinde del níquel",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["finland", "sweden"],
                    "commodities": ["lithium"],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 5,
                "test_category": "reset",
                "query": "Borra todos los filtros aplicados",
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

    # Episode 15: Environmental Legacy Liabilities
    {
        "episode_id": "EP-015",
        "title": "Environmental Legacy Liabilities with AMD Risk",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Instalaciones sin rehabilitar en Alemania",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["germany"],
                    "commodities": [],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": False
                }
            },
            {
                "turn": 2,
                "test_category": "expansion",
                "query": "Suma las que tengamos en Austria",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["germany", "austria"],
                    "commodities": [],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": False
                }
            },
            {
                "turn": 3,
                "test_category": "refinement",
                "query": "Conserva solo las que alberguen tungsteno",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["germany", "austria"],
                    "commodities": ["tungsten"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": False
                }
            },
            {
                "turn": 4,
                "test_category": "removal",
                "query": "Descarta los activos en Austria",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["germany"],
                    "commodities": ["tungsten"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": False
                }
            }
        ]
    },

    # Episode 16: Refractory & Technology Metals
    {
        "episode_id": "EP-16",
        "title": "Refractory Technology Metals in Spain & Portugal",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Escombreras de wolframio y estaño en España",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["spain"],
                    "commodities": ["tungsten", "tin"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "test_category": "expansion",
                "query": "Incorpora a Portugal a la selección",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["spain", "portugal"],
                    "commodities": ["tungsten", "tin"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "removal",
                "query": "Deja fuera el estaño",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["spain", "portugal"],
                    "commodities": ["tungsten"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "test_category": "refinement",
                "query": "Quédate únicamente con las que sigan activas hoy",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["spain", "portugal"],
                    "commodities": ["tungsten"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": ["active"],
                    "restored": None
                }
            }
        ]
    },

    # Episode 17: Contextual Interrogative Continuity
    {
        "episode_id": "EP-17",
        "title": "Contextual Interrogative Continuity Across Regions",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Balsas de residuos en Grecia",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["greece"],
                    "commodities": [],
                    "storage_facility_types": ["pond"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "test_category": "context",
                "query": "¿Y qué tenemos registrado en territorio transalpino?",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["greece", "italy"],
                    "commodities": [],
                    "storage_facility_types": ["pond"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "context",
                "query": "De las que me has dicho, ¿cuáles tienen níquel?",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["greece", "italy"],
                    "commodities": ["nickel"],
                    "storage_facility_types": ["pond"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "test_category": "removal",
                "query": "Olvídate de Grecia",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["italy"],
                    "commodities": ["nickel"],
                    "storage_facility_types": ["pond"],
                    "project_status": [],
                    "restored": None
                }
            }
        ]
    },

    # Episode 18: German-Scandinavian Corridor
    {
        "episode_id": "EP-18",
        "title": "German-Scandinavian Corridor with Rare Earths",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Escombreras en Alemania",
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
                "test_category": "expansion",
                "query": "Suma también las de la zona nórdica",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["germany", "sweden", "finland"],
                    "commodities": [],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "refinement",
                "query": "Quédate exclusivamente con tierras raras",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["germany", "sweden", "finland"],
                    "commodities": ["rare earth elements"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "test_category": "removal",
                "query": "Prescinde de Alemania",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["sweden", "finland"],
                    "commodities": ["rare earth elements"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            }
        ]
    },

    # Episode 19: Complex Multi-Metal Removal
    {
        "episode_id": "EP-19",
        "title": "Complex Multi-Metal Subtractive Sequence",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Instalaciones con cobre, cobalto y litio en Portugal y España",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["portugal", "spain"],
                    "commodities": ["copper", "cobalt", "lithium"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "test_category": "removal",
                "query": "Prescinde del cobre",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["portugal", "spain"],
                    "commodities": ["cobalt", "lithium"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "removal",
                "query": "Descarta España de la lista",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["portugal"],
                    "commodities": ["cobalt", "lithium"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "test_category": "refinement",
                "query": "Restringe a instalaciones activas",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["portugal"],
                    "commodities": ["cobalt", "lithium"],
                    "storage_facility_types": [],
                    "project_status": ["active"],
                    "restored": None
                }
            }
        ]
    },

    # Episode 20: Cross-Border Out-of-Scope Resilient Flow
    {
        "episode_id": "EP-20",
        "title": "Cross-Border Mixed Scope Dialogue",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Países del sur de Europa como Grecia o Albania que tengan níquel",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["greece"],
                    "commodities": ["nickel"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "test_category": "expansion",
                "query": "Agrega depósitos en Italia",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["greece", "italy"],
                    "commodities": ["nickel"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "removal",
                "query": "Saca las instalaciones de Grecia",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["italy"],
                    "commodities": ["nickel"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "test_category": "refinement",
                "query": "Quédate únicamente con balsas de relaves",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["italy"],
                    "commodities": ["nickel"],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": None
                }
            }
        ]
    },

    # Episode 21: Consecutive Refinements Sequence
    {
        "episode_id": "EP-21",
        "title": "Consecutive Multi-Dimensional Refinements",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Escombreras de estériles en Francia y Alemania",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["france", "germany"],
                    "commodities": [],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "test_category": "refinement",
                "query": "Quédate únicamente con las que contengan litio",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["france", "germany"],
                    "commodities": ["lithium"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "refinement",
                "query": "De esas solo las que estén activas hoy en día",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["france", "germany"],
                    "commodities": ["lithium"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": ["active"],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "test_category": "refinement",
                "query": "Y que además sigan sin restaurar",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["france", "germany"],
                    "commodities": ["lithium"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": ["active"],
                    "restored": False
                }
            }
        ]
    },

    # Episode 22: Rapid Switch and Exploration Reset
    {
        "episode_id": "EP-22",
        "title": "Rapid Exploration Pivot and Context Rebuilding",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Balsas de relaves en Suecia",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["sweden"],
                    "commodities": [],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "test_category": "reset",
                "query": "Limpia la búsqueda",
                "expected_action": "reset",
                "expected_accumulated_filters": {
                    "countries": [],
                    "commodities": [],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "search",
                "query": "Escombreras en España con tántalo",
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
                "turn": 4,
                "test_category": "expansion",
                "query": "Suma también las instalaciones en Portugal",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["spain", "portugal"],
                    "commodities": ["tantalum"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            }
        ]
    },

    # Episode 23: Anaphora with Negation & Metal Swap
    {
        "episode_id": "EP-23",
        "title": "Anaphora with Negation and Mineral Substitution",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Instalaciones en Finlandia con níquel",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["finland"],
                    "commodities": ["nickel"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "test_category": "context",
                "query": "¿Hay algo similar en Suecia?",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["finland", "sweden"],
                    "commodities": ["nickel"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "refinement",
                "query": "Descarta aquellas que ya hayan sido rehabilitadas",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["finland", "sweden"],
                    "commodities": ["nickel"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": False
                }
            },
            {
                "turn": 4,
                "test_category": "removal",
                "query": "Prescinde del níquel",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["finland", "sweden"],
                    "commodities": [],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": False
                }
            }
        ]
    },

    # Episode 24: Deep Subsurface Tailings Contrast
    {
        "episode_id": "EP-24",
        "title": "Tailings and Dumps Contrast in Czechia and Poland",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Presas de lodos y decantación en Chequia",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["czechia"],
                    "commodities": [],
                    "storage_facility_types": ["pond"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "test_category": "expansion",
                "query": "Añade escombreras de roca estéril en Polonia",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["czechia", "poland"],
                    "commodities": [],
                    "storage_facility_types": ["pond", "waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "refinement",
                "query": "Quédate solo con las que contengan cobre",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["czechia", "poland"],
                    "commodities": ["copper"],
                    "storage_facility_types": ["pond", "waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "test_category": "removal",
                "query": "Elimina Chequia de la búsqueda",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["poland"],
                    "commodities": ["copper"],
                    "storage_facility_types": ["pond", "waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 5,
                "test_category": "reset",
                "query": "Reinicia todos los criterios",
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

    # Episode 25: English Anaphora & Multi-Hop Exploration
    {
        "episode_id": "EP-25",
        "title": "English Multi-Hop Anaphora and Asset Selection",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Locate lithium extraction waste in France",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["france"],
                    "commodities": ["lithium"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "test_category": "context",
                "query": "Do the same for Germany",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["france", "germany"],
                    "commodities": ["lithium"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "refinement",
                "query": "From those, solely keep operational waste dumps",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["france", "germany"],
                    "commodities": ["lithium"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": ["active"],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "test_category": "removal",
                "query": "Drop French facilities",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["germany"],
                    "commodities": ["lithium"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": ["active"],
                    "restored": None
                }
            },
            {
                "turn": 5,
                "test_category": "reset",
                "query": "Clear all filters now",
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

    # Episode 26: Baltic & Scandinavian Cross-Turn Anaphora
    {
        "episode_id": "EP-26",
        "title": "Baltic and Scandinavian Anaphora with Operational Refinement",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Yacimientos con níquel en Finlandia",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["finland"],
                    "commodities": ["nickel"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "test_category": "context",
                "query": "¿Y qué tenemos en el país de al lado?",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["finland", "sweden"],
                    "commodities": ["nickel"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "context",
                "query": "¿Cuáles de las que me has dicho siguen activas a fecha de hoy?",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["finland", "sweden"],
                    "commodities": ["nickel"],
                    "storage_facility_types": [],
                    "project_status": ["active"],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "test_category": "removal",
                "query": "Prescinde de las instalaciones suecas",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["finland"],
                    "commodities": ["nickel"],
                    "storage_facility_types": [],
                    "project_status": ["active"],
                    "restored": None
                }
            },
            {
                "turn": 5,
                "test_category": "reset",
                "query": "Vuelve a empezar de cero",
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

    # Episode 27: Iberian Ellipsis and Compound Dialogue
    {
        "episode_id": "EP-27",
        "title": "Iberian Ellipsis and Multi-Commodity Synthesis",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Depósitos de litio en territorio luso",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["portugal"],
                    "commodities": ["lithium"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "test_category": "context",
                "query": "Suma lo que haya en la península ibérica que albergue tántalo",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["portugal", "spain"],
                    "commodities": ["lithium", "tantalum"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "refinement",
                "query": "Quédate exclusivamente con las escombreras de roca estéril",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["portugal", "spain"],
                    "commodities": ["lithium", "tantalum"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "test_category": "removal",
                "query": "Saca el tántalo",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["portugal", "spain"],
                    "commodities": ["lithium"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            }
        ]
    },

    # Episode 28: English Deictic Reference & Progressive Filtering
    {
        "episode_id": "EP-28",
        "title": "English Deictic Reference and Environmental Constraints",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Display tailings ponds in Germany",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["germany"],
                    "commodities": [],
                    "storage_facility_types": ["pond", "tailings storage facility"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "test_category": "context",
                "query": "What about in France?",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["germany", "france"],
                    "commodities": [],
                    "storage_facility_types": ["pond", "tailings storage facility"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "refinement",
                "query": "From the previous ones, solely keep unrestored sites",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["germany", "france"],
                    "commodities": [],
                    "storage_facility_types": ["pond", "tailings storage facility"],
                    "project_status": [],
                    "restored": False
                }
            },
            {
                "turn": 4,
                "test_category": "removal",
                "query": "Exclude the German deposits",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["france"],
                    "commodities": [],
                    "storage_facility_types": ["pond", "tailings storage facility"],
                    "project_status": [],
                    "restored": False
                }
            }
        ]
    },

    # Episode 29: Interrogative Status Shift in Austria & Italy
    {
        "episode_id": "EP-29",
        "title": "Interrogative Status Shift in Alpine Region",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Balsas de relaves en Austria",
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
                "test_category": "context",
                "query": "¿Y qué tenemos en territorio italiano?",
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
                "test_category": "context",
                "query": "De las anteriores, ¿hay alguna que esté cerrada o abandonada?",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["austria", "italy"],
                    "commodities": [],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": ["inactive"],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "test_category": "removal",
                "query": "Olvídate de Italia",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["austria"],
                    "commodities": [],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": ["inactive"],
                    "restored": None
                }
            },
            {
                "turn": 5,
                "test_category": "reset",
                "query": "Reinicia los filtros y muestra todo el mapa",
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

    # Episode 30: Complex Multi-Lingual Contextual Transfer
    {
        "episode_id": "EP-30",
        "title": "Complex Multi-Lingual Contextual Transfer and Refinement",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Mining waste deposits in Greece",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["greece"],
                    "commodities": [],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "test_category": "context",
                "query": "¿Y qué tenemos en España con cobre?",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["greece", "spain"],
                    "commodities": ["copper"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "refinement",
                "query": "Restringe a presas y balsas de lodos",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["greece", "spain"],
                    "commodities": ["copper"],
                    "storage_facility_types": ["pond", "tailings storage facility"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "test_category": "removal",
                "query": "Saca las instalaciones griegas",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["spain"],
                    "commodities": ["copper"],
                    "storage_facility_types": ["pond", "tailings storage facility"],
                    "project_status": [],
                    "restored": None
                }
            }
        ]
    }
]

def main():
    total_episodes = len(episodes)
    total_turns = sum(len(ep["turns"]) for ep in episodes)
    
    cat_counts = {}
    action_counts = {}
    for ep in episodes:
        for t in ep["turns"]:
            cat = t.get("test_category", "unknown")
            act = t.get("expected_action", "unknown")
            cat_counts[cat] = cat_counts.get(cat, 0) + 1
            action_counts[act] = action_counts.get(act, 0) + 1

    print(f"Generated {total_episodes} dialogue episodes ({total_turns} total turns).")
    print(f"Test Category Breakdown: {cat_counts}")
    print(f"Action Breakdown: {action_counts}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(episodes, f, indent=2, ensure_ascii=False)
    print(f"Saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
