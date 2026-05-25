#!/usr/bin/env python3
"""
Face Detection on Image/Video File
==================================

Runs YuNet face detection on a static image or video file.
Use this to verify face detection works without needing camera permissions.

Usage:
    python sandbox/test-face-image.py --input images/bus.jpg
    python sandbox/test-face-image.py --input ~/Downloads/my_video.mp4
    python sandbox/test-face-image.py --input 0   # webcam (same as test-camera.py)

Output:
    results/face_detected_<timestamp>.jpg
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = PROJECT_ROOT / "models" / "face_detection_yunet_2023mar.onnx"
RESULTS_DIR = PROJECT_ROOT / "results"

COLOR_BOX = (0, 255, 0)
COLOR_TEXT = (0, 255, 0)


def draw_face_box(frame, x1, y1, x2, y2, confidence, font_scale=0.6, thickness=2):
    cv2.rectangle(frame, (x1, y1), (x2, y2), COLOR_BOX, thickness)
    label = f"face {confidence:.0%}"
    (text_w, text_h), baseline = cv2.getTextSize(
        label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness
    )
    cv2.rectangle(
        frame,
        (x1, y1 - text_h - baseline - 4),
        (x1 + text_w + 4, y1),
        (0, 0, 0),
        -1,
    )
    cv2.putText(
        frame,
        label,
        (x1 + 2, y1 - baseline - 2),
        cv2.FONT_HERSHEY_SIMPLEX,
        font_scale,
        COLOR_TEXT,
        thickness,
        cv2.LINE_AA,
    )


def detect_faces(detector, frame, conf_threshold=0.6):
    h, w = frame.shape[:2]
    detector.setInputSize((w, h))
    _, faces = detector.detect(frame)

    detected = []
    if faces is not None:
        for face in faces:
            confidence = float(face[14])
            if confidence < conf_threshold:
                continue
            x, y, fw, fh = face[:4].astype(int)
            x1, y1 = max(0, x), max(0, y)
            x2, y2 = min(w, x + fw), min(h, y + fh)
            detected.append((x1, y1, x2, y2, confidence))
    return detected


def process_image(input_path, detector, conf_threshold):
    frame = cv2.imread(str(input_path))
    if frame is None:
        print(f"Error: Could not load image: {input_path}")
        sys.exit(1)

    faces = detect_faces(detector, frame, conf_threshold)

    for x1, y1, x2, y2, conf in faces:
        draw_face_box(frame, x1, y1, x2, y2, conf)

    # Add summary text
    summary = f"Faces detected: {len(faces)}"
    cv2.putText(
        frame, summary, (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA
    )

    # Save result
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    if input_path.is_file():
        stem = input_path.stem
    else:
        stem = "image"
    out_path = RESULTS_DIR / f"face_detected_{stem}.jpg"
    cv2.imwrite(str(out_path), frame)

    print(f"  Detected {len(faces)} face(s)")
    for i, (x1, y1, x2, y2, conf) in enumerate(faces, 1):
        print(f"    {i}. confidence={conf:.2%}  box=({x1},{y1},{x2},{y2})")
    print(f"  Result saved: {out_path}")

    # Show window (if display is available)
    try:
        cv2.imshow("Face Detection Result", frame)
        print("  Press any key to close window...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    except cv2.error:
        print("  (No display available — skipping window, file still saved)")


def process_video(input_path, detector, conf_threshold):
    cap = cv2.VideoCapture(str(input_path))
    if not cap.isOpened():
        print(f"Error: Could not open video: {input_path}")
        sys.exit(1)

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stem = Path(input_path).stem
    out_path = RESULTS_DIR / f"face_detected_{stem}.mp4"

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(out_path), fourcc, fps, (width, height))

    frame_count = 0
    face_total = 0
    start = time.time()

    print(f"  Processing video: {input_path.name}")
    print(f"  Resolution: {width}x{height}, FPS: {fps:.1f}")
    print("  Press 'q' to quit early")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        faces = detect_faces(detector, frame, conf_threshold)
        face_total += len(faces)

        for x1, y1, x2, y2, conf in faces:
            draw_face_box(frame, x1, y1, x2, y2, conf)

        # HUD
        cv2.putText(
            frame, f"Faces: {len(faces)}", (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA
        )

        writer.write(frame)
        try:
            cv2.imshow("Face Detection", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                print("  Stopped early by user")
                break
        except cv2.error:
            pass  # No display available

        frame_count += 1

    elapsed = time.time() - start
    cap.release()
    writer.release()
    cv2.destroyAllWindows()

    print(f"  Processed {frame_count} frames in {elapsed:.1f}s")
    print(f"  Total faces detected: {face_total}")
    print(f"  Output saved: {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Face Detection on Image or Video")
    parser.add_argument(
        "--input", "-i",
        type=str,
        required=True,
        help="Path to image, video, or '0' for webcam",
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.6,
        help="Confidence threshold (default: 0.6)",
    )
    args = parser.parse_args()

    if not MODEL_PATH.exists():
        print(f"Error: Model not found: {MODEL_PATH}")
        sys.exit(1)

    detector = cv2.FaceDetectorYN_create(
        str(MODEL_PATH), "", (320, 320), args.conf, 0.3, 5000
    )

    input_str = args.input
    if input_str == "0":
        # Webcam mode - delegates to test-camera.py logic
        print("Use 'python sandbox/test-camera.py' for webcam mode")
        sys.exit(1)

    input_path = Path(input_str)
    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        sys.exit(1)

    # Detect file type by extension
    ext = input_path.suffix.lower()
    image_exts = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}
    video_exts = {".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv"}

    print("=" * 50)
    print("  Face Detection Test")
    print("=" * 50)

    if ext in image_exts:
        process_image(input_path, detector, args.conf)
    elif ext in video_exts:
        process_video(input_path, detector, args.conf)
    else:
        print(f"Unknown file type: {ext}")
        print(f"Supported images: {image_exts}")
        print(f"Supported videos: {video_exts}")
        sys.exit(1)

    print("=" * 50)
    print("  Done!")
    print("=" * 50)


if __name__ == "__main__":
    main()
