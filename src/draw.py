import tkinter.font
import tkinter


class Draw:
    def __init__(self, top: int, left: int, right: int, bottom: int, color: str):
        self.top: int = top
        self.left: int = left
        self.right: int = right
        self.bottom: int = bottom
        self.color: str = color

    def execute(self, scroll: int, canvas: tkinter.Canvas):
        raise NotImplementedError


class DrawText(Draw):
    def __init__(
        self, x1: int, y1: int, text: str, font: tkinter.font.Font, color: str
    ):
        super().__init__(y1, x1, x1, y1 + font.metrics("linespace"), color)
        self.text = text
        self.font = font

    def execute(self, scroll, canvas):
        canvas.create_text(
            self.left,
            self.top - scroll,
            text=self.text,
            font=self.font,
            anchor="nw",
            fill=self.color,
        )

    def __repr__(self) -> str:
        return f"DrawText({self.left}, {self.top}, {self.text})"


class DrawRect(Draw):
    def __init__(self, x1: int, y1: int, x2: int, y2: int, color: str):
        super().__init__(y1, x1, x2, y2, color)

    def execute(self, scroll, canvas):
        canvas.create_rectangle(
            self.left,
            self.top - scroll,
            self.right,
            self.bottom - scroll,
            width=0,
            fill=self.color,
        )

    def __repr__(self) -> str:
        return f"DrawRect({self.color})"
