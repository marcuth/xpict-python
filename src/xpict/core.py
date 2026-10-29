from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from PIL import Image

from .context import RenderContext, TemplateSize
from .drawing import parse_color
from .error import XpictError
from .layers.layer import Layer, RenderOptions


@dataclass
class TemplateConfig:
    width: int
    height: int
    fill: Optional[str] = None


class Template:
    """A set of layers that, given some ``data``, produces a ``PIL.Image``.

    Use ``config`` (width, height and optional fill) **or** ``image_path`` (background image).
    """

    def __init__(
        self,
        layers: List[Layer],
        config: Union[TemplateConfig, Dict[str, Any], None] = None,
        image_path: Union[str, Path, None] = None,
    ) -> None:
        if isinstance(config, dict):
            config = TemplateConfig(**config)

        self.layers = layers
        self.config = config
        self.image_path = image_path

    def render(self, data: Any = None) -> Image.Image:
        if self.config:
            width, height = self.config.width, self.config.height
            fill = parse_color(self.config.fill) if self.config.fill else (0, 0, 0, 0)
            canvas = Image.new("RGBA", (width, height), fill)
        elif self.image_path:
            try:
                with Image.open(self.image_path) as background:
                    canvas = background.convert("RGBA")
            except Exception as error:
                raise XpictError(f"Failed to load background image ({self.image_path}): {error}") from error
            width, height = canvas.size
        else:
            raise XpictError("No config or image_path provided")

        options = RenderOptions(
            context=RenderContext(image=canvas),
            data=data,
            template_size=TemplateSize(width=width, height=height),
        )
        ctx = options.layer_context()

        for layer in self.layers:
            if layer.should_render(ctx):
                layer.render(options)

        return canvas
