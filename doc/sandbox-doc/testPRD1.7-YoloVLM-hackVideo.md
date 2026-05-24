# FastVLM + YOLO SOUP Cross-Validation Plan

## Summary
Add a BP hack video integration test that runs YOLO on `sandbox/BP-video/BP-hack.mp4`, calls FastVLM once at the end using the last 6 YOLO overlay frames, and sends the VLM answer into the SOUP Rule Engine through a new VLM-aware rule type. The expected outcome is `TASK_FINISHED=false`; the test passes when the hacked workflow is rejected.

## Key Changes
- Add a minimal SOUP rule type, e.g. `vlm_answer`, so a `.soup.json` rule can define:
  - `question`: `Has the person put the cuff on upper arm`
  - expected normalized answer: `yes`
  - event source/type carrying FastVLM’s final answer
  - failure message for `no` or `unsure`
- Add a new BP hack SOUP fixture, e.g. `sandbox/soup-engine/tests/fixtures/bp/bp_hack_vlm_crosscheck.soup.json`, using the existing BP measurement flow plus the VLM rule as the final validation gate.
- Add `sandbox/soup-engine/tests/integration/test_SOUP_bp_hack_vlm.py`:
  - extract 1 FPS frames from `BP-hack.mp4` into `sandbox/BP-video/BP-hack-raw`
  - run `images/BP_sc_runs/train/bp_sc_yolo26n.npz` on each frame
  - write filtered cuff/sleeve overlays into `sandbox/BP-video/BP-hack-yolo-overlay`
  - call FastVLM once after video processing, following `sandbox/macCamera`’s CLI pattern
  - send YOLO detections plus one VLM answer event into SOUP
  - write all output to `sandbox/BP-video/BP-hack.log`

## VLM Behavior
- Use FastVLM model id `fastvlm_0_5b`.
- Send the last 6 YOLO overlay frames as a time-ordered visual context.
- Prompt:
  `Has the person put the cuff on upper arm? Answer exactly one token: YES, NO, or UNSURE.`
- Normalize answer:
  - `YES` -> `yes`
  - `NO` -> `no`
  - anything else -> `unsure`
- Create one SOUP event at the final sampled timestamp:
  - type: `vlm_cuff_on_upper_arm_answer`
  - source: `fastvlm_0_5b`
  - metadata includes question, raw answer, normalized answer, selected frame paths, and model id.

## Logging And Result
- `BP-hack.log` will include:
  - video path, model path, class map, frame count
  - per-frame YOLO detections
  - VLM selected frame list
  - `VLM_QUESTION=...`
  - `VLM_ANSWER_RAW=...`
  - `VLM_ANSWER_NORMALIZED=no|yes|unsure`
  - per-step SOUP decision lines with state name, rule/tag context, SOUP decision, confidence, and message
  - `FINAL_SOUP_STATUS=failed` or `needs_review` when the VLM answer is not `yes`
  - `TASK_FINISHED=false`
  - `TEST=passed` when `TASK_FINISHED=false`

## Test Plan
- Add focused unit tests for the new `vlm_answer` rule:
  - `yes` passes when expected answer is `yes`
  - `no` fails
  - `unsure` produces a non-passing decision
  - missing VLM event produces a non-passing decision
- Add the integration test as opt-in/discovery-safe:
  - normal unittest discovery skips unless `SOUP_RUN_VIDEO_INTEGRATION=1`
  - direct script execution sets that flag internally
- Acceptance for `BP-hack.mp4`:
  - raw frame directory contains the expected 1 FPS extraction count, about 17 frames for the 16.38s video
  - overlay directory contains one image per processed frame
  - log contains YOLO detections, VLM answer, SOUP decisions, `TASK_FINISHED=false`, and `TEST=passed`

## Assumptions
- FastVLM is already installed locally; the test will preflight and skip cleanly with a logged reason if it is unavailable.
- The test will not auto-download FastVLM weights.
- YOLO remains responsible for cuff/sleeve detections; FastVLM is the final semantic cross-check for “cuff on upper arm.”
- The hack test passes by rejecting the workflow, not by requiring `FINAL_SOUP_STATUS=quit`.
