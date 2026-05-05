#!/usr/bin/env python3
# Copyright (c) 2026 webAI, Inc.
"""
YOLO26 Segmentation PyTorch MPS Training Benchmark
==================================================
Measures segmentation training performance using PyTorch MPS backend on Apple Silicon.

Usage:
    python benchmark_yolo26_seg_training_mps.py
    python benchmark_yolo26_seg_training_mps.py --models n s      # Specific models only
    python benchmark_yolo26_seg_training_mps.py --epochs 5        # Fewer epochs
    python benchmark_yolo26_seg_training_mps.py --batch 2         # Smaller batch size
    python benchmark_yolo26_seg_training_mps.py --output custom.json

Output:
    ../results/yolo26_seg_mps_training_final.json (default, overridable via --output)
"""

import argparse
import gc
import json
import logging
import platform
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from _mps_seg_perf_patch import apply_mps_seg_perf_patch
from _runtime_dirs import ensure_runtime_dirs
from _vectorized_seg_loss import apply_vectorized_seg_loss

logger = logging.getLogger(__name__)

# Apply two patches as soon as the module is imported, before any ultralytics
# ``Trainer`` builds its loss object:
#
# 1. ``apply_vectorized_seg_loss`` — replaces the per-image Python loop in
#    ``v8SegmentationLoss.calculate_segmentation_loss`` with a fully vectorized
#    pass. Modest win; numerically identical to the upstream Ultralytics
#    implementation (BCE + crop + per-mask-area normalize + sum, equivalent
#    execution shape — see the ``_vectorized_seg_loss`` module docstring).
#
# 2. ``apply_mps_seg_perf_patch`` — rewrites ``v8SegmentationLoss.loss``'s
#    semseg-mask clearing line ``sem_masks[bool_mask] = 0`` as a multiplicative
#    mask. This single boolean-scatter assign was the *real* per-step
#    bottleneck on Apple GPU (~4.7 s/step on yolo26n-seg, batch=2), and
#    replacing it gives a ~13× speedup. Numerically identical (verified by
#    ``_test_mps_seg_perf_patch.py``). Without this patch MPS is slower than
#    CPU for seg training; with it MPS is faster than CPU.
apply_vectorized_seg_loss()
apply_mps_seg_perf_patch()

# =============================================================================
# Configuration
# =============================================================================

EPOCHS = 10
BATCH_SIZE = 4
LEARNING_RATE = 0.00001
MODEL_SIZES = ["n", "s", "m", "l", "x"]

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR / ".."
RESULTS_DIR = PROJECT_DIR / "results"
MODELS_DIR = PROJECT_DIR / "models"
DATASETS_DIR = PROJECT_DIR / "datasets"


# =============================================================================
# Utility Functions
# =============================================================================


