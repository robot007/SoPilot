# Sandbox/macCamera
## VLM
* src/yolo26mlx/vlm/cli.py is the Python command-line interface that the Mac app uses to talk to the local VLM system.
```
vlm-model-manager list
vlm-model-manager download fastvlm_0_5b
vlm-model-manager activate fastvlm_0_5b
vlm-model-manager chat fastvlm_0_5b --frame-file frame1.jpg --prompt "What do you see?"
```
Main responsibilities:
* Uses VLMModelManager to list, download, activate, delete, and inspect local VLM models.
* Accepts chat inputs from Swift: prompt text, recent video frame files, optional system prompt.
* Calls chat.py, where the actual FastVLM inference happens.
* Writes JSON output so Swift can parse success/error responses reliably.

## Face recogniztion model
* Small face size with Yolo model
Root Cause
The app code is effectively identical between the two worktrees. The behavior difference comes from runtime files, not the Swift overlay math.
In this worktree, /Users/zhensong/project/SoPilot/models/yolo26n.npz exists. In /Users/zhensong/.codex/worktrees/9692/SoPilot, there is no models/ directory. Because of that:
Current worktree finds models/yolo26n.npz via YoloMLXWorker.swift (line 152).
9692 fails to find a YOLO model, so YoloMLXWorker.makeDefault() returns nil.
Then FaceDetector.swift (line 50) falls back to Apple Vision face detection, whose boxes look correct.
The current worktree is not using a real face model. It is using generic COCO yolo26n.npz, where class 0 is person, then the worker approximates a face box from the top of the person box. That heuristic is here: yolo_mlx_face_worker.py (line 79). The default face height is only 0.22 * person_h at line 154 (line 154), which explains why the green box is smaller than the actual face.

## Data flow

## AppConfig.
'static sendYoloOverlayVLM=true;'  in appConfig.swift, send Yolo overlayed image to VLM