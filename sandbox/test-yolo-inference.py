#!/usr/bin/env python3
"""
YOLO26 MLX Inference Test Script
=================================

Tests YOLO26 MLX inference across four phases:
  A. Basic inference sanity check (bus.jpg)
  B. Array / PIL input compatibility
  C. Performance micro-benchmark
  D. COCO val2017 validation subset (optional, if dataset present)

Usage:
    cd /Users/zhensong/project/SoPilot
    source .venv/bin/activate
    python sandbox/test-yolo-inference.py

Requirements:
    - models/yolo26n.npz  (converted MLX weights)
    - images/bus.jpg      (test image)
    - datasets/coco/      (optional, for Phase D)
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "models"
IMAGES_DIR = PROJECT_ROOT / "images"
RESULTS_DIR = PROJECT_ROOT / "results"
DATASETS_DIR = PROJECT_ROOT / "datasets" / "coco"

TEST_IMAGE = IMAGES_DIR / "bus.jpg"
MODEL_PATH = MODELS_DIR / "yolo26n.npz"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def banner(title: str) -> None:
    """Print a section banner."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def ok(msg: str) -> None:
    print(f"  ✅  {msg}")


def warn(msg: str) -> None:
    print(f"  ⚠️   {msg}")


def fail(msg: str) -> None:
    print(f"  ❌  {msg}")
    sys.exit(1)


def stat(label: str, value: str) -> None:
    print(f"  📊  {label:<30} {value}")


# ---------------------------------------------------------------------------
# Phase A – Basic Inference Sanity Check
# ---------------------------------------------------------------------------


def phase_a_basic_inference() -> dict:
    """Run inference on bus.jpg and verify detections exist."""
    banner("Phase A – Basic Inference Sanity Check")

    if not TEST_IMAGE.exists():
        fail(f"Test image not found: {TEST_IMAGE}")
    if not MODEL_PATH.exists():
        fail(f"Model weights not found: {MODEL_PATH}")

    from yolo26mlx import YOLO

    print(f"  Loading model: {MODEL_PATH.name}")
    model = YOLO(str(MODEL_PATH))
    model.info(verbose=False)
    ok("Model loaded")

    print(f"  Running inference on: {TEST_IMAGE.name}")
    results = model.predict(str(TEST_IMAGE), conf=0.25, imgsz=640)
    ok("Inference completed")

    assert len(results) == 1, f"Expected 1 result, got {len(results)}"
    result = results[0]

    n_detections = len(result)
    stat("Detections found", str(n_detections))
    stat("Original shape", str(result.orig_shape))

    if n_detections == 0:
        fail("No detections found — model or image may be invalid")

    # Print each detection
    print("\n  Top detections:")
    boxes = result.boxes
    for i in range(min(n_detections, 8)):
        cls_id = int(boxes.cls[i])
        conf = float(boxes.conf[i])
        name = result.names.get(cls_id, f"class_{cls_id}")
        print(f"    {i + 1}. {name:<15} conf={conf:.3f}  box={boxes.xyxy[i].tolist()}")

    # Save annotated result
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = result.save(str(RESULTS_DIR / "test_bus_annotated.jpg"))
    ok(f"Annotated image saved: {out_path}")

    return {
        "phase": "A",
        "status": "pass",
        "detections": n_detections,
        "image": str(TEST_IMAGE),
        "output": out_path,
    }


# ---------------------------------------------------------------------------
# Phase B – Array / PIL Input Compatibility
# ---------------------------------------------------------------------------


def phase_b_input_types() -> dict:
    """Verify inference works with numpy arrays and PIL Images."""
    banner("Phase B – Array / PIL Input Compatibility")

    from yolo26mlx import YOLO

    model = YOLO(str(MODEL_PATH))

    # Load once
    pil_img = Image.open(TEST_IMAGE)
    np_img = np.array(pil_img)

    print("  Testing PIL Image input...")
    results_pil = model.predict(pil_img, conf=0.25, imgsz=640)
    n_pil = len(results_pil[0])
    ok(f"PIL  → {n_pil} detections")

    print("  Testing numpy array input...")
    results_np = model.predict(np_img, conf=0.25, imgsz=640)
    n_np = len(results_np[0])
    ok(f"NumPy → {n_np} detections")

    # Allow small variance (sometimes 0–1 box difference due to resize interpolation)
    if abs(n_pil - n_np) > 1:
        fail(f"Detection count mismatch: PIL={n_pil}, NumPy={n_np}")

    ok("Input type consistency verified")

    return {
        "phase": "B",
        "status": "pass",
        "detections_pil": n_pil,
        "detections_np": n_np,
    }


# ---------------------------------------------------------------------------
# Phase C – Performance Micro-Benchmark
# ---------------------------------------------------------------------------


