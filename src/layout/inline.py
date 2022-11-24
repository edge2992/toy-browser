from __future__ import annotations

from typing import TYPE_CHECKING, List, Union

from src.draw import DrawRect
from src.global_value import FONT_RATIO, HSTEP, INPUT_WIDTH_PX

from src.layout.abstract import LayoutObject
from src.layout.input import InputLayout
from src.layout.line import LineLayout
from src.layout.text import TextLayout
from src.text import Element, Text

if TYPE_CHECKING:
    from src.draw import Draw
    from src.text import HTMLNode
    from src.layout.abstract_child import ChildLayoutObject


class InlineLayout(LayoutObject[LayoutObject, Union[LayoutObject, None], "LineLayout"]):
    def __init__(
        self,
        node: HTMLNode,
        parent: LayoutObject,
        previous: Union[LayoutObject, None],
        font_ratio: float = FONT_RATIO,
    ):
        super().__init__(node, parent, previous, font_ratio)
        self.previous_word: Union[ChildLayoutObject, None] = None

    def layout(self):
        self.width = self.parent.width
        self.x = self.parent.x

        if self.previous:
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y

        self.new_line()
        self.recurse(self.node)

        for line in self.children:
            line.layout()

        self.height = sum([line.height for line in self.children])

    def recurse(self, node: HTMLNode):
        if isinstance(node, Text):
            self.text(node)
        elif isinstance(node, Element):
            if node.tag == "br":
                self.new_line()
            elif node.tag == "input" or node.tag == "button":
                self.input(node)
            else:
                for child in node.children:
                    self.recurse(child)
        else:
            raise ValueError("Unknown node type")

    def text(self, node: Text) -> None:
        font = self.get_font(node)

        for word in node.text.split():
            w = font.measure(word)
            if self.cursor_x + w > self.width - HSTEP:
                self.new_line()
            line = self.children[-1]
            assert isinstance(line, LineLayout)
            text = TextLayout(node, word, line, self.previous_word, self.font_ratio)
            line.children.append(text)
            self.previous_word = text
            self.cursor_x += w + font.measure(" ")

    def new_line(self):
        self.previous_word = None
        self.cursor_x = self.x
        last_line = self.children[-1] if self.children else None
        new_line = LineLayout(self.node, self, last_line, self.font_ratio)
        self.children.append(new_line)

    def input(self, node: Element):
        w = INPUT_WIDTH_PX
        if self.cursor_x + w > self.x + self.width:
            self.new_line()
        line = self.children[-1]
        input = InputLayout(node, line, self.previous_word, self.font_ratio)
        line.children.append(input)
        self.previous_word = input
        font = self.get_font(node)
        self.cursor_x += w + font.measure(" ")

    def paint(self, display_list: List[Draw]) -> None:
        bgcolor = self.node.style.get("background-color", "transparent")
        is_atomic = not isinstance(self.node, Text) and (
            isinstance(self.node, Element)
            and self.node.tag
            in [
                "input",
                "button",
            ]
        )

        if not is_atomic:
            if bgcolor != "transparent":
                x2, y2 = self.x + self.width, self.y + self.height
                display_list.append(DrawRect(self.x, self.y, x2, y2, bgcolor))

        for child in self.children:
            child.paint(display_list)

    def __repr__(self) -> str:
        return "InlineLayout(x={}, y={}, width={}, height={}, node={})".format(
            self.x, self.y, self.width, self.height, self.node
        )
