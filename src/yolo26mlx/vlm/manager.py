# Copyright (c) 2026 webAI, Inc.
"""Local VLM model registry, storage, and config management."""

from __future__ import annotations

import inspect
import json
import os
import shutil
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

INSTALL_MARKER_NAME = ".sopilot_vlm_install.json"
DOWNLOAD_STATUS_NAME = "vlm_download_status.json"


@dataclass(frozen=True)
class VLMModelDefinition:
    id: str
    display_name: str
    description: str
    provider: str
    repo_id: str
    recommended: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


VLM_MODEL_REGISTRY: tuple[VLMModelDefinition, ...] = (
    VLMModelDefinition(
        id="fastvlm_0_5b",
        display_name="FastVLM 0.5B",
        description="Fastest local VLM option for Apple Silicon Macs.",
        provider="huggingface",
        repo_id="apple/FastVLM-0.5B",
        recommended=True,
    ),
    VLMModelDefinition(
        id="smolvlm2_500m",
        display_name="SmolVLM2 500M",
        description="Small local VLM for image/video Q&A.",
        provider="huggingface",
        repo_id="HuggingFaceTB/SmolVLM2-500M-Video-Instruct",
        recommended=False,
    ),
)
REGISTRY_BY_ID: dict[str, VLMModelDefinition] = {model.id: model for model in VLM_MODEL_REGISTRY}


class VLMModelManagerError(RuntimeError):
    """Base class for expected model-manager failures."""


class UnknownModelError(VLMModelManagerError):
    """Raised when a caller references a model outside the fixed registry."""


class UnsafeModelPathError(VLMModelManagerError):
    """Raised when a model path resolves outside the allowed model root."""


class ModelNotInstalledError(VLMModelManagerError):
    """Raised when activation is requested for a missing model."""


def default_app_support_dir() -> Path:
    return Path.home() / "Library" / "Application Support" / "SoPilot"


