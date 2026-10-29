from enum import Enum


class TextAlign(str, Enum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class TextBaseline(str, Enum):
    TOP = "top"
    HANGING = "hanging"
    MIDDLE = "middle"
    ALPHABETIC = "alphabetic"
    IDEOGRAPHIC = "ideographic"
    BOTTOM = "bottom"


__all__ = ["TextAlign", "TextBaseline"]
