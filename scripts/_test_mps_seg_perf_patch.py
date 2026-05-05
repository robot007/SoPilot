#!/usr/bin/env python3
# Copyright (c) 2026 webAI, Inc.
"""
Numerical parity test for ``_mps_seg_perf_patch.apply_mps_seg_perf_patch``.

Runs one yolo26n-seg training step with the original Ultralytics loss and
again with the MPS-fast patch on the *same* batch + same model state, and
asserts that both ``loss`` and ``loss_items`` match within float32 tolerance.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA_YAML = ROOT / "datasets" / "coco128_seg_local.yaml"
sys.path.insert(0, str(Path(__file__).parent))

logger = logging.getLogger("test")


def _build_one_step():
    """Return ``(model, batch)`` ready to call ``model.loss(batch, preds=preds)``."""
    from ultralytics.cfg import get_cfg
    from ultralytics.models.yolo.segment import SegmentationTrainer
    from ultralytics.utils import DEFAULT_CFG_DICT

    weights_pt = ROOT / "models" / "yolo26n-seg.pt"
    overrides = dict(DEFAULT_CFG_DICT)
    overrides.update(
        model=str(weights_pt) if weights_pt.exists() else "yolo26n-seg.pt",
        data=str(DATA_YAML),
        epochs=1,
        imgsz=640,
        batch=2,
        device="mps",
        workers=0,
        cache=False,
        amp=False,
        verbose=False,
        save=False,
        plots=False,
        val=False,
    )
    cfg = get_cfg(DEFAULT_CFG_DICT, overrides)
    trainer = SegmentationTrainer(cfg=cfg, overrides=overrides)
    try:
        trainer._setup_train(world_size=1)
    except TypeError:
        trainer._setup_train()
    batch = next(iter(trainer.train_loader))
    batch = trainer.preprocess_batch(batch)
    return trainer.model, batch


def main() -> None:
    """Compare original and patched losses on a single batch."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    import torch
    from _mps_seg_perf_patch import apply_mps_seg_perf_patch, revert_mps_seg_perf_patch

    model, batch = _build_one_step()
    model.train()

    torch.manual_seed(0)
    preds = model(batch["img"])
    loss_orig, items_orig = model.loss(batch, preds=preds)
    torch.mps.synchronize()
    loss_orig_v = loss_orig.detach().cpu()
    items_orig_v = items_orig.detach().cpu()

    apply_mps_seg_perf_patch()
    torch.manual_seed(0)
    preds = model(batch["img"])
    loss_new, items_new = model.loss(batch, preds=preds)
    torch.mps.synchronize()
    loss_new_v = loss_new.detach().cpu()
    items_new_v = items_new.detach().cpu()

    revert_mps_seg_perf_patch()

    rel_loss = (loss_orig_v - loss_new_v).abs() / loss_orig_v.abs().clamp(min=1e-9)
    rel_items = (items_orig_v - items_new_v).abs() / items_orig_v.abs().clamp(min=1e-9)

    logger.info(f"loss_orig: {loss_orig_v.tolist()}")
    logger.info(f"loss_new : {loss_new_v.tolist()}")
    logger.info(f"items_orig: {items_orig_v.tolist()}")
    logger.info(f"items_new : {items_new_v.tolist()}")
    logger.info(f"max rel diff (loss):  {rel_loss.max().item():.2e}")
    logger.info(f"max rel diff (items): {rel_items.max().item():.2e}")

    assert rel_loss.max().item() < 1e-4, "Patched loss diverges from original."
    assert rel_items.max().item() < 1e-4, "Patched loss_items diverge from original."
    logger.info("PASS: patched MPS loss is numerically equivalent.")


if __name__ == "__main__":
    main()