class VLMModelManager:
    """Manage the fixed local VLM registry and on-disk model state."""

    def __init__(self, app_support_dir: Path | None = None):
        self.app_support_dir = Path(app_support_dir) if app_support_dir else default_app_support_dir()
        self.model_root = self.app_support_dir / "models"
        self.config_path = self.app_support_dir / "config.json"
        self.download_status_path = self.app_support_dir / DOWNLOAD_STATUS_NAME

    def list_models(self) -> dict[str, Any]:
        active_model_id = self.get_active_model_id()
        models = [self.model_summary(model, active_model_id) for model in VLM_MODEL_REGISTRY]
        return {"models": models, "active_model_id": active_model_id}

    def model_summary(
        self,
        model: VLMModelDefinition,
        active_model_id: str | None = None,
    ) -> dict[str, Any]:
        local_path = self.model_path(model.id)
        installed = self.is_installed(model.id)
        download_status = self.get_download_status(model.id)

        if installed and active_model_id == model.id:
            status = "active"
        elif installed:
            status = "installed"
        elif download_status["status"] in {"downloading", "download_failed"}:
            status = download_status["status"]
        else:
            status = "not_installed"

        return {
            **model.to_dict(),
            "status": status,
            "size_on_disk_mb": self.size_on_disk_mb(local_path),
            "local_path": str(local_path),
        }

    def download_model(self, model_id: str) -> dict[str, Any]:
        model = self.get_model(model_id)
        local_path = self.model_path(model_id)
        self.ensure_base_dirs()
        local_path.mkdir(parents=True, exist_ok=True)
        self.set_download_status(model_id, "downloading", "Downloading model files...")

        try:
            from huggingface_hub import snapshot_download

            kwargs: dict[str, Any] = {
                "repo_id": model.repo_id,
                "local_dir": str(local_path),
            }
            if "local_dir_use_symlinks" in inspect.signature(snapshot_download).parameters:
                kwargs["local_dir_use_symlinks"] = False

            snapshot_download(**kwargs)
            self.write_install_marker(model)
            self.set_download_status(model_id, "installed", "Model downloaded.")
        except Exception as exc:
            self.set_download_status(model_id, "download_failed", self.safe_error_message(exc))
            raise VLMModelManagerError(self.safe_error_message(exc)) from exc

        return self.list_models()

    def activate_model(self, model_id: str) -> dict[str, Any]:
        self.get_model(model_id)
        if not self.is_installed(model_id):
            raise ModelNotInstalledError(f"Model is not installed: {model_id}")

        config = self.load_config()
        config["active_vlm_model_id"] = model_id
        self.write_config(config)
        return self.list_models()

    def delete_model(self, model_id: str) -> dict[str, Any]:
        self.get_model(model_id)
        local_path = self.model_path(model_id)
        if not self.is_safe_model_path(local_path):
            raise UnsafeModelPathError(f"Refusing to delete unsafe model path: {local_path}")

        try:
            if local_path.is_symlink():
                local_path.unlink()
            elif local_path.exists():
                shutil.rmtree(local_path)
        except Exception as exc:
            raise VLMModelManagerError(f"Could not delete model files: {exc}") from exc

        self.clear_download_status(model_id)
        if self.get_active_model_id() == model_id:
            config = self.load_config()
            config.pop("active_vlm_model_id", None)
            self.write_config(config)

        return self.list_models()

    def get_download_status(self, model_id: str) -> dict[str, Any]:
        self.get_model(model_id)
        statuses = self.load_download_statuses()
        status = statuses.get(model_id)
        if isinstance(status, dict):
            return {
                "model_id": model_id,
                "status": status.get("status", "not_installed"),
                "progress": None,
                "message": status.get("message", ""),
            }
        if self.is_installed(model_id):
            return {
                "model_id": model_id,
                "status": "installed",
                "progress": None,
                "message": "Model is installed.",
            }
        return {
            "model_id": model_id,
            "status": "not_installed",
            "progress": None,
            "message": "Model is not installed.",
        }

    def get_model(self, model_id: str) -> VLMModelDefinition:
        try:
            return REGISTRY_BY_ID[model_id]
        except KeyError as exc:
            raise UnknownModelError(f"Unknown VLM model id: {model_id}") from exc

    def model_path(self, model_id: str) -> Path:
        self.get_model(model_id)
        path = self.model_root / model_id
        if not self.path_is_under(path, self.model_root):
            raise UnsafeModelPathError(f"Unsafe model path for model id: {model_id}")
        return path

    def is_installed(self, model_id: str) -> bool:
        local_path = self.model_path(model_id)
        marker_path = local_path / INSTALL_MARKER_NAME
        return local_path.is_dir() and marker_path.is_file()

    def is_safe_model_path(self, path: Path) -> bool:
        return self.path_is_under(path, self.model_root)

    def get_active_model_id(self) -> str | None:
        active_model_id = self.load_config().get("active_vlm_model_id")
        if isinstance(active_model_id, str) and active_model_id in REGISTRY_BY_ID:
            return active_model_id
        return None

    def ensure_base_dirs(self) -> None:
        self.app_support_dir.mkdir(parents=True, exist_ok=True)
        self.model_root.mkdir(parents=True, exist_ok=True)

    def load_config(self) -> dict[str, Any]:
        try:
            with self.config_path.open("r", encoding="utf-8") as file:
                value = json.load(file)
            return value if isinstance(value, dict) else {}
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return {}

    def write_config(self, config: dict[str, Any]) -> None:
        self.ensure_base_dirs()
        self.atomic_write_json(self.config_path, config)

    def write_install_marker(self, model: VLMModelDefinition) -> None:
        marker_path = self.model_path(model.id) / INSTALL_MARKER_NAME
        payload = {
            "model_id": model.id,
            "repo_id": model.repo_id,
            "installed_at_utc": datetime.now(UTC).isoformat(),
        }
        self.atomic_write_json(marker_path, payload)

    def load_download_statuses(self) -> dict[str, Any]:
        try:
            with self.download_status_path.open("r", encoding="utf-8") as file:
                value = json.load(file)
            return value if isinstance(value, dict) else {}
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return {}

    def set_download_status(self, model_id: str, status: str, message: str) -> None:
        self.get_model(model_id)
        statuses = self.load_download_statuses()
        statuses[model_id] = {
            "status": status,
            "message": message,
            "updated_at_utc": datetime.now(UTC).isoformat(),
        }
        self.ensure_base_dirs()
        self.atomic_write_json(self.download_status_path, statuses)

    def clear_download_status(self, model_id: str) -> None:
        statuses = self.load_download_statuses()
        if model_id in statuses:
            statuses.pop(model_id, None)
            self.ensure_base_dirs()
            self.atomic_write_json(self.download_status_path, statuses)

    @staticmethod
    def path_is_under(path: Path, root: Path) -> bool:
        try:
            resolved_path = path.resolve(strict=False)
            resolved_root = root.resolve(strict=False)
            return os.path.commonpath([str(resolved_path), str(resolved_root)]) == str(
                resolved_root
            )
        except (OSError, ValueError):
            return False

    @staticmethod
    def size_on_disk_mb(path: Path) -> int:
        if not path.exists():
            return 0

        total_bytes = 0
        try:
            for root, dirs, files in os.walk(path, followlinks=False):
                dirs[:] = [name for name in dirs if not (Path(root) / name).is_symlink()]
                for name in files:
                    file_path = Path(root) / name
                    try:
                        total_bytes += file_path.stat(follow_symlinks=False).st_size
                    except OSError:
                        continue
        except OSError:
            return 0
        return round(total_bytes / (1024 * 1024))

    @staticmethod
    def safe_error_message(exc: Exception) -> str:
        message = str(exc).strip() or type(exc).__name__
        home = str(Path.home())
        if home and home in message:
            message = message.replace(home, "~")
        return message

    @staticmethod
    def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_name(f".{path.name}.tmp")
        tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        tmp_path.replace(path)
