from __future__ import annotations

from typing import Optional

from ..context import Dynamic, resolve
from ..drawing import Color, fill_rectangle
from .layer import Layer, RenderOptions, WhenFunction


class RectangleLayer(Layer):
    def __init__(
        self,
        x: Dynamic,
        y: Dynamic,
        width: Dynamic,
        height: Dynamic,
        fill: Color,
        border_radius: Optional[float] = None,
        when: Optional[WhenFunction] = None,
    ) -> None:
        super().__init__(when)
        self.x, self.y, self.width, self.height = x, y, width, height
        self.fill = fill
        self.border_radius = border_radius

    def render(self, options: RenderOptions) -> None:
        ctx = options.layer_context()
        rc = options.context

        width = resolve(self.width, ctx)
        height = resolve(self.height, ctx)
        radius = self.border_radius or 0
        radius = min(radius, width / 2, height / 2) if radius > 0 else 0

        fill_rectangle(
            rc.image,
            rc.offset_x + resolve(self.x, ctx),
            rc.offset_y + resolve(self.y, ctx),
            width,
            height,
            self.fill,
            radius,
        )
