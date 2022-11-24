from __future__ import annotations

from typing import TYPE_CHECKING, List, Union

from src.global_value import FONT_RATIO, HSTEP, VSTEP, WIDTH
from src.layout.abstract import LayoutObject
from src.layout.block import BlockLayout

if TYPE_CHECKING:
    from src.draw import Draw
    from src.text import HTMLNode


class DocumentLayout(LayoutObject):
    def __init__(
        self,
        node: HTMLNode,
        width: int = WIDTH - 2 * HSTEP,
        hstep: int = HSTEP,
        vstep: int = VSTEP,
        font_ratio: float = FONT_RATIO,
    ):
        self.node = node
        self.parent: Union[LayoutObject, None] = None
        self.children: List[LayoutObject] = []
        self.width = width
        self.height: int
        self.x = hstep
        self.y = vstep
        self.font_ratio = font_ratio

    def layout(self) -> None:
        child = BlockLayout(self.node, self, None, self.font_ratio)
        self.children.append(child)
        child.layout()
        self.height = child.height + 2 * VSTEP

    def paint(self, display_list: List[Draw]) -> None:
        self.children[0].paint(display_list)

    def __repr__(self):
        return "DocumentLayout()"
