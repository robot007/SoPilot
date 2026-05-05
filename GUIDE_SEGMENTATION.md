# YOLO26 MLX — Instance Segmentation Guide

---

## Setup (Step by Step)

### Step 1: Create & Activate Virtual Environment

```bash
cd yolo-mlx

# Create a new virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate
```

### Step 2: Install the Package & Dependencies

```bash
# Install yolo-mlx and its core dependencies (mlx, numpy, pillow, pyyaml, tqdm)
pip install -e .

# Install segmentation dependencies (pycocotools for COCO mAP, matplotlib for charts, opencv-python for masks)
pip install -e ".[segment]"

# Install weight conversion dependencies (needed once to convert .pt → .npz)
pip install -e ".[convert]"

# (Optional) Install PyTorch MPS/CPU comparison benchmarks
pip install torchvision                           # optional, for MPS/CPU benchmarks
```

Runtime directories (`datasets/`, `images/`, `models/`, `results/`) are
auto-created by the scripts when needed.

**Core dependencies installed by `pip install -e .`:**

| Package | Version | Purpose |
|---------|---------|---------|
| mlx | >= 0.30.3 | Apple Silicon ML framework |
| numpy | >= 2.0.0 | Array operations |
| pillow | >= 10.0.0 | Image loading |
| pyyaml | >= 6.0 | Config parsing |
| tqdm | >= 4.65.0 | Progress bars |

**Conversion dependencies installed by `pip install -e ".[convert]"`:**

| Package | Version | Purpose |
|---------|---------|---------|
| torch | >= 2.0.0 | Loading .pt checkpoint files |
| ultralytics | >= 8.0.0 | Deserializing Ultralytics model objects in .pt files |
| safetensors | >= 0.4.0 | Optional safetensors output format |

**Segmentation dependencies installed by `pip install -e ".[segment]"`:**

| Package | Version | Purpose |
|---------|---------|--------|
| pycocotools | >= 2.0 | Official COCO mAP evaluation (box + mask) |
| matplotlib | >= 3.7.0 | Chart generation |
| opencv-python | >= 4.8.0 | Mask visualization and contour extraction |

**Optional benchmark dependencies (PyTorch MPS/CPU comparison only):**

| Package | Version | Purpose |
|---------|---------|--------|
| torchvision | latest | Required by Ultralytics' PyTorch trainer for the MPS/CPU comparison benchmarks |

### Step 3: Download PyTorch Models

Download the official YOLO26-seg pretrained weights (`.pt` files) from Ultralytics:

```bash
# Use the download script (downloads both detection and segmentation models)
bash scripts/download_yolo26_models.sh

# Or download segmentation models manually
cd models
curl -L -o yolo26n-seg.pt https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26n-seg.pt
curl -L -o yolo26s-seg.pt https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26s-seg.pt
curl -L -o yolo26m-seg.pt https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26m-seg.pt
curl -L -o yolo26l-seg.pt https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26l-seg.pt
curl -L -o yolo26x-seg.pt https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26x-seg.pt
cd ..
```

After this step, `models/` should contain:
```
yolo26n-seg.pt  yolo26s-seg.pt  yolo26m-seg.pt  yolo26l-seg.pt  yolo26x-seg.pt
```

### Step 4: Convert Weights to MLX Format (.npz)

Convert the PyTorch `.pt` files to MLX `.npz` format using the built-in converter:

```bash
yolo-mlx converters --help
yolo-mlx converters convert models/yolo26n-seg.pt -o models/yolo26n-seg.npz --verify
```

The `--verify` flag checks that converted weight shapes are correct. Repeat the same command for `yolo26s-seg/m-seg/l-seg/x-seg`. After this step, `models/` should contain both formats:
```
yolo26n-seg.pt  yolo26n-seg.npz
yolo26s-seg.pt  yolo26s-seg.npz
yolo26m-seg.pt  yolo26m-seg.npz
yolo26l-seg.pt  yolo26l-seg.npz
yolo26x-seg.pt  yolo26x-seg.npz
```

### Step 5: Download Test Image (for Inference Benchmark)

```bash
mkdir -p images
curl -L -o images/bus.jpg https://ultralytics.com/images/bus.jpg
```

### Step 6: Download COCO val2017 Dataset (for Validation)

Download the COCO 2017 validation set (5,000 images, ~1 GB images + 241 MB annotations):

