"""SOUP package loading helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Union

from .schema import SoupPackage


def load_soup(path: Union[str, Path]) -> SoupPackage:
    """Load and validate a `.soup.json` package from disk."""

    package_path = Path(path)
    with package_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return SoupPackage.model_validate(data)
