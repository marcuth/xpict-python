from __future__ import annotations

from typing import List, Optional

from ..context import Dynamic, resolve
from .layer import Layer, RenderOptions, WhenFunction


class GroupLayer(Layer):
    """Groups layers, applying an ``(x, y)`` offset to all of them."""

    def __init__(
        self,
        layers: List[Layer],
        x: Dynamic = 0,
        y: Dynamic = 0,
        when: Optional[WhenFunction] = None,
    ) -> None:
        super().__init__(when)
        self.layers, self.x, self.y = layers, x, y

    def render(self, options: RenderOptions) -> None:
        ctx = options.layer_context()
        rc = options.context

        prev_x, prev_y = rc.offset_x, rc.offset_y
        rc.offset_x += resolve(self.x, ctx)
        rc.offset_y += resolve(self.y, ctx)

        try:
            for layer in self.layers:
                if layer.should_render(ctx):
                    layer.render(options)
        finally:
            rc.offset_x, rc.offset_y = prev_x, prev_y
