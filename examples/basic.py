from pathlib import Path

import xpict

HERE = Path(__file__).parent

poppins = xpict.utils.font(name="poppins", file_path=HERE / "Poppins-Bold.ttf", color="#ffffff")

template = xpict.template(
    config={"width": 1280, "height": 720, "fill": "#020817"},
    layers=[
        xpict.text(
            text=lambda ctx: f"Lap {ctx.data['number']}",
            x=640,
            y=80,
            align="center",
            baseline="middle",
            font=poppins(size=70),
        ),
        xpict.image(
            src=HERE / "dragon.png",
            x=40,
            y=420,
            height=260,
            transform=[xpict.effects.grayscale(40)],
        ),
        xpict.repeat(
            each=lambda ctx: ctx.data["nodes"],
            x=lambda ctx: 330 + (ctx.index % 2) * 450,
            y=lambda ctx: 170 + (ctx.index // 2) * 170,
            layer=lambda item, info: xpict.group(
                layers=[
                    xpict.rectangle(x=0, y=0, width=420, height=140, fill="#0F172A", border_radius=15),
                    xpict.circle(x=40, y=70, radius=22, fill="#38bdf8"),
                    xpict.text(
                        text=f"Node {item}",
                        x=80,
                        y=70,
                        baseline="middle",
                        font=poppins(size=34),
                        stroke={"fill": "#000", "width": 2},
                    ),
                    xpict.line(from_=(20, 125), to=(400, 125), color="#334155", width=3),
                ]
            ),
        ),
        xpict.text(
            text="Rotated",
            x=1150,
            y=620,
            rotation=-20,
            align="center",
            baseline="middle",
            font=poppins(size=40, color="#facc15"),
        ),
    ],
)

if __name__ == "__main__":
    template.render({"number": 7, "nodes": [1, 2, 3, 4]}).save(HERE / "output.png")
    print("saved", HERE / "output.png")
