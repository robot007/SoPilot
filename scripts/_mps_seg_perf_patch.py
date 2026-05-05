# Copyright (c) 2026 webAI, Inc.
"""
PyTorch MPS performance patch for Ultralytics' YOLO26 segmentation training.

The unpatched ``v8SegmentationLoss.loss`` contains a single line that
dominates wall time on Apple GPUs by ~20×:

    sem_masks[mask_zero.unsqueeze(1).expand_as(sem_masks)] = 0

Boolean-mask scatter assignment (``tensor[bool_mask] = value``) hits a
pathologically slow path on the PyTorch MPS backend for large 4-D tensors
(``[B, num_classes, H, W]``). Profiling shows this single statement
consuming ~4.7 s per training step for ``yolo26n-seg`` at ``batch=2,
imgsz=640`` — turning what should be ~600 ms/step into ~9.3 s/step
(15× slower than the Apple GPU is actually capable of and 13× slower
than CPU).

The mathematically equivalent multiplicative form

    keep = (~mask_zero).to(sem_masks.dtype).unsqueeze(1)
    sem_masks = sem_masks * keep

uses only elementwise multiply + broadcast and runs in well under a
millisecond on MPS, eliminating the bottleneck completely.

Apply once at process start::

    from _mps_seg_perf_patch import apply_mps_seg_perf_patch
    apply_mps_seg_perf_patch()
"""

from __future__ import annotations

import torch
import torch.nn.functional as F
from ultralytics.utils.loss import v8SegmentationLoss

_ORIGINAL_LOSS = v8SegmentationLoss.loss


def _fast_loss(
    self: v8SegmentationLoss,
    preds: dict[str, torch.Tensor],
    batch: dict[str, torch.Tensor],
) -> tuple[torch.Tensor, torch.Tensor]:
    """Drop-in replacement for ``v8SegmentationLoss.loss`` with MPS-fast semseg masking.

    Numerically identical to the upstream Ultralytics implementation; the
    only behavioural change is that the boolean-scatter mask-clearing
    statement is rewritten as an elementwise multiply against a 0/1
    indicator. This avoids the slow MPS path for ``Tensor.__setitem__``
    with a boolean mask on 4-D tensors.
    """
    pred_masks, proto = preds["mask_coefficient"].permute(0, 2, 1).contiguous(), preds["proto"]
    loss = torch.zeros(5, device=self.device)  # box, seg, cls, dfl, semseg
    if isinstance(proto, tuple) and len(proto) == 2:
        proto, pred_semseg = proto
    else:
        pred_semseg = None

    (fg_mask, target_gt_idx, target_bboxes, _, _), det_loss, _ = self.get_assigned_targets_and_loss(
        preds, batch
    )
    loss[0], loss[2], loss[3] = det_loss[0], det_loss[1], det_loss[2]

    batch_size, _, mask_h, mask_w = proto.shape
    if fg_mask.sum():
        masks = batch["masks"].to(self.device).float()
        if tuple(masks.shape[-2:]) != (mask_h, mask_w):
            proto = F.interpolate(proto, masks.shape[-2:], mode="bilinear", align_corners=False)

        imgsz = (
            torch.tensor(preds["feats"][0].shape[2:], device=self.device, dtype=pred_masks.dtype)
            * self.stride[0]
        )
        loss[1] = self.calculate_segmentation_loss(
            fg_mask,
            masks,
            target_gt_idx,
            target_bboxes,
            batch["batch_idx"].view(-1, 1),
            proto,
            pred_masks,
            imgsz,
        )
        if pred_semseg is not None:
            sem_masks = batch["sem_masks"].to(self.device)  # NxHxW
            sem_masks = (
                F.one_hot(sem_masks.long(), num_classes=self.nc).permute(0, 3, 1, 2).float()
            )  # NxCxHxW

            if self.overlap:
                # FAST PATH (MPS): replace boolean-scatter assign with multiply.
                # ``mask_zero`` is True where the merged instance mask is empty;
                # we want sem_masks=0 at those locations across all C channels.
                mask_zero = (masks == 0).unsqueeze(1)  # (N, 1, H, W) bool
                keep = (~mask_zero).to(sem_masks.dtype)  # (N, 1, H, W)
                sem_masks = sem_masks * keep
            else:
                # Non-overlap path: still vectorize the per-image clear
                # using scatter-style indexing on the batch axis.
                batch_idx = batch["batch_idx"].view(-1)
                # Build a per-image "any instance present" mask of shape (N, H, W)
                instance_present = torch.zeros(
                    batch_size,
                    masks.shape[-2],
                    masks.shape[-1],
                    device=self.device,
                    dtype=torch.bool,
                )
                for i in range(batch_size):
                    inst_i = masks[batch_idx == i]
                    if len(inst_i) > 0:
                        instance_present[i] = inst_i.sum(dim=0) > 0
                keep = instance_present.unsqueeze(1).to(sem_masks.dtype)
                sem_masks = sem_masks * keep

            loss[4] = self.bcedice_loss(pred_semseg, sem_masks)
            loss[4] *= self.hyp.box

    else:
        loss[1] += (proto * 0).sum() + (pred_masks * 0).sum()
        if pred_semseg is not None:
            loss[4] += (pred_semseg * 0).sum()

    loss[1] *= self.hyp.box
    return loss * batch_size, loss.detach()


def apply_mps_seg_perf_patch() -> None:
    """Monkey-patch ``v8SegmentationLoss.loss`` with the MPS-fast variant.

    Idempotent — calling this more than once has no additional effect.
    """
    if getattr(v8SegmentationLoss.loss, "__mps_patched__", False):
        return
    _fast_loss.__mps_patched__ = True  # type: ignore[attr-defined]
    v8SegmentationLoss.loss = _fast_loss


def revert_mps_seg_perf_patch() -> None:
    """Restore the original Ultralytics ``v8SegmentationLoss.loss``."""
    v8SegmentationLoss.loss = _ORIGINAL_LOSS
