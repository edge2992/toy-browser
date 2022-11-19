import tkinter.font
import tkinter


class Draw:
    def __init__(self):
        self.top: int
        self.left: int
        self.right: int
        self.bottom: int

    def execute(self, scroll: int, canvas: tkinter.Canvas):
        raise NotImplementedError


class DrawText(Draw):
    def __init__(self, x1, y1, text, font):
        self.top = y1
        self.left = x1
        self.text = text
        self.font = font
        self.bottom = y1 + font.metrics("linespace")

    def execute(self, scroll, canvas):
        canvas.create_text(
            self.left, self.top - scroll, text=self.text, font=self.font, anchor="nw"
        )

    def __repr__(self) -> str:
        return f"DrawText({self.left}, {self.top}, {self.text})"


class DrawRect(Draw):
    def __init__(self, x1, y1, x2, y2, color):
        self.top = y1
        self.left = x1
        self.right = x2
        self.bottom = y2
        self.color = color

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