def phase_c_benchmark(warmup: int = 3, runs: int = 10) -> dict:
    """Measure end-to-end inference latency and FPS."""
    banner("Phase C – Performance Micro-Benchmark")

    from yolo26mlx import YOLO

    model = YOLO(str(MODEL_PATH))
    image = Image.open(TEST_IMAGE)

    print(f"  Warmup ({warmup} runs)...")
    for _ in range(warmup):
        _ = model.predict(image, imgsz=640)
    ok("Warmup complete")

    print(f"  Timing ({runs} runs)...")
    times_ms = []
    for _ in range(runs):
        start = time.perf_counter()
        _ = model.predict(image, imgsz=640)
        elapsed = (time.perf_counter() - start) * 1000.0
        times_ms.append(elapsed)

    arr = np.array(times_ms)
    mean_ms = float(np.mean(arr))
    std_ms = float(np.std(arr))
    min_ms = float(np.min(arr))
    max_ms = float(np.max(arr))
    median_ms = float(np.median(arr))
    fps = 1000.0 / mean_ms

    stat("Mean latency", f"{mean_ms:.2f} ms")
    stat("Std dev", f"{std_ms:.2f} ms")
    stat("Min / Max", f"{min_ms:.2f} / {max_ms:.2f} ms")
    stat("Median", f"{median_ms:.2f} ms")
    stat("Throughput", f"{fps:.1f} FPS")

    ok("Benchmark complete")

    return {
        "phase": "C",
        "status": "pass",
        "warmup": warmup,
        "runs": runs,
        "mean_ms": mean_ms,
        "std_ms": std_ms,
        "min_ms": min_ms,
        "max_ms": max_ms,
        "median_ms": median_ms,
        "fps": fps,
    }


# ---------------------------------------------------------------------------
# Phase D – COCO val2017 Validation (subset)
# ---------------------------------------------------------------------------


def phase_d_coco_validation(subset: int = 100) -> dict | None:
    """Run COCO validation on a subset if dataset is available."""
    banner("Phase D – COCO val2017 Validation (Subset)")

    coco_images = DATASETS_DIR / "images" / "val2017"
    coco_ann = DATASETS_DIR / "annotations" / "instances_val2017.json"

    if not coco_images.exists() or not coco_ann.exists():
        warn("COCO val2017 dataset not found — skipping Phase D")
        print(f"      Expected: {coco_images}")
        print(f"      Expected: {coco_ann}")
        return None

    # Delegate to the existing evaluation script
    eval_script = PROJECT_ROOT / "scripts" / "evaluate_coco_val.py"
    if not eval_script.exists():
        warn("evaluate_coco_val.py not found — skipping Phase D")
        return None

    print(f"  Running COCO validation on first {subset} images...")
    print(f"  Script: {eval_script.name}")
    print(f"  Model:  yolo26n")
    print()

    import subprocess

    cmd = [
        sys.executable,
        str(eval_script),
        "--model", "yolo26n",
        "--data", str(DATASETS_DIR),
        "--subset", str(subset),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        fail(f"COCO evaluation failed:\n{result.stderr}")

    # Print last 40 lines of stdout (contains the mAP table)
    lines = result.stdout.strip().splitlines()
    for line in lines[-40:]:
        print("    " + line)

    ok(f"COCO validation complete ({subset} images)")

    return {
        "phase": "D",
        "status": "pass",
        "subset": subset,
        "stdout_tail": lines[-20:],
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="YOLO26 MLX Inference Test")
    parser.add_argument(
        "--skip-coco",
        action="store_true",
        help="Skip COCO validation phase",
    )
    parser.add_argument(
        "--coco-subset",
        type=int,
        default=100,
        help="Number of COCO images to validate (default: 100)",
    )
    parser.add_argument(
        "--benchmark-runs",
        type=int,
        default=10,
        help="Number of benchmark timing runs (default: 10)",
    )
    args = parser.parse_args()

    print("\n" + "🚀" * 35)
    print("  YOLO26 MLX Inference Test")
    print("🚀" * 35)

    report = {
        "model": str(MODEL_PATH),
        "test_image": str(TEST_IMAGE),
        "phases": [],
    }

    # Phase A
    report["phases"].append(phase_a_basic_inference())

    # Phase B
    report["phases"].append(phase_b_input_types())

    # Phase C
    report["phases"].append(phase_c_benchmark(runs=args.benchmark_runs))

    # Phase D
    if not args.skip_coco:
        d = phase_d_coco_validation(subset=args.coco_subset)
        if d is not None:
            report["phases"].append(d)
    else:
        warn("COCO validation skipped by --skip-coco")

    # Summary
    banner("Test Summary")
    passed = sum(1 for p in report["phases"] if p and p.get("status") == "pass")
    total = len(report["phases"])
    stat("Phases passed", f"{passed}/{total}")

    # Save JSON report
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = RESULTS_DIR / "test_yolo_inference_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    ok(f"Report saved: {report_path}")

    print("\n" + "✅" * 35)
    print("  All tests completed successfully!")
    print("✅" * 35 + "\n")


if __name__ == "__main__":
    main()