def get_device_info() -> dict[str, Any]:
    """Get system and device information.

    Returns:
        Dict with platform, processor, Python version, CPU name, PyTorch version, and MPS availability.
    """
    info = {
        "platform": platform.platform(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
    }

    # Try to get chip name on macOS
    try:
        result = subprocess.run(
            ["sysctl", "-n", "machdep.cpu.brand_string"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            info["cpu"] = result.stdout.strip()
    except Exception:
        pass

    # Get PyTorch and MPS info
    try:
        import torch

        info["torch_version"] = torch.__version__
        info["mps_available"] = torch.backends.mps.is_available()
        info["mps_built"] = torch.backends.mps.is_built()
    except ImportError:
        info["torch_version"] = "not installed"
        info["mps_available"] = False

    return info


def clear_pytorch_memory():
    """Run garbage collection and flush the MPS tensor cache between benchmark runs."""
    gc.collect()
    try:
        import torch

        if torch.backends.mps.is_available():
            torch.mps.empty_cache()
            torch.mps.synchronize()
    except Exception:
        pass


def get_pytorch_mps_memory() -> tuple[float, float]:
    """Get PyTorch MPS memory usage in MB.

    Returns:
        Tuple of (current_allocated_mb, driver_allocated_mb)

    Note: PyTorch MPS has limited memory introspection compared to CUDA.
          - current_allocated: GPU memory occupied by tensors
          - driver_allocated: Total GPU memory allocated by Metal driver
    """
    try:
        import torch

        if torch.backends.mps.is_available():
            current = torch.mps.current_allocated_memory() / 1024 / 1024
            driver = torch.mps.driver_allocated_memory() / 1024 / 1024
            return current, driver
    except Exception:
        pass
    return 0.0, 0.0


def setup_coco128_seg() -> Path:
    """Download and setup COCO128-Seg dataset (same 80 COCO classes as COCO128).

    Returns:
        Path to local YAML config file or standard coco128-seg.yaml
    """
    search_paths = [
        DATASETS_DIR / "coco128-seg",
        Path("datasets") / "coco128-seg",
        Path.cwd() / "coco128-seg",
    ]

    dataset_path = None
    for path in search_paths:
        if path.exists() and (path / "images").exists():
            dataset_path = path
            break

    if dataset_path is None:
        logger.info("  COCO128-Seg not found locally. Downloading...")
        DATASETS_DIR.mkdir(parents=True, exist_ok=True)
        zip_path = DATASETS_DIR / "coco128-seg.zip"
        url = "https://github.com/ultralytics/assets/releases/download/v0.0.0/coco128-seg.zip"
        try:
            import zipfile

            result = subprocess.run(
                ["curl", "-L", "-f", "-o", str(zip_path), url],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode != 0 or not zip_path.exists():
                raise RuntimeError(f"curl failed (code {result.returncode}): {result.stderr}")
            logger.info("  Extracting...")
            with zipfile.ZipFile(str(zip_path), "r") as zf:
                zf.extractall(str(DATASETS_DIR))
            zip_path.unlink()
            dataset_path = DATASETS_DIR / "coco128-seg"
            if not (dataset_path / "images").exists():
                raise RuntimeError("Extracted archive missing coco128-seg/images/ directory")
            logger.info(f"  Downloaded COCO128-Seg to: {dataset_path}")
        except Exception as e:
            logger.error(f"  ERROR: Failed to download COCO128-Seg: {e}")
            logger.warning("  Training will fall back to synthetic data.")
            if zip_path.exists():
                zip_path.unlink()
            return Path("coco128-seg.yaml")

    logger.info(f"  Found COCO128-Seg at: {dataset_path}")

    local_yaml = DATASETS_DIR / "coco128_seg_local.yaml"
    DATASETS_DIR.mkdir(parents=True, exist_ok=True)

    config = f"""# COCO128-Seg Local Configuration
path: {dataset_path.absolute()}
train: images/train2017
val: images/train2017
test:

names:
  0: person
  1: bicycle
  2: car
  3: motorcycle
  4: airplane
  5: bus
  6: train
  7: truck
  8: boat
  9: traffic light
  10: fire hydrant
  11: stop sign
  12: parking meter
  13: bench
  14: bird
  15: cat
  16: dog
  17: horse
  18: sheep
  19: cow
  20: elephant
  21: bear
  22: zebra
  23: giraffe
  24: backpack
  25: umbrella
  26: handbag
  27: tie
  28: suitcase
  29: frisbee
  30: skis
  31: snowboard
  32: sports ball
  33: kite
  34: baseball bat
  35: baseball glove
  36: skateboard
  37: surfboard
  38: tennis racket
  39: bottle
  40: wine glass
  41: cup
  42: fork
  43: knife
  44: spoon
  45: bowl
  46: banana
  47: apple
  48: sandwich
  49: orange
  50: broccoli
  51: carrot
  52: hot dog
  53: pizza
  54: donut
  55: cake
  56: chair
  57: couch
  58: potted plant
  59: bed
  60: dining table
  61: toilet
  62: tv
  63: laptop
  64: mouse
  65: remote
  66: keyboard
  67: cell phone
  68: microwave
  69: oven
  70: toaster
  71: sink
  72: refrigerator
  73: book
  74: clock
  75: vase
  76: scissors
  77: teddy bear
  78: hair drier
  79: toothbrush
"""

    with open(local_yaml, "w") as f:
        f.write(config)

    return local_yaml


def check_mps_available() -> bool:
    """Check if MPS is available.

    Returns:
        True if PyTorch MPS backend is both available and built, False otherwise.
    """
    try:
        import torch

        return torch.backends.mps.is_available() and torch.backends.mps.is_built()
    except ImportError:
        return False


def save_progress(results: list[dict], output_file: Path):
    """Save intermediate progress to file.

    Args:
        results: List of benchmark result dicts accumulated so far.
        output_file: Path to the JSON file where progress is written.
    """
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)


def _extract_val_metrics(val_results: Any) -> tuple[float, float, float, float]:
    """Read mask and box mAP from validation results; mask zeros if seg unavailable."""
    map50_mask = map50_95_mask = 0.0
    map50_box = map50_95_box = 0.0
    try:
        if hasattr(val_results, "box"):
            map50_box = float(val_results.box.map50)
            map50_95_box = float(val_results.box.map)
        else:
            map50_box = float(getattr(val_results, "map50", 0) or 0)
            map50_95_box = float(getattr(val_results, "map", 0) or 0)
    except Exception:
        map50_box = map50_95_box = 0.0
    try:
        if hasattr(val_results, "seg"):
            map50_mask = float(val_results.seg.map50)
            map50_95_mask = float(val_results.seg.map)
    except Exception:
        pass
    return map50_mask, map50_95_mask, map50_box, map50_95_box


def train_model_mps(
    model_size: str,
    data_path: Path,
    epochs: int,
    batch_size: int,
    lr: float,
) -> dict[str, Any] | None:
    """Train single segmentation PyTorch model with MPS backend and measure time.

    Args:
        model_size: Model size (n, s, m, l, x)
        data_path: Path to dataset YAML config
        epochs: Number of training epochs
        batch_size: Batch size
        lr: Learning rate

    Returns:
        Training results dict or None if failed
    """
    try:
        import torch

        if not torch.backends.mps.is_available():
            logger.warning("  ⚠️  MPS not available")
            return None
        device = "mps"
    except ImportError as e:
        logger.warning(f"  ⚠️  PyTorch not available: {e}")
        return None

    try:
        from ultralytics import YOLO
    except ImportError as e:
        logger.warning(f"  ⚠️  Ultralytics not available: {e}")
        return None

    model_name = f"yolo26{model_size}-seg"
    model_file = f"yolo26{model_size}-seg.pt"

    local_weights = MODELS_DIR / model_file
    if local_weights.exists():
        model_source = str(local_weights)
        logger.info(f"  Loading {model_name} from local weights: {local_weights}")
    else:
        model_source = model_file
        logger.info(f"  Loading {model_name} (will download if not cached)...")

    try:
        model = YOLO(model_source)
    except Exception as e:
        logger.error(f"  ⚠️  Failed to load model: {e}")
        import traceback

        traceback.print_exc()
        return None

    clear_pytorch_memory()

    logger.info(f"  Training for {epochs} epochs (batch={batch_size}, lr={lr}, device={device})...")
    start_time = time.perf_counter()

    # ``val=False`` skips per-epoch validation so the benchmark
    # measures pure training throughput. Final mAP is computed via
    # the explicit ``model.val(...)`` call after training.
    try:
        model.train(
            data=str(data_path),
            task="segment",
            epochs=epochs,
            imgsz=640,
            batch=batch_size,
            lr0=lr,
            patience=epochs + 1,
            save_period=-1,
            workers=4,
            device=device,
            project=str(RESULTS_DIR / "mps_runs"),
            name=model_name,
            exist_ok=True,
            verbose=True,
            val=False,
        )
    except Exception as e:
        logger.error(f"  ⚠️  Training failed: {e}")
        import traceback

        traceback.print_exc()
        return None

    training_time = time.perf_counter() - start_time

    current_memory, driver_memory = get_pytorch_mps_memory()

    logger.info("  Running validation...")
    map50_mask = map50_95_mask = map50_box = map50_95_box = 0.0
    try:
        val_results = model.val(data=str(data_path), batch=batch_size, device=device)
        map50_mask, map50_95_mask, map50_box, map50_95_box = _extract_val_metrics(val_results)
    except Exception as e:
        logger.warning(f"  ⚠️  Validation failed: {e}")

    return {
        "model": model_name,
        "training_time_seconds": round(training_time, 2),
        "time_per_epoch_seconds": round(training_time / epochs, 2),
        "epochs": epochs,
        "batch_size": batch_size,
        "learning_rate": lr,
        "mAP50_mask": round(map50_mask, 4) if map50_mask else 0.0,
        "mAP50-95_mask": round(map50_95_mask, 4) if map50_95_mask else 0.0,
        "mAP50_box": round(map50_box, 4) if map50_box else 0.0,
        "mAP50-95_box": round(map50_95_box, 4) if map50_95_box else 0.0,
        "current_memory_mb": round(current_memory, 1),
        "driver_memory_mb": round(driver_memory, 1),
        "device": "mps",
    }


def main():
    """Parse CLI args, verify MPS support, train each seg model on MPS, and save benchmark results."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    parser = argparse.ArgumentParser(
        description="YOLO26 Segmentation PyTorch MPS Training Benchmark"
    )
    parser.add_argument(
        "--models",
        nargs="+",
        default=MODEL_SIZES,
        choices=MODEL_SIZES,
        help="Model sizes to benchmark (default: all)",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=EPOCHS,
        help=f"Number of training epochs (default: {EPOCHS})",
    )
    parser.add_argument(
        "--batch",
        type=int,
        default=BATCH_SIZE,
        help=f"Batch size (default: {BATCH_SIZE})",
    )
    parser.add_argument(
        "--lr",
        type=float,
        default=LEARNING_RATE,
        help=f"Learning rate (default: {LEARNING_RATE})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=RESULTS_DIR / "yolo26_seg_mps_training_final.json",
        help="Output JSON path (default: results/yolo26_seg_mps_training_final.json)",
    )
    args = parser.parse_args()
    ensure_runtime_dirs(PROJECT_DIR)

    logger.info("=" * 70)
    logger.info("YOLO26 Segmentation PyTorch MPS Training Benchmark")
    logger.info("=" * 70)

    if not check_mps_available():
        logger.error("\n❌ MPS (Metal Performance Shaders) is not available.")
        logger.error("   This benchmark requires Apple Silicon with PyTorch MPS support.")
        sys.exit(1)

    logger.info("\n📱 Device Information:")
    device_info = get_device_info()
    for key, value in device_info.items():
        logger.info(f"   {key}: {value}")

    logger.info("\n📦 Setting up COCO128-Seg dataset...")
    data_path = setup_coco128_seg()
    logger.info(f"   Using: {data_path}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    progress_file = args.output.parent / (args.output.stem.replace("_final", "") + "_progress.json")
    final_file = args.output

    logger.info(f"\n🏃 Running training benchmarks for models: {args.models}")
    logger.info(f"   Epochs: {args.epochs}, Batch: {args.batch}, LR: {args.lr}")
    logger.info("-" * 70)

    all_results = []

    for i, model_size in enumerate(args.models, 1):
        logger.info(f"\n[{i}/{len(args.models)}] Benchmarking yolo26{model_size}-seg...")

        result = train_model_mps(
            model_size=model_size,
            data_path=data_path,
            epochs=args.epochs,
            batch_size=args.batch,
            lr=args.lr,
        )

        if result:
            all_results.append(result)
            logger.info(f"  ✅ Completed in {result['training_time_seconds']:.1f}s")
            logger.info(
                f"     mask mAP50: {result['mAP50_mask']:.4f}, mAP50-95: {result['mAP50-95_mask']:.4f} | "
                f"box mAP50: {result['mAP50_box']:.4f}, mAP50-95: {result['mAP50-95_box']:.4f}"
            )

            save_progress(all_results, progress_file)
        else:
            logger.warning("  ❌ Failed")

        clear_pytorch_memory()

    logger.info("\n" + "=" * 70)
    logger.info("📊 Final Results")
    logger.info("=" * 70)

    final_output = {
        "benchmark": "yolo26_seg_mps_training",
        "timestamp": datetime.now().isoformat(),
        "device_info": device_info,
        "config": {
            "epochs": args.epochs,
            "batch_size": args.batch,
            "learning_rate": args.lr,
            "device": "mps",
        },
        "results": all_results,
    }

    with open(final_file, "w") as f:
        json.dump(final_output, f, indent=2)

    logger.info(f"\n✅ Results saved to: {final_file}")

    if all_results:
        logger.info("\n" + "-" * 120)
        logger.info(
            f"{'Model':<16} {'Time (s)':<10} {'s/epoch':<10} "
            f"{'mAP50 mask':<12} {'mAP50-95 mask':<14} {'mAP50 box':<12} {'mAP50-95 box':<14}"
        )
        logger.info("-" * 120)
        for r in all_results:
            logger.info(
                f"{r['model']:<16} "
                f"{r['training_time_seconds']:<10.1f} "
                f"{r['time_per_epoch_seconds']:<10.2f} "
                f"{r['mAP50_mask']:<12.4f} "
                f"{r['mAP50-95_mask']:<14.4f} "
                f"{r['mAP50_box']:<12.4f} "
                f"{r['mAP50-95_box']:<14.4f}"
            )
        logger.info("-" * 120)

    logger.info("\n✨ PyTorch MPS segmentation training benchmark complete!")


if __name__ == "__main__":
    main()
