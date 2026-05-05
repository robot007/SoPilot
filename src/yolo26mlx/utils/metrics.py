# Copyright (c) 2026 webAI, Inc.
"""
Segmentation Metrics

Mask IoU and segmentation evaluation metrics for YOLO26 instance segmentation.
Includes helpers that match Ultralytics' internal grid-based segmentation
evaluation (proto resolution, no upsampling) so that MLX numbers can be
compared apples-to-apples with ``ultralytics.YOLO.val()`` mask mAP.
"""

import numpy as np


def mask_iou(
    mask1: np.ndarray,
    mask2: np.ndarray,
    eps: float = 1e-7,
) -> np.ndarray:
    """Compute IoU between two sets of binary masks.

    Args:
        mask1: Binary masks (N, H, W) as uint8 or bool.
        mask2: Binary masks (M, H, W) as uint8 or bool.
        eps: Small value for numerical stability.

    Returns:
        IoU matrix (N, M).
    """
    mask1 = mask1.reshape(mask1.shape[0], -1).astype(np.float32)  # (N, H*W)
    mask2 = mask2.reshape(mask2.shape[0], -1).astype(np.float32)  # (M, H*W)

    intersection = mask1 @ mask2.T  # (N, M)
    area1 = mask1.sum(axis=1, keepdims=True)  # (N, 1)
    area2 = mask2.sum(axis=1, keepdims=True)  # (1, M)
    union = area1 + area2.T - intersection

    return intersection / (union + eps)


