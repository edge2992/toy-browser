import skia

from src.util.draw_skia import draw_line, draw_rect, draw_text, linespace, parse_color


class Draw:
    def __init__(
        self,
        top: float,
        left: float,
        right: float,
        bottom: float,
        rect: skia.Rect,
        color: str,
    ):
        self.top: float = top
        self.left: float = left
        self.right: float = right
        self.bottom: float = bottom
        self.rect: skia.Rect = rect
        self.color: str = color

    def execute(self, canvas):
        raise NotImplementedError


class DrawText(Draw):
    def __init__(self, x1: float, y1: float, text: str, font: skia.Font, color: str):
        bottom = y1 + linespace(font)
        super().__init__(
            y1,
            x1,
            x1,
            bottom,
            skia.Rect.MakeLTRB(x1, y1, x1, bottom),
            color,
        )
        self.text = text
        self.font = font

    def execute(self, canvas):
        draw_text(
            canvas,
            self.left,
            self.top,
            self.text,
            self.font,
            self.color,
        )

    def __repr__(self) -> str:
        return f"DrawText({self.left}, {self.top}, {self.text})"


class DrawRect(Draw):
    def __init__(self, x1: float, y1: float, x2: float, y2: float, color: str):
        super().__init__(y1, x1, x2, y2, skia.Rect.MakeLTRB(x1, y1, x2, y2), color)

    def execute(self, canvas):
        draw_rect(
            canvas,
            self.left,
            self.top,
            self.right,
            self.bottom,
            fill=self.color,
        )

    def __repr__(self) -> str:
        return f"DrawRect({self.color})"


class DrawLine(Draw):
    def __init__(self, x1: float, y1: float, x2: float, y2: float):
        super().__init__(y1, x1, x2, y2, skia.Rect.MakeLTRB(x1, y1, x2, y2), "black")

    def execute(self, canvas):
        draw_line(
            canvas,
            self.left,
            self.top,
            self.right,
            self.bottom,
        )

    def __repr__(self) -> str:
        return f"DrawRect({self.color})"


class DrawRRect(Draw):
    def __init__(self, rect: skia.Rect, radius, color):
        self.rect = rect
        self.rrect = skia.RRect.MakeRectXY(rect, radius, radius)
        self.color = color

    def execute(self, canvas):
        sk_color = parse_color(self.color)
        canvas.drawRRect(self.rrect, paint=skia.Paint(Color=sk_color))

    def __repr__(self) -> str:
        return f"DrawRRect({self.color})"


class ClipRRect(Draw):
    def __init__(self, rect, radius, children, should_clip=True):
        self.rect = rect
        self.rrect = skia.RRect.MakeRectXY(rect, radius, radius)
        self.children = children
        self.should_clip = should_clip

    def execute(self, canvas):
        if self.should_clip:
            canvas.save()
            canvas.clipRRect(self.rrect)

        for cmd in self.children:
            cmd.execute(canvas)

        if self.should_clip:
            canvas.restore()
