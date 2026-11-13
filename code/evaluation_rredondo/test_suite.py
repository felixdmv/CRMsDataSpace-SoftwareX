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

EVAL_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = EVAL_DIR.parent
CODE_DIR = PROJECT_ROOT / "code"

if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from agent import process_chat_message


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


if __name__ == "__main__":
    unittest.main()