class SegmentationMetrics:
    """Accumulate and compute mask mAP for instance segmentation.

    Tracks both box true-positives and mask true-positives.

    Usage:
        metrics = SegmentationMetrics(num_classes=80)
        for pred, gt in data:
            metrics.update(pred, gt)
        results = metrics.compute()
    """

    IOU_THRESHOLDS = np.linspace(0.5, 0.95, 10)

    def __init__(self, num_classes: int = 80):
        """Initialize metrics tracker.

        Args:
            num_classes: Number of object classes.
        """
        self.num_classes = num_classes
        self._tp_mask: list[np.ndarray] = []
        self._tp_box: list[np.ndarray] = []
        self._confs: list[float] = []
        self._pred_cls: list[int] = []
        self._gt_cls_counts = np.zeros(num_classes, dtype=np.int64)

    def update(
        self,
        pred_boxes: np.ndarray,
        pred_scores: np.ndarray,
        pred_labels: np.ndarray,
        pred_masks: np.ndarray | None,
        gt_boxes: np.ndarray,
        gt_labels: np.ndarray,
        gt_masks: np.ndarray | None,
    ) -> None:
        """Update metrics with predictions and ground truth for one image.

        Args:
            pred_boxes: Predicted boxes (N, 4) xyxy.
            pred_scores: Predicted scores (N,).
            pred_labels: Predicted class indices (N,).
            pred_masks: Predicted binary masks (N, H, W) or None.
            gt_boxes: GT boxes (M, 4) xyxy.
            gt_labels: GT class indices (M,).
            gt_masks: GT binary masks (M, H, W) or None.
        """
        for c in gt_labels:
            if 0 <= c < self.num_classes:
                self._gt_cls_counts[c] += 1

        n_pred = len(pred_boxes)
        n_gt = len(gt_boxes)

        if n_pred == 0 or n_gt == 0:
            for i in range(n_pred):
                self._confs.append(float(pred_scores[i]))
                self._pred_cls.append(int(pred_labels[i]))
                self._tp_mask.append(np.zeros(len(self.IOU_THRESHOLDS), dtype=bool))
                self._tp_box.append(np.zeros(len(self.IOU_THRESHOLDS), dtype=bool))
            return

        has_masks = pred_masks is not None and gt_masks is not None

        # Match predictions to ground truth using the same algorithm as
        # ultralytics DetectionValidator.match_predictions: build a global
        # IoU matrix (GT × pred), zero out class mismatches, then for each
        # threshold greedily assign unique (GT, pred) pairs sorted by IoU.
        # IoU matrices: (n_gt, n_pred)
        b_iou = self._box_iou(gt_boxes, pred_boxes)  # (M, N)
        if has_masks:
            m_iou = mask_iou(gt_masks, pred_masks)  # (M, N)

        correct_class = gt_labels[:, None] == pred_labels[None, :]  # (M, N)
        b_iou_cls = b_iou * correct_class
        if has_masks:
            m_iou_cls = m_iou * correct_class

        tp_b_all = np.zeros((n_pred, len(self.IOU_THRESHOLDS)), dtype=bool)
        tp_m_all = np.zeros((n_pred, len(self.IOU_THRESHOLDS)), dtype=bool)

        for t, thr in enumerate(self.IOU_THRESHOLDS):
            # Box matching
            matches = np.nonzero(b_iou_cls >= thr)
            matches = np.array(matches).T  # (K, 2): [gt_idx, pred_idx]
            if matches.shape[0]:
                if matches.shape[0] > 1:
                    matches = matches[b_iou_cls[matches[:, 0], matches[:, 1]].argsort()[::-1]]
                    matches = matches[np.unique(matches[:, 1], return_index=True)[1]]
                    matches = matches[np.unique(matches[:, 0], return_index=True)[1]]
                tp_b_all[matches[:, 1].astype(int), t] = True

            # Mask matching
            if has_masks:
                m_matches = np.nonzero(m_iou_cls >= thr)
                m_matches = np.array(m_matches).T
                if m_matches.shape[0]:
                    if m_matches.shape[0] > 1:
                        m_matches = m_matches[
                            m_iou_cls[m_matches[:, 0], m_matches[:, 1]].argsort()[::-1]
                        ]
                        m_matches = m_matches[np.unique(m_matches[:, 1], return_index=True)[1]]
                        m_matches = m_matches[np.unique(m_matches[:, 0], return_index=True)[1]]
                    tp_m_all[m_matches[:, 1].astype(int), t] = True

        for i in range(n_pred):
            self._confs.append(float(pred_scores[i]))
            self._pred_cls.append(int(pred_labels[i]))
            self._tp_box.append(tp_b_all[i])
            self._tp_mask.append(tp_m_all[i])

    def compute(self) -> dict[str, float]:
        """Compute all metrics.

        Returns:
            Dict with keys: mAP50_mask, mAP50-95_mask, mAP50_box, mAP50-95_box,
            precision_mask, recall_mask.
        """
        if not self._confs:
            return {
                "mAP50_mask": 0.0,
                "mAP50-95_mask": 0.0,
                "mAP50_box": 0.0,
                "mAP50-95_box": 0.0,
                "precision_mask": 0.0,
                "recall_mask": 0.0,
            }

        confs = np.array(self._confs)
        pred_cls = np.array(self._pred_cls)
        tp_mask = np.stack(self._tp_mask)  # (N_total, 10)
        tp_box = np.stack(self._tp_box)

        order = np.argsort(-confs)
        tp_mask = tp_mask[order]
        tp_box = tp_box[order]
        pred_cls = pred_cls[order]

        # Per-class AP
        ap_mask = np.zeros((self.num_classes, len(self.IOU_THRESHOLDS)))
        ap_box = np.zeros((self.num_classes, len(self.IOU_THRESHOLDS)))

        for c in range(self.num_classes):
            cls_mask = pred_cls == c
            n_gt_c = self._gt_cls_counts[c]
            if n_gt_c == 0 or not cls_mask.any():
                continue

            tp_m_c = tp_mask[cls_mask]
            tp_b_c = tp_box[cls_mask]

            for t in range(len(self.IOU_THRESHOLDS)):
                ap_mask[c, t] = self._compute_ap(tp_m_c[:, t], n_gt_c)
                ap_box[c, t] = self._compute_ap(tp_b_c[:, t], n_gt_c)

        active = self._gt_cls_counts > 0
        n_active = active.sum()
        if n_active == 0:
            n_active = 1

        map50_mask = float(ap_mask[active, 0].sum() / n_active)
        map50_95_mask = float(ap_mask[active].mean(axis=1).sum() / n_active)
        map50_box = float(ap_box[active, 0].sum() / n_active)
        map50_95_box = float(ap_box[active].mean(axis=1).sum() / n_active)

        # Precision/recall at IoU=0.5
        tp_sum = tp_mask[:, 0].sum()
        n_pred_total = len(tp_mask)
        n_gt_total = self._gt_cls_counts.sum()
        precision = float(tp_sum / max(n_pred_total, 1))
        recall = float(tp_sum / max(n_gt_total, 1))

        return {
            "mAP50_mask": round(map50_mask, 4),
            "mAP50-95_mask": round(map50_95_mask, 4),
            "mAP50_box": round(map50_box, 4),
            "mAP50-95_box": round(map50_95_box, 4),
            "precision_mask": round(precision, 4),
            "recall_mask": round(recall, 4),
        }

    @staticmethod
    def _compute_ap(tp: np.ndarray, n_gt: int) -> float:
        """Compute average precision using 101-point interpolation (COCO-style).

        Matches ultralytics ``compute_ap`` for consistent comparison.

        Args:
            tp: Boolean array of true positives for one class at one IoU threshold.
            n_gt: Number of ground truth instances for this class.

        Returns:
            Average precision value.
        """
        if n_gt == 0:
            return 0.0
        cum_tp = np.cumsum(tp)
        recall = cum_tp / n_gt
        precision = cum_tp / np.arange(1, len(tp) + 1)

        mrec = np.concatenate(([0.0], recall, [1.0]))
        mpre = np.concatenate(([1.0], precision, [0.0]))

        mpre = np.flip(np.maximum.accumulate(np.flip(mpre)))

        x = np.linspace(0, 1, 101)
        ap = float(np.trapezoid(np.interp(x, mrec, mpre), x))
        return ap

    @staticmethod
    def _box_iou(box1: np.ndarray, box2: np.ndarray, eps: float = 1e-7) -> np.ndarray:
        """Compute box IoU between two sets of boxes in xyxy format.

        Args:
            box1: (N, 4) boxes.
            box2: (M, 4) boxes.
            eps: Numerical stability.

        Returns:
            IoU matrix (N, M).
        """
        area1 = (box1[:, 2] - box1[:, 0]) * (box1[:, 3] - box1[:, 1])
        area2 = (box2[:, 2] - box2[:, 0]) * (box2[:, 3] - box2[:, 1])

        inter_x1 = np.maximum(box1[:, None, 0], box2[None, :, 0])
        inter_y1 = np.maximum(box1[:, None, 1], box2[None, :, 1])
        inter_x2 = np.minimum(box1[:, None, 2], box2[None, :, 2])
        inter_y2 = np.minimum(box1[:, None, 3], box2[None, :, 3])

        inter = np.maximum(inter_x2 - inter_x1, 0) * np.maximum(inter_y2 - inter_y1, 0)
        union = area1[:, None] + area2[None, :] - inter
        return inter / (union + eps)


