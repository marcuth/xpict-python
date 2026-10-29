"""Anti-aliased (supersampled) drawing primitives on top of Pillow."""

from __future__ import annotations

import math
import re
from typing import Callable, Tuple, Union

from PIL import Image, ImageColor, ImageDraw

from .error import XpictError

RGBA = Tuple[int, int, int, int]
Color = Union[str, Tuple[int, ...]]

SUPERSAMPLE = 4

_RGBA_RE = re.compile(r"^rgba?\(\s*([^)]*)\)$", re.IGNORECASE)


def parse_color(value: Color) -> RGBA:
    """Convert a CSS color (hex, name, rgb()/rgba()) or a tuple to RGBA."""
    if isinstance(value, (tuple, list)):
        if len(value) == 3:
            return (int(value[0]), int(value[1]), int(value[2]), 255)
        if len(value) == 4:
            return (int(value[0]), int(value[1]), int(value[2]), int(value[3]))
        raise XpictError(f"Invalid color: {value!r}")

    text = str(value).strip()

    if text.lower() == "transparent":
        return (0, 0, 0, 0)

    match = _RGBA_RE.match(text)
    if match:
        parts = [p.strip() for p in re.split(r"[,\s/]+", match.group(1).strip()) if p.strip()]
        try:
            if len(parts) not in (3, 4):
                raise ValueError
            r, g, b = (max(0, min(255, round(float(p)))) for p in parts[:3])
            a = 255
            if len(parts) == 4:
                raw = parts[3]
                alpha = float(raw[:-1]) / 100 if raw.endswith("%") else float(raw)
                a = max(0, min(255, round(alpha * 255)))
            return (r, g, b, a)
        except ValueError:
            raise XpictError(f"Invalid color: {value!r}") from None

    try:
        return ImageColor.getcolor(text, "RGBA")  # type: ignore[return-value]
    except ValueError:
        raise XpictError(f"Invalid color: {value!r}") from None


def composite(canvas: Image.Image, overlay: Image.Image, x: int, y: int) -> None:
    """``alpha_composite`` that tolerates positions outside the canvas bounds."""
    left = max(0, x)
    top = max(0, y)
    right = min(canvas.width, x + overlay.width)
    bottom = min(canvas.height, y + overlay.height)

    if left >= right or top >= bottom:
        return

    if (left, top, right, bottom) != (x, y, x + overlay.width, y + overlay.height):
        overlay = overlay.crop((left - x, top - y, right - x, bottom - y))

    canvas.alpha_composite(overlay, (left, top))


Painter = Callable[[ImageDraw.ImageDraw, Callable[[float, float], Tuple[float, float]]], None]


def paint_shape(
    canvas: Image.Image,
    bounds: Tuple[float, float, float, float],
    color: Color,
    painter: Painter,
) -> None:
    """Paint an anti-aliased shape.

    ``painter(draw, to_ss)`` draws onto an enlarged mask; ``to_ss`` converts
    canvas coordinates to mask coordinates.
    """
    r, g, b, a = parse_color(color)
    if a == 0:
        return

    left = max(0, math.floor(bounds[0]) - 1)
    top = max(0, math.floor(bounds[1]) - 1)
    right = min(canvas.width, math.ceil(bounds[2]) + 1)
    bottom = min(canvas.height, math.ceil(bounds[3]) + 1)

    if left >= right or top >= bottom:
        return

    width, height = right - left, bottom - top
    mask = Image.new("L", (width * SUPERSAMPLE, height * SUPERSAMPLE), 0)

    def to_ss(px: float, py: float) -> Tuple[float, float]:
        return (px - left) * SUPERSAMPLE, (py - top) * SUPERSAMPLE

    painter(ImageDraw.Draw(mask), to_ss)

    mask = mask.resize((width, height), Image.BOX)
    if a < 255:
        mask = mask.point(lambda v: v * a // 255)

    overlay = Image.new("RGBA", (width, height), (r, g, b, 0))
    overlay.putalpha(mask)
    canvas.alpha_composite(overlay, (left, top))


def fill_rectangle(
    canvas: Image.Image, x: float, y: float, width: float, height: float, color: Color, radius: float = 0
) -> None:
    if width <= 0 or height <= 0:
        return

    def painter(draw: ImageDraw.ImageDraw, to_ss) -> None:
        x0, y0 = to_ss(x, y)
        x1, y1 = to_ss(x + width, y + height)
        box = (x0, y0, x1 - 1, y1 - 1)
        if radius > 0:
            draw.rounded_rectangle(box, radius=radius * SUPERSAMPLE, fill=255)
        else:
            draw.rectangle(box, fill=255)

    paint_shape(canvas, (x, y, x + width, y + height), color, painter)


def fill_circle(canvas: Image.Image, cx: float, cy: float, radius: float, color: Color) -> None:
    if radius <= 0:
        return

    def painter(draw: ImageDraw.ImageDraw, to_ss) -> None:
        x0, y0 = to_ss(cx - radius, cy - radius)
        x1, y1 = to_ss(cx + radius, cy + radius)
        draw.ellipse((x0, y0, x1 - 1, y1 - 1), fill=255)

    paint_shape(canvas, (cx - radius, cy - radius, cx + radius, cy + radius), color, painter)


def stroke_line(
    canvas: Image.Image, x1: float, y1: float, x2: float, y2: float, width: float, color: Color
) -> None:
    """Line with round caps (equivalent to canvas ``lineCap = "round"``)."""
    if width <= 0:
        return

    half = width / 2

    def painter(draw: ImageDraw.ImageDraw, to_ss) -> None:
        dx, dy = x2 - x1, y2 - y1
        length = math.hypot(dx, dy)

        if length > 0:
            nx, ny = -dy / length * half, dx / length * half
            draw.polygon(
                [
                    to_ss(x1 + nx, y1 + ny),
                    to_ss(x2 + nx, y2 + ny),
                    to_ss(x2 - nx, y2 - ny),
                    to_ss(x1 - nx, y1 - ny),
                ],
                fill=255,
            )

        for cx, cy in ((x1, y1), (x2, y2)):
            ex0, ey0 = to_ss(cx - half, cy - half)
            ex1, ey1 = to_ss(cx + half, cy + half)
            draw.ellipse((ex0, ey0, ex1 - 1, ey1 - 1), fill=255)

    paint_shape(
        canvas,
        (min(x1, x2) - half, min(y1, y2) - half, max(x1, x2) + half, max(y1, y2) + half),
        color,
        painter,
    )
