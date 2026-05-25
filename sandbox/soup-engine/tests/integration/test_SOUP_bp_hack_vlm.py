from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


REPO_ROOT = Path(__file__).resolve().parents[4]
SOUP_ENGINE_ROOT = REPO_ROOT / "sandbox" / "soup-engine"
VIDEO_PATH = REPO_ROOT / "sandbox" / "BP-video" / "BP-hack.mp4"
RAW_FRAME_DIR = REPO_ROOT / "sandbox" / "BP-video" / "BP-hack-raw"
OVERLAY_DIR = REPO_ROOT / "sandbox" / "BP-video" / "BP-hack-yolo-overlay"
LOG_PATH = REPO_ROOT / "sandbox" / "BP-video" / "BP-hack.log"
MODEL_PATH = REPO_ROOT / "images" / "BP_sc_runs" / "train" / "bp_sc_yolo26n.npz"
CLASS_MAP_PATH = REPO_ROOT / "images" / "BP_sc_dataset" / "classes.txt"
SOUP_PATH = SOUP_ENGINE_ROOT / "tests" / "fixtures" / "bp" / "bp_hack_vlm_crosscheck.soup.json"
VLM_SCRIPT_PATH = REPO_ROOT / "sandbox" / "macCamera" / "Resources" / "vlm_model_manager_cli.py"
FRAME_RATE = 1.0
EXPECTED_FRAME_COUNT = int(os.environ.get("SOUP_EXPECTED_FRAME_COUNT", "17"))
YOLO_CONFIDENCE = 0.1
YOLO_TAGS = {"cuff", "sleeve"}
VLM_MODEL_ID = "fastvlm_0_5b"
VLM_PROMPT = "Has the person put any object on upper arm? Answer exactly one token: YES, NO, or UNSURE."
VLM_SYSTEM_PROMPT = (
    "You are checking a blood pressure workflow. Upper arm means the object is placed on the "
    "person's upper arm for measurement. If the object is on top of a sleeve, clothing, or is "
    "not clearly on the upper arm, answer NO. If the visual evidence is insufficient, answer UNSURE."
)
RUN_ID = "BP_hack_vlm_video"


class VLMUnavailableSkip(RuntimeError):
    pass


def _ensure_import_paths() -> None:
    for path in (SOUP_ENGINE_ROOT / "src", REPO_ROOT / "src"):
        value = str(path)
        if value not in sys.path:
            sys.path.insert(0, value)


def _python_env() -> Dict[str, str]:
    env = os.environ.copy()
    paths = [str(SOUP_ENGINE_ROOT / "src"), str(REPO_ROOT / "src")]
    if env.get("PYTHONPATH"):
        paths.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(paths)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def _integration_enabled() -> bool:
    return os.environ.get("SOUP_RUN_VIDEO_INTEGRATION") == "1"


def _write_lines(lines: Sequence[str]) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _append_line(lines: List[str], line: str) -> None:
    lines.append(line)


