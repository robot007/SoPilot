# Copyright (c) 2026 webAI, Inc.
"""
Vectorized replacement for ``v8SegmentationLoss.calculate_segmentation_loss``.

Ultralytics' upstream implementation iterates over the batch dimension in a
Python ``for`` loop, with several boolean-indexed gathers per iteration
(``pred_masks_i[fg_mask_i]``, ``mxyxy_i[fg_mask_i]``, …). Both patterns are
pathological on the PyTorch MPS backend:

* the Python loop forces a host↔device sync each iteration via
  ``fg_mask_i.any()``;
* boolean gather kernels on MPS dispatch and synchronize per element ranges,
  producing per-call overhead that dominates for the small per-anchor tensors
  used in YOLO's per-image loop.

This module provides a drop-in replacement that processes **all positive
anchors across the batch in a single vectorized pass**, using fancy indexing
(``nonzero`` → integer indices) and inline mask cropping. Apply with
``apply_vectorized_seg_loss()`` once at process start; subsequent
``model.train(...)`` calls will use it transparently.

Numerics are equivalent (BCE + crop + per-mask-area normalize + sum). The
only difference is execution shape — no per-image branch — so on Apple GPU
this turns the segmentation loss from a per-step bottleneck into a single
fused dispatch.
"""

from __future__ import annotations

import torch
import torch.nn.functional as F
from ultralytics.utils.loss import v8SegmentationLoss
from ultralytics.utils.ops import xyxy2xywh

_ORIGINAL = v8SegmentationLoss.calculate_segmentation_loss