def gt_instance_masks_from_overlap(
    overlap: np.ndarray,
) -> tuple[np.ndarray, int]:
    """Split a COCODataset overlap mask into per-instance binary masks.

    The dataloader rasterizes polygon segments into a single (H, W) overlap
    map where pixel value ``i`` (1-indexed) marks the pixels belonging to
    the i-th instance. This helper splits it into a (K, H, W) stack of
    per-instance binary masks at the same resolution as the overlap map.

    Args:
        overlap: Overlap mask (H, W) with int instance ids (0 = background).

    Returns:
        ``(stack, k)`` where ``stack`` has shape ``(k, H, W)`` (float32) and
        ``k`` is the number of instances. Returns empty arrays when ``k=0``.
    """
    if overlap is None or overlap.size == 0:
        return np.zeros((0, 0, 0), dtype=np.float32), 0
    k = int(overlap.max())
    if k <= 0:
        return np.zeros((0, overlap.shape[0], overlap.shape[1]), dtype=np.float32), 0
    stacked = np.stack([(overlap == i).astype(np.float32) for i in range(1, k + 1)])
    return stacked, k


def process_masks_at_proto(
    det_pred: np.ndarray,
    protos: np.ndarray,
    conf: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Compute predicted masks at prototype resolution (proto grid).

    Mirrors Ultralytics' internal SegmentMetrics evaluation: linearly combine
    mask coefficients with the proto grid, crop by the predicted box (in proto
    space), then binarize. No upsampling — kept at proto resolution so IoU
    matches the Ultralytics validator that uses 160×160 masks for 640×640
    input.

    Args:
        det_pred: ``(max_det, 6+nm)`` per-image detections in letterbox space:
            ``[cx, cy, w, h, conf, cls, c0, ..., c_{nm-1}]``.
        protos: ``(mh, mw, c)`` HWC proto features from the segmentation head.
        conf: Confidence threshold; rows with ``score <= conf`` are dropped.

    Returns:
        ``(masks_grid, lb_boxes_norm, scores, labels)``:
            - ``masks_grid``: ``(N, mh, mw)`` uint8 binary masks at proto resolution.
            - ``lb_boxes_norm``: ``(N, 4)`` xyxy boxes normalized to ``[0, 1]`` in
              the letterbox square (suitable for direct IoU vs the dataloader's
              normalized-letterbox GT boxes).
            - ``scores``: ``(N,)`` float scores.
            - ``labels``: ``(N,)`` int64 class indices.
        Empty arrays when no detection passes ``conf``.
    """
    if det_pred is None or len(det_pred) == 0 or protos is None:
        return np.empty((0,)), np.empty((0, 4)), np.empty((0,)), np.empty((0,))

    if det_pred.ndim == 1:
        det_pred = det_pred.reshape(1, -1)
    if det_pred.shape[-1] <= 6:
        return np.empty((0,)), np.empty((0, 4)), np.empty((0,)), np.empty((0,))

    det_cols = det_pred[:, :6]
    mask_coeffs = det_pred[:, 6:]

    scores = det_cols[:, 4]
    keep = scores > conf
    det_cols = det_cols[keep]
    mask_coeffs = mask_coeffs[keep]
    if len(det_cols) == 0:
        return np.empty((0,)), np.empty((0, 4)), np.empty((0,)), np.empty((0,))

    scores = det_cols[:, 4]
    labels = det_cols[:, 5].astype(np.int64)

    cx, cy, w, h = det_cols[:, 0], det_cols[:, 1], det_cols[:, 2], det_cols[:, 3]
    lb_boxes = np.stack([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], axis=1)

    mh, mw, c = protos.shape
    masks = mask_coeffs @ protos.reshape(-1, c).T  # (N, mh*mw)
    masks = masks.reshape(-1, mh, mw)

    # Proto is 1/4 of letterbox: convert letterbox-pixel boxes to proto-pixel.
    letterbox_h = mh * 4
    letterbox_w = mw * 4

    width_ratio = mw / letterbox_w
    height_ratio = mh / letterbox_h
    scaled_boxes = lb_boxes * np.array([width_ratio, height_ratio, width_ratio, height_ratio])
    x1, y1, x2, y2 = np.split(scaled_boxes[:, :, None], 4, axis=1)
    r = np.arange(mw, dtype=np.float32)[None, None, :]
    c_range = np.arange(mh, dtype=np.float32)[None, :, None]
    masks = masks * ((r >= x1) * (r < x2) * (c_range >= y1) * (c_range < y2))
    masks = (masks > 0).astype(np.uint8)

    lb_boxes_norm = lb_boxes / np.array([letterbox_w, letterbox_h, letterbox_w, letterbox_h])

    return masks, lb_boxes_norm, scores, labels
