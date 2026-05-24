from __future__ import annotations

import unittest

from sopilot_rules.privacy import build_privacy_log


class PrivacyTests(unittest.TestCase):
    def test_privacy_defaults_are_local_first(self):
        log = build_privacy_log(["yolo", "demo_marker"])
        self.assertFalse(log.raw_video_leaves_device)
        self.assertFalse(log.sop_rules_leave_device)
        self.assertFalse(log.yolo_model_leaves_device)
        self.assertFalse(log.cloud_vlm_used)
        self.assertEqual(log.final_decision_source, "local_rule_engine")

    def test_local_vlm_source_sets_local_flag(self):
        self.assertTrue(build_privacy_log(["local_vlm"]).local_vlm_used)

    def test_cloud_vlm_source_sets_cloud_flag(self):
        self.assertTrue(build_privacy_log(["cloud_vlm"]).cloud_vlm_used)


if __name__ == "__main__":
    unittest.main()
