from __future__ import annotations

import unittest

from sopilot_rules.rules.any_of import evaluate_any_of
from sopilot_rules.rules.base import EvaluationContext
from sopilot_rules.schema import AnyOfRule, Detection


def det(tag, x1, y1, x2, y2, confidence=0.9, frame="frame", timestamp=1.0):
    return Detection(
        id="%s_%s" % (tag, x1),
        frame_id=frame,
        timestamp_sec=timestamp,
        tag=tag,
        confidence=confidence,
        bbox={"x1": x1, "y1": y1, "x2": x2, "y2": y2},
    )


class AnyOfRuleTests(unittest.TestCase):
    def rule(self):
        return AnyOfRule.model_validate(
            {
                "id": "any",
                "step_id": "S1",
                "type": "any_of",
                "conditions": [
                    {
                        "id": "no_sleeve",
                        "type": "not_exists",
                        "tag": "sleeve",
                        "min_confidence": 0.5,
                    },
                    {
                        "id": "sleeve_on_upper_arm",
                        "type": "overlap",
                        "source_tag": "sleeve",
                        "target_tag": "upper_arm",
                        "min_overlap_ratio": 0.25,
                        "min_confidence": 0.5,
                    },
                ],
            }
        )

    def test_passes_when_no_sleeve_is_detected(self):
        result = evaluate_any_of(
            self.rule(),
            EvaluationContext(
                detections=[det("upper_arm", 0, 0, 100, 100)],
                events=[],
                prior_results={},
            ),
        )
        self.assertEqual(result.status, "passed")
        self.assertIsNone(result.completed_at_sec)

    def test_passes_when_sleeve_overlaps_upper_arm(self):
        result = evaluate_any_of(
            self.rule(),
            EvaluationContext(
                detections=[
                    det("upper_arm", 0, 0, 100, 100, timestamp=1),
                    det("sleeve", 10, 10, 50, 50, timestamp=2),
                ],
                events=[],
                prior_results={},
            ),
        )
        self.assertEqual(result.status, "passed")
        self.assertEqual(result.completed_at_sec, 2)

    def test_fails_when_sleeve_exists_but_does_not_overlap_upper_arm(self):
        result = evaluate_any_of(
            self.rule(),
            EvaluationContext(
                detections=[
                    det("upper_arm", 0, 0, 100, 100),
                    det("sleeve", 200, 0, 250, 50),
                ],
                events=[],
                prior_results={},
            ),
        )
        self.assertEqual(result.status, "failed")

    def test_uncertain_when_no_pass_and_one_condition_is_uncertain(self):
        result = evaluate_any_of(
            self.rule(),
            EvaluationContext(
                detections=[
                    det("upper_arm", 0, 0, 100, 100),
                    det("sleeve", 10, 10, 50, 50, confidence=0.3),
                ],
                events=[],
                prior_results={},
            ),
        )
        self.assertEqual(result.status, "uncertain")


if __name__ == "__main__":
    unittest.main()
