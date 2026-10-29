from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, List, Optional, Union

from PIL import Image

from ..context import Dynamic, LayerContext, resolve
from ..drawing import composite
from ..error import XpictError
from .layer import Layer, RenderOptions, WhenFunction

ImageSource = Union[str, Path, bytes, Image.Image]


@dataclass
class TransformOptions:
    data: Any
    index: int
    image: Image.Image


# Receives TransformOptions; may return a new image or modify ``options.image`` in place.
ImageTransformFunction = Callable[[TransformOptions], Optional[Image.Image]]


def _open(source: ImageSource) -> Image.Image:
    if isinstance(source, Image.Image):
        return source.convert("RGBA")
    if isinstance(source, (bytes, bytearray)):
        source = io.BytesIO(source)  # type: ignore[assignment]
    with Image.open(source) as opened:
        return opened.convert("RGBA")


class ImageLayer(Layer):
    def __init__(
        self,
        src: Union[ImageSource, Callable[[LayerContext], ImageSource]],
        x: Dynamic,
        y: Dynamic,
        width: Optional[Dynamic] = None,
        height: Optional[Dynamic] = None,
        flip_x: bool = False,
        flip_y: bool = False,
        rotate: Optional[float] = None,
        transform: Optional[List[ImageTransformFunction]] = None,
        when: Optional[WhenFunction] = None,
    ) -> None:
        super().__init__(when)
        self.src, self.x, self.y = src, x, y
        self.width, self.height = width, height
        self.flip_x, self.flip_y, self.rotate = flip_x, flip_y, rotate
        self.transform = transform or []

    def render(self, options: RenderOptions) -> None:
        ctx = options.layer_context()
        rc = options.context

        x = rc.offset_x + resolve(self.x, ctx)
        y = rc.offset_y + resolve(self.y, ctx)

        width = resolve(self.width, ctx) if self.width is not None else None
        height = resolve(self.height, ctx) if self.height is not None else None

        source = self.src(ctx) if callable(self.src) else self.src
        label = source if isinstance(source, (str, Path)) else type(source).__name__

        try:
            image = _open(source)

            if width and height:
                size = (width, height)
            elif width:
                size = (width, width / image.width * image.height)
            elif height:
                size = (height / image.height * image.width, height)
            else:
                size = image.size

            size = (max(1, round(size[0])), max(1, round(size[1])))
            if size != image.size:
                image = image.resize(size, Image.LANCZOS)

            if self.flip_x:
                image = image.transpose(Image.FLIP_LEFT_RIGHT)
            if self.flip_y:
                image = image.transpose(Image.FLIP_TOP_BOTTOM)

            if self.rotate:
                # rotate within the same frame (like the canvas); positive = clockwise
                image = image.convert("RGBa").rotate(-self.rotate, resample=Image.BICUBIC).convert("RGBA")

            for transform in self.transform:
                result = transform(TransformOptions(data=options.data, index=options.index, image=image))
                if result is not None:
                    image = result.convert("RGBA")

            composite(rc.image, image, round(x), round(y))
        except Exception as error:
            raise XpictError(f"Failed to render image layer ({label}): {error}") from error
