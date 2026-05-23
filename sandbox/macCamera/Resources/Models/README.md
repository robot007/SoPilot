# YOLO MLX Model

The face detector backend looks for a model in this order:

1. Environment override: `YOLO_MLX_MODEL=/path/to/model.npz`
2. `Resources/Models/yolo-face.npz` or `.safetensors` (face-trained)
3. `Resources/Models/yolo26n.npz` or `.safetensors` (COCO, person-class)
4. `<repo-root>/models/yolo26n.npz` (the repo's existing COCO weights)

If a COCO model is loaded, the Python worker detects class `0` ("person")
and derives an approximate face box from the upper portion of each person
bbox. Tune the approximation via:

```bash
YOLO_MLX_APPROX_FACE_FROM_PERSON=1   # default 1 (set 0 to use raw boxes)
YOLO_MLX_FACE_HEIGHT_RATIO=0.22      # face_h / person_h
YOLO_MLX_FACE_WIDTH_RATIO=0.55       # face_w / person_w upper bound
YOLO_MLX_FACE_ASPECT=0.78            # face_w / face_h cap
YOLO_MLX_FACE_CLASS_IDS=0            # which model classes count as faces
YOLO_MLX_CONF=0.35                   # detection confidence threshold
YOLO_MLX_IMAGE_SIZE=640              # inference image size
```

If neither the YOLO model nor the Python venv is available, the app falls
back to Apple Vision automatically.
