from __future__ import annotations

from typing import TYPE_CHECKING, List, Union

from src.layout.abstract_child import ChildLayoutObject
from src.draw import DrawRect, DrawText
from src.global_value import FONT_RATIO, INPUT_WIDTH_PX
from src.layout.line import LineLayout
from src.text import Element, Text

if TYPE_CHECKING:
    import skia

    from src.draw import Draw
    from src.text import HTMLNode


class InputLayout(ChildLayoutObject):
    def __init__(
        self,
        node: HTMLNode,
        parent: "LineLayout",
        previous: Union[ChildLayoutObject, None],
        font_ratio: float = FONT_RATIO,
    ):
        super().__init__(node, parent, previous, font_ratio)
        self.font: skia.Font

    def layout(self):
        super().layout()
        self.width = INPUT_WIDTH_PX

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
