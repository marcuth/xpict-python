from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Optional

from ..context import LayerContext, RenderContext, TemplateSize

WhenFunction = Callable[[LayerContext], bool]


@dataclass
class RenderOptions:
    context: RenderContext
    data: Any
    template_size: TemplateSize
    index: int = 0

    def layer_context(self) -> LayerContext:
        return LayerContext(data=self.data, index=self.index, template_size=self.template_size)


class Layer(ABC):
    def __init__(self, when: Optional[WhenFunction] = None) -> None:
        self.when = when

    def should_render(self, ctx: LayerContext) -> bool:
        return bool(self.when(ctx)) if self.when else True

    @abstractmethod
    def render(self, options: RenderOptions) -> None: ...
