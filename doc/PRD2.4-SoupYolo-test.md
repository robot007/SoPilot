# SOUP Sleeve/Cuff Video Integration Test

## Summary
Add `sandbox/soup-engine/tests/integration/test_SOUP_sleeve.py` as an opt-in/direct-run integration test for `sandbox/BP-video/BP_correct.mp4`. It will extract 1 FPS frames, run `images/BP_sc_runs/train/bp_sc_yolo26n.npz`, convert YOLO detections into SOUP detections, evaluate the existing BP SOUP package, write overlays/logs, and report whether the BP task is finished.

## Key Changes
- Add a runnable unittest script that resolves paths from the repo root and imports both:
  - `sandbox/soup-engine/src` for `sopilot_rules`
  - `src` for `yolo26mlx`
- Use these fixed artifacts:
  - Video: `sandbox/BP-video/BP_correct.mp4`
  - Model: `images/BP_sc_runs/train/bp_sc_yolo26n.npz`
  - Class map: `images/BP_sc_dataset/classes.txt`
  - SOUP package: `sandbox/soup-engine/tests/fixtures/bp/bp_monitor.soup.json`
- Extract frames at 1 FPS into `sandbox/BP-video/BP-sc-test-raw`, clearing only generated `.jpg` files first.
- Run YOLO on each raw frame with `conf=0.1`, `imgsz=640`; map only class IDs `0..2` to `cuff`, `sleeve`, `upper_arm`, and ignore other class IDs.
- Save filtered YOLO overlays with correct BP labels into `sandbox/BP-video/BP-sc-test-yolo-overlay`.

## SOUP Evaluation Behavior
- Keep the full existing BP SOUP package.
- Add a deterministic synthetic `blood_pressure_monitor` detection at the first frame because the trained model does not include that class.
- Derive synthetic events from the video pass:
  - `measure_started`: earliest sampled timestamp where YOLO evidence satisfies cuff-on-upper-arm setup; if no setup-ready frame exists, use the last sampled timestamp so SOUP returns a real failed/needs_review decision.
  - `measurement_done`: last sampled timestamp.
- Convert each retained YOLO box into SOUP `Detection` records with stable IDs, frame ID, timestamp, tag, confidence, bbox, source `yolo_bp_sc`, and model/class metadata.
- Define `task_finished = result.status == "passed"`; the BP_correct integration test should assert this is true.

## Logging
- Write all text output to `sandbox/BP-video/test_log_SOUP_sleeve.log`.
- Include:
  - model path, video path, frame count, and class map
  - per-frame detections with timestamp, tag, confidence, bbox
  - synthetic event/proxy records
  - per-step SOUP lines containing state name, tag/rule context, SOUP decision, confidence, and message
  - final SOUP status and `TASK_FINISHED=true|false`

## Test Plan
- Direct run:
  - `cd /Users/zhensong/project/SoPilot/sandbox/soup-engine`
  - `../../.venv/bin/python tests/integration/test_SOUP_sleeve.py`
- Discovery-safe behavior:
  - When run by normal unittest discovery, skip unless `SOUP_RUN_VIDEO_INTEGRATION=1` is set.
  - In direct script mode, set that env flag internally so the test runs.
- Before importing `yolo26mlx`, run an MLX preflight subprocess; if MLX/Metal is unavailable, skip cleanly and log the skip reason instead of crashing the whole test process.
- Acceptance checks:
  - raw frame dir contains 54 extracted `.jpg` files for the 54-second video at 1 FPS
  - overlay dir contains one overlay per processed frame
  - log contains detections, SOUP step decisions, and final task status
  - `BP_correct.mp4` evaluates to `result.status == "passed"`

## Assumptions
- User-selected scope: full BP SOUP with synthetic monitor/events.
- User-selected cadence: 1 FPS.
- The trained `.npz` has an 80-class head, so the script must not trust `model.names`; `classes.txt` is the source of truth for BP labels.
