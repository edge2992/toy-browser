from __future__ import annotations

from typing import TYPE_CHECKING, List, Union

from src.draw import DrawText
from src.global_value import FONT_RATIO
from src.layout.abstract import LayoutObject

if TYPE_CHECKING:
    import tkinter.font

    from src.draw import Draw
    from src.layout.input import InputLayout
    from src.layout.line import LineLayout
    from src.text import HTMLNode


class TextLayout(
    LayoutObject["LineLayout", Union["TextLayout", "InputLayout", None], LayoutObject]
):
    def __init__(
        self,
        node: HTMLNode,
        word: str,
        parent: "LineLayout",
        previous: Union[TextLayout, InputLayout, None],
        font_ratio: float = FONT_RATIO,
    ):
        super().__init__(node, parent, previous, font_ratio)
        self.word = word
        self.font: tkinter.font.Font

    def layout(self):
        self.font = self.get_font(self.node)
        self.width = self.font.measure(self.word)
        if self.previous:
            space = self.previous.font.measure(" ")
            self.x = self.previous.x + space + self.previous.width
        else:
            self.x = self.parent.x

        self.height = self.font.metrics("linespace")

    def paint(self, display_list: List[Draw]) -> None:
        color = self.node.style["color"]
        display_list.append(DrawText(self.x, self.y, self.word, self.font, color))

    def __repr__(self) -> str:
        return ("TextLayout(x={}, y={}, width={}, height={}, node={}, word={})").format(
            self.x, self.y, self.width, self.height, self.node, self.word
        )
