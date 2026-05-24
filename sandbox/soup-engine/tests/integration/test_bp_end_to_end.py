from __future__ import annotations

import json
import unittest
from pathlib import Path

from sopilot_rules import RuleEngine, load_soup

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "bp"
FIXTURE_NAMES = [
    "all_pass.json",
    "sleeve_not_rolled.json",
    "missing_sleeve.json",
    "cuff_not_on_upper_arm.json",
    "measure_too_early.json",
    "no_measure_event.json",
    "low_confidence_cuff.json",
    "multiple_good_frames.json",
]


class BPEndToEndTests(unittest.TestCase):
    def setUp(self):
        self.engine = RuleEngine(load_soup(FIXTURE_DIR / "bp_monitor.soup.json"))

    def load_fixture(self, name):
        return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))

    def test_all_bp_fixtures_match_expected_statuses(self):
        for name in FIXTURE_NAMES:
            with self.subTest(name=name):
                fixture = self.load_fixture(name)
                result = self.engine.evaluate(fixture["detections"], fixture["events"], run_id=fixture["name"])
                expected = fixture["expected"]
                self.assertEqual(result.status, expected["status"])
                by_status = _steps_by_status(result)
                self.assertEqual(by_status["failed"], sorted(expected["failed_steps"]))
                self.assertEqual(by_status["uncertain"], sorted(expected["uncertain_steps"]))

    def test_engine_output_is_deterministic(self):
        fixture = self.load_fixture("all_pass.json")
        first = self.engine.evaluate(fixture["detections"], fixture["events"], run_id="determinism")
        second = self.engine.evaluate(fixture["detections"], fixture["events"], run_id="determinism")
        self.assertEqual(first.to_json(), second.to_json())

    def test_privacy_log_is_local_first_for_bp_fixture(self):
        fixture = self.load_fixture("all_pass.json")
        result = self.engine.evaluate(fixture["detections"], fixture["events"])
        self.assertFalse(result.privacy_log.cloud_vlm_used)
        self.assertFalse(result.privacy_log.raw_video_leaves_device)
        self.assertEqual(result.privacy_log.final_decision_source, "local_rule_engine")

    def test_multiple_good_frames_selects_best_cuff_evidence(self):
        fixture = self.load_fixture("multiple_good_frames.json")
        result = self.engine.evaluate(fixture["detections"], fixture["events"])
        cuff_evidence = [
            evidence
            for evidence in result.evidence
            if evidence.step_id == "S2"
        ]
        self.assertTrue(cuff_evidence)
        self.assertTrue(any(item.frame_id == "frame_006" for item in cuff_evidence))

    def test_bp_package_has_only_requested_tags_and_states(self):
        package = load_soup(FIXTURE_DIR / "bp_monitor.soup.json")
        self.assertEqual(
            [tag.id for tag in package.tags],
            ["blood_pressure_monitor", "cuff", "upper_arm", "sleeve"],
        )
        self.assertEqual(
            [(step.id, step.name) for step in package.steps],
            [
                ("S0", "Start"),
                ("S1", "Roll sleeve"),
                ("S2", "Put Cuff On Upper Arm"),
                ("S3", "Measure"),
                ("S4", "Done"),
            ],
        )


def _steps_by_status(result):
    return {
        "failed": sorted(step.step_id for step in result.steps if step.status == "failed"),
        "uncertain": sorted(step.step_id for step in result.steps if step.status == "uncertain"),
    }


if __name__ == "__main__":
    unittest.main()
