from __future__ import annotations

from typing import TYPE_CHECKING, List, Union

from src.draw import DrawRect, DrawText
from src.global_value import FONT_RATIO, INPUT_WIDTH_PX
from src.layout.abstract import LayoutObject
from src.layout.line import LineLayout
from src.text import Element, Text

if TYPE_CHECKING:
    import tkinter.font

    from src.draw import Draw
    from src.layout.text import TextLayout
    from src.text import HTMLNode


class InputLayout(
    LayoutObject[
        LineLayout,
        Union["TextLayout", "InputLayout", None],
        Union["TextLayout", "InputLayout"],
    ]
):
    def __init__(
        self,
        node: HTMLNode,
        parent: LineLayout,
        previous: Union[TextLayout, "InputLayout", None],
        font_ratio: float = FONT_RATIO,
    ):
        super().__init__(node, parent, previous, font_ratio)
        # self.word = word
        self.font: tkinter.font.Font

    def layout(self):
        self.font = self.get_font(self.node)

        self.width = INPUT_WIDTH_PX
        if self.previous:
            space = self.previous.font.measure(" ")
            self.x = self.previous.x + space + self.previous.width
        else:
            self.x = self.parent.x

        self.height = self.font.metrics("linespace")

    def paint(self, display_list: List[Draw]) -> None:
        bgcolor = self.node.style.get("background-color", "transparent")
        if bgcolor != "transparent":
            x2, y2 = self.x + self.width, self.y + self.height
            rect = DrawRect(self.x, self.y, x2, y2, bgcolor)
            display_list.append(rect)

        assert isinstance(self.node, Element)

        if self.node.tag == "input":
            text = self.node.attributes.get("value", "")
        elif self.node.tag == "button":
            assert isinstance(self.node.children[0], Text)
            text = self.node.children[0].text
        else:
            raise ValueError("Invalid tag for InputLayout")

        color = self.node.style["color"]
        display_list.append(DrawText(self.x, self.y, text, self.font, color))

        color = self.node.style["color"]
        display_list.append(DrawText(self.x, self.y, text, self.font, color))

    def __repr__(self) -> str:
        return ("InputLayout(x={}, y={}, width={}, height={}, node={})").format(
            self.x, self.y, self.width, self.height, self.node
        )
