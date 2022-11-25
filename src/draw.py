import skia

from src.util.draw_skia import draw_line, draw_rect, draw_text


class Draw:
    def __init__(self, top: int, left: int, right: int, bottom: int, color: str):
        self.top: int = top
        self.left: int = left
        self.right: int = right
        self.bottom: int = bottom
        self.color: str = color

    def execute(self, scroll: int, canvas):
        raise NotImplementedError


class DrawText(Draw):
    def __init__(self, x1: int, y1: int, text: str, font: skia.Font, color: str):
        super().__init__(
            y1,
            x1,
            x1,
            y1 - font.getMetrics().fAscent + font.getMetrics().fDescent,
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
    def __init__(self, x1: int, y1: int, x2: int, y2: int, color: str):
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
    def __init__(self, x1: int, y1: int, x2: int, y2: int):
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
