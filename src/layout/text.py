from __future__ import annotations

from typing import TYPE_CHECKING, List, Union
from src.layout.abstract_child import ChildLayoutObject

from src.draw import DrawText
from src.global_value import FONT_RATIO

if TYPE_CHECKING:
    import skia

    from src.draw import Draw
    from src.layout.line import LineLayout
    from src.text import HTMLNode


class TextLayout(ChildLayoutObject):
    def __init__(
        self,
        node: HTMLNode,
        word: str,
        parent: "LineLayout",
        previous: Union[ChildLayoutObject, None],
        font_ratio: float = FONT_RATIO,
    ):
        super().__init__(node, parent, previous, font_ratio)
        self.word = word
        self.font: skia.Font

    def layout(self):
        super().layout()
        self.width = self.font.measureText(self.word)

    def paint(self, display_list: List[Draw]) -> None:
        color = self.node.style["color"]
        display_list.append(DrawText(self.x, self.y, self.word, self.font, color))

    def __repr__(self) -> str:
        return ("TextLayout(x={}, y={}, width={}, height={}, node={}, word={})").format(
            self.x, self.y, self.width, self.height, self.node, self.word
        )
