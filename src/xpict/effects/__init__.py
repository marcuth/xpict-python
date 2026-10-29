from __future__ import annotations

from PIL import Image, ImageFilter

from ..layers.image_layer import TransformOptions


def blur(radius: float):
    """Gaussian blur (``radius`` is the standard deviation in pixels)."""

    def apply(options: TransformOptions) -> Image.Image:
        if radius <= 0:
            return options.image
        premultiplied = options.image.convert("RGBa")
        return premultiplied.filter(ImageFilter.GaussianBlur(radius)).convert("RGBA")

    return apply


def box_blur(radius: int):
    """Box blur (window of ``2 * radius + 1`` pixels)."""

    def apply(options: TransformOptions) -> Image.Image:
        r = int(radius)
        if r <= 0:
            return options.image
        premultiplied = options.image.convert("RGBa")
        return premultiplied.filter(ImageFilter.BoxBlur(r)).convert("RGBA")

    return apply


def grayscale(amount: float = 100):
    """Grayscale; ``amount`` ranges from 0 to 100 (%)."""

    def apply(options: TransformOptions) -> Image.Image:
        if amount <= 0:
            return options.image
        image = options.image
        gray = image.convert("L").convert("RGBA")
        gray.putalpha(image.getchannel("A"))
        if amount >= 100:
            return gray
        return Image.blend(image, gray, amount / 100)

    return apply


__all__ = ["blur", "box_blur", "grayscale"]
