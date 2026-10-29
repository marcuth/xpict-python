from __future__ import annotations

from typing import Optional, Tuple

from ..context import Dynamic, resolve
from ..drawing import Color, stroke_line
from .layer import Layer, RenderOptions, WhenFunction

Point = Tuple[Dynamic, Dynamic]


class LineLayer(Layer):
    """Line between ``from_`` and ``to`` (``(x, y)`` tuples)."""

    def __init__(
        self,
        from_: Point,
        to: Point,
        color: Color,
        width: Dynamic,
        when: Optional[WhenFunction] = None,
    ) -> None:
        super().__init__(when)
        self.from_, self.to, self.color, self.width = from_, to, color, width

    def render(self, options: RenderOptions) -> None:
        ctx = options.layer_context()
        rc = options.context

        stroke_line(
            rc.image,
            rc.offset_x + resolve(self.from_[0], ctx),
            rc.offset_y + resolve(self.from_[1], ctx),
            rc.offset_x + resolve(self.to[0], ctx),
            rc.offset_y + resolve(self.to[1], ctx),
            resolve(self.width, ctx),
            self.color,
        )
