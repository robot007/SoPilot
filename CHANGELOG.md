# Changelog

## 0.3.0 — 2026-05-05

- **Segmentation**: Native MLX instance segmentation (`Segment26` head + `Proto26`) — inference, training, and COCO val2017 mAP eval
- **Segmentation**: Mask mAP within 0.3–0.4 pp of Ultralytics across all 5 sizes; MLX seg training fastest on every size (1.25×–3.31× vs MPS)
- **Trainer**: Added MLX `AdamW` optimizer with `optimizer="auto"` (AdamW for short fine-tunes, MuSGD otherwise)
- **Trainer**: Tree-form `mx.eval(tree)` syncs fix upstream `[eval] Attempting to eval an array without a primitive` crash on mlx 0.31.x
- **Packaging**: Pinned `mlx>=0.30.3,<0.31`; anchored `.gitignore` patterns to repo root
- **Benchmarks**: Added segmentation inference, COCO val mAP, and training benchmark scripts and charts
- **Docs**: Added `GUIDE_SEGMENTATION.md` and segmentation Quick Start sections

## 0.2.0 — 2026-04-01

- **Tracking**: Batched Kalman filter updates (single `mx.linalg.inv` call per association stage)
- **Tracking**: Batch-precomputed coordinates reduce MLX graph dispatch overhead
- **Tracking**: MLX tracking now matches or exceeds PyTorch MPS speed
- **Packaging**: Moved `scipy` from core dependencies to `[tracking]` extra
- **Packaging**: Added clear error message when tracking dependencies are missing
- **Benchmarks**: Added tracking benchmark scripts and charts

## 0.1.0 — 2026-03-18

- Initial release: detection, training, COCO validation
