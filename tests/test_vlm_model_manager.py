# Copyright (c) 2026 webAI, Inc.
"""Tests for local VLM model-management safety and state."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from yolo26mlx.vlm.manager import (
    INSTALL_MARKER_NAME,
    ModelNotInstalledError,
    UnknownModelError,
    UnsafeModelPathError,
    VLM_MODEL_REGISTRY,
    VLMModelManager,
)


def _manager(tmp_path: Path) -> VLMModelManager:
    return VLMModelManager(app_support_dir=tmp_path / "Application Support" / "SoPilot")


def _mark_installed(manager: VLMModelManager, model_id: str) -> None:
    model = manager.get_model(model_id)
    path = manager.model_path(model_id)
    path.mkdir(parents=True, exist_ok=True)
    (path / INSTALL_MARKER_NAME).write_text(
        json.dumps({"model_id": model.id, "repo_id": model.repo_id}),
        encoding="utf-8",
    )


def test_registry_returns_exactly_two_models() -> None:
    assert [model.id for model in VLM_MODEL_REGISTRY] == ["fastvlm_0_5b", "smolvlm2_500m"]


def test_model_path_is_under_allowed_root(tmp_path: Path) -> None:
    manager = _manager(tmp_path)

    path = manager.model_path("fastvlm_0_5b")

    assert manager.path_is_under(path, manager.model_root)
    assert path == manager.model_root / "fastvlm_0_5b"


def test_unknown_model_id_is_rejected(tmp_path: Path) -> None:
    manager = _manager(tmp_path)

    with pytest.raises(UnknownModelError):
        manager.model_path("../not_allowed")


def test_is_installed_returns_false_for_missing_folder(tmp_path: Path) -> None:
    manager = _manager(tmp_path)

    assert manager.is_installed("fastvlm_0_5b") is False


def test_delete_model_refuses_unsafe_symlink_path(tmp_path: Path) -> None:
    manager = _manager(tmp_path)
    manager.model_root.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    manager.model_path("fastvlm_0_5b").symlink_to(outside, target_is_directory=True)

    with pytest.raises(UnsafeModelPathError):
        manager.delete_model("fastvlm_0_5b")

    assert outside.exists()


def test_deleting_active_model_clears_active_model_config(tmp_path: Path) -> None:
    manager = _manager(tmp_path)
    _mark_installed(manager, "fastvlm_0_5b")
    manager.activate_model("fastvlm_0_5b")

    manager.delete_model("fastvlm_0_5b")

    assert manager.get_active_model_id() is None
    assert "active_vlm_model_id" not in manager.load_config()


def test_activating_missing_model_fails(tmp_path: Path) -> None:
    manager = _manager(tmp_path)

    with pytest.raises(ModelNotInstalledError):
        manager.activate_model("fastvlm_0_5b")


def test_activating_installed_model_writes_config(tmp_path: Path) -> None:
    manager = _manager(tmp_path)
    _mark_installed(manager, "fastvlm_0_5b")

    manager.activate_model("fastvlm_0_5b")

    assert manager.load_config()["active_vlm_model_id"] == "fastvlm_0_5b"


def test_model_list_returns_expected_statuses(tmp_path: Path) -> None:
    manager = _manager(tmp_path)
    _mark_installed(manager, "fastvlm_0_5b")
    manager.activate_model("fastvlm_0_5b")

    response = manager.list_models()
    statuses = {model["id"]: model["status"] for model in response["models"]}

    assert response["active_model_id"] == "fastvlm_0_5b"
    assert statuses == {
        "fastvlm_0_5b": "active",
        "smolvlm2_500m": "not_installed",
    }
