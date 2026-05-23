# Copyright (c) 2026 webAI, Inc.
"""Local VLM model-management helpers for the FaceBoxDemo macOS app."""

from yolo26mlx.vlm.manager import (
    INSTALL_MARKER_NAME,
    REGISTRY_BY_ID,
    VLM_MODEL_REGISTRY,
    VLMModelDefinition,
    VLMModelManager,
    VLMModelManagerError,
)

__all__ = [
    "INSTALL_MARKER_NAME",
    "REGISTRY_BY_ID",
    "VLM_MODEL_REGISTRY",
    "VLMModelDefinition",
    "VLMModelManager",
    "VLMModelManagerError",
]
