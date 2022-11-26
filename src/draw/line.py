import skia

from src.draw.abstract import Draw
from src.util.draw_skia import draw_line


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
