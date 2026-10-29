from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Callable, Dict, Optional, Union

from PIL import ImageFont

_REGISTRY: Dict[str, str] = {}


@dataclass(frozen=True)
class Font:
    size: float
    name: Optional[str] = None
    color: Optional[str] = None
    weight: Optional[str] = None


def font(
    name: str,
    file_path: Union[str, Path, None] = None,
    color: Optional[str] = None,
    weight: Optional[str] = None,
) -> Callable[..., Font]:
    """Register a font (optionally from a file) and return a factory.

    ``font(...)(size=60, color="#fff")`` produces a :class:`Font` for a ``TextLayer``.
    """
    if file_path is not None:
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Font file not found: {path}")
        _REGISTRY[name] = str(path)
        load_font.cache_clear()

    def build(size: float, color: Optional[str] = color, weight: Optional[str] = weight) -> Font:
        return Font(size=size, name=name, color=color, weight=weight)

    return build


@lru_cache(maxsize=128)
def load_font(name: Optional[str], size: float) -> ImageFont.FreeTypeFont:
    """Load the registered (or system) font at ``size``; falls back to Pillow's default font."""
    size = max(1, size)
    candidates = []

    if name:
        if name in _REGISTRY:
            candidates.append(_REGISTRY[name])
        candidates.extend([name, f"{name}.ttf"])

    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue

    return ImageFont.load_default(size)  # type: ignore[return-value]
