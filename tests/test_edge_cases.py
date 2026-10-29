import io

import pytest
from PIL import Image

import xpict
from xpict.drawing import composite, fill_circle, fill_rectangle, parse_color, stroke_line


def blank(w=20, h=20):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def render(layers, w=20, h=20, data=None):
    return xpict.template(config={"width": w, "height": h}, layers=layers).render(data)


def opaque_bbox(img):
    return img.getchannel("A").getbbox()


# --- color parsing -----------------------------------------------------------


def test_parse_color_tuples():
    assert parse_color((1, 2, 3)) == (1, 2, 3, 255)
    assert parse_color([1, 2, 3, 4]) == (1, 2, 3, 4)


def test_parse_color_invalid_tuple_length():
    with pytest.raises(xpict.XpictError):
        parse_color((1, 2))


def test_parse_color_rgb_and_percent_alpha():
    assert parse_color("rgb(10, 20, 30)") == (10, 20, 30, 255)
    assert parse_color("rgba(10 20 30 / 50%)") == (10, 20, 30, 128)


@pytest.mark.parametrize("value", ["rgb(1, 2)", "rgba(a, b, c)", "rgb(1,2,3,4,5)"])
def test_parse_color_invalid_rgb(value):
    with pytest.raises(xpict.XpictError):
        parse_color(value)


# --- compositing and shapes outside the canvas -------------------------------


def test_composite_fully_outside_is_noop():
    canvas = blank()
    composite(canvas, Image.new("RGBA", (5, 5), (255, 0, 0, 255)), 100, 100)
    composite(canvas, Image.new("RGBA", (5, 5), (255, 0, 0, 255)), -50, 0)
    assert opaque_bbox(canvas) is None


def test_composite_is_cropped_at_edges():
    canvas = blank()
    composite(canvas, Image.new("RGBA", (10, 10), (255, 0, 0, 255)), -5, 15)
    assert opaque_bbox(canvas) == (0, 15, 5, 20)


def test_fully_transparent_shape_is_skipped():
    canvas = blank()
    fill_rectangle(canvas, 0, 0, 10, 10, "rgba(255,0,0,0)")
    assert opaque_bbox(canvas) is None


def test_shapes_outside_canvas_are_skipped():
    canvas = blank()
    fill_rectangle(canvas, 100, 100, 10, 10, "#f00")
    fill_circle(canvas, -50, -50, 5, "#f00")
    stroke_line(canvas, 100, 100, 120, 120, 2, "#f00")
    assert opaque_bbox(canvas) is None


def test_degenerate_shapes_are_skipped():
    canvas = blank()
    fill_rectangle(canvas, 0, 0, 0, 10, "#f00")
    fill_rectangle(canvas, 0, 0, 10, -1, "#f00")
    fill_circle(canvas, 10, 10, 0, "#f00")
    stroke_line(canvas, 0, 0, 10, 10, 0, "#f00")
    assert opaque_bbox(canvas) is None


def test_zero_length_line_draws_a_dot():
    canvas = blank()
    stroke_line(canvas, 10, 10, 10, 10, 6, "#f00")
    assert canvas.getpixel((10, 10)) == (255, 0, 0, 255)


# --- image layer -------------------------------------------------------------


def png_bytes(size=(10, 10), color=(255, 0, 0, 255)):
    buffer = io.BytesIO()
    Image.new("RGBA", size, color).save(buffer, format="PNG")
    return buffer.getvalue()


def test_image_from_bytes():
    img = render([xpict.image(src=png_bytes(), x=0, y=0)])
    assert opaque_bbox(img) == (0, 0, 10, 10)


def test_image_width_only_keeps_aspect_ratio():
    img = render([xpict.image(src=png_bytes((10, 20)), x=0, y=0, width=5)], 20, 30)
    assert opaque_bbox(img) == (0, 0, 5, 10)


