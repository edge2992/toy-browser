import skia

from src.draw.abstract import Draw
from src.util.draw_skia import draw_text, linespace


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
