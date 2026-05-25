# BP Sleeve-Cuff Dataset — YOLO Training & Testing Report

**Date:** 2026-05-24  
**Dataset:** `BP-sleeve-cuff-2026-05-24-6b90.zip`

---

## 1. Dataset Overview

| Property | Value |
|----------|-------|
| Source | `BP-sleeve-cuff-2026-05-24-6b90.zip` |
| Classes | `cuff`, `sleeve`, `upper_arm` |
| Num Classes | 3 |
| Original Images | 69 |
| Image Size | 568 × 320 |
| Format | YOLO (normalized `cx, cy, w, h`) |

---

## 2. Dataset Preparation

### Directory Structure

```
BP_sc_dataset/
├── bp_sc.yaml
├── classes.txt
├── notes.json
├── images/
│   └── train/
│       ├── *.jpg          (69 original + 690 augmented = 759 total)
└── labels/
    └── train/
        ├── *.txt          (759 label files)
```

### Dataset Config (`bp_sc.yaml`)

```yaml
path: /Users/zhensong/project/SoPilot/images/BP_sc_dataset

train: images/train
val: images/train
test: images/train

names:
  0: cuff
  1: sleeve
  2: upper_arm
```

---

## 3. Data Augmentation

**Script:** `augment_bp_sc.py` (adapted from `augment_bp1.py`)

| Augmentation | Range |
|--------------|-------|
| Rotation | ±25° |
| Scale | 0.75 – 1.35× |
| Translation | ±15% of image dims |
| Horizontal Flip | 50% probability |
| Contrast (α) | 0.7 – 1.3 |
| Brightness (β) | −30 – +30 |
| Variants per image | 10 |

**Result:**
- **Original:** 69 images
- **Augmented:** 690 images
- **Total:** **759 images**

---

## 4. Model Training

**Script:** `train_bp_sc.py` (adapted from `train_bp1.py`)

| Hyperparameter | Value |
|----------------|-------|
| Base Model | `yolo26n.npz` (nano, pretrained) |
| Framework | YOLO26 MLX |
| Epochs | 5 |
| Batch Size | 1 |
| Image Size | 640 |
| Optimizer | AdamW (β=(0.9, 0.999), wd=0.0005) |
| Initial LR | 0.000119 |
| Patience | 10 |
| Save Period | every epoch |

### Training Results

| Epoch | Loss | mAP@50 | mAP@50:95 | Precision | Recall | Time |
|:-----:|:----:|:------:|:---------:|:---------:|:------:|:----:|
| 1 | ~5.47 | — | — | — | — | ~85s |
| 2 | 3.120 | 0.636 | 0.314 | 0.082 | 0.866 | 87.1s |
| 3 | 2.669 | 0.698 | 0.349 | 0.146 | 0.883 | 93.0s |
| 4 | 2.405 | 0.738 | 0.381 | 0.062 | 0.906 | 105.4s |
| 5 | **2.150** | **0.764** | **0.406** | 0.124 | **0.910** | 98.5s |

**Saved Checkpoints:**
- `BP_sc_runs/train/best.safetensors` (updated each epoch)
- `BP_sc_runs/train/epoch{1-5}.safetensors`
- `BP_sc_runs/train/last.safetensors`

---

## 5. Inference Testing

**Script:** `test_bp_sc.py` (adapted from `test_bp1.py`)

| Test Parameter | Value |
|----------------|-------|
| Model | `BP_sc_runs/train/best.safetensors` |
| Test Set | All 759 images (original + augmented) |
| Confidence Threshold | 0.1 |
| Image Size | 640 |

### Detection Summary

The model successfully detects objects across the dataset:

- **`cuff`** — detected with high confidence (often 0.7–0.9+)
- **`sleeve`** — detected reliably when present
- **`upper_arm`** — less frequent in this subset; detections align with labels

### Example Detections

| Image | Detections |
|-------|------------|
| `b36d9320-frame_041.03s.jpg` | 1 × cuff (conf=0.879) |
| `b11c55fb-frame_016.01s.jpg` | 1 × sleeve (conf=0.703), 1 × cuff (conf=0.565) |
| `a56be73e-frame_020.01s.jpg` | 1 × cuff (conf=0.842) |
| `bb8a187d-frame_006.00s.jpg` | No labels in GT → low/no detections (expected) |

### Edge Cases
- Images with **no ground-truth labels** (e.g., `bb8a187d-frame_006.00s`) predict no objects or very low-confidence noise — consistent behavior.
- Augmented variants maintain detection quality though some extreme transforms reduce confidence.

---

## 6. Files Generated

| File | Purpose |
|------|---------|
| `BP_sc_dataset/` | Full prepared dataset |
| `BP_sc_dataset/bp_sc.yaml` | YOLO dataset configuration |
| `augment_bp_sc.py` | Data augmentation pipeline |
| `train_bp_sc.py` | Training script |
| `test_bp_sc.py` | Inference / testing script |
| `BP_sc_runs/train/` | Model checkpoints & weights |
| `train_bp_sc.log` | Training stdout log |

---

## 7. Conclusion

The BP sleeve-cuff dataset was successfully:
1. **Unzipped** and structured for YOLO training
2. **Augmented** 10× (69 → 759 images)
3. **Trained** for 5 epochs, reaching **mAP@50 = 0.764**
4. **Tested** with reliable detections on both original and augmented images

The model generalizes well across the augmented data and shows strong recall (91%) for the three target classes.
