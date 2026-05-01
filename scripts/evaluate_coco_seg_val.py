#!/usr/bin/env python3
# Copyright (c) 2026 webAI, Inc.
"""
YOLO26 MLX - COCO val2017 Segmentation Evaluation Script

Evaluates YOLO26-seg MLX models on COCO val2017 using the official COCO evaluation
protocol. Reports both box mAP and mask mAP.

Usage:
    python scripts/evaluate_coco_seg_val.py --model yolo26n-seg
    python scripts/evaluate_coco_seg_val.py --model all
    python scripts/evaluate_coco_seg_val.py --model yolo26n-seg --subset 100
"""

import argparse
import io
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

import mlx.core as mx
import numpy as np
from _runtime_dirs import ensure_runtime_dirs

_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_DIR = _SCRIPT_DIR.parent
MODELS_DIR = _PROJECT_DIR / "models"
RESULTS_DIR = _PROJECT_DIR / "results"

sys.path.insert(0, str(_PROJECT_DIR / "src"))

from yolo26mlx import YOLO  # noqa: E402
from yolo26mlx.data.coco_dataset import COCODataset  # noqa: E402
from yolo26mlx.engine.predictor import Predictor  # noqa: E402
from yolo26mlx.utils.metrics import (  # noqa: E402
    SegmentationMetrics,
    gt_instance_masks_from_overlap,
    process_masks_at_proto,
)

try:
    from pycocotools.coco import COCO
    from pycocotools.cocoeval import COCOeval

    PYCOCOTOOLS_AVAILABLE = True
except ImportError:
    PYCOCOTOOLS_AVAILABLE = False

try:
    from pycocotools import mask as coco_mask_util

    PYCOCO_MASK_AVAILABLE = True
except ImportError:
    PYCOCO_MASK_AVAILABLE = False

try:
    import cv2

    _HAS_CV2 = True
except ImportError:
    _HAS_CV2 = False

logger = logging.getLogger(__name__)

ALL_MODELS = ["yolo26n-seg", "yolo26s-seg", "yolo26m-seg", "yolo26l-seg", "yolo26x-seg"]


def find_coco_dataset(data_arg: str | None) -> Path | None:
    """Locate COCO root containing annotations/instances_val2017.json.

    Args:
        data_arg: Explicit dataset path from CLI, or None to search defaults.

    Returns:
        Resolved dataset root, or None if not found.
    """
    candidates: list[Path] = []
    if data_arg:
        candidates.append(Path(data_arg).expanduser().resolve())
    candidates.extend(
        [
            (_PROJECT_DIR / "datasets" / "coco").resolve(),
            (Path.home() / "datasets" / "coco").resolve(),
        ]
    )
    seen: set[Path] = set()
    for root in candidates:
        if root in seen:
            continue
        seen.add(root)
        ann = root / "annotations" / "instances_val2017.json"
        if ann.is_file():
            return root
    return None


def _orig_xyxy_to_norm_letterbox(
    xyxy: np.ndarray,
    orig_h: int,
    orig_w: int,
    ratio: float,
    pad: tuple[float, float],
    img_size: int,
) -> np.ndarray:
    """Map boxes from original pixel xyxy to normalized xyxy in letterboxed square."""
    if len(xyxy) == 0:
        return xyxy.astype(np.float32)
    pad_w, pad_h = pad[0], pad[1]
    x1, y1, x2, y2 = xyxy[:, 0], xyxy[:, 1], xyxy[:, 2], xyxy[:, 3]
    x1n = (x1 * ratio + pad_w) / img_size
    y1n = (y1 * ratio + pad_h) / img_size
    x2n = (x2 * ratio + pad_w) / img_size
    y2n = (y2 * ratio + pad_h) / img_size
    out = np.stack(
        [
            np.clip(x1n, 0, 1),
            np.clip(y1n, 0, 1),
            np.clip(x2n, 0, 1),
            np.clip(y2n, 0, 1),
        ],
        axis=1,
    ).astype(np.float32)
    return out


