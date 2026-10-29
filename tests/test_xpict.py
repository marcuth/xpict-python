from pathlib import Path

import pytest
from PIL import Image

import xpict

HERE = Path(__file__).parent
FONT = HERE.parent / "examples" / "Poppins-Bold.ttf"


def px(image, x, y):
    return image.getpixel((x, y))


def test_template_fill_and_size():
    img = xpict.template(config={"width": 20, "height": 10, "fill": "#ff0000"}, layers=[]).render()
    assert img.size == (20, 10)
    assert px(img, 5, 5) == (255, 0, 0, 255)


def test_template_requires_config_or_image():
    with pytest.raises(xpict.XpictError):
        xpict.template(layers=[]).render()


def test_template_image_path_background(tmp_path):
    bg = tmp_path / "bg.png"
    Image.new("RGBA", (30, 12), (0, 255, 0, 255)).save(bg)
    img = xpict.template(image_path=bg, layers=[]).render()
    assert img.size == (30, 12)
    assert px(img, 1, 1) == (0, 255, 0, 255)


def test_rectangle_and_offset_group():
    img = xpict.template(
        config={"width": 40, "height": 40},
        layers=[
            xpict.group(
                x=10,
                y=10,
                layers=[xpict.rectangle(x=0, y=0, width=10, height=10, fill="#0000ff")],
            )
        ],
    ).render()
    assert px(img, 15, 15) == (0, 0, 255, 255)
    assert px(img, 5, 5)[3] == 0


def test_rectangle_alpha_blends():
    img = xpict.template(
        config={"width": 10, "height": 10, "fill": "#ffffff"},
        layers=[xpict.rectangle(x=0, y=0, width=10, height=10, fill="rgba(0,0,0,0.5)")],
    ).render()
    assert 120 <= px(img, 5, 5)[0] <= 135


def test_border_radius_clears_corner():
    img = xpict.template(
        config={"width": 40, "height": 40},
        layers=[xpict.rectangle(x=0, y=0, width=40, height=40, fill="#fff", border_radius=15)],
    ).render()
    assert px(img, 0, 0)[3] == 0
    assert px(img, 20, 20)[3] == 255


def test_circle_and_line():
    img = xpict.template(
        config={"width": 60, "height": 60},
        layers=[
            xpict.circle(x=20, y=20, radius=10, fill="#f00"),
            xpict.line(from_=(0, 50), to=(59, 50), color="#00f", width=4),
        ],
    ).render()
    assert px(img, 20, 20) == (255, 0, 0, 255)
    assert px(img, 0, 0)[3] == 0
    assert px(img, 30, 50) == (0, 0, 255, 255)


def test_when_and_repeat_index():
    img = xpict.template(
        config={"width": 40, "height": 10},
        layers=[
            xpict.repeat(
                each=lambda ctx: ["a", "b", "c"],
                x=lambda ctx: ctx.index * 10,
                y=0,
                layer=lambda item, info: xpict.rectangle(
                    x=0, y=0, width=10, height=10, fill="#fff", when=lambda ctx: item != "b"
                ),
            ),
            xpict.rectangle(x=0, y=0, width=5, height=5, fill="#f00", when=lambda ctx: False),
        ],
    ).render()
    assert px(img, 5, 5)[3] == 255
    assert px(img, 15, 5)[3] == 0
    assert px(img, 25, 5)[3] == 255


def test_text_renders_and_rotation():
    poppins = xpict.utils.font(name="poppins-test", file_path=FONT, color="#fff")
    for rotation in (0, 90):
        img = xpict.template(
            config={"width": 200, "height": 100, "fill": "#000"},
            layers=[
                xpict.text(
                    text=lambda ctx: ctx.data,
                    x=100,
                    y=50,
                    align="center",
                    baseline="middle",
                    font=poppins(size=40),
                    stroke={"fill": "#f00", "width": 4},
                    rotation=rotation,
                )
            ],
        ).render("Hi")
        assert img.convert("RGB").getbbox() is not None
        assert px(img, 0, 0) == (0, 0, 0, 255)


def test_text_enum_and_missing_font_fallback():
    font = xpict.utils.font(name="does-not-exist")(size=20, color="#fff")
    img = xpict.template(
        config={"width": 100, "height": 40},
        layers=[
            xpict.text(
                text="x", x=50, y=20, font=font, align=xpict.TextAlign.CENTER, baseline=xpict.TextBaseline.MIDDLE
            )
        ],
    ).render()
    assert img.getchannel("A").getbbox() is not None


def test_font_missing_file():
    with pytest.raises(FileNotFoundError):
        xpict.utils.font(name="x", file_path="nope.ttf")


def test_image_layer_resize_flip_transform(tmp_path):
    src = Image.new("RGBA", (10, 10), (255, 0, 0, 255))
    src.putpixel((0, 0), (0, 255, 0, 255))
    path = tmp_path / "a.png"
    src.save(path)

    img = xpict.template(
        config={"width": 40, "height": 40},
        layers=[
            xpict.image(src=path, x=0, y=0, width=20, flip_x=True),
            xpict.image(src=lambda ctx: src, x=20, y=20, transform=[xpict.effects.grayscale()]),
        ],
    ).render()

    assert px(img, 19, 0) == (0, 255, 0, 255)  # green corner, flipped and scaled
    r, g, b, _ = px(img, 25, 25)
    assert r == g == b


def test_image_layer_error_wrapped():
    with pytest.raises(xpict.XpictError):
        xpict.template(
            config={"width": 10, "height": 10},
            layers=[xpict.image(src="missing.png", x=0, y=0)],
        ).render()


@pytest.mark.parametrize("effect", [xpict.effects.blur(2), xpict.effects.box_blur(2), xpict.effects.grayscale(50)])
def test_effects_keep_size_and_transparency(effect):
    base = Image.new("RGBA", (20, 20), (0, 0, 0, 0))
    base.paste((255, 0, 0, 255), (5, 5, 15, 15))
    out = effect(xpict.TransformOptions(data=None, index=0, image=base))
    assert out.size == (20, 20)
    assert out.getpixel((0, 0))[3] < 5
    assert out.getpixel((10, 10))[3] > 200


def test_effects_noop_for_zero():
    base = Image.new("RGBA", (4, 4), (1, 2, 3, 255))
    opts = xpict.TransformOptions(data=None, index=0, image=base)
    for effect in (xpict.effects.blur(0), xpict.effects.box_blur(0), xpict.effects.grayscale(0)):
        assert effect(opts) is base


def test_wrap_text():
    assert xpict.wrap_text("aaa bbb ccc", 7) == ["aaa ", "bbb ", "ccc "]


@pytest.mark.parametrize(
    "value,expected",
    [("#fff", (255, 255, 255, 255)), ("rgba(255,0,0,0.5)", (255, 0, 0, 128)), ("transparent", (0, 0, 0, 0))],
)
def test_parse_color(value, expected):
    from xpict.drawing import parse_color

    assert parse_color(value) == expected
    with pytest.raises(xpict.XpictError):
        parse_color("not-a-color")