class SOUPBPHackVLMIntegrationTests(unittest.TestCase):
    def test_bp_hack_video_is_rejected_by_vlm_crosscheck(self):
        if not _integration_enabled():
            self.skipTest("Set SOUP_RUN_VIDEO_INTEGRATION=1 to run the BP hack VLM test.")

        log_lines = [
            "SOUP BP hack FastVLM/YOLO integration",
            "=====================================",
            "repo_root=%s" % REPO_ROOT,
            "video_path=%s" % VIDEO_PATH,
            "model_path=%s" % MODEL_PATH,
            "class_map_path=%s" % CLASS_MAP_PATH,
            "soup_path=%s" % SOUP_PATH,
            "vlm_script_path=%s" % VLM_SCRIPT_PATH,
            "vlm_model_id=%s" % VLM_MODEL_ID,
            "run_id=%s" % RUN_ID,
        ]

        self._assert_required_files()

        preflight_error = _mlx_preflight()
        if preflight_error is not None:
            _append_line(log_lines, "SKIP_REASON=%s" % preflight_error)
            _write_lines(log_lines)
            self.skipTest(preflight_error)

        vlm_preflight_error = _vlm_preflight(log_lines)
        if vlm_preflight_error is not None:
            _append_line(log_lines, "SKIP_REASON=%s" % vlm_preflight_error)
            _write_lines(log_lines)
            self.skipTest(vlm_preflight_error)

        _ensure_import_paths()

        import cv2

        class_map = _load_class_map(CLASS_MAP_PATH)
        _append_line(log_lines, "class_map=%s" % class_map)

        frame_records = _extract_frames(cv2, VIDEO_PATH, RAW_FRAME_DIR, FRAME_RATE)
        _append_line(log_lines, "raw_frame_count=%d" % len(frame_records))
        self.assertEqual(len(frame_records), EXPECTED_FRAME_COUNT)

        detections_by_frame = _run_yolo_on_frames(
            frame_records=frame_records,
            class_map=class_map,
            log_lines=log_lines,
        )

        _clear_generated_jpegs(OVERLAY_DIR)
        for index, (frame_path, timestamp_sec) in enumerate(frame_records):
            _save_overlay(
                cv2=cv2,
                frame_path=frame_path,
                output_path=OVERLAY_DIR / frame_path.name,
                detections=detections_by_frame.get(frame_path.stem, []),
            )
            _append_line(
                log_lines,
                "overlay frame_index=%03d timestamp=%.2f path=%s"
                % (index, timestamp_sec, OVERLAY_DIR / frame_path.name),
            )

        overlay_count = len(sorted(OVERLAY_DIR.glob("*.jpg")))
        _append_line(log_lines, "overlay_frame_count=%d" % overlay_count)
        self.assertEqual(overlay_count, len(frame_records))

        vlm_frame_paths = _select_vlm_frames(OVERLAY_DIR, max_frames=6)
        for index, path in enumerate(vlm_frame_paths):
            _append_line(log_lines, "vlm_frame index=%d path=%s" % (index, path))
        _append_line(log_lines, "VLM_QUESTION=%s" % VLM_PROMPT)

        try:
            vlm_answer = _call_fastvlm(vlm_frame_paths)
        except VLMUnavailableSkip as exc:
            _append_line(log_lines, "SKIP_REASON=%s" % exc)
            _write_lines(log_lines)
            self.skipTest(str(exc))

        normalized_answer = _normalize_vlm_answer(vlm_answer)
        _append_line(log_lines, "VLM_ANSWER_RAW=%s" % vlm_answer)
        _append_line(log_lines, "VLM_ANSWER_NORMALIZED=%s" % normalized_answer)

        soup_detections = _flatten_detections(detections_by_frame)
        vlm_event = _build_vlm_event(
            raw_answer=vlm_answer,
            normalized_answer=normalized_answer,
            frame_records=frame_records,
            vlm_frame_paths=vlm_frame_paths,
        )
        _append_line(log_lines, "vlm_event=%s" % vlm_event)

        evaluation = _evaluate_soup(
            detections=soup_detections,
            events=[vlm_event],
            run_id=RUN_ID,
        )

        step_names = evaluation["step_names"]
        rule_tags = evaluation["rule_tags"]
        result = evaluation["result"]
        for step in result["steps"]:
            _append_line(
                log_lines,
                (
                    "SOUP state=%s tag=%s rule=%s decision=%s confidence=%s "
                    "completed_at=%s message=%s"
                )
                % (
                    step_names.get(step["step_id"], step["step_id"]),
                    rule_tags.get(step["rule_id"], "<none>"),
                    step["rule_id"],
                    step["status"],
                    step.get("confidence"),
                    step.get("completed_at_sec"),
                    step["message"],
                ),
            )

        task_finished = result["status"] == "passed"
        _append_line(log_lines, "FINAL_SOUP_STATUS=%s" % result["status"])
        _append_line(log_lines, "TASK_FINISHED=%s" % str(task_finished).lower())
        _append_line(log_lines, "TEST=%s" % ("passed" if not task_finished else "failed"))
        _write_lines(log_lines)

        log_text = LOG_PATH.read_text(encoding="utf-8")
        self.assertIn("VLM_ANSWER_NORMALIZED=", log_text)
        self.assertIn("FINAL_SOUP_STATUS=", log_text)
        self.assertIn("TASK_FINISHED=false", log_text)
        self.assertFalse(task_finished, "%s should be rejected by the BP hack SOUP test." % VIDEO_PATH.name)

    def _assert_required_files(self) -> None:
        missing = [
            str(path)
            for path in (VIDEO_PATH, MODEL_PATH, CLASS_MAP_PATH, SOUP_PATH, VLM_SCRIPT_PATH)
            if not path.exists()
        ]
        if missing:
            self.fail("Missing required integration artifact(s): %s" % ", ".join(missing))


