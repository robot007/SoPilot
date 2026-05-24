from __future__ import annotations

import unittest

from sopilot_rules.rules.above import evaluate_above
from sopilot_rules.rules.base import EvaluationContext
from sopilot_rules.schema import AboveRule, Detection


def det(tag, y1, y2, confidence=0.9, frame="frame"):
    return Detection(
        id="%s_%s" % (tag, y1),
        frame_id=frame,
        timestamp_sec=1,
        tag=tag,
        confidence=confidence,
        bbox={"x1": 0, "y1": y1, "x2": 100, "y2": y2},
    )


class AboveRuleTests(unittest.TestCase):
    def rule(self):
        return AboveRule(
            id="above",
            step_id="S1",
            type="above",
            source_tag="sleeve",
            target_tag="upper_arm",
            margin_px=20,
            ambiguity_margin_px=30,
        )

    def test_passes_when_source_is_above_target(self):
        result = evaluate_above(
            self.rule(),
            EvaluationContext(
                detections=[det("sleeve", 100, 140), det("upper_arm", 220, 260)],
                events=[],
                prior_results={},
            ),
        )
        self.assertEqual(result.status, "passed")

    def test_fails_when_source_is_below_target(self):
        result = evaluate_above(
            self.rule(),
            EvaluationContext(
                detections=[det("sleeve", 220, 260), det("upper_arm", 100, 140)],
                events=[],
                prior_results={},
            ),
        )
        self.assertEqual(result.status, "failed")

    def test_uncertain_when_relation_is_borderline(self):
        result = evaluate_above(
            self.rule(),
            EvaluationContext(
                detections=[det("sleeve", 100, 140), det("upper_arm", 110, 150)],
                events=[],
                prior_results={},
            ),
        )
        self.assertEqual(result.status, "uncertain")

    def test_uncertain_when_target_missing(self):
        result = evaluate_above(
            self.rule(),
            EvaluationContext(detections=[det("sleeve", 100, 140)], events=[], prior_results={}),
        )
        self.assertEqual(result.status, "uncertain")


if __name__ == "__main__":
    unittest.main()