def _vectorized_calculate_segmentation_loss(
    self,
    fg_mask: torch.Tensor,
    masks: torch.Tensor,
    target_gt_idx: torch.Tensor,
    target_bboxes: torch.Tensor,
    batch_idx: torch.Tensor,
    proto: torch.Tensor,
    pred_masks: torch.Tensor,
    imgsz: torch.Tensor,
) -> torch.Tensor:
    """Vectorized seg-loss; numerically equivalent to upstream Ultralytics.

    Replaces the per-image Python loop with a single batch-flat pass over all
    positive anchors. Shapes match the upstream contract exactly so this can
    be monkey-patched into ``v8SegmentationLoss`` without touching any
    surrounding training code.

    Args:
        fg_mask: ``(B, N_anchors)`` bool — positive anchors.
        masks: ``(B, mh, mw)`` overlap-encoded GT (``overlap=True``) or
            ``(K_total, mh, mw)`` per-instance binary GT (``overlap=False``).
        target_gt_idx: ``(B, N_anchors)`` long — assigned GT idx per anchor.
        target_bboxes: ``(B, N_anchors, 4)`` xyxy in image pixels.
        batch_idx: ``(K_total, 1)`` image idx per GT instance.
        proto: ``(B, NC, mh, mw)`` proto features.
        pred_masks: ``(B, N_anchors, NC)`` predicted mask coefficients.
        imgsz: ``(2,)`` ``[H, W]`` of the input image.

    Returns:
        Scalar mean BCE-mask loss, normalized by the same denominator
        (``fg_mask.sum()``) as the upstream implementation.
    """
    _, _, mask_h, mask_w = proto.shape
    device = proto.device
    dtype = pred_masks.dtype

    target_bboxes_normalized = target_bboxes / imgsz[[1, 0, 1, 0]]
    marea = xyxy2xywh(target_bboxes_normalized)[..., 2:].prod(2)  # (B, N_anchors)
    mxyxy = target_bboxes_normalized * torch.tensor(
        [mask_w, mask_h, mask_w, mask_h], device=device, dtype=dtype
    )

    pos_idx = fg_mask.nonzero(as_tuple=False)  # (K, 2)
    n_pos = pos_idx.shape[0]
    fg_sum = fg_mask.sum()

    if n_pos == 0:
        # Match upstream's anti-DDP-unused-grad fallback exactly.
        return (proto * 0).sum() + (pred_masks * 0).sum()

    b_idx = pos_idx[:, 0]
    a_idx = pos_idx[:, 1]

    pred_pos = pred_masks[b_idx, a_idx]  # (K, NC)
    # Build pred_mask_pos without gathering ``proto[b_idx]`` — that path
    # materialises a ``(K, NC, mh, mw)`` tensor and crashes the MPS backward
    # kernel on larger K. Instead: flatten ``proto`` to ``(B, NC, mh*mw)``,
    # index per-positive-anchor by b_idx, then bmm against ``pred_pos``.
    B, NC = proto.shape[0], proto.shape[1]
    proto_flat = proto.reshape(B, NC, mask_h * mask_w)  # (B, NC, mh*mw)
    proto_pos = torch.index_select(proto_flat, 0, b_idx)  # (K, NC, mh*mw)
    pred_mask_pos = torch.bmm(
        pred_pos.unsqueeze(1),  # (K, 1, NC)
        proto_pos,  # (K, NC, mh*mw)
    ).reshape(n_pos, mask_h, mask_w)

    gt_idx_pos = target_gt_idx[b_idx, a_idx]  # (K,)

    if self.overlap:
        gt_mask_pos = (masks[b_idx] == (gt_idx_pos + 1).view(-1, 1, 1)).to(pred_mask_pos.dtype)
    else:
        # Non-overlap: ``masks`` is concatenated per-instance; reconstruct the
        # per-image instance offset so we can fancy-index in one shot.
        bi = batch_idx.view(-1)  # (K_total,)
        b_size = int(fg_mask.shape[0])
        per_image_counts = torch.bincount(bi, minlength=b_size)
        offsets = torch.zeros(b_size, dtype=torch.long, device=device)
        offsets[1:] = per_image_counts.cumsum(0)[:-1]
        linear_idx = offsets[b_idx] + gt_idx_pos
        gt_mask_pos = masks[linear_idx].to(pred_mask_pos.dtype)

    # BCE per-pixel.
    loss_per_pixel = F.binary_cross_entropy_with_logits(
        pred_mask_pos, gt_mask_pos, reduction="none"
    )  # (K, mh, mw)

    # Inline vectorized crop. Matches ``ops.crop_mask`` *fast-path* (n < 50
    # CPU branch) by rounding boxes to integer pixel edges with min=0 — both
    # branches of upstream ``crop_mask`` end up zeroing the same pixels, but
    # the rounded form is what the per-image fallback uses for small batches,
    # and we replicate it so numerics agree to float precision.
    xyxy_pos = mxyxy[b_idx, a_idx].clamp(min=0).round()  # (K, 4) integer pixel coords
    x1, y1, x2, y2 = torch.chunk(xyxy_pos[:, :, None], 4, 1)
    r = torch.arange(mask_w, device=device, dtype=x1.dtype)[None, None, :]
    c = torch.arange(mask_h, device=device, dtype=x1.dtype)[None, :, None]
    crop = (r >= x1) * (r < x2) * (c >= y1) * (c < y2)
    loss_cropped = loss_per_pixel * crop  # (K, mh, mw)

    area_pos = marea[b_idx, a_idx]  # (K,) — no clamp; matches upstream
    loss_per_inst = loss_cropped.mean(dim=(1, 2)) / area_pos
    return loss_per_inst.sum() / fg_sum


def apply_vectorized_seg_loss() -> None:
    """Monkey-patch ``v8SegmentationLoss.calculate_segmentation_loss``.

    Idempotent — repeated calls leave the patch in place. Call once at
    process startup before constructing the trainer.
    """
    v8SegmentationLoss.calculate_segmentation_loss = (  # type: ignore[assignment]
        _vectorized_calculate_segmentation_loss
    )


def restore_seg_loss() -> None:
    """Restore the original Ultralytics implementation (for tests / parity checks)."""
    v8SegmentationLoss.calculate_segmentation_loss = _ORIGINAL  # type: ignore[assignment]
