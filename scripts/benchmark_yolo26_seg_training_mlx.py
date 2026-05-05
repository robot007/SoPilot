#!/usr/bin/env python3
# Copyright (c) 2026 webAI, Inc.
"""
YOLO26 Segmentation Training Benchmark (Pure MLX)
=================================================
Measures training performance for YOLO26 segmentation models using native MLX on Apple Silicon.

This benchmark uses the pure MLX implementation of YOLO26 for training,
providing accurate measurements of MLX-native training performance.

Usage:
    python benchmark_yolo26_seg_training_mlx.py
    python benchmark_yolo26_seg_training_mlx.py --models n s      # Specific models only
    python benchmark_yolo26_seg_training_mlx.py --epochs 5        # Fewer epochs
    python benchmark_yolo26_seg_training_mlx.py --batch 2           # Smaller batch size
    python benchmark_yolo26_seg_training_mlx.py --output custom.json

Output:
    ../results/yolo26_seg_mlx_training_final.json (default, overridable via --output)
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

from _runtime_dirs import ensure_runtime_dirs

logger = logging.getLogger(__name__)

# =============================================================================
# Configuration
# =============================================================================

EPOCHS = 10
BATCH_SIZE = 4
# Default LR matches Ultralytics' ``optimizer='auto'`` short-run choice for
# nc=80: ``round(0.002 * 5 / (4 + 80), 6) == 0.000119``. With the default
# ``--optimizer auto`` this is consumed by AdamW (the optimizer Ultralytics
# itself picks for ``iterations <= 10000``); see ``Trainer._setup_optimizer``.
LEARNING_RATE = 0.000119
DEFAULT_OPTIMIZER = "auto"
MODEL_SIZES = ["n", "s", "m", "l", "x"]

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR / ".."
RESULTS_DIR = PROJECT_DIR / "results"
MODELS_DIR = PROJECT_DIR / "models"
DATASETS_DIR = PROJECT_DIR / "datasets"


# =============================================================================
# Utility Functions
# =============================================================================


def _lr_source_label(lr_used: float) -> str:
    """Describe whether ``lr_used`` came from the auto formula or the user.

    Returns:
        ``"auto (Ultralytics build_optimizer, nc=80)"`` when ``lr_used`` matches
        the script default (which equals ``round(0.002 * 5 / (4 + 80), 6)``);
        otherwise ``"user-provided (--lr)"``.
    """
    return (
        "auto (Ultralytics build_optimizer, nc=80)"
        if lr_used == LEARNING_RATE
        else "user-provided (--lr)"
    )


def _optimizer_label(choice: str) -> str:
    """Pretty label for the optimizer ``--optimizer`` choice for benchmark JSON."""
    if choice == "auto":
        return "auto (AdamW for iter<=10000, MuSGD otherwise — matches Ultralytics)"
    if choice == "adamw":
        return "AdamW (forced)"
    if choice == "musgd":
        return "MuSGD (Muon + Nesterov SGD, forced)"
    return choice


def get_device_info() -> dict[str, Any]:
    """Get system and device information.

    Returns:
        Dict with platform, processor, Python version, and CPU name (macOS).
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

    return info


def clear_mlx_memory():
    """Run garbage collection, flush the MLX Metal cache, and reset peak memory tracking."""
    gc.collect()
    import mlx.core as mx

    mx.clear_cache()
    mx.reset_peak_memory()


def get_mlx_memory() -> tuple[float, float]:
    """Get MLX Metal memory usage in MB.

    Returns:
        Tuple of (active_memory_mb, peak_memory_mb)
    """
    import mlx.core as mx

    active = mx.get_active_memory() / 1024 / 1024
    peak = mx.get_peak_memory() / 1024 / 1024
    return active, peak


def setup_coco128_seg() -> Path:
    """Download and setup COCO128-Seg dataset.

    Returns:
        Path to local YAML config file
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


def save_results(results: dict, output_path: Path, prefix: str = "") -> None:
    """Save results to JSON file.

    Args:
        results: Dict containing benchmark metadata and per-model result entries.
        output_path: Destination path for the JSON output file.
        prefix: Optional log-line prefix (e.g. emoji) prepended to the saved-path message.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    if prefix:
        logger.info(f"{prefix} Results saved to: {output_path}")
    else:
        logger.info(f"✅ Results saved to: {output_path}")


# =============================================================================
# MLX Training Benchmark
# =============================================================================


def _validation_map_from_metrics(val_metrics: dict[str, Any]) -> tuple[float, float]:
    """Prefer mask mAP when present; otherwise use box mAP (same as detection)."""
    if "mAP50_mask" in val_metrics or "mAP50-95_mask" in val_metrics:
        map50 = float(val_metrics.get("mAP50_mask", val_metrics.get("mAP50", 0.0)))
        map50_95 = float(val_metrics.get("mAP50-95_mask", val_metrics.get("mAP50-95", 0.0)))
    else:
        map50 = float(val_metrics.get("mAP50", 0.0))
        map50_95 = float(val_metrics.get("mAP50-95", 0.0))
    return map50, map50_95


