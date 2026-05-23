#!/usr/bin/env python3
"""
Line-oriented YOLO MLX face detection worker for FaceBoxDemo.

Input:  one JSON object per line with base64 JPEG data.
Output: one JSON object per line with pixel-space detections.

When the model is COCO-trained (class 0 = person, not face), the worker
approximates a face box from the upper portion of each person bbox. Enable
this via YOLO_MLX_APPROX_FACE_FROM_PERSON=1 (default on).
"""

from __future__ import annotations

import base64
import io
import json
import os
import sys
from pathlib import Path

import numpy as np
from PIL import Image


# Protocol stdout is captured up front so any stray prints (MLX/Metal banner,
# YOLO progress, etc.) cannot corrupt the JSON-lines stream.
_PROTOCOL_STDOUT = sys.stdout
sys.stdout = sys.stderr


def write_response(payload: dict) -> None:
    _PROTOCOL_STDOUT.write(json.dumps(payload, separators=(",", ":")) + "\n")
    _PROTOCOL_STDOUT.flush()


def env_flag(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def parse_face_class_ids() -> set[int]:
    raw = os.environ.get("YOLO_MLX_FACE_CLASS_IDS", "0")
    values: set[int] = set()
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        values.add(int(part))
    return values or {0}


def load_model():
    model_path = os.environ.get("YOLO_MLX_MODEL")
    if not model_path:
        raise RuntimeError("YOLO_MLX_MODEL is not set")

    path = Path(model_path)
    if not path.exists():
        raise RuntimeError(f"YOLO MLX model does not exist: {path}")

    from yolo26mlx import YOLO

    return YOLO(str(path), verbose=False)


def decode_image(payload: dict) -> np.ndarray:
    encoded = payload.get("image")
    if not isinstance(encoded, str):
        raise ValueError("Missing base64 image")

    image_bytes = base64.b64decode(encoded)
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return np.array(image)


def approximate_face_box(
    x1: float, y1: float, x2: float, y2: float,
    height_ratio: float, width_ratio: float, aspect: float,
) -> tuple[float, float, float, float]:
    """Derive a face bbox from a person bbox.

    Takes the top portion of the person box as the face region:
      face_h = height_ratio * person_h
      face_w = min(width_ratio * person_w, aspect * face_h)
      centered horizontally, anchored at the top of the person bbox.
    """
    person_w = max(x2 - x1, 1.0)
    person_h = max(y2 - y1, 1.0)

    face_h = person_h * height_ratio
    face_w = min(person_w * width_ratio, aspect * face_h)

    cx = (x1 + x2) / 2.0
    fx1 = cx - face_w / 2.0
    fy1 = y1
    fx2 = cx + face_w / 2.0
    fy2 = y1 + face_h

    return fx1, fy1, fx2, fy2


def extract_boxes(
    result,
    face_class_ids: set[int],
    approximate: bool,
    height_ratio: float,
    width_ratio: float,
    aspect: float,
) -> list[dict]:
    boxes = getattr(result, "boxes", None)
    if boxes is None:
        return []

    xyxy = np.asarray(boxes.xyxy)
    conf = np.asarray(boxes.conf)
    cls = np.asarray(boxes.cls).astype(int)

    detections: list[dict] = []
    for box, score, class_id in zip(xyxy, conf, cls):
        if class_id not in face_class_ids:
            continue

        x1, y1, x2, y2 = (float(v) for v in box)
        if approximate:
            x1, y1, x2, y2 = approximate_face_box(
                x1, y1, x2, y2,
                height_ratio=height_ratio,
                width_ratio=width_ratio,
                aspect=aspect,
            )

        detections.append(
            {
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "confidence": float(score),
            }
        )
    return detections


def main() -> int:
    try:
        model = load_model()
        face_class_ids = parse_face_class_ids()
        confidence = float(os.environ.get("YOLO_MLX_CONF", "0.35"))
        image_size = int(os.environ.get("YOLO_MLX_IMAGE_SIZE", "640"))
        approximate = env_flag("YOLO_MLX_APPROX_FACE_FROM_PERSON", True)
        height_ratio = float(os.environ.get("YOLO_MLX_FACE_HEIGHT_RATIO", "0.22"))
        width_ratio = float(os.environ.get("YOLO_MLX_FACE_WIDTH_RATIO", "0.55"))
        aspect = float(os.environ.get("YOLO_MLX_FACE_ASPECT", "0.78"))
    except Exception as exc:
        write_response({"ok": False, "error": f"init: {exc}", "detections": []})
        return 1

    for line in sys.stdin:
        try:
            payload = json.loads(line)
            image = decode_image(payload)
            results = model.predict(image, conf=confidence, imgsz=image_size, rect=False)
            detections = (
                extract_boxes(
                    results[0],
                    face_class_ids=face_class_ids,
                    approximate=approximate,
                    height_ratio=height_ratio,
                    width_ratio=width_ratio,
                    aspect=aspect,
                )
                if results
                else []
            )
            write_response({"ok": True, "error": None, "detections": detections})
        except Exception as exc:
            write_response({"ok": False, "error": str(exc), "detections": []})

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
