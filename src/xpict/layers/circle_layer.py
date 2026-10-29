from __future__ import annotations

from typing import Optional

from ..context import Dynamic, resolve
from ..drawing import Color, fill_circle
from .layer import Layer, RenderOptions, WhenFunction


class CircleLayer(Layer):
    """Circle whose ``(x, y)`` is its center."""

    def __init__(
        self,
        x: Dynamic,
        y: Dynamic,
        radius: float,
        fill: Color,
        when: Optional[WhenFunction] = None,
    ) -> None:
        super().__init__(when)
        self.x, self.y, self.radius, self.fill = x, y, radius, fill

    def render(self, options: RenderOptions) -> None:
        ctx = options.layer_context()
        rc = options.context

        fill_circle(
            rc.image,
            rc.offset_x + resolve(self.x, ctx),
            rc.offset_y + resolve(self.y, ctx),
            self.radius,
            self.fill,
        )