def train_model_mlx(
    model_size: str,
    data_path: Path,
    epochs: int,
    batch_size: int,
    lr: float,
    optimizer_choice: str = DEFAULT_OPTIMIZER,
) -> dict[str, Any] | None:
    """Train YOLO26 segmentation model using native MLX and measure time.

    Uses the pure MLX implementation of YOLO26 for training with the
    MLX-native trainer and data loader.

    Args:
        model_size: Model size (n, s, m, l, x)
        data_path: Path to dataset YAML config
        epochs: Number of training epochs
        batch_size: Batch size
        lr: Learning rate
        optimizer_choice: ``"auto"`` (default; mirrors Ultralytics' AdamW vs
            MuSGD selection), ``"adamw"``, or ``"musgd"``.

    Returns:
        Training results dict or None if failed
    """

    model_name = f"yolo26{model_size}-seg"
    weights_file = MODELS_DIR / f"yolo26{model_size}-seg.npz"
    if not weights_file.exists():
        weights_file = MODELS_DIR / f"yolo26{model_size}-seg.safetensors"
    if not weights_file.exists():
        logger.warning(f"  ⚠️  MLX weights not found for {model_name} (tried .npz and .safetensors)")
        logger.warning(f"  Please run: python convert_weights.py --models {model_size}")
        return None

    try:
        from yolo26mlx import YOLO
        from yolo26mlx.engine.trainer import Trainer
    except ImportError as e:
        logger.warning(f"  ⚠️  YOLO26 MLX not available: {e}")
        return None

    logger.info(f"  Loading {model_name} from: {weights_file}")
    try:
        model = YOLO(str(weights_file))
    except Exception as e:
        logger.error(f"  ⚠️  Failed to load model: {e}")
        import traceback

        traceback.print_exc()
        return None

    clear_mlx_memory()

    trainer = Trainer(model=model.model, task="segment")

    logger.info(
        f"  Training for {epochs} epochs (batch={batch_size}, lr={lr}, "
        f"optimizer={optimizer_choice})..."
    )
    logger.info("  Using pure MLX training with real COCO data")
    start_time = time.perf_counter()

    try:
        # ``val=False`` skips per-epoch validation so the benchmark
        # measures pure training throughput. Final mAP is computed via
        # the single ``trainer._validate(...)`` call after training.
        train_results = trainer(
            data=str(data_path),
            epochs=epochs,
            imgsz=640,
            batch=batch_size,
            patience=epochs + 1,
            save_period=-1,
            project=str(RESULTS_DIR / "mlx_runs"),
            name=model_name,
            exist_ok=True,
            lr=lr,
            optimizer=optimizer_choice,
            val=False,
            verbose=True,
        )
    except Exception as e:
        logger.error(f"  ⚠️  Training failed: {e}")
        import traceback

        traceback.print_exc()
        return None

    training_time = time.perf_counter() - start_time

    _, peak_memory = get_mlx_memory()

    logger.info("  Running validation...")
    val_metrics: dict[str, Any] = {}
    try:
        model.model.eval()
        val_metrics = trainer._validate(batch_size, 640)
        map50, map50_95 = _validation_map_from_metrics(val_metrics)
    except Exception as e:
        logger.warning(f"  ⚠️  Validation failed: {e}")
        map50, map50_95 = 0.0, 0.0

    final_loss = train_results.get("final_loss", 0.0)

    map50_mask = float(val_metrics.get("mAP50_mask", 0.0))
    map5095_mask = float(val_metrics.get("mAP50-95_mask", 0.0))
    map50_box = float(val_metrics.get("mAP50_box", 0.0))
    map5095_box = float(val_metrics.get("mAP50-95_box", 0.0))

    result: dict[str, Any] = {
        "model": model_name,
        "task": "segment",
        "training_time_seconds": round(training_time, 2),
        "time_per_epoch_seconds": round(training_time / epochs, 2),
        "epochs": epochs,
        "batch_size": batch_size,
        "learning_rate": lr,
        "final_loss": round(float(final_loss), 4),
        # Legacy headline values: keep ``mAP50``/``mAP50-95`` so older
        # downstream readers keep working. For segmentation these mirror
        # the mask values via ``Trainer._validate_segment``.
        "mAP50": round(float(map50), 4) if map50 else 0.0,
        "mAP50-95": round(float(map50_95), 4) if map50_95 else 0.0,
        "peak_memory_mb": round(peak_memory, 1),
        "framework": "MLX",
    }

    # Emit explicit mask/box keys when the segmentation validator returned
    # them so the collect-results script and chart generator can show
    # apples-to-apples mask mAP next to PyTorch MPS/CPU.
    if "mAP50_mask" in val_metrics or "mAP50-95_mask" in val_metrics:
        result["mAP50_mask"] = round(map50_mask, 4)
        result["mAP50-95_mask"] = round(map5095_mask, 4)
        result["mAP50_box"] = round(map50_box, 4)
        result["mAP50-95_box"] = round(map5095_box, 4)

    return result


# =============================================================================
# Main
# =============================================================================