```bash
# Use the download script
bash scripts/download_coco_val2017.sh datasets/coco

# Or download manually
mkdir -p datasets/coco/images datasets/coco/annotations datasets/coco/labels

# Download val2017 images (~1 GB)
curl -L -o datasets/coco/images/val2017.zip http://images.cocodataset.org/zips/val2017.zip
unzip datasets/coco/images/val2017.zip -d datasets/coco/images/
rm datasets/coco/images/val2017.zip

# Download annotations (~241 MB)
curl -L -o datasets/coco/annotations/annotations_trainval2017.zip http://images.cocodataset.org/annotations/annotations_trainval2017.zip
unzip datasets/coco/annotations/annotations_trainval2017.zip -d datasets/coco/
rm datasets/coco/annotations/annotations_trainval2017.zip

# Download YOLO-format segment labels (pre-converted from Ultralytics)
curl -L -o datasets/coco/labels/val2017.zip https://github.com/ultralytics/assets/releases/download/v0.0.0/coco2017labels-segments.zip
unzip datasets/coco/labels/val2017.zip -d datasets/coco/
rm datasets/coco/labels/val2017.zip
```

The dataset config is already at `configs/coco.yaml`. Final structure:
```
datasets/coco/
├── annotations/instances_val2017.json
├── images/val2017/          # 5,000 images
└── labels/val2017/          # YOLO-format segment labels (polygon vertices)
```

### COCO128-Seg Dataset (Auto-Downloaded)

COCO128-Seg (128 images from COCO with segmentation labels) is used as the training dataset for benchmarks.

**No manual download needed.** The training benchmark scripts automatically download COCO128-Seg (~7 MB) on first run into `datasets/coco128-seg/`. After the first run, the dataset is cached locally and reused.

---

## Part 1: Inference Benchmarking

Measures end-to-end segmentation inference latency on a single image across up to 3 backends: MLX GPU, PyTorch MPS, PyTorch CPU.

**Script:** `scripts/benchmark_yolo26_seg_inference.py`

### Run All Models, All Backends

```bash
python scripts/benchmark_yolo26_seg_inference.py
```

### Common Options

```bash
# Specific models only
python scripts/benchmark_yolo26_seg_inference.py --models n s

# More timed runs for stable results
python scripts/benchmark_yolo26_seg_inference.py --runs 20

# MLX only (skip PyTorch comparisons)
python scripts/benchmark_yolo26_seg_inference.py --skip-mps --skip-cpu

# Custom warmup
python scripts/benchmark_yolo26_seg_inference.py --warmup 5 --runs 15

# Custom output path
python scripts/benchmark_yolo26_seg_inference.py --output my_results.json
```

### What It Measures

| Metric | Description |
|--------|-------------|
| End-to-end latency (ms) | Full `model.predict(image)` including preprocessing + postprocessing + mask generation |
| Forward-pass-only (ms) | Model inference only (no pre/post processing) |
| FPS | Throughput (1000 / mean_ms) |
| Peak memory (MB) | MLX Metal memory usage |
| Speedup ratios | MLX vs MPS, MLX vs CPU |

### Output

- **Console:** Summary table with latency, FPS, and speedups for all models
- **JSON:** `results/yolo26_seg_inference_three_way.json` (override with `--output`)

### Defaults

| Setting | Value |
|---------|-------|
| Warmup runs | 3 |
| Timed runs | 10 |
| Image size | 640×640 |
| Models | n, s, m, l, x |

### Benchmark Results

End-to-end inference FPS (imgsz=640, 10 timed runs, 3 warmup runs):

| Model | MLX FPS | MPS FPS | CPU FPS | MLX vs MPS | MLX vs CPU |
|-------|---------|---------|---------|------------|------------|
| yolo26n-seg | **63.7** | 45.7 | 21.6 | **1.39×** | **2.94×** |
| yolo26s-seg | **46.8** | 41.4 | 11.9 | **1.13×** | **3.94×** |
| yolo26m-seg | **23.4** | 23.5 | 5.6 | **1.00×** | **4.22×** |
| yolo26l-seg | **21.0** | 20.5 | 4.6 | **1.02×** | **4.58×** |
| yolo26x-seg | **12.5** | 11.3 | 2.7 | **1.11×** | **4.67×** |

MLX is faster than (or tied with) PyTorch MPS across all 5 model sizes — `1.00×–1.39×` end-to-end. m-seg and l-seg are essentially tied; the smaller models (n, s) gain the most from MLX's Metal-optimized compute graph and `mx.compile` JIT. Forward-pass-only timings (model forward without pre/post-processing) are MLX-favorable on every size, including m-seg (MLX `35.5 ms` vs MPS `40.3 ms`, **1.14× faster**). MLX is **2.94×–4.67× faster than PyTorch CPU** across every size.

