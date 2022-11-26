import skia

from src.draw.abstract import Draw
from src.util.draw_skia import draw_rect, parse_color


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
