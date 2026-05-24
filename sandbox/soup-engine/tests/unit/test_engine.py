from __future__ import annotations

import json
import unittest
from pathlib import Path

from sopilot_rules import RuleEngine, load_soup

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "bp"


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.engine = RuleEngine(load_soup(FIXTURE_DIR / "bp_monitor.soup.json"))

    def test_engine_returns_failed_when_any_required_step_fails(self):
        fixture = json.loads((FIXTURE_DIR / "sleeve_not_rolled.json").read_text(encoding="utf-8"))
        result = self.engine.evaluate(fixture["detections"], fixture["events"])
        self.assertEqual(result.status, "failed")

    def test_engine_returns_needs_review_when_required_step_is_uncertain(self):
        fixture = json.loads((FIXTURE_DIR / "low_confidence_cuff.json").read_text(encoding="utf-8"))
        result = self.engine.evaluate(fixture["detections"], fixture["events"])
        self.assertEqual(result.status, "needs_review")

    def test_result_json_is_stable_and_parseable(self):
        fixture = json.loads((FIXTURE_DIR / "all_pass.json").read_text(encoding="utf-8"))
        result = self.engine.evaluate(fixture["detections"], fixture["events"])
        decoded = json.loads(result.to_json())
        self.assertEqual(decoded["status"], "passed")
        self.assertIn("privacy_log", decoded)


if __name__ == "__main__":
    unittest.main()
