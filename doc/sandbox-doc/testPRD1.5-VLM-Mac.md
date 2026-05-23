You are a senior macOS desktop app engineer and full-stack ML app engineer.

Implement a “Local VLM Model Manager” feature for this Mac app.

Context:
- This is a local-first macOS app named SoPilot.
- The app will eventually run YOLO MLX and a SOUP rule engine locally.
- For now, implement only the VLM model-management feature.
- The user should not need Terminal commands after installing the app.
- The app should support exactly two selectable local VLMs.
- Users can download one of the two models, activate it, ask questions with the active model later, and delete old downloaded models.
- Do not implement full VLM inference yet unless there is already an inference adapter in the repo. Implement the model manager, API, UI, persistent state, and safe file handling.

Assumed architecture:
- Frontend: React / TypeScript UI, preferably inside a Tauri app.
- Backend: Python local backend sidecar if present.
- If the repo uses a different stack, inspect the repo and adapt naturally.
- Do not create a completely separate app unless necessary.
- Keep the implementation minimal, readable, and testable.

Feature requirements:

1. Model Registry

Create a model registry with exactly two models:

- FastVLM 0.5B
  id: fastvlm_0_5b
  display_name: FastVLM 0.5B
  description: Fastest local VLM option for Apple Silicon Macs.
  provider: huggingface
  repo_id: apple/FastVLM-0.5B
  recommended: true

- SmolVLM2 500M
  id: smolvlm2_500m
  display_name: SmolVLM2 500M
  description: Small local VLM for image/video Q&A.
  provider: huggingface
  repo_id: HuggingFaceTB/SmolVLM2-500M-Video-Instruct
  recommended: false

Make the registry easy to edit later.

2. Local Model Storage

Downloaded models must be stored outside the app bundle.

Use this directory on macOS:

~/Library/Application Support/SoPilot/models/

Expected layout:

~/Library/Application Support/SoPilot/models/
  fastvlm_0_5b/
  smolvlm2_500m/

Persist active model selection in:

~/Library/Application Support/SoPilot/config.json

Example config:

{
  "active_vlm_model_id": "fastvlm_0_5b"
}

Never store downloaded models inside SoPilot.app.

3. Backend API

Implement or add these local API endpoints.

If the backend is FastAPI, use these exact routes:

GET /api/vlm/models
POST /api/vlm/models/{model_id}/download
POST /api/vlm/models/{model_id}/activate
DELETE /api/vlm/models/{model_id}
GET /api/vlm/models/{model_id}/download-status

Response shape for GET /api/vlm/models:

{
  "models": [
    {
      "id": "fastvlm_0_5b",
      "display_name": "FastVLM 0.5B",
      "description": "Fastest local VLM option for Apple Silicon Macs.",
      "provider": "huggingface",
      "repo_id": "apple/FastVLM-0.5B",
      "recommended": true,
      "status": "not_installed | downloading | installed | active | download_failed",
      "size_on_disk_mb": 0,
      "local_path": "/Users/.../Library/Application Support/SoPilot/models/fastvlm_0_5b"
    }
  ],
  "active_model_id": "fastvlm_0_5b"
}

Download endpoint:
- Starts download.
- Must not block the UI forever.
- It can run synchronously for the first implementation if simpler, but expose status so the UI can show progress.
- Prefer background task/thread if the backend structure supports it.
- Use huggingface_hub.snapshot_download if Python backend exists.
- Use local_dir set to the model’s local folder.
- Avoid symlink-based storage. Use local_dir_use_symlinks=False if supported by the installed huggingface_hub version.
- Create the model root directory if needed.
- Mark status as downloading while active.
- Mark status as installed when complete.
- Mark status as download_failed on error.
- Return a useful but non-sensitive error message.

Activate endpoint:
- Only allow activation if the model is installed.
- Write active_vlm_model_id into config.json.
- Return updated model list.

Delete endpoint:
- Safely delete the selected model folder.
- If the deleted model is active, clear active_vlm_model_id.
- Never accept arbitrary paths from the frontend.
- Only delete folders whose resolved path is inside:
  ~/Library/Application Support/SoPilot/models/
- Return updated model list.

Download status endpoint:
- Return:
{
  "model_id": "fastvlm_0_5b",
  "status": "downloading",
  "progress": null,
  "message": "Downloading model files..."
}
- If exact byte progress is hard, progress may be null and the UI should show an indeterminate progress bar.

4. Frontend UI

Add a visible “Local VLM” section in the app UI.

Place it wherever this repo’s app has settings/runtime controls. If no such page exists, create a simple page or panel named “Local Runtime”.

UI should include:

Title:
Local VLM

Status:
- No VLM installed
- FastVLM 0.5B installed
- FastVLM 0.5B active
- Downloading SmolVLM2 500M…

Dropdown:
- FastVLM 0.5B — Recommended
- SmolVLM2 500M

Buttons:
- Download
- Use
- Delete

Button behavior:
- If selected model is not installed: show Download enabled, Use disabled, Delete disabled.
- If selected model is installed but not active: show Use enabled and Delete enabled.
- If selected model is active: show Use disabled or “Active”, Delete enabled.
- If selected model is downloading: disable all buttons and show progress/indeterminate spinner.
- If download fails: show retry-friendly error and keep Download enabled.

Deletion confirmation:
Before deleting, show a confirmation dialog:
“Delete FastVLM 0.5B? This removes the local model files from this Mac. You can download it again later.”

If active model is being deleted, warning:
“This model is currently active. Deleting it will turn off Local VLM until another model is selected.”

5. User-facing copy

Use clear local-first copy:

- “Models are stored locally on this Mac.”
- “No cloud VLM is used by this setting.”
- “Downloaded models can be removed anytime.”
- “YOLO and rule-engine decisions do not depend on the VLM.”

6. Error handling

Handle:
- Unknown model id.
- Hugging Face download failure.
- Network unavailable.
- Disk write permission failure.
- Delete failure.
- Activating a model that is not installed.
- Config file missing or corrupted.

Do not crash the app for any of these.

7. Tests

Add tests for the model manager logic.

At minimum test:
- Registry returns exactly two models.
- Model path is under the allowed model root.
- Unknown model id is rejected.
- is_installed returns false for missing folder.
- delete_model refuses unsafe paths.
- deleting active model clears active model config.
- activating missing model fails.
- activating installed model writes config.
- GET model list returns expected statuses.

If frontend tests are already used in the repo, add a simple component test for:
- dropdown renders two models.
- not installed model shows Download.
- installed model shows Use/Delete.
- active model shows Active.

8. Implementation constraints

- Keep code small and readable.
- Do not add a large framework unless already present.
- Do not implement unlimited Hugging Face model search.
- Do not allow arbitrary repo IDs from user input.
- Do not download models into the app bundle.
- Do not make cloud VLM calls.
- Do not make the VLM final decision maker.
- Do not break existing YOLO/rule-engine code if present.

9. Deliverables

After implementation, provide:
- Summary of changed files.
- How to run locally.
- How to test.
- Any missing dependency I need to add.
- Known limitations.

Start by inspecting the repository structure. Then implement the smallest clean version that works.