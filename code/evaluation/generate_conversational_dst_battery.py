#!/usr/bin/env python3
"""
generate_conversational_dst_battery.py
Generates an extensive, realistic, publication-grade benchmark battery of 30 multi-turn
dialogue episodes (132 total conversational turns) in ENGLISH for Dialogue State Tracking (DST)
and multi-criteria spatial search in CRMsDataSpace.

Specifically tagged by test categories to evaluate:
- "search": Initial spatial search with natural linguistic variation, periphrasis, asset & metal synonyms
- "expansion": Additive disjunction (OR) using natural conversational phrasing without rigid triggers
- "refinement": Progressive conjunction (AND) with complex constraints and natural periphrasis
- "removal": Subtractive exclusion with diverse natural verbs (drop, exclude, remove, discard, leave out)
- "context": Anaphoric, elliptical, and conversational continuity (neighboring country, do the same for..., of those...)
- "reset": Natural conversational resets (start over, clear filters, reset map, display entire catalog)
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
                "query": "Show tailings ponds in the Iberian Peninsula",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["spain", "portugal"],
                    "commodities": [],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": [],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "test_category": "expansion",
                "query": "Include also deposits located in France",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["spain", "portugal", "france"],
                    "commodities": [],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": [],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "refinement",
                "query": "Keep only those that are currently active today",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["spain", "portugal", "france"],
                    "commodities": [],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": [],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": ["active"],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "test_category": "refinement",
                "query": "Narrow down to those containing lithium or cobalt",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["spain", "portugal", "france"],
                    "commodities": ["lithium", "cobalt"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["lithium", "cobalt"],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": ["active"],
                    "restored": None
                }
            },
            {
                "turn": 5,
                "test_category": "removal",
                "query": "Remove cobalt from the selection",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["spain", "portugal", "france"],
                    "commodities": ["lithium"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["lithium"],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": ["active"],
                    "restored": None
                }
            },
            {
                "turn": 6,
                "test_category": "reset",
                "query": "Start over from scratch",
                "expected_action": "reset",
                "expected_accumulated_filters": {
                    "countries": [],
                    "commodities": [],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": [],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            }
        ]
    },

    # Episode 2: Central European Corridor with Negative Status Constraints
    {
        "episode_id": "EP-02",
        "title": "Central European Corridor with Negative Status Constraints",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Show waste dumps and spoil heaps in Germany",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["germany"],
                    "commodities": [],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": [],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "test_category": "expansion",
                "query": "Also add facilities in Czechia",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["germany", "czechia"],
                    "commodities": [],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": [],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "refinement",
                "query": "Filter to those that remain unrestored",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["germany", "czechia"],
                    "commodities": [],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": [],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": False
                }
            },
            {
                "turn": 4,
                "test_category": "refinement",
                "query": "I am only interested in those containing tungsten",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["germany", "czechia"],
                    "commodities": ["tungsten"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["tungsten"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": False
                }
            },
            {
                "turn": 5,
                "test_category": "removal",
                "query": "Forget about those in Czechia",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["germany"],
                    "commodities": ["tungsten"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["tungsten"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": False
                }
            }
        ]
    },

    # Episode 3: Nordic Critical Raw Materials & Environmental Audit
    {
        "episode_id": "EP-03",
        "title": "Nordic Critical Raw Materials & Environmental Audit",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Locate active tailings storage facilities in Sweden",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["sweden"],
                    "commodities": [],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": [],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": ["active"],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "test_category": "expansion",
                "query": "Include facilities in Finland in the view",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["sweden", "finland"],
                    "commodities": [],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": [],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": ["active"],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "refinement",
                "query": "Of all those, keep only the ones with rare earth elements or nickel",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["sweden", "finland"],
                    "commodities": ["rare earth elements", "nickel"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["rare earth elements", "nickel"],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": ["active"],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "test_category": "removal",
                "query": "Drop the ones located in Sweden",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["finland"],
                    "commodities": ["rare earth elements", "nickel"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["rare earth elements", "nickel"],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": ["active"],
                    "restored": None
                }
            }
        ]
    },

    # Episode 4: Contextual Anaphora and Cross-Border Neighbor Query
    {
        "episode_id": "EP-04",
        "title": "Contextual Anaphora and Cross-Border Neighbor Query",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Find lithium waste dumps in Spain",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["spain"],
                    "commodities": ["lithium"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["lithium"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "test_category": "context",
                "query": "And what do we have in the neighboring country with tungsten?",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["spain", "portugal"],
                    "commodities": ["lithium", "tungsten"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["lithium", "tungsten"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "refinement",
                "query": "Keep solely those that are still operating today",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["spain", "portugal"],
                    "commodities": ["lithium", "tungsten"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["lithium", "tungsten"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": ["active"],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "test_category": "removal",
                "query": "Discard Spain from the selection",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["portugal"],
                    "commodities": ["lithium", "tungsten"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["lithium", "tungsten"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": ["active"],
                    "restored": None
                }
            }
        ]
    },

    # Episode 5: Mediterranean Corridor Exploration and Facility Filtering
    {
        "episode_id": "EP-05",
        "title": "Mediterranean Corridor Exploration and Facility Filtering",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Mining waste deposits in Greece",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["greece"],
                    "commodities": [],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": [],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "test_category": "expansion",
                "query": "Also add what we have registered in Italy",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["greece", "italy"],
                    "commodities": [],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": [],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "refinement",
                "query": "Keep only tailings storage facilities and ponds",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["greece", "italy"],
                    "commodities": [],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": [],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "test_category": "refinement",
                "query": "Filter for those containing titanium",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["greece", "italy"],
                    "commodities": ["titanium"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["titanium"],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 5,
                "test_category": "reset",
                "query": "Clear the map view",
                "expected_action": "reset",
                "expected_accumulated_filters": {
                    "countries": [],
                    "commodities": [],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": [],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            }
        ]
    },

    # Episode 6: Alpine Corridor with Environmental Acid Risk
    {
        "episode_id": "EP-06",
        "title": "Alpine Corridor with Environmental Acid Risk",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Facilities in Austria with manganese",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["austria"],
                    "commodities": ["manganese"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["manganese"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "test_category": "expansion",
                "query": "Include waste dumps in Germany",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["austria", "germany"],
                    "commodities": ["manganese"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["manganese"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "expansion",
                "query": "Also add tungsten minerals",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["austria", "germany"],
                    "commodities": ["manganese", "tungsten"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["manganese", "tungsten"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "test_category": "removal",
                "query": "Drop manganese from the search",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["austria", "germany"],
                    "commodities": ["tungsten"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["tungsten"],
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
                "query": "Lithium waste dumps in France",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["france"],
                    "commodities": ["lithium"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["lithium"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "test_category": "context",
                "query": "Apply the exact same criteria for Germany",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["france", "germany"],
                    "commodities": ["lithium"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["lithium"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "expansion",
                "query": "Also add cobalt",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["france", "germany"],
                    "commodities": ["lithium", "cobalt"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["lithium", "cobalt"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "test_category": "refinement",
                "query": "Keep only those that are still active operations",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["france", "germany"],
                    "commodities": ["lithium", "cobalt"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["lithium", "cobalt"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": ["active"],
                    "restored": None
                }
            },
            {
                "turn": 5,
                "test_category": "removal",
                "query": "Exclude French facilities",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["germany"],
                    "commodities": ["lithium", "cobalt"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["lithium", "cobalt"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": ["active"],
                    "restored": None
                }
            }
        ]
    },

    # Episode 8: Multi-Commodity Refinement and Subtraction
    {
        "episode_id": "EP-08",
        "title": "Multi-Commodity Refinement and Subtraction",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Sites with titanium and graphite in Italy",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["italy"],
                    "commodities": ["titanium", "graphite"],
                    "commodity_operator": "AND",
                    "commodities_and": ["titanium", "graphite"],
                    "commodities_or": [],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "test_category": "expansion",
                "query": "Also add locations in Greece",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["italy", "greece"],
                    "commodities": ["titanium", "graphite"],
                    "commodity_operator": "AND",
                    "commodities_and": ["titanium", "graphite"],
                    "commodities_or": [],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "removal",
                "query": "I am no longer interested in graphite, leave it out",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["italy", "greece"],
                    "commodities": ["titanium"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["titanium"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "test_category": "refinement",
                "query": "Narrow down to those not restored yet",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["italy", "greece"],
                    "commodities": ["titanium"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["titanium"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": False
                }
            }
        ]
    },

    # Episode 9: Polish-Czech Copper Exploration and Reset
    {
        "episode_id": "EP-09",
        "title": "Polish-Czech Copper Exploration and Reset",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Waste dumps in Poland",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["poland"],
                    "commodities": [],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": [],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "test_category": "expansion",
                "query": "Include facilities in Czechia",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["poland", "czechia"],
                    "commodities": [],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": [],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "refinement",
                "query": "Keep only those containing copper",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["poland", "czechia"],
                    "commodities": ["copper"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["copper"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "test_category": "removal",
                "query": "Remove Polish facilities from the filters",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["czechia"],
                    "commodities": ["copper"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["copper"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 5,
                "test_category": "reset",
                "query": "Display the entire European dataset again",
                "expected_action": "reset",
                "expected_accumulated_filters": {
                    "countries": [],
                    "commodities": [],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": [],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            }
        ]
    },

    # Episode 10: English Spatial Search with Regional Concepts
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
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": [],
                    "storage_facility_types": ["tailings storage facility", "pond"],
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
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": [],
                    "storage_facility_types": ["tailings storage facility", "pond"],
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
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["lithium", "cobalt"],
                    "storage_facility_types": ["tailings storage facility", "pond"],
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
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["lithium", "cobalt"],
                    "storage_facility_types": ["tailings storage facility", "pond"],
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
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": [],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            }
        ]
    },

    # Episode 11: English Elliptical Context and Neighbor Shift
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
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["tungsten"],
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
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["tungsten"],
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
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["tungsten"],
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
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["tungsten"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": False
                }
            }
        ]
    },

    # Episode 12: English Multi-Element Exclusion and Status Refinement
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
                    "commodity_operator": "AND",
                    "commodities_and": ["titanium", "graphite"],
                    "commodities_or": [],
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
                    "commodity_operator": "AND",
                    "commodities_and": ["titanium", "graphite"],
                    "commodities_or": [],
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
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["titanium"],
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
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["titanium"],
                    "storage_facility_types": [],
                    "project_status": ["active"],
                    "restored": None
                }
            }
        ]
    },

    # Episode 13: Atlantic Corridor Exploration
    {
        "episode_id": "EP-13",
        "title": "Atlantic Corridor Exploration",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Tailings ponds in Ireland",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["ireland"],
                    "commodities": [],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": [],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "test_category": "expansion",
                "query": "Include mining facilities in Spain",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["ireland", "spain"],
                    "commodities": [],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": [],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "refinement",
                "query": "Keep only those that are still operating today",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["ireland", "spain"],
                    "commodities": [],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": [],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": ["active"],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "test_category": "removal",
                "query": "Discard deposits in Ireland",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["spain"],
                    "commodities": [],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": [],
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
                "query": "Deposits with lithium and nickel in Finland",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["finland"],
                    "commodities": ["lithium", "nickel"],
                    "commodity_operator": "AND",
                    "commodities_and": ["lithium", "nickel"],
                    "commodities_or": [],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "test_category": "expansion",
                "query": "Also add mining sites in Sweden",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["finland", "sweden"],
                    "commodities": ["lithium", "nickel"],
                    "commodity_operator": "AND",
                    "commodities_and": ["lithium", "nickel"],
                    "commodities_or": [],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "refinement",
                "query": "Restrict query to tailings ponds",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["finland", "sweden"],
                    "commodities": ["lithium", "nickel"],
                    "commodity_operator": "AND",
                    "commodities_and": ["lithium", "nickel"],
                    "commodities_or": [],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "test_category": "removal",
                "query": "Drop nickel",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["finland", "sweden"],
                    "commodities": ["lithium"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["lithium"],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 5,
                "test_category": "reset",
                "query": "Clear all applied filters",
                "expected_action": "reset",
                "expected_accumulated_filters": {
                    "countries": [],
                    "commodities": [],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": [],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            }
        ]
    },

    # Episode 15: Environmental Legacy Liabilities with AMD Risk
    {
        "episode_id": "EP-015",
        "title": "Environmental Legacy Liabilities with AMD Risk",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Unrestored facilities in Germany",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["germany"],
                    "commodities": [],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": [],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": False
                }
            },
            {
                "turn": 2,
                "test_category": "expansion",
                "query": "Add those we have in Austria",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["germany", "austria"],
                    "commodities": [],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": [],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": False
                }
            },
            {
                "turn": 3,
                "test_category": "refinement",
                "query": "Keep only those with tungsten",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["germany", "austria"],
                    "commodities": ["tungsten"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["tungsten"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": False
                }
            },
            {
                "turn": 4,
                "test_category": "removal",
                "query": "Discard assets in Austria",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["germany"],
                    "commodities": ["tungsten"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["tungsten"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": False
                }
            }
        ]
    },

    # Episode 16: Refractory Technology Metals in Spain & Portugal
    {
        "episode_id": "EP-16",
        "title": "Refractory Technology Metals in Spain & Portugal",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Tungsten and tin waste dumps in Spain",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["spain"],
                    "commodities": ["tungsten", "tin"],
                    "commodity_operator": "AND",
                    "commodities_and": ["tungsten", "tin"],
                    "commodities_or": [],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "test_category": "expansion",
                "query": "Include Portugal in the selection",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["spain", "portugal"],
                    "commodities": ["tungsten", "tin"],
                    "commodity_operator": "AND",
                    "commodities_and": ["tungsten", "tin"],
                    "commodities_or": [],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "removal",
                "query": "Leave tin out",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["spain", "portugal"],
                    "commodities": ["tungsten"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["tungsten"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "test_category": "refinement",
                "query": "Keep only those that are still active today",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["spain", "portugal"],
                    "commodities": ["tungsten"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["tungsten"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": ["active"],
                    "restored": None
                }
            }
        ]
    },

    # Episode 17: Contextual Interrogative Continuity Across Regions
    {
        "episode_id": "EP-17",
        "title": "Contextual Interrogative Continuity Across Regions",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Tailings ponds in Greece",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["greece"],
                    "commodities": [],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": [],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "test_category": "context",
                "query": "And what do we have registered in Italy?",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["greece", "italy"],
                    "commodities": [],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": [],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "context",
                "query": "Of those you mentioned, which ones have nickel?",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["greece", "italy"],
                    "commodities": ["nickel"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["nickel"],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "test_category": "removal",
                "query": "Forget about Greece",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["italy"],
                    "commodities": ["nickel"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["nickel"],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": None
                }
            }
        ]
    },

    # Episode 18: German-Scandinavian Corridor with Rare Earths
    {
        "episode_id": "EP-18",
        "title": "German-Scandinavian Corridor with Rare Earths",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Waste dumps in Germany",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["germany"],
                    "commodities": [],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": [],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "test_category": "expansion",
                "query": "Also add those in northern Europe",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["germany", "sweden", "finland"],
                    "commodities": [],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": [],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "refinement",
                "query": "Keep exclusively rare earth elements",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["germany", "sweden", "finland"],
                    "commodities": ["rare earth elements"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["rare earth elements"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "test_category": "removal",
                "query": "Drop Germany",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["sweden", "finland"],
                    "commodities": ["rare earth elements"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["rare earth elements"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            }
        ]
    },

    # Episode 19: Complex Multi-Metal Subtractive Sequence
    {
        "episode_id": "EP-19",
        "title": "Complex Multi-Metal Subtractive Sequence",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Facilities with copper, cobalt and lithium in Portugal and Spain",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["portugal", "spain"],
                    "commodities": ["copper", "cobalt", "lithium"],
                    "commodity_operator": "AND",
                    "commodities_and": ["copper", "cobalt", "lithium"],
                    "commodities_or": [],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "test_category": "removal",
                "query": "Drop copper",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["portugal", "spain"],
                    "commodities": ["cobalt", "lithium"],
                    "commodity_operator": "AND",
                    "commodities_and": ["cobalt", "lithium"],
                    "commodities_or": [],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "removal",
                "query": "Discard Spain from the list",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["portugal"],
                    "commodities": ["cobalt", "lithium"],
                    "commodity_operator": "AND",
                    "commodities_and": ["cobalt", "lithium"],
                    "commodities_or": [],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "test_category": "refinement",
                "query": "Restrict to active facilities",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["portugal"],
                    "commodities": ["cobalt", "lithium"],
                    "commodity_operator": "AND",
                    "commodities_and": ["cobalt", "lithium"],
                    "commodities_or": [],
                    "storage_facility_types": [],
                    "project_status": ["active"],
                    "restored": None
                }
            }
        ]
    },

    # Episode 20: Cross-Border Mixed Scope Dialogue
    {
        "episode_id": "EP-20",
        "title": "Cross-Border Mixed Scope Dialogue",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Southern European countries like Greece or Albania that have nickel",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["greece"],
                    "commodities": ["nickel"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["nickel"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "test_category": "expansion",
                "query": "Add deposits in Italy",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["greece", "italy"],
                    "commodities": ["nickel"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["nickel"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "removal",
                "query": "Remove facilities in Greece",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["italy"],
                    "commodities": ["nickel"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["nickel"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "test_category": "refinement",
                "query": "Keep only tailings storage facilities and ponds",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["italy"],
                    "commodities": ["nickel"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["nickel"],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": None
                }
            }
        ]
    },

    # Episode 21: Consecutive Multi-Dimensional Refinements
    {
        "episode_id": "EP-21",
        "title": "Consecutive Multi-Dimensional Refinements",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Waste dumps in France and Germany",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["france", "germany"],
                    "commodities": [],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": [],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "test_category": "refinement",
                "query": "Keep only those containing lithium",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["france", "germany"],
                    "commodities": ["lithium"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["lithium"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "refinement",
                "query": "Of those, only the ones that are currently active",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["france", "germany"],
                    "commodities": ["lithium"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["lithium"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": ["active"],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "test_category": "refinement",
                "query": "And that also remain unrestored",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["france", "germany"],
                    "commodities": ["lithium"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["lithium"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": ["active"],
                    "restored": False
                }
            }
        ]
    },

    # Episode 22: Rapid Exploration Pivot and Context Rebuilding
    {
        "episode_id": "EP-22",
        "title": "Rapid Exploration Pivot and Context Rebuilding",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Tailings ponds in Sweden",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["sweden"],
                    "commodities": [],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": [],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "test_category": "reset",
                "query": "Clear search",
                "expected_action": "reset",
                "expected_accumulated_filters": {
                    "countries": [],
                    "commodities": [],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": [],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "search",
                "query": "Waste dumps in Spain with tantalum",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["spain"],
                    "commodities": ["tantalum"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["tantalum"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "test_category": "expansion",
                "query": "Also add facilities in Portugal",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["spain", "portugal"],
                    "commodities": ["tantalum"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["tantalum"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            }
        ]
    },

    # Episode 23: Anaphora with Negation and Mineral Substitution
    {
        "episode_id": "EP-23",
        "title": "Anaphora with Negation and Mineral Substitution",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Facilities in Finland with nickel",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["finland"],
                    "commodities": ["nickel"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["nickel"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "test_category": "context",
                "query": "Is there anything similar in Sweden?",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["finland", "sweden"],
                    "commodities": ["nickel"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["nickel"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "refinement",
                "query": "Discard those that have already been restored",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["finland", "sweden"],
                    "commodities": ["nickel"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["nickel"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": False
                }
            },
            {
                "turn": 4,
                "test_category": "removal",
                "query": "Remove nickel",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["finland", "sweden"],
                    "commodities": [],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": [],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": False
                }
            }
        ]
    },

    # Episode 24: Tailings and Dumps Contrast in Czechia and Poland
    {
        "episode_id": "EP-24",
        "title": "Tailings and Dumps Contrast in Czechia and Poland",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Tailings ponds in Czechia",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["czechia"],
                    "commodities": [],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": [],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "test_category": "expansion",
                "query": "Add waste dumps in Poland",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["czechia", "poland"],
                    "commodities": [],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": [],
                    "storage_facility_types": ["tailings storage facility", "pond", "waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "refinement",
                "query": "Keep only those containing copper",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["czechia", "poland"],
                    "commodities": ["copper"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["copper"],
                    "storage_facility_types": ["tailings storage facility", "pond", "waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "test_category": "removal",
                "query": "Remove Czechia from the search",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["poland"],
                    "commodities": ["copper"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["copper"],
                    "storage_facility_types": ["tailings storage facility", "pond", "waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 5,
                "test_category": "reset",
                "query": "Reset all criteria",
                "expected_action": "reset",
                "expected_accumulated_filters": {
                    "countries": [],
                    "commodities": [],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": [],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            }
        ]
    },

    # Episode 25: English Multi-Hop Anaphora and Asset Selection
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
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["lithium"],
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
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["lithium"],
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
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["lithium"],
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
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["lithium"],
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
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": [],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            }
        ]
    },

    # Episode 26: Baltic and Scandinavian Anaphora with Operational Refinement
    {
        "episode_id": "EP-26",
        "title": "Baltic and Scandinavian Anaphora with Operational Refinement",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Deposits with nickel in Finland",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["finland"],
                    "commodities": ["nickel"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["nickel"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "test_category": "context",
                "query": "And what do we have in the country next door?",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["finland", "sweden"],
                    "commodities": ["nickel"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["nickel"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "context",
                "query": "Which of those mentioned are still active today?",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["finland", "sweden"],
                    "commodities": ["nickel"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["nickel"],
                    "storage_facility_types": [],
                    "project_status": ["active"],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "test_category": "removal",
                "query": "Drop Swedish facilities",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["finland"],
                    "commodities": ["nickel"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["nickel"],
                    "storage_facility_types": [],
                    "project_status": ["active"],
                    "restored": None
                }
            },
            {
                "turn": 5,
                "test_category": "reset",
                "query": "Start over from scratch again",
                "expected_action": "reset",
                "expected_accumulated_filters": {
                    "countries": [],
                    "commodities": [],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": [],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            }
        ]
    },

    # Episode 27: Iberian Ellipsis and Multi-Commodity Synthesis
    {
        "episode_id": "EP-27",
        "title": "Iberian Ellipsis and Multi-Commodity Synthesis",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Lithium deposits in Portugal",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["portugal"],
                    "commodities": ["lithium"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["lithium"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "test_category": "context",
                "query": "Add what is in the Iberian peninsula containing tantalum",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["portugal", "spain"],
                    "commodities": ["lithium", "tantalum"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["lithium", "tantalum"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "refinement",
                "query": "Keep exclusively barren rock waste dumps",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["portugal", "spain"],
                    "commodities": ["lithium", "tantalum"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["lithium", "tantalum"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "test_category": "removal",
                "query": "Drop tantalum",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["portugal", "spain"],
                    "commodities": ["lithium"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["lithium"],
                    "storage_facility_types": ["waste dump"],
                    "project_status": [],
                    "restored": None
                }
            }
        ]
    },

    # Episode 28: English Deictic Reference and Environmental Constraints
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
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": [],
                    "storage_facility_types": ["tailings storage facility", "pond"],
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
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": [],
                    "storage_facility_types": ["tailings storage facility", "pond"],
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
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": [],
                    "storage_facility_types": ["tailings storage facility", "pond"],
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
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": [],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": False
                }
            }
        ]
    },

    # Episode 29: Interrogative Status Shift in Alpine Region
    {
        "episode_id": "EP-29",
        "title": "Interrogative Status Shift in Alpine Region",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Tailings ponds in Austria",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["austria"],
                    "commodities": [],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": [],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "test_category": "context",
                "query": "And what do we have in Italy?",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["austria", "italy"],
                    "commodities": [],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": [],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "context",
                "query": "From the previous ones, are there any that are inactive or abandoned?",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["austria", "italy"],
                    "commodities": [],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": [],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": ["inactive"],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "test_category": "removal",
                "query": "Forget about Italy",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["austria"],
                    "commodities": [],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": [],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": ["inactive"],
                    "restored": None
                }
            },
            {
                "turn": 5,
                "test_category": "reset",
                "query": "Reset filters and display the entire map",
                "expected_action": "reset",
                "expected_accumulated_filters": {
                    "countries": [],
                    "commodities": [],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": [],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            }
        ]
    },

    # Episode 30: Complex Contextual Transfer and Refinement
    {
        "episode_id": "EP-30",
        "title": "Complex Contextual Transfer and Refinement",
        "turns": [
            {
                "turn": 1,
                "test_category": "search",
                "query": "Mining waste deposits in Greece",
                "expected_action": "new_search",
                "expected_accumulated_filters": {
                    "countries": ["greece"],
                    "commodities": [],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": [],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 2,
                "test_category": "context",
                "query": "And what do we have in Spain with copper?",
                "expected_action": "expand",
                "expected_accumulated_filters": {
                    "countries": ["greece", "spain"],
                    "commodities": ["copper"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["copper"],
                    "storage_facility_types": [],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 3,
                "test_category": "refinement",
                "query": "Restrict to tailings storage facilities and ponds",
                "expected_action": "refine",
                "expected_accumulated_filters": {
                    "countries": ["greece", "spain"],
                    "commodities": ["copper"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["copper"],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": None
                }
            },
            {
                "turn": 4,
                "test_category": "removal",
                "query": "Remove Greek facilities",
                "expected_action": "remove",
                "expected_accumulated_filters": {
                    "countries": ["spain"],
                    "commodities": ["copper"],
                    "commodity_operator": "OR",
                    "commodities_and": [],
                    "commodities_or": ["copper"],
                    "storage_facility_types": ["tailings storage facility", "pond"],
                    "project_status": [],
                    "restored": None
                }
            }
        ]
    }
]

if __name__ == "__main__":
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(episodes, f, indent=2, ensure_ascii=False)
    total_turns = sum(len(ep["turns"]) for ep in episodes)
    print(f"Successfully generated {len(episodes)} episodes ({total_turns} turns) in English with boolean operators to {OUTPUT_FILE}")
