from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Union

from PIL import Image, ImageDraw

from ..context import Dynamic, resolve
from ..drawing import Color, composite, parse_color
from ..enums import TextAlign, TextBaseline
from ..utils.fonts import Font, load_font
from .layer import Layer, RenderOptions, WhenFunction

_ANCHOR_X = {"left": "l", "center": "m", "right": "r"}
_ANCHOR_Y = {
    "top": "a",
    "hanging": "a",
    "middle": "m",
    "alphabetic": "s",
    "ideographic": "d",
    "bottom": "d",
}
_PAD = 2


@dataclass
class Stroke:
    fill: Color
    width: float


def _value(v: Union[str, TextAlign, TextBaseline]) -> str:
    return v.value if hasattr(v, "value") else str(v)


class TextLayer(Layer):
    def __init__(
        self,
        text: Union[str, Dynamic],
        font: Font,
        x: Dynamic,
        y: Dynamic,
        align: Union[str, TextAlign, None] = None,
        baseline: Union[str, TextBaseline, None] = None,
        stroke: Union[Stroke, dict, None] = None,
        rotation: float = 0,
        when: Optional[WhenFunction] = None,
    ) -> None:
        super().__init__(when)
        self.text, self.font, self.x, self.y = text, font, x, y
        self.align = _value(align) if align else "left"
        self.baseline = _value(baseline) if baseline else "alphabetic"
        self.stroke = Stroke(**stroke) if isinstance(stroke, dict) else stroke
        self.rotation = rotation

    def render(self, options: RenderOptions) -> None:
        ctx = options.layer_context()
        rc = options.context

        content = str(resolve(self.text, ctx))
        if not content:
            return

        x = rc.offset_x + resolve(self.x, ctx)
        y = rc.offset_y + resolve(self.y, ctx)

        pil_font = load_font(self.font.name, self.font.size)
        anchor = _ANCHOR_X[self.align] + _ANCHOR_Y[self.baseline]
        has_stroke = self.stroke is not None and self.stroke.width > 0
        # the canvas stroke is centered on the glyph edge; in Pillow it grows outward
        stroke_width = self.stroke.width / 2 if has_stroke else 0

        measure = ImageDraw.Draw(Image.new("L", (1, 1)))
        left, top, right, bottom = measure.textbbox(
            (0, 0), content, font=pil_font, anchor=anchor, stroke_width=stroke_width
        )

        rotated = self.rotation % 360 != 0
        if rotated:
            radius = math.ceil(math.hypot(max(-left, right), max(-top, bottom))) + _PAD
            width = height = radius * 2
            origin_x = origin_y = radius
        else:
            origin_x = math.ceil(-left) + _PAD
            origin_y = math.ceil(-top) + _PAD
            width = origin_x + math.ceil(right) + _PAD
            height = origin_y + math.ceil(bottom) + _PAD

        def mask(stroked: bool) -> Image.Image:
            layer = Image.new("L", (width, height), 0)
            ImageDraw.Draw(layer).text(
                (origin_x, origin_y),
                content,
                fill=255,
                font=pil_font,
                anchor=anchor,
                stroke_width=stroke_width if stroked else 0,
                stroke_fill=255,
            )
            if rotated:
                # on the canvas, positive angles rotate clockwise
                layer = layer.rotate(-self.rotation, resample=Image.BICUBIC, center=(origin_x, origin_y))
            return layer

        def colored(color: Color, glyphs: Image.Image) -> Image.Image:
            r, g, b, a = parse_color(color)
            layer = Image.new("RGBA", (width, height), (r, g, b, 0))
            layer.putalpha(glyphs.point(lambda v: v * a // 255))
            return layer

        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))

        if has_stroke:
            overlay.alpha_composite(colored(self.stroke.fill, mask(True)))  # type: ignore[union-attr]

        overlay.alpha_composite(colored(self.font.color or "#000", mask(False)))

        composite(rc.image, overlay, round(x) - origin_x, round(y) - origin_y)
