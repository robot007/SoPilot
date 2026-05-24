from __future__ import annotations

import unittest

from sopilot_rules.rules.base import EvaluationContext
from sopilot_rules.rules.overlap import evaluate_overlap
from sopilot_rules.schema import Detection, OverlapRule


def det(tag, x1, y1, x2, y2, confidence=0.9, frame="frame"):
    return Detection(
        id="%s_%s" % (tag, x1),
        frame_id=frame,
        timestamp_sec=1,
        tag=tag,
        confidence=confidence,
        bbox={"x1": x1, "y1": y1, "x2": x2, "y2": y2},
    )


class OverlapRuleTests(unittest.TestCase):
    def rule(self):
        return OverlapRule(
            id="overlap",
            step_id="S2",
            type="overlap",
            source_tag="cuff",
            target_tag="upper_arm",
            min_overlap_ratio=0.25,
        )

    def test_passes_when_source_overlaps_target(self):
        result = evaluate_overlap(
            self.rule(),
            EvaluationContext(
                detections=[det("upper_arm", 0, 0, 100, 100), det("cuff", 10, 10, 50, 50)],
                events=[],
                prior_results={},
            ),
        )
        self.assertEqual(result.status, "passed")

    def test_fails_when_overlap_is_too_small(self):
        result = evaluate_overlap(
            self.rule(),
            EvaluationContext(
                detections=[det("upper_arm", 0, 0, 100, 100), det("cuff", 200, 200, 250, 250)],
                events=[],
                prior_results={},
            ),
        )
        self.assertEqual(result.status, "failed")

    def test_uncertain_when_overlap_is_borderline(self):
        result = evaluate_overlap(
            self.rule(),
            EvaluationContext(
                detections=[det("upper_arm", 0, 0, 20, 100), det("cuff", 0, 0, 100, 100)],
                events=[],
                prior_results={},
            ),
        )
        self.assertEqual(result.status, "uncertain")

    def test_uncertain_when_source_is_low_confidence(self):
        result = evaluate_overlap(
            self.rule(),
            EvaluationContext(
                detections=[
                    det("upper_arm", 0, 0, 100, 100),
                    det("cuff", 10, 10, 50, 50, confidence=0.2),
                ],
                events=[],
                prior_results={},
            ),
        )
        self.assertEqual(result.status, "uncertain")


if __name__ == "__main__":
    unittest.main()
