# Changelog

## 0.3.0 — 2026-04-27

- **Segmentation**: Native MLX instance segmentation (`Segment26` head + `Proto26`) — inference, training, and COCO val2017 eval.
- **Segmentation**: COCO val2017 mask mAP within 0.3–0.4 pp of Ultralytics across all 5 sizes; box mAP within 0.1–0.4 pp.
- **Segmentation**: Mask post-processing now matches `process_mask_native` (upsample float masks to original resolution, then crop with pixel-accurate xyxy edges). Mask mAP@0.5:0.95 improves +3.1 → +6.8 pp across `n→x`; small-object AP for `n-seg` jumps `0.087 → 0.136`.
- **Segmentation**: Validator runs the mask head and reports mask mAP at proto resolution (matching Ultralytics `SegmentMetrics`); benchmark JSON now exposes explicit `mAP50_mask`, `mAP50-95_mask`, `mAP50_box`, `mAP50-95_box` keys.
- **Segmentation**: `evaluate_coco_seg_val.py` reports pycocotools (orig-resolution RLE) mask mAP as the primary metric, matching `model.val(save_json=True)`.
- **Segmentation**: Promoted `process_masks_at_proto` + `gt_instance_masks_from_overlap` into `yolo26mlx.utils.metrics` so trainer and standalone evaluator share one code path.
- **Segmentation**: Pure-MLX training loop is faster than both PyTorch MPS and CPU on COCO128-Seg across all 5 sizes.
- **Segmentation (mask-loss fix)**: Derive `imgsz_px` from `feats[0].shape * stride[0]` (was `proto.shape * stride[0]`, which doubled the value because `Proto26` upsamples 2× from P3 — boxes were half-scale in mask coords, silently degrading mask mAP).
- **Segmentation (Metal heap fix)**: `mx.clear_cache()` at every-epoch + every-8-batch sync points; `yolo26x-seg` drops from unstable ~140 s/epoch to stable 81.5 s/epoch and stops hanging with `kIOGPUCommandBufferCallbackError`.
- **Segmentation (MPS perf patch)**: `_mps_seg_perf_patch.py` rewrites the boolean-scatter `sem_masks[mask] = 0` to a multiplicative form, dodging [pytorch/pytorch#57515](https://github.com/pytorch/pytorch/issues/57515); MPS seg training is 6.2×–14.9× faster than before and 1.10×–2.80× faster than CPU.
- **Segmentation (MPS bench)**: Vectorized `v8SegmentationLoss.calculate_segmentation_loss` (batch-flat `index_select` + `bmm`); fixes an MPS backward-pass `index out of bounds` crash.
- **Trainer (mx.eval)**: Switched per-batch and per-step state syncs from `mx.eval(*flat_arrays)` to tree-form `mx.eval(tree)` (the MLX-recommended idiom — see [ml-explore/mlx#2914](https://github.com/ml-explore/mlx/discussions/2914)). Fixes user-reported `RuntimeError: [eval] Attempting to eval an array without a primitive` on mlx 0.31.x; verified on both 0.30.3 (no regression) and 0.31.2 (crash gone).
- **Trainer**: Added MLX `AdamW` (`yolo26mlx/optim/adamw.py`) with Ultralytics-style decoupled per-group weight decay; `_setup_optimizer` auto-branch picks `AdamW(lr=0.002*5/(4+nc))` for ≤10k-iter runs, `MuSGD(lr=0.01)` otherwise. Head `lr*3` boost is correctly scoped to MuSGD only.
- **Trainer**: `freeze_bn` flag (auto-on for ≤10k-iter runs) forces every `nn.BatchNorm` into eval mode after every `model.train()` so pretrained running stats don't drift.
- **Trainer**: `Trainer.__call__(lr=...)` now overrides `MuSGD.auto_lr` (was silently ignored).
- **Trainer**: Per-epoch log prints `(val skipped)` instead of `mAP50=0.0000` when `val=False`, so throughput-benchmark output stops looking like training collapsed.
- **Trainer**: Benchmark JSON `config.learning_rate` records the actual value used + a `learning_rate_source` field (was a hardcoded string regardless of `--lr`).
- **API**: `YOLO.train(...)` now forwards `val` and `verbose` kwargs to the trainer (previously accepted by `Trainer.__call__` but unreachable from the public API).
- **Converter (npz fix)**: `convert_pt_to_mlx` writes via `np.savez` instead of `mx.savez`. The MLX nanobind binding caps `**kwargs` at 1024; `yolo26{l,x}-seg.pt` carry ~1094 weights and previously failed conversion with `TypeError: nanobind::detail::nb_func_vectorcall(): too many (> 1024) keyword arguments`. Same `.npz` archive layout, `--verify` passes for all 5 sizes.
- **Packaging (.gitignore)**: Anchored the runtime-scratch patterns (`/datasets/`, `/models/`, `/results/`, `/images/`, `/runs/`) to repo root. The unanchored versions matched at any depth and silently excluded `src/yolo26mlx/cfg/datasets/*.yaml` and `src/yolo26mlx/cfg/models/26/*.yaml` from the repo, so a fresh clone hit `FileNotFoundError: Data config not found: coco128` on the README's quick-start despite `package_data` being correct.
- **Dependencies**: Pinned `mlx>=0.30.3,<0.31`. Fresh installs resolve to `mlx 0.31.2`, where `yolo26x-seg` training hangs with `kIOGPUCommandBufferCallbackError` within 2–5 epochs even with the per-epoch `mx.clear_cache()` fix; `mlx 0.30.3` runs all 10 epochs cleanly. The trainer-side `mx.eval` tree-form fix above also unblocks training on `0.31.x`, so the pin is now belt-and-suspenders.
- **Docs**: Added `GUIDE_SEGMENTATION.md` (setup, inference, COCO mAP, MLX/MPS/CPU training benchmarks, charts, per-component reference). README gains segmentation result tables and a 5-model × 3-backend training-time chart. Fixed `YOLO` class docstring example (`yolo26n.yaml` → `models/yolo26n.npz`).
- **Cleanup**: Removed orphan root-level `configs/coco128-seg.yaml` (unreferenced duplicate of `src/yolo26mlx/cfg/datasets/coco128-seg.yaml`). Kept `configs/coco.yaml` — referenced by README and 2 guides as the COCO val2017 reference.
- **Cleanup**: Removed `tests/deep_test_mlx_tracking.py` — 1.1k-line standalone MLX-0.30.3 tracking sanity script that pytest never collected (filename outside the `test_*.py` discovery pattern), unreachable from CI/docs, and superseded by `tests/test_tracking.py` + `tests/test_botsort.py` + `tests/test_mot_metrics.py`.
- **Cleanup**: `make clean` target removes build artifacts, Python/tool caches, runtime download dirs (`datasets/`, `models/`, `runs/`, `results/`, `images/`), and `.DS_Store` files.

## 0.2.0 — 2026-04-01

- **Tracking**: Batched Kalman filter updates (single `mx.linalg.inv` call per association stage)
- **Tracking**: Batch-precomputed coordinates reduce MLX graph dispatch overhead
- **Tracking**: MLX tracking now matches or exceeds PyTorch MPS speed
- **Packaging**: Moved `scipy` from core dependencies to `[tracking]` extra
- **Packaging**: Added clear error message when tracking dependencies are missing
- **Benchmarks**: Added tracking benchmark scripts and charts

## 0.1.0 — 2026-03-18

- Initial release: detection, training, COCO validation