def main():
    """Parse CLI args, set up dataset, train each model with native MLX, and save benchmark results."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    parser = argparse.ArgumentParser(description="YOLO26 Segmentation MLX Training Benchmark")
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
        "--optimizer",
        choices=["auto", "adamw", "musgd"],
        default=DEFAULT_OPTIMIZER,
        help=(
            "Optimizer choice. 'auto' (default) mirrors Ultralytics' "
            "optimizer='auto': AdamW for short fine-tune runs (iter <= 10000), "
            "MuSGD for long from-scratch runs."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=RESULTS_DIR / "yolo26_seg_mlx_training_final.json",
        help="Output JSON path (default: results/yolo26_seg_mlx_training_final.json)",
    )
    args = parser.parse_args()
    ensure_runtime_dirs(PROJECT_DIR)

    logger.info("=" * 70)
    logger.info("  YOLO26 Segmentation MLX Training Benchmark")
    logger.info("=" * 70)
    logger.info(f"  Models: {', '.join(args.models)}")
    logger.info(f"  Epochs: {args.epochs}")
    logger.info(f"  Batch size: {args.batch}")
    logger.info(f"  Learning rate: {args.lr}")
    logger.info("=" * 70)
    logger.info("")

    try:
        import mlx.core as mx

        mx.set_default_device(mx.gpu)
        logger.info(f"✅ MLX device: {mx.default_device()}")
    except ImportError:
        logger.error("❌ MLX not available. Please install: pip install mlx")
        sys.exit(1)

    device_info = get_device_info()
    logger.info(f"✅ Platform: {device_info.get('cpu', device_info.get('processor', 'Unknown'))}")

    logger.info("\n📦 Setting up COCO128-Seg dataset...")
    data_path = setup_coco128_seg()
    logger.info(f"✅ Dataset config: {data_path}")
    logger.info("")

    results = []

    progress_path = args.output.parent / (args.output.stem.replace("_final", "") + "_progress.json")

    for i, size in enumerate(args.models):
        model_name = f"yolo26{size}-seg"
        logger.info(f"\n{'=' * 50}")
        logger.info(f"  [{i + 1}/{len(args.models)}] Training: {model_name}")
        logger.info(f"{'=' * 50}")

        clear_mlx_memory()

        result = train_model_mlx(
            model_size=size,
            data_path=data_path,
            epochs=args.epochs,
            batch_size=args.batch,
            lr=args.lr,
            optimizer_choice=args.optimizer,
        )

        if result:
            results.append(result)
            logger.info(f"\n  ✅ {model_name} completed:")
            logger.info(
                f"     Training time: {result['training_time_seconds']:.1f}s ({result['time_per_epoch_seconds']:.1f}s/epoch)"
            )
            logger.info(f"     mAP50: {result['mAP50']:.4f}")
            logger.info(f"     Peak memory: {result['peak_memory_mb']:.1f} MB")

            progress = {
                "benchmark": "YOLO26 Segmentation MLX Training (in progress)",
                "task": "segment",
                "timestamp": datetime.now().isoformat(),
                "device_info": device_info,
                "config": {
                    "epochs": args.epochs,
                    "batch_size": args.batch,
                    "learning_rate": float(args.lr),
                    "learning_rate_source": _lr_source_label(float(args.lr)),
                    "optimizer": _optimizer_label(args.optimizer),
                    "dataset": str(data_path),
                },
                "results": results,
            }
            save_results(progress, progress_path, prefix="📝")
        else:
            logger.warning(f"\n  ❌ {model_name} failed")

    logger.info("\n" + "=" * 70)
    logger.info("  Training Benchmark Summary")
    logger.info("=" * 70)

    logger.info(
        f"\n{'Model':<18} {'Time (s)':<12} {'Time/Epoch':<12} {'mAP50':<10} {'Memory (MB)':<12}"
    )
    logger.info("-" * 64)

    results_by_model = {r["model"]: r for r in results}

    for size in args.models:
        model_name = f"yolo26{size}-seg"
        if model_name in results_by_model:
            r = results_by_model[model_name]
            logger.info(
                f"{model_name:<18} {r['training_time_seconds']:<12.1f} {r['time_per_epoch_seconds']:<12.1f} {r['mAP50']:<10.4f} {r['peak_memory_mb']:<12.1f}"
            )
        else:
            logger.warning(f"{model_name:<18} {'FAILED':<12} {'-':<12} {'-':<10} {'-':<12}")

    logger.info("-" * 64)
    logger.info("")

    lr_used = float(args.lr)

    final_output = {
        "benchmark": "YOLO26 Segmentation MLX Training (Pure MLX)",
        "task": "segment",
        "timestamp": datetime.now().isoformat(),
        "device_info": device_info,
        "config": {
            "epochs": args.epochs,
            "batch_size": args.batch,
            "learning_rate": lr_used,
            "learning_rate_source": _lr_source_label(lr_used),
            "optimizer": _optimizer_label(args.optimizer),
            "dataset": "COCO128-Seg",
            "framework": "MLX (native)",
        },
        "results": results,
    }

    save_results(final_output, args.output)

    logger.info("\n🎉 MLX Training benchmark complete!")
    logger.info(f"   Results: {args.output}")


if __name__ == "__main__":
    main()
