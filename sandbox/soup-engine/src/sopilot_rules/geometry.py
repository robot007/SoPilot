"""Deterministic geometry helpers for bounding-box rules."""

from __future__ import annotations

import math
from typing import Tuple

from .schema import BBox


def bbox_width(box: BBox) -> float:
    return box.x2 - box.x1


def bbox_height(box: BBox) -> float:
    return box.y2 - box.y1


def bbox_area(box: BBox) -> float:
    return bbox_width(box) * bbox_height(box)


def bbox_center(box: BBox) -> Tuple[float, float]:
    return ((box.x1 + box.x2) / 2.0, (box.y1 + box.y2) / 2.0)


def intersection_area(a: BBox, b: BBox) -> float:
    x1 = max(a.x1, b.x1)
    y1 = max(a.y1, b.y1)
    x2 = min(a.x2, b.x2)
    y2 = min(a.y2, b.y2)
    if x2 <= x1 or y2 <= y1:
        return 0.0
    return (x2 - x1) * (y2 - y1)


def iou(a: BBox, b: BBox) -> float:
    intersection = intersection_area(a, b)
    union = bbox_area(a) + bbox_area(b) - intersection
    if union <= 0:
        return 0.0
    return intersection / union


def overlap_ratio(source: BBox, target: BBox) -> float:
    """Return source-over-target coverage: intersection / source area."""

    area = bbox_area(source)
    if area <= 0:
        return 0.0
    return intersection_area(source, target) / area


def center_distance_px(a: BBox, b: BBox) -> float:
    ax, ay = bbox_center(a)
    bx, by = bbox_center(b)
    return math.hypot(ax - bx, ay - by)


def vertical_delta_px(source: BBox, target: BBox) -> float:
    """Positive value means the source center is above the target center."""

    _, source_y = bbox_center(source)
    _, target_y = bbox_center(target)
    return target_y - source_y


def above_with_margin(source: BBox, target: BBox, margin_px: float, ambiguity_margin_px: float) -> str:
    delta = vertical_delta_px(source, target)
    if delta >= margin_px:
        return "passed"
    if delta >= margin_px - ambiguity_margin_px:
        return "uncertain"
    return "failed"