def _mlx_preflight() -> Optional[str]:
    script = (
        "import mlx.core as mx; "
        "value = mx.array([1.0]); "
        "mx.eval(value); "
        "print('mlx preflight ok')"
    )
    try:
        completed = subprocess.run(
            [sys.executable, "-c", script],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except Exception as exc:  # pragma: no cover - defensive around platform/runtime failures.
        return "MLX preflight could not run: %s" % exc

    if completed.returncode == 0:
        return None

    stderr = " ".join((completed.stderr or "").split())
    stdout = " ".join((completed.stdout or "").split())
    detail = stderr or stdout or "exit code %s" % completed.returncode
    return "MLX/Metal preflight failed before yolo26mlx import: %s" % detail


def _vlm_preflight(log_lines: List[str]) -> Optional[str]:
    completed = subprocess.run(
        _vlm_base_command() + ["list"],
        check=False,
        capture_output=True,
        text=True,
        env=_python_env(),
        timeout=30,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        return "FastVLM model manager preflight failed: %s" % (detail or completed.returncode)

    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        return "FastVLM model manager returned invalid JSON: %s" % exc

    _append_line(log_lines, "vlm_model_list=%s" % payload)
    for model in payload.get("models", []):
        if model.get("id") == VLM_MODEL_ID:
            status = model.get("status")
            _append_line(log_lines, "vlm_model_status=%s" % status)
            if status in ("installed", "active"):
                return None
            return "FastVLM model is not installed: %s" % status

    return "FastVLM model id was not found in registry: %s" % VLM_MODEL_ID


def _vlm_base_command() -> List[str]:
    command = [sys.executable, str(VLM_SCRIPT_PATH)]
    app_support_dir = os.environ.get("SOUP_VLM_APP_SUPPORT_DIR")
    if app_support_dir:
        command.extend(["--app-support-dir", app_support_dir])
    return command


def _load_class_map(path: Path) -> Dict[int, str]:
    names = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    return {index: name for index, name in enumerate(names) if name}


def _clear_generated_jpegs(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for path in directory.glob("*.jpg"):
        path.unlink()


def _extract_frames(cv2, video_path: Path, output_dir: Path, fps: float) -> List[Tuple[Path, float]]:
    _clear_generated_jpegs(output_dir)

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise AssertionError("Could not open video: %s" % video_path)

    video_fps = cap.get(cv2.CAP_PROP_FPS)
    if video_fps <= 0:
        cap.release()
        raise AssertionError("Video FPS was not available for %s" % video_path)

    frame_interval = max(1, int(round(video_fps / fps)))
    frame_idx = 0
    records: List[Tuple[Path, float]] = []

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        if frame_idx % frame_interval == 0:
            timestamp_sec = frame_idx / video_fps
            output_path = output_dir / ("frame_%06.2fs.jpg" % timestamp_sec)
            cv2.imwrite(str(output_path), frame)
            records.append((output_path, timestamp_sec))

        frame_idx += 1

    cap.release()
    return records


def _run_yolo_on_frames(
    frame_records: Sequence[Tuple[Path, float]],
    class_map: Dict[int, str],
    log_lines: List[str],
) -> Dict[str, List[Dict]]:
    _ensure_import_paths()

    from yolo26mlx import YOLO

    model = YOLO(MODEL_PATH, task="detect")
    detections_by_frame: Dict[str, List[Dict]] = {}

    for frame_index, (frame_path, timestamp_sec) in enumerate(frame_records):
        results = model.predict(source=str(frame_path), conf=YOLO_CONFIDENCE, imgsz=640)
        frame_detections: List[Dict] = []

        for result in results:
            boxes = getattr(result, "boxes", None)
            if boxes is None or len(boxes) == 0:
                continue

            for box_index, (xyxy, confidence, cls_id) in enumerate(
                zip(boxes.xyxy, boxes.conf, boxes.cls)
            ):
                class_id = int(cls_id)
                tag = class_map.get(class_id)
                if tag not in YOLO_TAGS:
                    continue

                x1, y1, x2, y2 = [float(value) for value in xyxy]
                detection = {
                    "id": "%s_%03d_%02d" % (tag, frame_index, box_index),
                    "frame_id": frame_path.stem,
                    "timestamp_sec": timestamp_sec,
                    "tag": tag,
                    "confidence": float(confidence),
                    "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                    "source": "yolo_bp_sc",
                    "metadata": {
                        "model_path": str(MODEL_PATH),
                        "class_id": class_id,
                        "class_name": tag,
                    },
                }
                frame_detections.append(detection)
                _append_line(log_lines, "detection=%s" % _summarize_detection(detection))

        detections_by_frame[frame_path.stem] = frame_detections
        _append_line(
            log_lines,
            "frame frame_id=%s timestamp=%.2f retained_detections=%d"
            % (frame_path.stem, timestamp_sec, len(frame_detections)),
        )

    return detections_by_frame


def _select_vlm_frames(overlay_dir: Path, max_frames: int) -> List[Path]:
    paths = sorted(overlay_dir.glob("*.jpg"))
    if not paths:
        raise AssertionError("No YOLO overlay frames were available for VLM: %s" % overlay_dir)
    return paths[-max_frames:]


def _call_fastvlm(frame_paths: Sequence[Path]) -> str:
    system_prompt_path = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            suffix=".txt",
            prefix="sopilot-vlm-system-",
            encoding="utf-8",
            delete=False,
        ) as handle:
            handle.write(VLM_SYSTEM_PROMPT)
            system_prompt_path = Path(handle.name)

        command = _vlm_base_command() + [
            "chat",
            VLM_MODEL_ID,
            "--prompt",
            VLM_PROMPT,
            "--system-prompt-file",
            str(system_prompt_path),
            "--max-new-tokens",
            "16",
        ]
        for frame_path in frame_paths:
            command.extend(["--frame-file", str(frame_path)])

        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            env=_python_env(),
            timeout=300,
        )
    except Exception as exc:  # pragma: no cover - defensive around local model runtime failures.
        raise VLMUnavailableSkip("FastVLM chat could not run: %s" % exc) from exc
    finally:
        if system_prompt_path is not None:
            try:
                system_prompt_path.unlink()
            except FileNotFoundError:
                pass

    if completed.returncode != 0:
        detail = (completed.stdout or completed.stderr or "").strip()
        raise VLMUnavailableSkip("FastVLM chat failed: %s" % (detail or completed.returncode))

    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise VLMUnavailableSkip("FastVLM chat returned invalid JSON: %s" % exc) from exc

    answer = str(payload.get("answer", "")).strip()
    if not answer:
        raise VLMUnavailableSkip("FastVLM chat returned an empty answer.")
    return answer


def _normalize_vlm_answer(answer: str) -> str:
    normalized = answer.strip().lower()
    if normalized.startswith("yes"):
        return "yes"
    if normalized.startswith("no"):
        return "no"
    return "unsure"


def _build_vlm_event(
    raw_answer: str,
    normalized_answer: str,
    frame_records: Sequence[Tuple[Path, float]],
    vlm_frame_paths: Sequence[Path],
) -> Dict:
    confidence = 1.0 if normalized_answer in {"yes", "no"} else 0.5
    return {
        "id": "evt_vlm_cuff_on_upper_arm",
        "type": "vlm_cuff_on_upper_arm_answer",
        "timestamp_sec": frame_records[-1][1],
        "confidence": confidence,
        "source": VLM_MODEL_ID,
        "metadata": {
            "question": VLM_PROMPT,
            "raw_answer": raw_answer,
            "answer_normalized": normalized_answer,
            "model_id": VLM_MODEL_ID,
            "frame_ids": [path.stem for path in vlm_frame_paths],
            "frame_paths": [str(path) for path in vlm_frame_paths],
        },
    }


def _flatten_detections(detections_by_frame: Dict[str, List[Dict]]) -> List[Dict]:
    detections: List[Dict] = []
    for frame_id in sorted(detections_by_frame):
        detections.extend(detections_by_frame[frame_id])
    return detections


def _evaluate_soup(detections: Sequence[Dict], events: Sequence[Dict], run_id: str) -> Dict:
    _ensure_import_paths()
    try:
        from sopilot_rules import RuleEngine, load_soup
    except ModuleNotFoundError:
        return _evaluate_soup_with_python3(detections=detections, events=events, run_id=run_id)

    engine = RuleEngine(load_soup(SOUP_PATH))
    result = engine.evaluate(detections=detections, events=events, run_id=run_id)
    return {
        "result": json.loads(result.to_json()),
        "step_names": {step.id: step.name for step in engine.soup.steps},
        "rule_tags": _rule_tag_context(engine.soup.rules),
    }


def _evaluate_soup_with_python3(
    detections: Sequence[Dict],
    events: Sequence[Dict],
    run_id: str,
) -> Dict:
    payload = {
        "detections": list(detections),
        "events": list(events),
        "run_id": run_id,
        "soup_path": str(SOUP_PATH),
    }
    script = r"""
import json
import sys

from sopilot_rules import RuleEngine, load_soup


def rule_tag_context(rules):
    contexts = {}
    for rule in rules:
        rule_id = getattr(rule, "id", "")
        values = []
        for attr in ("tag", "source_tag", "target_tag", "event", "question", "expected_answer"):
            value = getattr(rule, attr, None)
            if value:
                values.append("%s=%s" % (attr, value))
        conditions = getattr(rule, "conditions", None)
        if conditions:
            condition_bits = []
            for condition in conditions:
                parts = []
                for attr in ("tag", "source_tag", "target_tag"):
                    value = getattr(condition, attr, None)
                    if value:
                        parts.append("%s=%s" % (attr, value))
                condition_bits.append(
                    "%s(%s)" % (getattr(condition, "type", ""), ",".join(parts))
                )
            values.append("conditions=%s" % ";".join(condition_bits))
        contexts[rule_id] = " ".join(values) if values else "<none>"
    return contexts


payload = json.load(sys.stdin)
engine = RuleEngine(load_soup(payload["soup_path"]))
result = engine.evaluate(
    detections=payload["detections"],
    events=payload["events"],
    run_id=payload["run_id"],
)
print(
    json.dumps(
        {
            "result": json.loads(result.to_json()),
            "step_names": {step.id: step.name for step in engine.soup.steps},
            "rule_tags": rule_tag_context(engine.soup.rules),
        },
        sort_keys=True,
    )
)
"""
    completed = subprocess.run(
        ["python3", "-c", script],
        input=json.dumps(payload),
        check=False,
        capture_output=True,
        text=True,
        env=_python_env(),
    )
    if completed.returncode != 0:
        raise AssertionError(
            "SOUP evaluation failed in python3 subprocess: %s"
            % ((completed.stderr or completed.stdout).strip())
        )
    return json.loads(completed.stdout)


def _save_overlay(cv2, frame_path: Path, output_path: Path, detections: Sequence[Dict]) -> None:
    image = cv2.imread(str(frame_path))
    if image is None:
        raise AssertionError("Could not read frame for overlay: %s" % frame_path)

    colors = {
        "cuff": (255, 80, 80),
        "sleeve": (80, 200, 255),
    }
    for detection in detections:
        bbox = detection["bbox"]
        x1, y1, x2, y2 = [int(round(bbox[key])) for key in ("x1", "y1", "x2", "y2")]
        tag = detection["tag"]
        color = colors.get(tag, (255, 255, 255))
        label = "%s %.2f" % (tag, detection["confidence"])

        cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
        text_origin = (max(0, x1), max(15, y1 - 6))
        (text_width, text_height), _ = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1
        )
        cv2.rectangle(
            image,
            (text_origin[0], text_origin[1] - text_height - 4),
            (text_origin[0] + text_width + 4, text_origin[1] + 4),
            color,
            -1,
        )
        cv2.putText(
            image,
            label,
            text_origin,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (0, 0, 0),
            1,
            cv2.LINE_AA,
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), image)


