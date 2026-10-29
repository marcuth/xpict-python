# Xpict (Python)

**Xpict** is a [Pillow](https://python-pillow.org)-based library for building declarative templates that generate standardized images from data, whether static or dynamic. It supports conditional rendering, axes computed at runtime and dynamic text. This is the Python port of the Node.js `xpict` library.

## 📦 Installation

```bash
poetry add xpict
# or
pip install xpict
```

For development:

```bash
poetry install
poetry run pytest
```

## 🚀 Usage

```python
import xpict

poppins = xpict.utils.font(name="poppins", file_path="Poppins-Bold.ttf", color="#ffffff")

template = xpict.template(
    config={"width": 1280, "height": 720, "fill": "#020817"},  # fill is optional
    layers=[
        xpict.text(
            text=lambda ctx: f"Hello, {ctx.data['name']}!",
            x=640, y=360,
            align="center", baseline="middle",
            font=poppins(size=60),
            stroke={"width": 4, "fill": "#000000"},
        ),
    ],
)

image = template.render({"name": "World"})  # PIL.Image.Image (RGBA)
image.save("out.png")
```

Or use an image as the background: `xpict.template(image_path="bg.png", layers=[...])`.

### Dynamic values

Every axis, dimension and text accepts either a fixed value or a function that receives a `LayerContext` with `data`, `index` (useful inside `repeat`) and `template_size`:

```python
x=lambda ctx: ctx.index * 110
```

Every layer also accepts `when=lambda ctx: bool` for conditional rendering.

### Layers

| Factory | Main parameters |
| --- | --- |
| `xpict.text` | `text`, `font`, `x`, `y`, `align`, `baseline`, `stroke`, `rotation` |
| `xpict.image` | `src` (path, bytes or `PIL.Image`), `x`, `y`, `width`, `height`, `flip_x`, `flip_y`, `rotate`, `transform` |
| `xpict.rectangle` | `x`, `y`, `width`, `height`, `fill`, `border_radius` |
| `xpict.circle` | `x`, `y` (center), `radius`, `fill` |
| `xpict.line` | `from_=(x, y)`, `to=(x, y)`, `color`, `width` |
| `xpict.group` | `layers`, `x`, `y` (offset) |
| `xpict.repeat` | `each`, `layer=lambda item, info: ...` (`info.index`, `info.length`), `x`, `y` |

Colors accept hex (`#rgb`, `#rrggbb`, `#rrggbbaa`), CSS names, `rgb()`/`rgba()` and tuples.

### Transformations and effects

`transform` takes functions `(options) -> Image | None`, where `options` exposes `image`, `data` and `index`. Return a new image (or `None` if you modified it in place):

```python
xpict.image(
    src="photo.png", x=0, y=0,
    transform=[
        xpict.effects.blur(2.5),
        xpict.effects.grayscale(50),
        lambda opts: opts.image.rotate(10),
    ],
)
```

Available effects: `blur`, `box_blur`, `grayscale`.

## Differences from the Node.js version

- The API is synchronous; `render()` returns a `PIL.Image` instead of a `Canvas`.
- Dynamic functions receive a single `LayerContext` instead of a destructured object.
- `image_path` is actually drawn as the background.
- Font `weight` is accepted but has no effect; register one font file per weight instead.

## 📝 License

MIT.