def _resize_masks_to_grid(masks: np.ndarray, out_h: int, out_w: int) -> np.ndarray:
    """Resize (N, H, W) instance masks to (N, out_h, out_w)."""
    if len(masks) == 0:
        return masks
    n = masks.shape[0]
    if masks.shape[1] == out_h and masks.shape[2] == out_w:
        return masks.astype(np.float32)
    out = np.zeros((n, out_h, out_w), dtype=np.float32)
    if _HAS_CV2:
        for i in range(n):
            out[i] = cv2.resize(masks[i], (out_w, out_h), interpolation=cv2.INTER_NEAREST)
    else:
        import math

        sh = max(1, math.ceil(out_h / masks.shape[1]))
        sw = max(1, math.ceil(out_w / masks.shape[2]))
        tmp = np.repeat(np.repeat(masks.astype(np.float32), sh, axis=1), sw, axis=2)
        out = tmp[:, :out_h, :out_w]
    return out


# Mask-mAP helpers ``process_masks_at_proto`` and
# ``gt_instance_masks_from_overlap`` now live in
# ``yolo26mlx.utils.metrics`` so the trainer's own validator can reuse them.


def _encode_mask_rle(binary_hw: np.ndarray) -> dict | None:
    """Encode a single binary (H, W) mask as COCO RLE dict for JSON."""
    if not PYCOCO_MASK_AVAILABLE:
        return None
    m = (binary_hw > 0).astype(np.uint8)
    if m.size == 0:
        return None
    fort = np.asfortranarray(m)
    rle = coco_mask_util.encode(fort)
    return {
        "size": [int(rle["size"][0]), int(rle["size"][1])],
        "counts": rle["counts"].decode("utf-8")
        if isinstance(rle["counts"], bytes)
        else rle["counts"],
    }


def _append_coco_pred_entries(
    results: list[dict],
    image_id: int,
    xyxy_orig: np.ndarray,
    scores: np.ndarray,
    labels: np.ndarray,
    masks_hw: np.ndarray | None,
    orig_size: tuple[int, int],
) -> None:
    """Append COCO detection (+ optional segmentation) entries."""
    orig_h, orig_w = orig_size
    for i in range(len(xyxy_orig)):
        x1, y1, x2, y2 = xyxy_orig[i]
        x1 = max(0, min(orig_w, float(x1)))
        y1 = max(0, min(orig_h, float(y1)))
        x2 = max(0, min(orig_w, float(x2)))
        y2 = max(0, min(orig_h, float(y2)))
        bw = x2 - x1
        bh = y2 - y1
        if bw <= 0 or bh <= 0:
            continue
        cat = int(COCODataset.COCO_IDS[int(labels[i])])
        entry: dict = {
            "image_id": int(image_id),
            "category_id": cat,
            "bbox": [float(x1), float(y1), float(bw), float(bh)],
            "score": float(scores[i]),
        }
        if masks_hw is not None and i < masks_hw.shape[0]:
            rle = _encode_mask_rle(masks_hw[i])
            if rle is not None:
                entry["segmentation"] = rle
        results.append(entry)


def evaluate_with_pycocotools(ann_file: str, pred_file: str) -> dict:
    """Run official COCO bbox and (if available) mask evaluation."""
    if not PYCOCOTOOLS_AVAILABLE:
        raise ImportError("pycocotools not installed. Run: pip install pycocotools")

    with open(pred_file) as f:
        preds = json.load(f)
    pred_img_ids = list({int(p["image_id"]) for p in preds})
    has_segm = any("segmentation" in p for p in preds)

    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    coco_gt = COCO(ann_file)
    sys.stdout = old_stdout

    coco_dt = coco_gt.loadRes(pred_file)

    coco_eval_b = COCOeval(coco_gt, coco_dt, "bbox")
    coco_eval_b.params.imgIds = pred_img_ids
    coco_eval_b.evaluate()
    coco_eval_b.accumulate()
    coco_eval_b.summarize()

    out: dict = {
        "mAP50-95_box": float(coco_eval_b.stats[0]),
        "mAP50_box": float(coco_eval_b.stats[1]),
        "mAP75_box": float(coco_eval_b.stats[2]),
        "mAP50-95_mask": None,
        "mAP50_mask": None,
        "mAP75_mask": None,
    }

    if has_segm and PYCOCO_MASK_AVAILABLE:
        try:
            coco_eval_s = COCOeval(coco_gt, coco_dt, "segm")
            coco_eval_s.params.imgIds = pred_img_ids
            coco_eval_s.evaluate()
            coco_eval_s.accumulate()
            coco_eval_s.summarize()
            out["mAP50-95_mask"] = float(coco_eval_s.stats[0])
            out["mAP50_mask"] = float(coco_eval_s.stats[1])
            out["mAP75_mask"] = float(coco_eval_s.stats[2])
        except Exception as e:
            logger.warning("pycocotools segmentation eval failed: %s", e)

    return out


