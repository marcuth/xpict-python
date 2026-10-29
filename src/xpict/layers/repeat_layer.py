from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, List, Optional

from ..context import Dynamic, LayerContext, resolve
from .layer import Layer, RenderOptions, WhenFunction


@dataclass(frozen=True)
class RepeatInfo:
    index: int
    length: int


EachFunction = Callable[[LayerContext], List[Any]]
LayerFunction = Callable[[Any, RepeatInfo], Layer]


class RepeatLayer(Layer):
    """Generates one layer per item of ``each``; ``index`` becomes the item's index."""

    def __init__(
        self,
        each: EachFunction,
        layer: LayerFunction,
        x: Dynamic = 0,
        y: Dynamic = 0,
        when: Optional[WhenFunction] = None,
    ) -> None:
        super().__init__(when)
        self.each, self.layer, self.x, self.y = each, layer, x, y

    def render(self, options: RenderOptions) -> None:
        items = self.each(options.layer_context())

        if not items:
            return

        rc = options.context

        for index, item in enumerate(items):
            child = RenderOptions(
                context=rc, data=options.data, template_size=options.template_size, index=index
            )
            ctx = child.layer_context()

            prev_x, prev_y = rc.offset_x, rc.offset_y
            rc.offset_x += resolve(self.x, ctx)
            rc.offset_y += resolve(self.y, ctx)

            try:
                layer = self.layer(item, RepeatInfo(index=index, length=len(items)))
                if layer.should_render(ctx):
                    layer.render(child)
            finally:
                rc.offset_x, rc.offset_y = prev_x, prev_y
