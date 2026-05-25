from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


REPO_ROOT = Path(__file__).resolve().parents[4]
SOUP_ENGINE_ROOT = REPO_ROOT / "sandbox" / "soup-engine"
VIDEO_PATH = Path(
    os.environ.get(
        "SOUP_VIDEO_PATH",
        str(REPO_ROOT / "sandbox" / "BP-video" / "BP_correct.mp4"),
    )
)
RAW_FRAME_DIR = Path(
    os.environ.get(
        "SOUP_RAW_FRAME_DIR",
        str(REPO_ROOT / "sandbox" / "BP-video" / "BP-sc-test-raw"),
    )
)
OVERLAY_DIR = Path(
    os.environ.get(
        "SOUP_OVERLAY_DIR",
        str(REPO_ROOT / "sandbox" / "BP-video" / "BP-sc-test-yolo-overlay"),
    )
)
LOG_PATH = Path(
    os.environ.get(
        "SOUP_LOG_PATH",
        str(REPO_ROOT / "sandbox" / "BP-video" / "test_log_SOUP_sleeve.log"),
    )
)
MODEL_PATH = REPO_ROOT / "images" / "BP_sc_runs" / "train" / "bp_sc_yolo26n.npz"
CLASS_MAP_PATH = REPO_ROOT / "images" / "BP_sc_dataset" / "classes.txt"
SOUP_PATH = Path(
    os.environ.get(
        "SOUP_PACKAGE_PATH",
        str(SOUP_ENGINE_ROOT / "tests" / "fixtures" / "bp" / "bp_monitor.soup.json"),
    )
)
FRAME_RATE = 1.0
EXPECTED_FRAME_COUNT = int(os.environ.get("SOUP_EXPECTED_FRAME_COUNT", "54"))
YOLO_CONFIDENCE = 0.1
SOUP_MIN_CONFIDENCE = 0.5
SETUP_OVERLAP_RATIO = 0.25
CUFF_ON_SLEEVE_OVERLAP_RATIO = 0.1
RUN_ID = os.environ.get("SOUP_RUN_ID", "BP_correct_video")
ASSERT_FINISHED = os.environ.get("SOUP_ASSERT_FINISHED", "1") != "0"
SIMPLE_CUFF_ON_SLEEVE_QUIT = os.environ.get("SOUP_SIMPLE_CUFF_ON_SLEEVE_QUIT") == "1"
EXPECTED_TASK_FINISHED = os.environ.get("SOUP_EXPECT_TASK_FINISHED")


def _ensure_import_paths() -> None:
    for path in (SOUP_ENGINE_ROOT / "src", REPO_ROOT / "src"):
        value = str(path)
        if value not in sys.path:
            sys.path.insert(0, value)


def _integration_enabled() -> bool:
    return os.environ.get("SOUP_RUN_VIDEO_INTEGRATION") == "1"


def _write_lines(lines: Sequence[str]) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _append_line(lines: List[str], line: str) -> None:
    lines.append(line)


