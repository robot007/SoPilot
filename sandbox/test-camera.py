#!/usr/bin/env python3
"""
Face Detection Camera Test
==========================

Opens the default webcam and runs real-time face detection using
OpenCV's YuNet (FaceDetectorYN). Draws bounding boxes with
"face" labels and confidence scores.

Usage:
    cd /Users/zhensong/project/SoPilot
    source .venv/bin/activate
    python sandbox/test-camera.py

Controls:
    q / ESC  — Quit
    s        — Save current frame to results/capture_<timestamp>.jpg

Requirements:
    - models/face_detection_yunet_2023mar.onnx
    - Webcam (built-in or USB)
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = PROJECT_ROOT / "models" / "face_detection_yunet_2023mar.onnx"
RESULTS_DIR = PROJECT_ROOT / "results"

# YuNet input size
INPUT_SIZE = (320, 320)

# Confidence threshold
SCORE_THRESHOLD = 0.6
NMS_THRESHOLD = 0.3
TOP_K = 5000

# Colors (BGR)
COLOR_BOX = (0, 255, 0)       # Green
COLOR_TEXT = (0, 255, 0)      # Green
COLOR_BG = (0, 0, 0)          # Black background for text


def draw_face_box(
    frame: np.ndarray,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    confidence: float,
    font_scale: float = 0.6,
    thickness: int = 2,
) -> None:
    """Draw a bounding box with 'face' label and confidence percentage."""
    # Draw rectangle
    cv2.rectangle(frame, (x1, y1), (x2, y2), COLOR_BOX, thickness)

    # Prepare label text
    label = f"face {confidence:.0%}"
    (text_w, text_h), baseline = cv2.getTextSize(
        label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness
    )

    # Draw filled rectangle behind text for readability
    cv2.rectangle(
        frame,
        (x1, y1 - text_h - baseline - 4),
        (x1 + text_w + 4, y1),
        COLOR_BG,
        -1,
    )

    # Draw text
    cv2.putText(
        frame,
        label,
        (x1 + 2, y1 - baseline - 2),
        cv2.FONT_HERSHEY_SIMPLEX,
        font_scale,
        COLOR_TEXT,
        thickness,
        lineType=cv2.LINE_AA,
    )


def main():
    parser = argparse.ArgumentParser(description="Face Detection Camera Test")
    parser.add_argument(
        "--device",
        type=int,
        default=0,
        help="Camera device index (default: 0)",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=640,
        help="Capture width (default: 640)",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=480,
        help="Capture height (default: 480)",
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=SCORE_THRESHOLD,
        help=f"Confidence threshold (default: {SCORE_THRESHOLD})",
    )
    args = parser.parse_args()

    # Verify model exists
    if not MODEL_PATH.exists():
        print(f"Error: YuNet model not found at {MODEL_PATH}")
        print("Download it with:")
        print(
            "  curl -L -o models/face_detection_yunet_2023mar.onnx "
            "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
        )
        sys.exit(1)

    # Initialize face detector
    detector = cv2.FaceDetectorYN_create(
        str(MODEL_PATH),
        "",
        INPUT_SIZE,
        args.conf,
        NMS_THRESHOLD,
        TOP_K,
    )

    # Open webcam
    cap = cv2.VideoCapture(args.device)
    if not cap.isOpened():
        print(f"Error: Could not open camera device {args.device}")
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)

    actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    print("=" * 50)
    print("  Face Detection Camera Test")
    print("=" * 50)
    print(f"  Camera:     device {args.device}")
    print(f"  Resolution: {actual_width}x{actual_height}")
    print(f"  FPS:        {fps:.1f}")
    print(f"  Model:      {MODEL_PATH.name}")
    print(f"  Conf thresh:{args.conf}")
    print("-" * 50)
    print("  Controls:")
    print("    q / ESC  — Quit")
    print("    s        — Save snapshot")
    print("=" * 50)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    frame_count = 0
    start_time = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Warning: Failed to capture frame")
            break

        h, w = frame.shape[:2]
        frame_count += 1

        # Update detector input size to match frame
        detector.setInputSize((w, h))

        # Detect faces
        _, faces = detector.detect(frame)

        face_count = 0
        if faces is not None:
            face_count = len(faces)
            for face in faces:
                # YuNet output: [x, y, w, h, x_re, y_re, x_le, y_le, x_nt, y_nt, x_rcm, y_rcm, x_lcm, y_lcm, score]
                x, y, fw, fh = face[:4].astype(int)
                confidence = float(face[14])

                x1, y1 = max(0, x), max(0, y)
                x2, y2 = min(w, x + fw), min(h, y + fh)

                draw_face_box(frame, x1, y1, x2, y2, confidence)

        # Draw HUD
        elapsed = time.time() - start_time
        current_fps = frame_count / elapsed if elapsed > 0 else 0

        hud_text = f"Faces: {face_count} | FPS: {current_fps:.1f}"
        cv2.putText(
            frame,
            hud_text,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )

        # Show frame
        cv2.imshow("Face Detection", frame)

        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), 27):  # q or ESC
            break
        elif key == ord("s"):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = RESULTS_DIR / f"capture_{timestamp}.jpg"
            cv2.imwrite(str(save_path), frame)
            print(f"  📸  Snapshot saved: {save_path}")

    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    print("\nCamera closed.")


if __name__ == "__main__":
    main()