def evaluate_model(
    model_name: str,
    dataset_root: Path,
    img_size: int,
    subset: int | None,
    verbose: bool,
    output_dir: Path,
    conf: float = 0.001,
    batch_size: int = 16,
) -> dict | None:
    """Run val2017 segmentation eval for one model.

    Returns:
        Results dict with box and mask mAP, or None if weights are missing.
    """
    logger.info("\n" + "=" * 70)
    logger.info("Evaluating: %s", model_name)
    logger.info("=" * 70)

    weights_candidates = [
        MODELS_DIR / f"{model_name}.safetensors",
        MODELS_DIR / f"{model_name}.npz",
        MODELS_DIR / f"{model_name}.pt",
    ]
    weights_path = next((p for p in weights_candidates if p.exists()), None)
    if weights_path is None:
        logger.warning("No weights found for %s (tried safetensors, npz, pt).", model_name)
        logger.warning("Searched under %s", MODELS_DIR)
        return None

    logger.info("Loading model from %s ...", weights_path)
    try:
        model = YOLO(str(weights_path), task="segment", verbose=verbose)
    except Exception as e:
        logger.error("Failed to load model %s: %s", model_name, e)
        return None

    inner = model.model
    if inner is None:
        logger.error("Model has no inner module loaded.")
        return None
    if hasattr(inner, "eval"):
        inner.eval()
    if hasattr(inner, "compile_for_inference"):
        inner.compile_for_inference()

    predictor = Predictor(inner, task="segment", names=model.names, stride=model.stride)

    dataset = COCODataset(
        str(dataset_root),
        split="val2017",
        img_size=img_size,
        task="segment",
    )
    num_images = len(dataset)
    if subset is not None:
        num_images = min(int(subset), num_images)

    seg_metrics = SegmentationMetrics(num_classes=80)
    coco_predictions: list[dict] = []

    preprocess_time = 0.0
    inference_time = 0.0
    postprocess_time = 0.0
    processed = 0
    masks_available = True

    logger.info("%s images to process", num_images)

    for _batch_idx, (images, annotations) in enumerate(dataset.get_dataloader(batch_size)):
        if processed >= num_images:
            break
        actual_batch = min(images.shape[0], num_images - processed)

        t0 = time.perf_counter()
        t_pre = time.perf_counter()

        batch_mx = images[:actual_batch]
        outputs = inner(batch_mx)
        if isinstance(outputs, tuple):
            mx.eval(outputs[0], outputs[1])
        else:
            mx.eval(outputs)

        t_inf = time.perf_counter()

        det_np = np.array(outputs[0]) if isinstance(outputs, tuple) else None
        proto_np = np.array(outputs[1]) if isinstance(outputs, tuple) and len(outputs) > 1 else None

        if det_np is None or proto_np is None:
            logger.warning("Unexpected model output (expected det, proto tuple); skipping batch.")
            masks_available = False
            postprocess_time += time.perf_counter() - t_inf
            preprocess_time += t_pre - t0
            inference_time += t_inf - t_pre
            continue

        for i in range(actual_batch):
            ann = annotations[i]
            orig_h, orig_w = ann["orig_size"]
            letterbox_info = {
                "ratio": float(ann["ratio"]),
                "dw": float(ann["pad"][0]),
                "dh": float(ann["pad"][1]),
            }

            pred_i = det_np[i]
            proto_i = proto_np[i]

            boxes_obj, masks_obj = predictor._postprocess_segment(
                pred_i,
                proto_i,
                (orig_h, orig_w),
                letterbox_info,
                conf,
            )

            xyxy_orig = boxes_obj.xyxy
            scores = boxes_obj.conf
            labels = boxes_obj.cls.astype(np.int64)

            # Full-res masks for pycocotools RLE
            pred_masks_full: np.ndarray | None = None
            if masks_obj.data is not None and masks_obj.data.size > 0:
                pred_masks_full = masks_obj.data.astype(np.float32)

            # Grid-res masks (at proto resolution) for ultralytics-style metric
            grid_masks, grid_boxes, grid_scores, grid_labels = process_masks_at_proto(
                pred_i,
                proto_i,
                conf,
            )

            overlap = ann.get("masks")
            gt_stack, k_inst = gt_instance_masks_from_overlap(
                np.array(overlap) if overlap is not None else np.array([])
            )
            if k_inst > 0:
                gt_boxes = ann["boxes"][:k_inst].astype(np.float32)
                gt_labels = ann["labels"][:k_inst].astype(np.int64)
                gt_masks_arg = gt_stack
            else:
                gt_boxes = ann["boxes"].astype(np.float32)
                gt_labels = ann["labels"].astype(np.int64)
                gt_masks_arg = None

            seg_metrics.update(
                grid_boxes,
                grid_scores,
                grid_labels,
                grid_masks if grid_masks.size > 0 else None,
                gt_boxes,
                gt_labels,
                gt_masks_arg,
            )

            _append_coco_pred_entries(
                coco_predictions,
                ann["image_id"],
                xyxy_orig,
                scores,
                labels,
                pred_masks_full,
                (orig_h, orig_w),
            )

        t_post = time.perf_counter()
        preprocess_time += t_pre - t0
        inference_time += t_inf - t_pre
        postprocess_time += t_post - t_inf
        processed += actual_batch

        if verbose or processed % 100 == 0:
            logger.info("  Processed %s/%s images", processed, num_images)

    logger.info("Processed %s/%s images", processed, num_images)

    output_dir.mkdir(parents=True, exist_ok=True)
    pred_path = output_dir / f"{model_name}_coco_seg_predictions.json"
    with open(pred_path, "w") as f:
        json.dump(coco_predictions, f, indent=2)
        f.write("\n")
    logger.info("Saved %s COCO-format predictions to %s", len(coco_predictions), pred_path)

    custom = seg_metrics.compute()
    ann_file = dataset_root / "annotations" / "instances_val2017.json"

    use_pycoco = PYCOCOTOOLS_AVAILABLE and len(coco_predictions) > 0 and ann_file.is_file()
    pycoco: dict | None = None
    if use_pycoco:
        try:
            logger.info("Running official pycocotools evaluation...")
            pycoco = evaluate_with_pycocotools(str(ann_file), str(pred_path))
            logger.info("%s", "=" * 80)
            logger.info("Official COCO box metrics (pycocotools)")
            logger.info("%s", "=" * 80)
            logger.info("  mAP@0.5:0.95 (box) = %.1f%%", pycoco["mAP50-95_box"] * 100)
            logger.info("  mAP@0.5 (box)      = %.1f%%", pycoco["mAP50_box"] * 100)
            if pycoco.get("mAP50_mask") is not None:
                logger.info("%s", "=" * 80)
                logger.info("Official COCO mask metrics (pycocotools)")
                logger.info("%s", "=" * 80)
                logger.info("  mAP@0.5:0.95 (mask) = %.1f%%", pycoco["mAP50-95_mask"] * 100)
                logger.info("  mAP@0.5 (mask)      = %.1f%%", pycoco["mAP50_mask"] * 100)
            else:
                logger.info(
                    "Mask mAP from pycocotools unavailable (add RLE segmentations or fix pycocotools mask)."
                )
        except Exception as e:
            logger.warning("pycocotools evaluation failed, using SegmentationMetrics only: %s", e)
            pycoco = None

    # Prefer pycocotools (orig-resolution masks via RLE) for the primary
    # metrics. This matches the methodology Ultralytics uses for its
    # published numbers (model.val(save_json=True) -> process_mask_native
    # + pycocotools), so MLX vs PyTorch is apples-to-apples. The grid /
    # proto-resolution custom metric is preserved in metrics_custom for
    # backward compatibility and as a sanity cross-check.
    if pycoco is not None:
        m50b = pycoco["mAP50_box"]
        m5095b = pycoco["mAP50-95_box"]
        m50m = pycoco.get("mAP50_mask", custom["mAP50_mask"])
        m5095m = pycoco.get("mAP50-95_mask", custom["mAP50-95_mask"])
    else:
        m50b = custom["mAP50_box"]
        m5095b = custom["mAP50-95_box"]
        m50m = custom["mAP50_mask"]
        m5095m = custom["mAP50-95_mask"]
    if not masks_available:
        logger.info(
            "Mask predictions were not available; mask mAP reflects box-only matching for masks."
        )

    avg_pre = preprocess_time / max(processed, 1) * 1000
    avg_inf = inference_time / max(processed, 1) * 1000
    avg_post = postprocess_time / max(processed, 1) * 1000
    avg_total = avg_pre + avg_inf + avg_post

    logger.info(
        "Speed: %.1fms preprocess, %.1fms inference, %.1fms postprocess per image",
        avg_pre,
        avg_inf,
        avg_post,
    )
    logger.info("Total: %.1fms per image (%.1f FPS)", avg_total, 1000.0 / max(avg_total, 1e-9))

    results = {
        "model": model_name,
        "framework": "mlx",
        "dataset": "coco_val2017",
        "num_images": processed,
        "imgsz": img_size,
        "conf_thresh": conf,
        "pycocotools": pycoco is not None,
        "metrics": {
            "mAP50_mask": float(m50m),
            "mAP50-95_mask": float(m5095m),
            "mAP50_box": float(m50b),
            "mAP50-95_box": float(m5095b),
        },
        "metrics_custom": {k: float(v) for k, v in custom.items()},
        "speed": {
            "preprocess_ms": avg_pre,
            "inference_ms": avg_inf,
            "postprocess_ms": avg_post,
            "total_ms": avg_total,
            "fps": 1000.0 / max(avg_total, 1e-9),
        },
        "timestamp": datetime.now().isoformat(),
    }

    per_model_json = output_dir / f"{model_name}_coco_seg_val2017_results.json"
    with open(per_model_json, "w") as f:
        json.dump(results, f, indent=2)
    logger.info("Results saved to %s", per_model_json)

    return results


