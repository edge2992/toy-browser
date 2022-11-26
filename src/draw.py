import skia

from src.util.draw_skia import draw_line, draw_rect, draw_text, linespace, parse_color


class Draw:
    def __init__(
        self, top: float, left: float, right: float, bottom: float, color: str
    ):
        self.top: float = top
        self.left: float = left
        self.right: float = right
        self.bottom: float = bottom
        self.color: str = color

    def execute(self, scroll: float, canvas):
        raise NotImplementedError


class DrawText(Draw):
    def __init__(self, x1: float, y1: float, text: str, font: skia.Font, color: str):
        super().__init__(
            y1,
            x1,
            x1,
            y1 + linespace(font),
            color,
        )
        self.rect = skia.Rect.MakeLTRB(x1, y1, self.right, self.bottom)
        self.text = text
        self.font = font

    def execute(self, scroll, canvas):
        draw_text(
            canvas,
            self.left,
            self.top - scroll,
            self.text,
            self.font,
            self.color,
        )

    def __repr__(self) -> str:
        return f"DrawText({self.left}, {self.top}, {self.text})"


class DrawRect(Draw):
    def __init__(self, x1: float, y1: float, x2: float, y2: float, color: str):
        super().__init__(y1, x1, x2, y2, color)
        self.rect = skia.Rect.MakeLTRB(x1, y1, x2, y2)

    def execute(self, scroll, canvas):
        draw_rect(
            canvas,
            self.left,
            self.top - scroll,
            self.right,
            self.bottom - scroll,
            fill=self.color,
        )

    def __repr__(self) -> str:
        return f"DrawRect({self.color})"


class DrawLine(Draw):
    def __init__(self, x1: float, y1: float, x2: float, y2: float):
        super().__init__(y1, x1, x2, y2, "black")
        self.rect = skia.Rect.MakeLTRB(x1, y1, x2, y2)

    def execute(self, scroll, canvas):
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
        super().__init__(rect.top(), rect.left(), rect.right(), rect.bottom(), color)
        self.rect = rect
        self.rrect = skia.RRect.MakeRectXY(rect, radius, radius)
        self.color = color

    def execute(self, scroll, canvas):
        sk_color = parse_color(self.color)
        canvas.drawRRect(self.rrect, paint=skia.Paint(Color=sk_color))

    def __repr__(self) -> str:
        return f"DrawRRect(top={self.top}, left={self.left}, right={self.right}, bottom={self.bottom}, color={self.color})"