def test_image_height_only_keeps_aspect_ratio():
    img = render([xpict.image(src=png_bytes((20, 10)), x=0, y=0, height=5)], 30, 20)
    assert opaque_bbox(img) == (0, 0, 10, 5)


def test_image_flip_y():
    src = Image.new("RGBA", (4, 4), (255, 0, 0, 255))
    src.putpixel((0, 0), (0, 255, 0, 255))
    img = render([xpict.image(src=src, x=0, y=0, flip_y=True)], 4, 4)
    assert img.getpixel((0, 3)) == (0, 255, 0, 255)
    assert img.getpixel((0, 0)) == (255, 0, 0, 255)


def test_image_rotate_clips_to_original_frame():
    src = Image.new("RGBA", (10, 10), (255, 0, 0, 255))
    img = render([xpict.image(src=src, x=0, y=0, rotate=45)], 10, 10)
    assert img.getpixel((5, 5)) == (255, 0, 0, 255)  # center stays filled
    assert img.getpixel((0, 0))[3] == 0  # corner rotated out of the frame


def test_image_transform_in_place_returning_none():
    def paint(options):
        options.image.putpixel((0, 0), (0, 0, 255, 255))

    src = Image.new("RGBA", (4, 4), (255, 0, 0, 255))
    img = render([xpict.image(src=src, x=0, y=0, transform=[paint])], 4, 4)
    assert img.getpixel((0, 0)) == (0, 0, 255, 255)


def test_image_error_for_non_path_source_names_the_type():
    with pytest.raises(xpict.XpictError, match="bytes"):
        render([xpict.image(src=b"not an image", x=0, y=0)])


# --- template ----------------------------------------------------------------


def test_template_background_image_missing(tmp_path):
    with pytest.raises(xpict.XpictError, match="background"):
        xpict.template(image_path=tmp_path / "missing.png", layers=[]).render()


def test_template_config_dataclass():
    config = xpict.TemplateConfig(width=8, height=4, fill="#fff")
    assert xpict.template(config=config, layers=[]).render().size == (8, 4)


# --- text and repeat ---------------------------------------------------------


def test_empty_text_renders_nothing():
    font = xpict.utils.font(name="empty-text")(size=20, color="#fff")
    img = render([xpict.text(text="", x=5, y=5, font=font)])
    assert opaque_bbox(img) is None


def test_stroke_dataclass_and_default_text_color():
    font = xpict.utils.font(name="default-color")(size=20)
    img = render(
        [xpict.text(text="A", x=10, y=15, font=font, stroke=xpict.Stroke(fill="#f00", width=2))],
        30,
        30,
    )
    assert opaque_bbox(img) is not None


@pytest.mark.parametrize("items", [[], None])
def test_repeat_with_no_items_renders_nothing(items):
    img = render(
        [
            xpict.repeat(
                each=lambda ctx: items,
                layer=lambda item, info: xpict.rectangle(x=0, y=0, width=5, height=5, fill="#f00"),
            )
        ]
    )
    assert opaque_bbox(img) is None


def test_repeat_info_and_nested_group_offsets():
    seen = []

    def build(item, info):
        seen.append((item, info.index, info.length))
        return xpict.group(
            x=1,
            layers=[xpict.rectangle(x=0, y=0, width=1, height=1, fill="#f00")],
        )

    img = render(
        [
            xpict.group(
                x=2,
                y=2,
                layers=[xpict.repeat(each=lambda ctx: ["a", "b"], x=lambda ctx: ctx.index * 5, layer=build)],
            )
        ]
    )
    assert seen == [("a", 0, 2), ("b", 1, 2)]
    assert img.getpixel((3, 2)) == (255, 0, 0, 255)
    assert img.getpixel((8, 2)) == (255, 0, 0, 255)


def test_image_width_and_height_resize_exactly():
    img = render([xpict.image(src=png_bytes((10, 10)), x=0, y=0, width=8, height=4)])
    assert opaque_bbox(img) == (0, 0, 8, 4)