def parse_args():
    parser = argparse.ArgumentParser(
        description="Evaluate YOLO26-seg MLX on COCO val2017 (box + mask mAP).",
    )
    parser.add_argument(
        "--model",
        type=str,
        nargs="+",
        default=["yolo26n-seg"],
        help="Model variant(s). Use 'all' for all five sizes.",
    )
    parser.add_argument(
        "--data",
        type=str,
        default=None,
        help="COCO root (default: search datasets/coco and ~/datasets/coco).",
    )
    parser.add_argument("--imgsz", type=int, default=640, help="Input image size")
    parser.add_argument("--batch", type=int, default=16, help="Batch size")
    parser.add_argument(
        "--conf",
        type=float,
        default=0.001,
        help="Confidence threshold for inference",
    )
    parser.add_argument(
        "--subset",
        type=int,
        default=None,
        help="Use only the first N images (quick test)",
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    parser.add_argument(
        "--output",
        type=str,
        default=str(RESULTS_DIR),
        help="Output directory for JSON and prediction files",
    )
    return parser.parse_args()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = parse_args()
    ensure_runtime_dirs(_PROJECT_DIR)

    models = args.model
    if "all" in [m.lower() for m in models]:
        models = list(ALL_MODELS)
    else:
        for m in models:
            if m not in ALL_MODELS:
                logger.error("Unknown model: %s", m)
                logger.error("Available: %s", ", ".join(ALL_MODELS))
                return 1

    data_root = find_coco_dataset(args.data)
    if data_root is None:
        logger.error("COCO val2017 not found. Expected annotations/instances_val2017.json")
        logger.error(
            "Tried --data (if set), %s, ~/datasets/coco", _PROJECT_DIR / "datasets" / "coco"
        )
        logger.error("Hint: ./scripts/download_coco_val2017.sh")
        return 1

    logger.info("=" * 70)
    logger.info("YOLO26 MLX - COCO val2017 Segmentation Evaluation")
    logger.info("=" * 70)
    logger.info("Models:       %s", ", ".join(models))
    logger.info("Dataset:      %s", data_root)
    logger.info("Image size:   %s", args.imgsz)
    logger.info("Batch size:   %s", args.batch)
    logger.info("Conf thresh:  %s", args.conf)
    if args.subset:
        logger.info("Subset:       %s images", args.subset)
    logger.info("=" * 70)

    output_dir = Path(args.output)
    all_results: dict[str, dict] = {}

    for name in models:
        try:
            r = evaluate_model(
                name,
                data_root,
                args.imgsz,
                args.subset,
                args.verbose,
                output_dir,
                conf=args.conf,
                batch_size=args.batch,
            )
            if r is not None:
                all_results[name] = r
        except Exception as e:
            logger.error("Failed to evaluate %s: %s", name, e)
            import traceback

            traceback.print_exc()

    if all_results:
        # Reference mAP@0.5:0.95 from the Ultralytics YOLO26 docs
        # (https://docs.ultralytics.com/models/yolo26/). MLX numbers above
        # use pycocotools at original-image resolution (RLE), matching
        # `model.val(save_json=True)` -> process_mask_native + pycocotools,
        # so MLX vs Official is apples-to-apples.
        official_box5095 = {
            "yolo26n-seg": 39.6,
            "yolo26s-seg": 47.3,
            "yolo26m-seg": 52.5,
            "yolo26l-seg": 54.4,
            "yolo26x-seg": 56.5,
        }
        official_mask5095 = {
            "yolo26n-seg": 33.9,
            "yolo26s-seg": 40.0,
            "yolo26m-seg": 44.1,
            "yolo26l-seg": 45.5,
            "yolo26x-seg": 47.0,
        }

        logger.info("\n" + "=" * 102)
        logger.info("SUMMARY - Box vs mask mAP@0.5:0.95 (%%)")
        logger.info("=" * 102)
        logger.info(
            "%-14s %14s %12s %14s %12s %8s %10s",
            "Model",
            "mAP50-95 box",
            "(Official)",
            "mAP50-95 mask",
            "(Official)",
            "FPS",
            "ms/img",
        )
        logger.info("-" * 102)
        for m in ALL_MODELS:
            if m not in all_results:
                continue
            r = all_results[m]
            b5095 = r["metrics"]["mAP50-95_box"] * 100
            m5095 = r["metrics"]["mAP50-95_mask"] * 100
            off_b = official_box5095.get(m, 0.0)
            off_m = official_mask5095.get(m, 0.0)
            fps = r["speed"]["fps"]
            ms = r["speed"]["total_ms"]
            logger.info(
                "%-14s %13.1f%% %10.1f%% %13.1f%% %10.1f%% %7.1f %9.1fms",
                m,
                b5095,
                off_b,
                m5095,
                off_m,
                fps,
                ms,
            )
        logger.info("=" * 102)

        combined = output_dir / "yolo26_seg_coco_val_results.json"
        with open(combined, "w") as f:
            json.dump(all_results, f, indent=2)
        logger.info("\nCombined results saved to %s", combined)

    if args.subset:
        logger.info(
            "\nNote: subset mode (%s images). Full val2017 has 5000 images.",
            args.subset,
        )

    return 0 if all_results else 1


if __name__ == "__main__":
    sys.exit(main())
