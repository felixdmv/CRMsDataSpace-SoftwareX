#!/usr/bin/env python3
"""
test_suite.py
Automated unit & regression test suite for evaluation_rredondo.
Can be executed directly via:
    python3 evaluation_rredondo/test_suite.py
or via pytest:
    pytest evaluation_rredondo/test_suite.py
"""

import unittest
import sys
import json
from pathlib import Path
from unittest.mock import patch

EVAL_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = EVAL_DIR.parent
CODE_DIR = PROJECT_ROOT / "code"

if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from agent import process_chat_message
from benchmark_rredondo import (
    evaluate_boolean_sum,
    evaluate_conversational_memory,
    evaluate_single_turn
)


class TestEvaluationRRedondo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        battery_file = EVAL_DIR / "test_battery_rredondo.json"
        with open(battery_file, "r", encoding="utf-8") as f:
            cls.battery = json.load(f)

    def test_01_out_of_domain_sports_rejection(self):
        """Verify non-mining sports query is rejected without database search."""
        res = process_chat_message("¿Quién ganó el mundial de fútbol de 2022 en Catar?", provider="mock")
        self.assertEqual(res.get("num_found"), 0, "Non-mining query must return 0 documents")
        self.assertEqual(res.get("extracted_json", {}).get("intent"), "generic_qa")
        resp_lower = res.get("response_text", "").lower()
        self.assertTrue(any(kw in resp_lower for kw in ["fuera de ámbito", "out-of-scope", "non-mining"]))

    def test_02_out_of_domain_unsupported_country(self):
        """Verify non-EU country query (Chile) is rejected with clear jurisdiction notice."""
        res = process_chat_message("Muestra escombreras de litio en Chile", provider="mock")
        self.assertEqual(res.get("num_found"), 0, "Query for Chile must yield 0 results in European catalog")
        self.assertTrue(any(kw in res.get("response_text", "").lower() for kw in ["cobertura", "chile", "12 países", "out-of-scope"]))

    def test_03_out_of_domain_adversarial_sql(self):
        """Verify SQL injection is safely neutralized and produces 0 documents."""
        res = process_chat_message("SELECT * FROM users WHERE '1'='1' UNION SELECT password FROM admin; --", provider="mock")
        self.assertEqual(res.get("num_found"), 0, "Injection attempts must return 0 database records")

    def test_04_boolean_disjunction_sum_countries(self):
        """Verify disjunctive query evaluates exact mathematical sum of escombreras."""
        res = process_chat_message("Escombreras en España o Portugal", provider="mock")
        self.assertEqual(res.get("filters", {}).get("commodity_operator"), "OR")
        self.assertEqual(set(res.get("filters", {}).get("countries", [])), {"spain", "portugal"})
        # 3 waste dumps in Spain + 2 waste dumps in Portugal = 5
        self.assertEqual(res.get("num_found"), 5, "Disjunctive sum of Spain (3) + Portugal (2) waste dumps must equal 5")

    def test_05_boolean_conjunction_co_occurrence(self):
        """Verify conjunction requiring simultaneous co-occurrence in same facility."""
        res = process_chat_message("Escombreras con litio y cobalto", provider="mock")
        self.assertEqual(res.get("filters", {}).get("commodity_operator"), "AND")
        self.assertEqual(res.get("num_found"), 2, "Conjunction of lithium and cobalt in waste dumps must match exactly 2 sites (EU-CRM-045 and EU-CRM-097)")

    def test_06_boolean_conjunction_zero_result_disambiguation(self):
        """Verify zero-result conjunction triggers interactive disambiguation options."""
        res = process_chat_message("Balsas de relaves con litio y cobalto", provider="mock")
        self.assertEqual(res.get("filters", {}).get("commodity_operator"), "AND")
        self.assertEqual(res.get("num_found"), 0)
        self.assertIsNotNone(res.get("disambiguation_options"), "Zero-result conjunction must offer AND vs OR disambiguation options")

    def test_07_conversational_memory_expansion_y_tambien(self):
        """Verify conversational memory correctly handles 'y también...' additive expansion."""
        t1 = process_chat_message("Muestra escombreras en España", provider="mock")
        self.assertEqual(t1.get("num_found"), 3)

        t2 = process_chat_message("y también en Portugal", 
                                  provider="mock",
                                  conversation_history=t1.get("conversation_history"),
                                  current_filters=t1.get("current_filters"))
        self.assertEqual(t2.get("dialogue_action"), "expand", "'y también...' must trigger expansion dialogue action")
        self.assertEqual(set(t2.get("current_filters", {}).get("countries", [])), {"spain", "portugal"})
        self.assertEqual(t2.get("num_found"), 5, "Accumulated state must include all 5 Iberian waste dumps")

    def test_08_conversational_memory_refinement_de_esas(self):
        """Verify conversational memory progressive narrowing with 'de esas...'."""
        t1 = process_chat_message("Muestra escombreras en España", provider="mock")
        t2 = process_chat_message("y también en Portugal", 
                                  provider="mock",
                                  conversation_history=t1.get("conversation_history"),
                                  current_filters=t1.get("current_filters"))
        t3 = process_chat_message("y de esas solo las que tienen wolframio",
                                  provider="mock",
                                  conversation_history=t2.get("conversation_history"),
                                  current_filters=t2.get("current_filters"))
        self.assertEqual(t3.get("dialogue_action"), "refine", "'de esas...' must trigger refinement dialogue action")
        self.assertEqual(t3.get("current_filters", {}).get("commodities"), ["tungsten"])
        self.assertEqual(t3.get("num_found"), 2, "Must retain Iberian waste dumps and filter to tungsten (2 sites)")

    def test_09_conversational_memory_reset(self):
        """Verify conversation reset clears all accumulated filters back to 100 sites."""
        t1 = process_chat_message("Muestra escombreras en España", provider="mock")
        t2 = process_chat_message("reiniciar búsqueda",
                                  provider="mock",
                                  conversation_history=t1.get("conversation_history"),
                                  current_filters=t1.get("current_filters"))
        self.assertEqual(t2.get("dialogue_action"), "reset")
        self.assertEqual(t2.get("num_found"), 100, "Reset must restore complete 100-site European inventory")

    def test_10_single_turn_slot_metrics_are_accumulated_and_exact(self):
        test_case = {
            "id": "REG-SLOT",
            "query": "lithium in Spain",
            "expected_intent": "filter_search",
            "expected_filters": {
                "countries": ["spain"],
                "commodities": ["lithium"]
            }
        }
        response = {
            "extracted_json": {
                "intent": "filter_search",
                "filters": {"countries": [], "commodities": ["lithium"]}
            },
            "filters": {"countries": [], "commodities": ["lithium"]},
            "num_found": 1
        }
        with patch("benchmark_rredondo.process_chat_message", return_value=response):
            result = evaluate_single_turn("mock", [test_case])

        self.assertEqual(result["mean_slot_f1"], 50.0)
        self.assertEqual(result["passed_tests"], 0)

    def test_11_boolean_follow_up_uses_prior_conversation_and_annotations(self):
        prior_history = [{"role": "user", "content": "Spain"}]
        prior_response = {
            "conversation_history": prior_history,
            "current_filters": {"countries": ["spain"]}
        }
        current_response = {
            "filters": {
                "countries": ["spain", "portugal"],
                "storage_facility_types": [],
                "commodities_and": [],
                "commodities_or": [],
                "commodity_operator": "OR"
            },
            "num_found": 5,
            "matched_ids": ["S1"],
            "disambiguation_options": None
        }
        test_case = {
            "id": "REG-FOLLOW-UP",
            "prior_query": "Show waste dumps in Spain",
            "query": "and Portugal",
            "expected_operator": "OR",
            "expected_countries": ["spain", "portugal"],
            "expected_facility_types": [],
            "expected_commodities_and": [],
            "expected_commodities_or": [],
            "expected_count": 5,
            "expected_disambiguation": False,
            "expected_site_ids": ["S1"],
            "is_sum_query": True
        }
        with patch(
            "benchmark_rredondo.process_chat_message",
            side_effect=[prior_response, current_response]
        ) as process:
            result = evaluate_boolean_sum("mock", [test_case])

        follow_up_call = process.call_args_list[1]
        self.assertEqual(follow_up_call.kwargs["conversation_history"], prior_history)
        self.assertEqual(
            follow_up_call.kwargs["current_filters"],
            prior_response["current_filters"]
        )
        self.assertEqual(result["passed_tests"], 1)
        self.assertEqual(result["disambiguation_accuracy"], 100.0)
        self.assertEqual(result["site_ids_accuracy"], 100.0)

    def test_12_dst_checks_both_state_schemas_and_compound_logic(self):
        expected_state = {
            "countries": ["finland"],
            "commodities": ["lithium", "nickel", "cobalt"],
            "commodities_and": ["lithium", "nickel"],
            "commodities_or": ["cobalt"],
            "commodity_operator": "COMPOUND",
            "project_status": [],
            "restored": False
        }
        response = {
            "dialogue_action": "new_search",
            "current_filters": expected_state,
            "conversation_history": [],
            "num_found": 2
        }
        episodes = [
            {
                "episode_id": "REG-EXPECTED-FILTERS",
                "turns": [{
                    "turn": 1,
                    "query": "lithium and nickel or cobalt in Finland",
                    "expected_action": "new_search",
                    "expected_filters": expected_state,
                    "expected_count": 2
                }]
            },
            {
                "episode_id": "REG-ACCUMULATED-FILTERS",
                "turns": [{
                    "turn": 1,
                    "query": "lithium and nickel or cobalt in Finland",
                    "expected_action": "new_search",
                    "expected_accumulated_filters": expected_state,
                    "expected_count": 2
                }]
            }
        ]
        with patch(
            "benchmark_rredondo.process_chat_message",
            side_effect=[response, response]
        ):
            result = evaluate_conversational_memory("mock", episodes)

        self.assertEqual(result["passed_turns"], 2)
        self.assertEqual(result["commodity_operator_accuracy"], 100.0)
        self.assertEqual(result["commodity_logic_accuracy"], 100.0)
        self.assertEqual(result["restored_accuracy"], 100.0)
        self.assertIsNone(result["expansion_turn_pass_rate"])

    def test_13_compound_battery_case_has_and_or_labels(self):
        compound_case = next(
            case for case in self.battery["boolean_and_compound_logic"]
            if case["id"] == "CC-063"
        )
        self.assertEqual(compound_case["expected_commodities_and"], ["lithium", "nickel"])
        self.assertEqual(compound_case["expected_commodities_or"], ["cobalt"])


if __name__ == "__main__":
    unittest.main()
