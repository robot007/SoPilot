from __future__ import annotations

import unittest

from sopilot_rules.geometry import above_with_margin, bbox_area, bbox_center, center_distance_px, iou, overlap_ratio
from sopilot_rules.schema import BBox


class GeometryTests(unittest.TestCase):
    def test_iou_fully_overlapping(self):
        box = BBox(x1=0, y1=0, x2=100, y2=100)
        self.assertEqual(iou(box, box), 1.0)

    def test_iou_non_overlapping(self):
        a = BBox(x1=0, y1=0, x2=10, y2=10)
        b = BBox(x1=20, y1=20, x2=30, y2=30)
        self.assertEqual(iou(a, b), 0.0)

    def test_overlap_ratio_uses_source_area(self):
        source = BBox(x1=0, y1=0, x2=10, y2=10)
        target = BBox(x1=0, y1=0, x2=5, y2=10)
        self.assertEqual(overlap_ratio(source, target), 0.5)

    def test_center_distance(self):
        a = BBox(x1=0, y1=0, x2=10, y2=10)
        b = BBox(x1=30, y1=40, x2=40, y2=50)
        self.assertEqual(center_distance_px(a, b), 50.0)

    def test_bbox_area_and_center(self):
        box = BBox(x1=10, y1=20, x2=30, y2=60)
        self.assertEqual(bbox_area(box), 800)
        self.assertEqual(bbox_center(box), (20, 40))

    def test_above_with_margin_passes(self):
        cuff = BBox(x1=0, y1=100, x2=100, y2=140)
        elbow = BBox(x1=0, y1=220, x2=100, y2=260)
        self.assertEqual(above_with_margin(cuff, elbow, 20, 30), "passed")

    def test_above_with_margin_uncertain_boundary(self):
        cuff = BBox(x1=0, y1=100, x2=100, y2=140)
        elbow = BBox(x1=0, y1=110, x2=100, y2=150)
        self.assertEqual(above_with_margin(cuff, elbow, 20, 30), "uncertain")

    def test_above_with_margin_fails(self):
        cuff = BBox(x1=0, y1=220, x2=100, y2=260)
        elbow = BBox(x1=0, y1=100, x2=100, y2=140)
        self.assertEqual(above_with_margin(cuff, elbow, 20, 30), "failed")


if __name__ == "__main__":
    unittest.main()