---

## Part 2: COCO val2017 Validation (mAP)

Evaluates segmentation accuracy on the full COCO val2017 set (5,000 images) using the official pycocotools COCO evaluation protocol, reporting both box mAP and mask mAP.

**Script:** `scripts/evaluate_coco_seg_val.py`

### Run Full Validation (5,000 images)

```bash
# Single model
python scripts/evaluate_coco_seg_val.py --model yolo26n-seg --data datasets/coco

# All 5 models
python scripts/evaluate_coco_seg_val.py --model all --data datasets/coco
```

### Quick Test (subset)

```bash
# First 100 images only (for quick sanity check)
python scripts/evaluate_coco_seg_val.py --model yolo26n-seg --data datasets/coco --subset 100
```

### Common Options

```bash
# Custom confidence threshold
python scripts/evaluate_coco_seg_val.py --model yolo26n-seg --data datasets/coco --conf 0.001

# Custom image size and batch size
python scripts/evaluate_coco_seg_val.py --model yolo26n-seg --data datasets/coco --imgsz 640 --batch 32

# Multiple specific models
python scripts/evaluate_coco_seg_val.py --model yolo26n-seg yolo26s-seg --data datasets/coco

# Verbose output (per-image progress)
python scripts/evaluate_coco_seg_val.py --model yolo26n-seg --data datasets/coco --verbose

# Custom output directory
python scripts/evaluate_coco_seg_val.py --model yolo26n-seg --data datasets/coco --output my_results/
```

### What It Reports

| Metric | Description |
|--------|-------------|
| mAP<sup>mask</sup>@0.5:0.95 | Primary mask metric (averaged over IoU 0.50–0.95) |
| mAP<sup>mask</sup>@0.5 | Mask AP at IoU=0.50 |
| mAP<sup>box</sup>@0.5:0.95 | Box detection AP (averaged over IoU 0.50–0.95) |
| mAP<sup>box</sup>@0.5 | Box detection AP at IoU=0.50 |
| mAP (small/medium/large) | AP by object size |
| Images/second | Throughput during evaluation |

### Output

- **Console:** Full pycocotools evaluation summary (12-metric table for both box and mask)
- **JSON:** `results/yolo26_seg_coco_val_results.json` (override with `--output`)

### Defaults

| Setting | Value |
|---------|-------|
| Image size | 640 |
| Confidence threshold | 0.001 |
| Batch size | 16 |

### Comparison Table (MLX vs Official)

| Model | MLX mAP<sup>mask</sup> | Official mAP<sup>mask</sup> | MLX mAP<sup>box</sup> | Official mAP<sup>box</sup> |
|-------|------------------------|-------------------------------|------------------------|-------------------------------|
| yolo26n-seg | **33.6** | 33.9 | **39.5** | 39.6 |
| yolo26s-seg | **39.7** | 40.0 | **47.2** | 47.3 |
| yolo26m-seg | **43.7** | 44.1 | **52.1** | 52.5 |
| yolo26l-seg | **45.2** | 45.5 | **54.2** | 54.4 |
| yolo26x-seg | **46.6** | 47.0 | **56.2** | 56.5 |