def _rule_tag_context(rules: Sequence[object]) -> Dict[str, str]:
    contexts = {}
    for rule in rules:
        rule_id = getattr(rule, "id", "")
        values = []
        for attr in ("tag", "source_tag", "target_tag", "event", "question", "expected_answer"):
            value = getattr(rule, attr, None)
            if value:
                values.append("%s=%s" % (attr, value))
        conditions = getattr(rule, "conditions", None)
        if conditions:
            condition_bits = []
            for condition in conditions:
                parts = []
                for attr in ("tag", "source_tag", "target_tag"):
                    value = getattr(condition, attr, None)
                    if value:
                        parts.append("%s=%s" % (attr, value))
                condition_bits.append("%s(%s)" % (getattr(condition, "type", ""), ",".join(parts)))
            values.append("conditions=%s" % ";".join(condition_bits))
        contexts[rule_id] = " ".join(values) if values else "<none>"
    return contexts


def _summarize_detection(detection: Dict) -> str:
    bbox = detection["bbox"]
    return (
        "id=%s frame=%s timestamp=%.2f tag=%s confidence=%.3f "
        "bbox=[%.1f,%.1f,%.1f,%.1f] source=%s"
    ) % (
        detection["id"],
        detection["frame_id"],
        detection["timestamp_sec"],
        detection["tag"],
        detection["confidence"],
        bbox["x1"],
        bbox["y1"],
        bbox["x2"],
        bbox["y2"],
        detection["source"],
    )


if __name__ == "__main__":
    os.environ.setdefault("SOUP_RUN_VIDEO_INTEGRATION", "1")
    unittest.main()
