# Xpict (Python)

**Xpict** is a [Pillow](https://python-pillow.org)-based library for building declarative templates that generate standardized images from data, whether static or dynamic. It supports conditional rendering, axes computed at runtime and dynamic text. This is the Python port of the Node.js `xpict` library.

## Contents

- [Installation](#-installation)
- [Quick start](#-quick-start)
- [How it works](#how-it-works)
- [Template](#template)
- [Dynamic values and `when`](#dynamic-values-and-when)
- [Layers](#layers)
  - [Text](#text) · [Image](#image) · [Rectangle](#rectangle) · [Circle](#circle) · [Line](#line) · [Group](#group) · [Repeat](#repeat)
- [Fonts](#fonts)
- [Colors](#colors)
- [Transformations and effects](#transformations-and-effects)
- [Custom layers](#custom-layers)
- [Errors](#errors)
- [Development](#development)
- [Differences from the Node.js version](#differences-from-the-nodejs-version)

## 📦 Installation

```bash
poetry add xpict
# or
pip install xpict
```

Requires Python 3.9+ and Pillow 11.2+ (with FreeType support, which the official wheels include).

## 🚀 Quick start

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

A template is built once and can be rendered any number of times with different data.

## How it works

1. **A template is a list of layers.** `template.render(data)` creates an RGBA canvas and draws each layer on top of the previous ones, in list order (later layers cover earlier ones).
2. **Layers are plain Python objects.** `xpict.text(...)`, `xpict.rectangle(...)` and friends are just aliases for the layer classes (`TextLayer`, `RectangleLayer`, ...), so `xpict.rectangle(...)` and `xpict.RectangleLayer(...)` are the same thing. Use whichever reads better.
3. **Almost every value can be a function.** Wherever a layer takes a coordinate, size or text, you can pass a fixed value or a function of a `LayerContext`. The function is evaluated at render time, so one template adapts to any data.
4. **Coordinates are relative to a moving origin.** The origin is `(0, 0)` at the top-left of the canvas. `group` and `repeat` shift the origin for the layers inside them (see [Group](#group)). `x` grows to the right and `y` grows downward.
5. **The result is a regular `PIL.Image.Image`** in `RGBA` mode, so you can keep processing it with Pillow, or call `.save()`, `.convert("RGB")`, etc.

Shapes (rectangles, circles, lines) are drawn with 4x supersampling for smooth edges, and every color is alpha-blended with what is already on the canvas, so semi-transparent fills behave as expected.

## Template

`xpict.template(...)` (alias of `xpict.Template`) takes `layers` plus **one** of two ways to define the canvas.

**Using `config` (width, height and optional fill):**

```python
xpict.template(
    config={"width": 1280, "height": 720, "fill": "#020817"},
    layers=[...],
)
```

`config` may be a dict or an `xpict.TemplateConfig(width, height, fill=None)`. Without `fill`, the canvas starts fully transparent.

**Using an image as the background:**

```python
xpict.template(image_path="path/to/background.png", layers=[...])
```

The canvas takes the size of the image, the image is drawn first, and the layers are drawn over it. The file is read on every `render()` call.

`render(data=None)` returns a **new** image each time. `data` can be anything (a dict, a dataclass, a pydantic model...); Xpict never inspects it, it only hands it to your functions.

If neither `config` nor `image_path` is given, `render()` raises `XpictError`.

## Dynamic values and `when`

Every dynamic value is a function that receives one argument, a `LayerContext`:

| Attribute | Meaning |
| --- | --- |
| `ctx.data` | The object passed to `template.render(data)`. |
| `ctx.index` | `0` at the top level. Inside a [`repeat`](#repeat), the index of the current item. |
| `ctx.template_size` | A `TemplateSize` with `.width` and `.height` of the canvas (handy for centering). |

```python
x=lambda ctx: ctx.index * 110
y=lambda ctx: ctx.template_size.height - 40
text=lambda ctx: ctx.data["title"].upper()
```

The parameters that accept a value *or* a function are: `x`, `y`, `width`, `height` (rectangles and images), line coordinates and `width`, `text`, the image `src`, the `x`/`y` of `group` and `repeat`.

Every layer also accepts `when`, a function returning a boolean. If it is omitted the layer always renders; if it returns falsy the layer (and, for groups, everything inside it) is skipped:

```python
xpict.text(..., when=lambda ctx: ctx.data.get("subtitle"))
```

`when` is evaluated with the same `ctx` the layer would receive, so inside a `repeat` it can depend on `ctx.index`.

## Layers

### Text

```python
xpict.text(
    text="Hello World",            # str or function
    font=poppins(size=60),         # see Fonts
    x=640, y=360,
    align="center",                # optional: left (default) | center | right
    baseline="middle",             # optional: top | hanging | middle | alphabetic (default) | ideographic | bottom
    stroke={"width": 4, "fill": "#000000"},   # optional
    rotation=-20,                  # optional, degrees
)
```

- `(x, y)` is the **anchor point** of the text, interpreted through `align` and `baseline`. With `align="center", baseline="middle"` it is the center of the text.
- `align` and `baseline` accept plain strings or the `xpict.TextAlign` / `xpict.TextBaseline` enums.
- `stroke` draws an outline *behind* the fill. `width` is the full line width as on an HTML canvas (the outline extends `width / 2` outside the glyph). Accepts a dict or `xpict.Stroke(fill=..., width=...)`.
- `rotation` is in degrees, **clockwise** for positive values, around the anchor point.
- Text color comes from the font (`font(size=..., color=...)`); it defaults to black.
- An empty string renders nothing.
- Text is drawn on a single line; use `xpict.wrap_text(text, max_chars)` to split a long string into lines and render each one with its own layer (for example inside a `repeat`).

`wrap_text(text, max_width)` splits on spaces and returns a list of lines of roughly `max_width` characters (it counts characters, not pixels). Each returned line keeps a trailing space.

### Image

```python
xpict.image(
    src="path/to/image.png",       # path, bytes, PIL.Image, or a function returning one of them
    x=0, y=0,
    width=200,                     # optional
    height=100,                    # optional
    flip_x=False, flip_y=False,    # optional
    rotate=45,                     # optional, degrees clockwise
    transform=[...],               # optional, see "Transformations and effects"
)
```

- **Sizing:** with both `width` and `height` the image is resized to exactly that size. With only one, the other is computed to keep the aspect ratio. With neither, the original size is used. Resizing uses Lanczos resampling.
- **Order of operations:** load → resize → flips → rotation → `transform` functions → composite onto the canvas at `(x, y)`.
- **Rotation** happens inside the image's own frame (like the Node version): the image is rotated around its center and **not** enlarged, so corners that leave the frame are clipped.
- Transparency in the source is preserved.
- A dynamic `src` lets one template show a different image per render or per `repeat` item:

  ```python
  src=lambda ctx: ctx.data["avatar_path"]
  ```

### Rectangle

```python
xpict.rectangle(x=0, y=0, width=150, height=50, fill="#ffffff", border_radius=5)
```

`(x, y)` is the top-left corner. `border_radius` is optional and is clamped to half of the smaller side, so a large value produces a pill shape instead of an artifact.

### Circle

```python
xpict.circle(x=100, y=100, radius=50, fill="#ffffff")
```

`(x, y)` is the **center** of the circle.

### Line

```python
xpict.line(from_=(0, 0), to=(0, 50), color="#ffffff", width=1)
```

The start point parameter is named `from_` because `from` is a Python keyword. The points are `(x, y)` tuples whose members can also be functions. Lines have round caps.

### Group

Groups layers that share a coordinate system, and optionally offsets all of them:

```python
xpict.group(
    x=50, y=50,
    layers=[
        xpict.rectangle(x=0, y=0, width=200, height=80, fill="#0F172A"),
        xpict.text(text="Card", x=10, y=40, font=poppins(size=24)),   # drawn at (60, 90)
    ],
)
```

The group's `x`/`y` are **added** to the current origin while its children render, then restored. Groups can be nested, and the offsets accumulate. A group's `when` skips all of its children; each child's own `when` is also respected.

### Repeat

Generates one layer per item of a list, which is the way to handle variable-length data:

```python
xpict.repeat(
    each=lambda ctx: ctx.data["images"],              # returns a list
    x=lambda ctx: ctx.index * 50,                     # offset for item `ctx.index`
    y=lambda ctx: ctx.index * 50,
    layer=lambda item, info: xpict.image(             # returns ONE layer for this item
        src=item, x=0, y=0,
    ),
)
```

- `each(ctx)` returns the list of items. An empty list (or `None`) renders nothing.
- For every item, the origin is shifted by `(x, y)` (evaluated with `ctx.index` set to the item's index), then `layer(item, info)` is called. `info.index` and `info.length` are the item's position and the list size. The layer is rendered and the origin is restored.
- Inside the produced layer, `ctx.index` is the item's index. Return an `xpict.group(...)` to render several layers per item.
- Use `info.length` to special-case, for example, the last item.

## Fonts

```python
poppins = xpict.utils.font(
    name="poppins",
    file_path="Poppins-Bold.ttf",   # optional
    color="#ffffff",                # optional default color
)

poppins(size=60)                    # -> Font(size=60, name="poppins", color="#ffffff")
poppins(size=60, color="#facc15")   # override the color for this use
```

- `font(...)` registers `name` → `file_path` in a global registry (re-registering a name replaces it) and returns a factory. Call the factory with `size` (required) and optionally `color`/`weight` to get a `Font` to pass to `xpict.text(font=...)`.
- If `file_path` does not exist, `FileNotFoundError` is raised immediately.
- If a name is not registered, Xpict tries to find a system font with that name (`name` and `name.ttf`, using Pillow's font lookup), and finally falls back to Pillow's built-in font so text always renders.
- Loaded fonts are cached per `(name, size)`.
- `weight` is stored on the `Font` but does not change the rendering. To use several weights, register one file per weight under different names (`poppins-bold`, `poppins-light`, ...).

## Colors

Anywhere a color is expected (`fill`, `color`, `stroke.fill`, template `fill`) you can use:

- Hex: `#rgb`, `#rrggbb`, `#rrggbbaa`
- CSS names: `"red"`, `"rebeccapurple"`, ... and `"transparent"`
- `rgb(255, 0, 0)` / `rgba(255, 0, 0, 0.5)` (alpha from 0 to 1, or a percentage)
- Tuples: `(r, g, b)` or `(r, g, b, a)` with 0-255 values

An invalid color raises `XpictError`.

## Transformations and effects

The image layer's `transform` is a list of functions applied in order after the image has been resized, flipped and rotated. Each one receives a `TransformOptions` with:

| Attribute | Meaning |
| --- | --- |
| `options.image` | The current `PIL.Image` (RGBA), at its final size. |
| `options.data` | The data passed to `render()`. |
| `options.index` | The current index (see `repeat`). |

A transform may **return a new image** (which replaces the current one) or return `None` after modifying `options.image` in place:

```python
from PIL import ImageEnhance

def brighten(options):
    return ImageEnhance.Brightness(options.image).enhance(1.4)

xpict.image(
    src="photo.png", x=0, y=0,
    transform=[
        xpict.effects.blur(2.5),
        xpict.effects.grayscale(50),
        brighten,
        lambda opts: opts.image.rotate(10),
    ],
)
```

Built-in effects (available as `xpict.effects.*`). They are alpha-aware, so transparent regions do not bleed dark halos into the image:

| Effect | Description |
| --- | --- |
| `blur(radius)` | Gaussian blur; `radius` is the standard deviation in pixels. `radius <= 0` does nothing. |
| `box_blur(radius)` | Box blur using a window of `2 * radius + 1` pixels; `radius` is truncated to an integer. `radius <= 0` does nothing. |
| `grayscale(amount=100)` | Desaturates the image; `amount` is a percentage from 0 (unchanged) to 100 (fully gray). |

## Custom layers

Subclass `xpict.Layer`, implement `render(options)` and draw on `options.context.image` (a `PIL.Image`). Add `options.context.offset_x` / `offset_y` to your coordinates so your layer cooperates with `group` and `repeat`:

```python
from PIL import ImageDraw
import xpict
from xpict.context import resolve
from xpict.layers import RenderOptions


class DotLayer(xpict.Layer):
    def __init__(self, x, y, when=None):
        super().__init__(when)
        self.x, self.y = x, y

    def render(self, options: RenderOptions) -> None:
        ctx = options.layer_context()
        rc = options.context
        x = rc.offset_x + resolve(self.x, ctx)
        y = rc.offset_y + resolve(self.y, ctx)
        ImageDraw.Draw(rc.image).point((x, y), fill="white")
```

`resolve(value, ctx)` returns `value(ctx)` for callables and the value itself otherwise. `Layer.should_render(ctx)` (which evaluates `when`) is called by the template, group and repeat before `render`, so you do not need to call it yourself.

## Errors

All Xpict failures raise `xpict.XpictError`:

- Missing `config`/`image_path` on a template.
- A background image that cannot be loaded.
- An invalid color.
- Any failure while rendering an image layer (missing file, unsupported format, an exception inside a `transform`...). The message includes the image path, and the original exception is chained (`__cause__`).

A missing font file raises `FileNotFoundError` when you call `font(...)`.

## Development

```bash
poetry install
poetry run pytest
poetry run python examples/basic.py   # writes examples/output.png
```

Project layout:

```
src/xpict/
  __init__.py     public API and factory aliases
  core.py         Template, TemplateConfig
  context.py      LayerContext, RenderContext, resolve()
  drawing.py      color parsing, supersampled shapes, safe compositing
  layers/         one module per layer
  effects/        blur, box_blur, grayscale
  utils/          font registry, wrap_text
```

## Differences from the Node.js version

- The API is synchronous; `render()` returns a `PIL.Image` instead of a `Canvas`.
- Dynamic functions receive a single `LayerContext` instead of a destructured object, and options use `snake_case` (`border_radius`, `flip_x`, `from_`, ...).
- `image_path` is actually drawn as the background.
- Image transforms operate on a `PIL.Image` (returned or modified in place) instead of a canvas context.
- Font `weight` is accepted but has no effect; register one font file per weight instead.
- Text `baseline` values map to Pillow's text anchors, so vertical placement can differ from the canvas by a few pixels.
- `when` is evaluated with the real `index` inside `group` and `repeat`, including for the layers a `repeat` produces.

## 📝 License

MIT.