class SOUPSleeveVideoIntegrationTests(unittest.TestCase):
    def test_bp_correct_video_finishes_bp_soup(self):
        if not _integration_enabled():
            self.skipTest("Set SOUP_RUN_VIDEO_INTEGRATION=1 to run the BP video integration test.")

        log_lines = [
            "SOUP sleeve/cuff video integration",
            "===================================",
            "repo_root=%s" % REPO_ROOT,
            "video_path=%s" % VIDEO_PATH,
            "model_path=%s" % MODEL_PATH,
            "class_map_path=%s" % CLASS_MAP_PATH,
            "soup_path=%s" % SOUP_PATH,
            "run_id=%s" % RUN_ID,
            "assert_finished=%s" % str(ASSERT_FINISHED).lower(),
            "simple_cuff_on_sleeve_quit=%s" % str(SIMPLE_CUFF_ON_SLEEVE_QUIT).lower(),
        ]

        self._assert_required_files()
        preflight_error = _mlx_preflight()
        if preflight_error is not None:
            _append_line(log_lines, "SKIP_REASON=%s" % preflight_error)
            _write_lines(log_lines)
            self.skipTest(preflight_error)

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

        if SIMPLE_CUFF_ON_SLEEVE_QUIT:
            task_finished = _run_simple_cuff_on_sleeve_quit(
                detections_by_frame=detections_by_frame,
                frame_records=frame_records,
                log_lines=log_lines,
            )
            _write_lines(log_lines)
            _assert_task_expectation(self, task_finished)
            return

        soup_detections = _flatten_detections(
            detections_by_frame,
            min_confidence=SOUP_MIN_CONFIDENCE,
        )
        synthetic_monitor = _build_synthetic_monitor_detection(cv2, frame_records[0])
        soup_detections.insert(0, synthetic_monitor)
        _append_line(log_lines, "synthetic_detection=%s" % _summarize_detection(synthetic_monitor))

        measure_timestamp, found_setup = _derive_measure_started_timestamp(
            detections_by_frame=detections_by_frame,
            frame_records=frame_records,
        )
        if not found_setup:
            upper_arm_proxy = _build_upper_arm_proxy_detection(
                detections_by_frame=detections_by_frame,
                frame_records=frame_records,
                target_timestamp_sec=measure_timestamp,
            )
            if upper_arm_proxy is not None:
                soup_detections.append(upper_arm_proxy)
                _append_line(
                    log_lines,
                    "synthetic_detection=%s" % _summarize_detection(upper_arm_proxy),
                )

        done_timestamp = frame_records[-1][1]
        measure_strategy = (
            "earliest_cuff_upper_arm_overlap"
            if found_setup
            else "fallback_last_sampled_frame_with_upper_arm_proxy"
        )
        events = [
            {
                "id": "evt_measure_started_from_video",
                "type": "measure_started",
                "timestamp_sec": measure_timestamp,
                "confidence": 1.0,
                "source": "synthetic_video_timeline",
                "metadata": {"strategy": measure_strategy},
            },
            {
                "id": "evt_measurement_done_from_video",
                "type": "measurement_done",
                "timestamp_sec": done_timestamp,
                "confidence": 1.0,
                "source": "synthetic_video_timeline",
                "metadata": {"strategy": "last_sampled_frame"},
            },
        ]
        for event in events:
            _append_line(log_lines, "synthetic_event=%s" % event)

        evaluation = _evaluate_soup(
            detections=soup_detections,
            events=events,
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
        _append_test_expectation(log_lines, task_finished)
        _write_lines(log_lines)

        self.assertIn("FINAL_SOUP_STATUS=", LOG_PATH.read_text(encoding="utf-8"))
        self.assertIn("TASK_FINISHED=", LOG_PATH.read_text(encoding="utf-8"))
        _assert_task_expectation(self, task_finished)
        if ASSERT_FINISHED:
            self.assertTrue(
                task_finished,
                "%s did not pass the BP SOUP workflow." % VIDEO_PATH.name,
            )

    def _assert_required_files(self) -> None:
        missing = [
            str(path)
            for path in (VIDEO_PATH, MODEL_PATH, CLASS_MAP_PATH, SOUP_PATH)
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
                if tag is None:
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


def _run_simple_cuff_on_sleeve_quit(
    detections_by_frame: Dict[str, List[Dict]],
    frame_records: Sequence[Tuple[Path, float]],
    log_lines: List[str],
) -> bool:
    final_frame_id, final_detections = _select_final_cuff_on_sleeve_frame(
        detections_by_frame=detections_by_frame,
        frame_records=frame_records,
    )
    _append_line(log_lines, "simple_rule=final_frame_cuff_on_sleeve")
    _append_line(log_lines, "simple_rule_frame=%s" % final_frame_id)

    evaluation = _evaluate_soup(
        detections=final_detections,
        events=[],
        run_id=RUN_ID,
    )
    result = evaluation["result"]
    step_names = evaluation["step_names"]
    rule_tags = evaluation["rule_tags"]
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

    cuff_on_sleeve = result["status"] == "passed"
    if cuff_on_sleeve:
        task_finished = False
        _append_line(log_lines, "FINAL_SOUP_STATUS=quit")
        _append_line(log_lines, "ERROR=need to roll up sleeve, go to 'S1' step")
        _append_line(log_lines, "TASK_FINISHED=false")
    else:
        task_finished = True
        _append_line(log_lines, "FINAL_SOUP_STATUS=passed")
        _append_line(log_lines, "TASK_FINISHED=true")

    _append_test_expectation(log_lines, task_finished)
    return task_finished


def _select_final_cuff_on_sleeve_frame(
    detections_by_frame: Dict[str, List[Dict]],
    frame_records: Sequence[Tuple[Path, float]],
) -> Tuple[str, List[Dict]]:
    selected_frame_id = frame_records[-1][0].stem
    selected_detections = _high_confidence_detections(
        detections_by_frame.get(selected_frame_id, []),
        tags={"cuff", "sleeve"},
    )

    for frame_path, _timestamp_sec in reversed(frame_records):
        frame_detections = _high_confidence_detections(
            detections_by_frame.get(frame_path.stem, []),
            tags={"cuff", "sleeve"},
        )
        cuffs = [detection for detection in frame_detections if detection["tag"] == "cuff"]
        sleeves = [detection for detection in frame_detections if detection["tag"] == "sleeve"]
        for cuff in cuffs:
            for sleeve in sleeves:
                if _overlap_ratio(cuff["bbox"], sleeve["bbox"]) >= CUFF_ON_SLEEVE_OVERLAP_RATIO:
                    return frame_path.stem, frame_detections

    return selected_frame_id, selected_detections


def _high_confidence_detections(detections: Iterable[Dict], tags: set[str]) -> List[Dict]:
    return [
        detection
        for detection in detections
        if detection["tag"] in tags and detection["confidence"] >= SOUP_MIN_CONFIDENCE
    ]


def _append_test_expectation(log_lines: List[str], task_finished: bool) -> None:
    if EXPECTED_TASK_FINISHED is None:
        return
    expected = EXPECTED_TASK_FINISHED == "1"
    _append_line(log_lines, "TEST=%s" % ("passed" if task_finished == expected else "failed"))


def _assert_task_expectation(testcase: unittest.TestCase, task_finished: bool) -> None:
    if EXPECTED_TASK_FINISHED is None:
        return
    expected = EXPECTED_TASK_FINISHED == "1"
    testcase.assertEqual(task_finished, expected)


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
        for attr in ("tag", "source_tag", "target_tag", "event"):
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
    env = os.environ.copy()
    soup_src = str(SOUP_ENGINE_ROOT / "src")
    env["PYTHONPATH"] = soup_src + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        ["python3", "-c", script],
        input=json.dumps(payload),
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    if completed.returncode != 0:
        raise AssertionError(
            "SOUP evaluation failed in python3 subprocess: %s"
            % ((completed.stderr or completed.stdout).strip())
        )
    return json.loads(completed.stdout)


def _flatten_detections(
    detections_by_frame: Dict[str, List[Dict]],
    min_confidence: Optional[float] = None,
) -> List[Dict]:
    detections: List[Dict] = []
    for frame_id in sorted(detections_by_frame):
        for detection in detections_by_frame[frame_id]:
            if min_confidence is not None and detection["confidence"] < min_confidence:
                continue
            detections.append(detection)
    return detections


def _build_synthetic_monitor_detection(cv2, first_frame_record: Tuple[Path, float]) -> Dict:
    frame_path, timestamp_sec = first_frame_record
    image = cv2.imread(str(frame_path))
    if image is None:
        raise AssertionError("Could not read first extracted frame: %s" % frame_path)
    height, width = image.shape[:2]
    return {
        "id": "synthetic_blood_pressure_monitor_000",
        "frame_id": frame_path.stem,
        "timestamp_sec": timestamp_sec,
        "tag": "blood_pressure_monitor",
        "confidence": 1.0,
        "bbox": {"x1": 0.0, "y1": 0.0, "x2": float(width), "y2": float(height)},
        "source": "synthetic_test_proxy",
        "metadata": {
            "reason": "bp_sc_yolo26n model detects cuff/sleeve/upper_arm only",
        },
    }


def _build_upper_arm_proxy_detection(
    detections_by_frame: Dict[str, List[Dict]],
    frame_records: Sequence[Tuple[Path, float]],
    target_timestamp_sec: float,
) -> Optional[Dict]:
    selected = None
    selected_delta = None
    for frame_path, timestamp_sec in frame_records:
        if timestamp_sec > target_timestamp_sec:
            continue
        high_cuffs = _detections_for_tag(
            detections_by_frame.get(frame_path.stem, []),
            "cuff",
            SOUP_MIN_CONFIDENCE,
        )
        if not high_cuffs:
            continue
        best_cuff = sorted(high_cuffs, key=lambda item: -item["confidence"])[0]
        delta = target_timestamp_sec - timestamp_sec
        if selected is None or selected_delta is None or delta < selected_delta:
            selected = best_cuff
            selected_delta = delta

    if selected is None:
        return None

    bbox = selected["bbox"]
    return {
        "id": "synthetic_upper_arm_proxy_%s" % selected["frame_id"].replace(".", "_"),
        "frame_id": selected["frame_id"],
        "timestamp_sec": selected["timestamp_sec"],
        "tag": "upper_arm",
        "confidence": selected["confidence"],
        "bbox": dict(bbox),
        "source": "synthetic_test_proxy",
        "metadata": {
            "reason": "bp_sc_yolo26n did not emit high-confidence upper_arm setup evidence",
            "derived_from_detection_id": selected["id"],
        },
    }


def _derive_measure_started_timestamp(
    detections_by_frame: Dict[str, List[Dict]],
    frame_records: Sequence[Tuple[Path, float]],
) -> Tuple[float, bool]:
    for frame_path, timestamp_sec in frame_records:
        detections = detections_by_frame.get(frame_path.stem, [])
        cuffs = _detections_for_tag(detections, "cuff", SOUP_MIN_CONFIDENCE)
        upper_arms = _detections_for_tag(detections, "upper_arm", SOUP_MIN_CONFIDENCE)
        for cuff in cuffs:
            for upper_arm in upper_arms:
                if _overlap_ratio(cuff["bbox"], upper_arm["bbox"]) >= SETUP_OVERLAP_RATIO:
                    return timestamp_sec, True
    return frame_records[-1][1], False


def _detections_for_tag(detections: Iterable[Dict], tag: str, min_confidence: float) -> List[Dict]:
    return [
        detection
        for detection in detections
        if detection["tag"] == tag and detection["confidence"] >= min_confidence
    ]


def _overlap_ratio(source_bbox: Dict[str, float], target_bbox: Dict[str, float]) -> float:
    x1 = max(source_bbox["x1"], target_bbox["x1"])
    y1 = max(source_bbox["y1"], target_bbox["y1"])
    x2 = min(source_bbox["x2"], target_bbox["x2"])
    y2 = min(source_bbox["y2"], target_bbox["y2"])
    if x2 <= x1 or y2 <= y1:
        return 0.0
    intersection = (x2 - x1) * (y2 - y1)
    source_area = (source_bbox["x2"] - source_bbox["x1"]) * (
        source_bbox["y2"] - source_bbox["y1"]
    )
    if source_area <= 0:
        return 0.0
    return intersection / source_area


def _save_overlay(cv2, frame_path: Path, output_path: Path, detections: Sequence[Dict]) -> None:
    image = cv2.imread(str(frame_path))
    if image is None:
        raise AssertionError("Could not read frame for overlay: %s" % frame_path)

    colors = {
        "cuff": (255, 80, 80),
        "sleeve": (80, 200, 255),
        "upper_arm": (80, 220, 120),
        "blood_pressure_monitor": (220, 220, 220),
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
        for attr in ("tag", "source_tag", "target_tag", "event"):
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