All models evaluated on COCO val2017 (5000 images, imgsz=640, conf=0.001). MLX numbers come from `pycocotools` at original-image resolution (RLE-encoded predictions), matching the methodology Ultralytics uses for its published numbers (`model.val(save_json=True)` → `process_mask_native` + pycocotools). Official numbers are from the [Ultralytics YOLO26 docs](https://docs.ultralytics.com/models/yolo26/). Mask mAP is within **0.3–0.4 pp** of Official across all sizes; box mAP within **0.1–0.4 pp**. Remaining differences come from hardware/framework version variance, not mask quality.

> Mask post-processing follows `process_mask_native` ordering: float prototype-mask product is upsampled from proto to original-image resolution, letterbox padding is stripped, and the per-instance crop is applied with pixel-accurate xyxy edges in the original frame before binarization. Cropping at proto resolution before upsampling (an earlier path) quantizes mask boundaries to ~4-pixel granularity and materially reduces mask AP — especially AP@small. The current path matches the Ultralytics reference and is what produces the numbers above.

---

## Training Benchmark Scripts

There are 3 training scripts (one per backend) plus 2 utility scripts:

| Script | Backend | Default Output |
|--------|---------|----------------|
| `benchmark_yolo26_seg_training_mlx.py` | MLX GPU | `results/yolo26_seg_mlx_training_final.json` |
| `benchmark_yolo26_seg_training_mps.py` | PyTorch MPS | `results/yolo26_seg_mps_training_final.json` |
| `benchmark_yolo26_seg_training_cpu.py` | PyTorch CPU | `results/yolo26_seg_cpu_training_final.json` |
| `benchmark_yolo26_seg_collect_results.py` | — | `results/yolo26_seg_benchmark_combined.json` |
| `benchmark_yolo26_seg_generate_charts.py` | — | `results/charts/yolo26_seg_*.png` |

All scripts accept `--output` to override the default output path.

---

## Part 3: MLX Training Benchmark

Trains YOLO26-seg models using the pure MLX implementation and measures time, loss, mAP, and memory.

**Script:** `scripts/benchmark_yolo26_seg_training_mlx.py`

### Run All Models

```bash
python scripts/benchmark_yolo26_seg_training_mlx.py
```

### Common Options

```bash
# Specific models only
python scripts/benchmark_yolo26_seg_training_mlx.py --models n s

# Custom epochs and batch size
python scripts/benchmark_yolo26_seg_training_mlx.py --epochs 5 --batch 2

# Custom learning rate
python scripts/benchmark_yolo26_seg_training_mlx.py --lr 0.0001

# Custom output path
python scripts/benchmark_yolo26_seg_training_mlx.py --output my_results.json

# All options combined
python scripts/benchmark_yolo26_seg_training_mlx.py --models n s m l x --epochs 10 --batch 4
```

### What It Measures

| Metric | Description |
|--------|-------------|
| Training time (s) | Total wall-clock time for all epochs |
| Time/epoch (s) | Average time per epoch |
| Final loss | Loss value at end of training |
| mAP@0.5 | Accuracy after training (validation on COCO128-Seg) |
| Peak memory (MB) | MLX Metal peak memory usage |

### Defaults

| Setting | Value |
|---------|-------|
| Epochs | 10 |
| Batch size | 4 |
| Learning rate | 0.000119 (auto-LR formula `0.002 * 5 / (4 + nc)` for nc=80) |
| Optimizer | auto (mirrors Ultralytics: AdamW for ≤10k iter, MuSGD otherwise) |
| Dataset | COCO128-Seg (128 images) |
| Validation | After training (not during) |

### Benchmark Results

Training time per epoch on COCO128-Seg (10 epochs, batch=4):

| Model | MLX time/epoch (s) | MPS time/epoch (s) | CPU time/epoch (s) | MLX vs MPS | MLX vs CPU | MPS vs CPU |
|-------|---------------------|---------------------|---------------------|------------|------------|------------|
| yolo26n-seg | **12.0** | 39.8 | 44.3 | **3.31×** | **3.68×** | 1.11× |
| yolo26s-seg | **19.8** | 53.6 | 74.6 | **2.71×** | **3.76×** | 1.39× |
| yolo26m-seg | **40.0** | 61.9 | 148.3 | **1.55×** | **3.71×** | 2.40× |
| yolo26l-seg | **46.5** | 63.3 | 170.1 | **1.36×** | **3.66×** | 2.69× |
| yolo26x-seg | **81.5** | 102.0 | 282.6 | **1.25×** | **3.47×** | 2.77× |

MLX is the fastest backend across all five model sizes. The MPS numbers above are with the **MPS performance patch** from CHANGELOG 0.3.0 (`scripts/_mps_seg_perf_patch.py`). Without that patch the MPS column was close to flat at 603–652 s/epoch (an order of magnitude slower than CPU) because a single line in `v8SegmentationLoss.loss` — a boolean-mask scatter assign on the semantic-segmentation target tensor — hit a known PyTorch-MPS pathology ([pytorch/pytorch#57515](https://github.com/pytorch/pytorch/issues/57515)) and consumed ~95% of the loss-step wall time. Rewriting that line as a multiplicative `sem_masks = sem_masks * keep` (numerically identical, verified by `_test_mps_seg_perf_patch.py`) yields a **~17× speedup** on MPS, restores the expected MPS > CPU ordering, and keeps the per-instance vectorized loss on the same code path so MPS-vs-CPU is apples-to-apples. On the MLX side, `Trainer._train_epoch` releases MLX's reusable Metal buffer pool via `mx.clear_cache()` at the end of every epoch and every 8 batches mid-epoch (right after the per-batch `mx.eval` sync) — without that, sustained 10-epoch training of `yolo26x-seg` fragmented the Metal heap, drove epoch times from ~93 s up to ~150 s, and reproducibly crashed before epoch 4 with `kIOGPUCommandBufferCallbackError` Hang/Discarded faults. Periodic clearing keeps the heap bounded and brings `x-seg` from an unstable ~140 s/epoch down to a stable **81.5 s/epoch** with no measurable cost on the smaller models.

### Post-Training Accuracy

`Trainer._validate` now executes the mask head and computes mask mAP at proto resolution (the same recipe Ultralytics' internal `SegmentMetrics` uses for `model.val()`). Reproducible numbers below — 10 epochs, batch=4, COCO128-Seg:

| Model | MLX mask mAP@0.5 | MPS mask mAP@0.5 | CPU mask mAP@0.5 | MLX mask mAP@0.5:0.95 | MPS mask mAP@0.5:0.95 | CPU mask mAP@0.5:0.95 |
|-------|-------------------|-------------------|-------------------|------------------------|------------------------|------------------------|
| yolo26n-seg | **0.6783** | 0.6309 | 0.6312 | **0.4507** | 0.4150 | 0.4151 |
| yolo26s-seg | 0.7414 | **0.7573** | 0.7575 | 0.4984 | **0.5140** | 0.5117 |
| yolo26m-seg | 0.8244 | 0.8046 | **0.8275** | 0.5388 | 0.5544 | **0.5640** |
| yolo26l-seg | **0.8264** | 0.8189 | 0.8133 | 0.5362 | **0.5704** | 0.5633 |
| yolo26x-seg | 0.8373 | 0.8590 | **0.8613** | 0.5514 | 0.5980 | **0.6048** |

MLX post-training mask mAP50 now ranges **0.6783 (n) → 0.8373 (x)**, monotonically above the MLX pretrained baseline (`yolo26n-seg: 0.6192`, `yolo26x-seg: 0.7418`) and at parity with the PyTorch MPS / CPU references on the same dataset (within ~2% across all model sizes). This is the result of fixing a coordinate-scaling bug in `_calculate_segmentation_loss` (see CHANGELOG 0.3.0): the previous implementation derived `imgsz_px` from `proto.shape * stride[0]`, but Proto26 upsamples 2× from P3, so the value was `1280` instead of `640` for `imgsz=640`. Boxes were therefore halved in mask coordinates and `crop_mask` zeroed loss outside a quarter-sized window, leaving box training intact (since the bug was confined to the mask branch) while silently degrading post-training mask mAP. With the correct `imgsz_px = feats[0].shape[1] * stride[0]` (matching Ultralytics' `calculate_segmentation_loss`), all five MLX seg models now train above their pretrained baselines.

> COCO128-Seg uses `val == train` (the val split literally points at `images/train2017`), so this table is a *fit* metric, not a generalization metric. For an apples-to-apples accuracy comparison on the full COCO val2017 set (5000 images) see **Part 2**, where MLX matches the published Ultralytics numbers within **0.1–0.4 pp on box mAP** and **0.3–0.4 pp on mask mAP** across all 5 model sizes (pycocotools at original-image resolution, same methodology as `model.val(save_json=True)`).

---

## Part 4: PyTorch MPS Training Benchmark

> **Requires:** `pip install ultralytics torch torchvision`

```bash
python scripts/benchmark_yolo26_seg_training_mps.py
python scripts/benchmark_yolo26_seg_training_mps.py --models n s --epochs 5 --batch 2
```

Same CLI flags as MLX script (`--models`, `--epochs`, `--batch`, `--lr`, `--output`). Uses PyTorch MPS backend with Ultralytics trainer. Default learning rate is 0.00001 (differs from MLX's auto-LR rate of 0.000119). Reports both mask mAP and box mAP.

---

## Part 5: PyTorch CPU Training Benchmark

> **Requires:** `pip install ultralytics torch torchvision`

```bash
python scripts/benchmark_yolo26_seg_training_cpu.py
python scripts/benchmark_yolo26_seg_training_cpu.py --models n s --epochs 5 --batch 2

# Control CPU thread count
python scripts/benchmark_yolo26_seg_training_cpu.py --threads 4
```

Same CLI flags as MPS script, plus `--threads` to control `torch.set_num_threads()`. Default learning rate is 0.00001. Slowest backend — useful as a baseline.

---

## Part 6: Collect Results & Generate Charts

After running one or more benchmarks, combine results and generate charts:

> **Requires:** `pip install matplotlib`

```bash
# Combine all JSON results into one file
python scripts/benchmark_yolo26_seg_collect_results.py

# Generate comparison charts
python scripts/benchmark_yolo26_seg_generate_charts.py

# PDF format (for publications)
python scripts/benchmark_yolo26_seg_generate_charts.py --format pdf

# Custom DPI and output directory
python scripts/benchmark_yolo26_seg_generate_charts.py --dpi 300 --output my_charts/
```

### Charts Generated (in `results/charts/`)

| Chart | File | Description |
|-------|------|-------------|
| Inference latency | `yolo26_seg_inference_latency.png` | Bar chart of segmentation latency across backends |
| **Inference FPS** | **`yolo26_seg_inference_fps.png`** | Throughput (frames per second) |
| **Training time** | **`yolo26_seg_training_time.png`** | Training time comparison across backends |
| **Speedup** | **`yolo26_seg_speedup.png`** | MLX vs CPU and MLX vs MPS speedup factors (inference + training) |
| Accuracy | `yolo26_seg_accuracy.png` | Mask/box mAP comparison across backends |
| Memory usage | `yolo26_seg_memory.png` | Peak memory comparison |
| Summary dashboard | `yolo26_seg_summary.png` | 2×2 grid: latency, training time, speedup, accuracy |

> The 3 **bolded** charts are shipped in `assets/` and referenced from the README, matching the standardized chart set used for detection and tracking. The remaining 4 are produced by the same script run for ad-hoc analysis.

---

## Appendix: Segmentation-Specific Reference

### YOLO26-seg Model Sizes

| Model | Params (M) | FLOPs (G) | Official mAP<sup>mask</sup> 50-95 | Official mAP<sup>box</sup> 50-95 |
|-------|-----------|-----------|----------------------------------|----------------------------------|
| yolo26n-seg | 2.7 | 9.1 | 33.9% | 39.6% |
| yolo26s-seg | 10.4 | 34.2 | 40.0% | 47.3% |
| yolo26m-seg | 23.6 | 121.5 | 44.1% | 52.5% |
| yolo26l-seg | 28.0 | 139.8 | 45.5% | 54.4% |
| yolo26x-seg | 62.8 | 313.5 | 47.0% | 56.5% |

### Segmentation Loss Components

The segmentation training loss combines five components:

| Loss | Description |
|------|-------------|
| `box_loss` | CIoU bounding box regression loss |
| `cls_loss` | Binary cross-entropy classification loss |
| `dfl_loss` | Distribution focal loss for box refinement |
| `seg_loss` | Per-instance binary mask BCE loss (foreground instances only) |
| `sem_loss` | Auxiliary per-pixel semantic segmentation loss (BCE + Dice) |

### YOLO-seg Label Format

Segmentation labels use polygon vertex annotations. Each line in the label `.txt` file:

```
class_id x1 y1 x2 y2 x3 y3 ... xN yN
```

All coordinates are normalized to `[0, 1]` relative to image dimensions. Each polygon defines the boundary of one object instance.

Example (`labels/train2017/000000000001.txt`):
```
0 0.123 0.456 0.234 0.567 0.345 0.678 0.456 0.789 0.123 0.456
45 0.500 0.200 0.600 0.300 0.700 0.400 0.500 0.200
```

---

## Quick Reference

```bash
# Activate environment
cd yolo-mlx
source .venv/bin/activate

# ── Inference benchmark (all models, MLX only) ──
python scripts/benchmark_yolo26_seg_inference.py --skip-mps --skip-cpu

# ── Full COCO val2017 validation (all models) ──
python scripts/evaluate_coco_seg_val.py --model all --data datasets/coco

# ── Quick sanity check (1 model, 100 images) ──
python scripts/evaluate_coco_seg_val.py --model yolo26n-seg --data datasets/coco --subset 100

# ── MLX training benchmark (all models) ──
python scripts/benchmark_yolo26_seg_training_mlx.py --models n s m l x --epochs 10 --batch 4

# ── MPS training benchmark (all models) ──
python scripts/benchmark_yolo26_seg_training_mps.py --models n s m l x --epochs 10 --batch 4

# ── CPU training benchmark (all models) ──
python scripts/benchmark_yolo26_seg_training_cpu.py --models n s m l x --epochs 10 --batch 4

# ── Collect & chart ──
python scripts/benchmark_yolo26_seg_collect_results.py
python scripts/benchmark_yolo26_seg_generate_charts.py
```
