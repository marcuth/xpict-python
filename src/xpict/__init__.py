"""Xpict: standardized image generation from declarative templates, built on Pillow."""

from . import effects, utils
from .context import LayerContext, RenderContext, TemplateSize
from .core import Template, TemplateConfig
from .enums import TextAlign, TextBaseline
from .error import XpictError
from .layers import (
    CircleLayer,
    GroupLayer,
    ImageLayer,
    Layer,
    LineLayer,
    RectangleLayer,
    RepeatInfo,
    RepeatLayer,
    Stroke,
    TextLayer,
    TransformOptions,
)
from .utils import Font, font, wrap_text

# Factories in the same style as the Node.js version: xpict.rectangle(...), xpict.text(...), ...
rectangle = RectangleLayer
circle = CircleLayer
text = TextLayer
image = ImageLayer
repeat = RepeatLayer
group = GroupLayer
line = LineLayer
template = Template

__all__ = [
    "effects",
    "utils",
    "LayerContext",
    "RenderContext",
    "TemplateSize",
    "Template",
    "TemplateConfig",
    "TextAlign",
    "TextBaseline",
    "XpictError",
    "CircleLayer",
    "GroupLayer",
    "ImageLayer",
    "Layer",
    "LineLayer",
    "RectangleLayer",
    "RepeatInfo",
    "RepeatLayer",
    "Stroke",
    "TextLayer",
    "TransformOptions",
    "Font",
    "font",
    "wrap_text",
    "rectangle",
    "circle",
    "text",
    "image",
    "repeat",
    "group",
    "line",
    "template",
]
