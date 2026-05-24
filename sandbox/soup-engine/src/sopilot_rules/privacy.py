"""Privacy-log construction."""

from __future__ import annotations

from typing import Iterable

from .schema import PrivacyLog


def build_privacy_log(sources: Iterable[str]) -> PrivacyLog:
    unique_sources = sorted({source for source in sources if source})
    cloud_vlm_used = any("cloud" in source.lower() and "vlm" in source.lower() for source in unique_sources)
    local_vlm_used = any("vlm" in source.lower() and "cloud" not in source.lower() for source in unique_sources)
    return PrivacyLog(
        cloud_vlm_used=cloud_vlm_used,
        local_vlm_used=local_vlm_used,
        sources_used=unique_sources,
    )
