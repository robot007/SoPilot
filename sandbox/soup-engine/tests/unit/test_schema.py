from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from pydantic import ValidationError

from sopilot_rules.schema import BBox, Detection, SoupPackage

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "bp"


class SchemaTests(unittest.TestCase):
    def load_package_data(self):
        return json.loads((FIXTURE_DIR / "bp_monitor.soup.json").read_text(encoding="utf-8"))

    def test_valid_bp_package_loads(self):
        package = SoupPackage.model_validate(self.load_package_data())
        self.assertEqual(package.package.id, "bp_monitor_sop_checker")
        self.assertEqual(len(package.rules), 5)
        self.assertEqual(package.rules[1].type, "any_of")
        self.assertEqual([condition.type for condition in package.rules[1].conditions], ["not_exists", "overlap"])

    def test_duplicate_rule_id_rejected(self):
        data = self.load_package_data()
        data["rules"][1]["id"] = data["rules"][0]["id"]
        with self.assertRaises(ValidationError):
            SoupPackage.model_validate(data)

    def test_unknown_tag_rejected(self):
        data = self.load_package_data()
        data["rules"][0]["tag"] = "not_a_tag"
        with self.assertRaises(ValidationError):
            SoupPackage.model_validate(data)

    def test_unknown_step_rejected(self):
        data = self.load_package_data()
        data["rules"][0]["step_id"] = "not_a_step"
        with self.assertRaises(ValidationError):
            SoupPackage.model_validate(data)

    def test_future_major_schema_rejected(self):
        data = self.load_package_data()
        data["schema_version"] = "1.0.0"
        with self.assertRaises(ValidationError):
            SoupPackage.model_validate(data)

    def test_invalid_bbox_rejected(self):
        with self.assertRaises(ValidationError):
            BBox(x1=10, y1=0, x2=5, y2=20)

    def test_invalid_confidence_rejected(self):
        with self.assertRaises(ValidationError):
            Detection(
                frame_id="f",
                timestamp_sec=0,
                tag="cuff",
                confidence=1.5,
                bbox={"x1": 0, "y1": 0, "x2": 1, "y2": 1},
            )

    def test_missing_required_rule_field_rejected(self):
        data = self.load_package_data()
        broken = copy.deepcopy(data)
        del broken["rules"][1]["conditions"][1]["source_tag"]
        with self.assertRaises(ValidationError):
            SoupPackage.model_validate(broken)

    def test_any_of_condition_unknown_tag_rejected(self):
        data = self.load_package_data()
        data["rules"][1]["conditions"][0]["tag"] = "not_a_tag"
        with self.assertRaises(ValidationError):
            SoupPackage.model_validate(data)

    def test_any_of_duplicate_condition_id_rejected(self):
        data = self.load_package_data()
        data["rules"][1]["conditions"][1]["id"] = data["rules"][1]["conditions"][0]["id"]
        with self.assertRaises(ValidationError):
            SoupPackage.model_validate(data)


if __name__ == "__main__":
    unittest.main()
