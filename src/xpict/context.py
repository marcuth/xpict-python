from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Generic, TypeVar, Union

from PIL import Image

Data = TypeVar("Data")


@dataclass(frozen=True)
class TemplateSize:
    width: int
    height: int


@dataclass(frozen=True)
class LayerContext(Generic[Data]):
    """Argument received by every dynamic value (x, y, text, when...)."""

    data: Any
    index: int
    template_size: TemplateSize


@dataclass
class RenderContext:
    """Mutable render state: the target image and the current offset."""

    image: Image.Image
    offset_x: float = 0
    offset_y: float = 0


Dynamic = Union[float, int, Callable[[LayerContext], Any]]


def resolve(value: Any, ctx: LayerContext) -> Any:
    """Return ``value(ctx)`` if ``value`` is callable, otherwise ``value`` itself."""
    return value(ctx) if callable(value) else value
