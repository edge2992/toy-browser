from __future__ import annotations

from typing import TYPE_CHECKING, List, Union

from src.layout.abstract_child import ChildLayoutObject
from src.draw import DrawRRect, DrawText
from src.global_value import FONT_RATIO, INPUT_WIDTH_PX
from src.layout.line import LineLayout
from src.text import Element, Text
import skia

if TYPE_CHECKING:

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
        cmds: List[Draw] = []

        rect = skia.Rect.MakeLTRB(
            self.x, self.y, self.x + self.width, self.y + self.height
        )
        bgcolor = self.node.style.get("background-color", "transparent")
        if bgcolor != "transparent":
            radius = float(self.node.style.get("border-radius", "0px")[:-2])
            cmds.append(DrawRRect(rect, radius, bgcolor))

        assert isinstance(self.node, Element)

        if self.node.tag == "input":
            text = self.node.attributes.get("value", "")
        elif self.node.tag == "button":
            assert isinstance(self.node.children[0], Text)
            text = self.node.children[0].text
        else:
            raise ValueError("Invalid tag for InputLayout")

        color = self.node.style["color"]
        cmds.append(DrawText(self.x, self.y, text, self.font, color))

        cmds = self.paint_visual_effects(self.node, cmds, rect)

        display_list.extend(cmds)

    def __repr__(self) -> str:
        return ("InputLayout(x={}, y={}, width={}, height={}, node={})").format(
            self.x, self.y, self.width, self.height, self.node
        )
