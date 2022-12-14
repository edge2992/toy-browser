from __future__ import annotations

from typing import TYPE_CHECKING, List, Union
from src.layout.abstract_child import ChildLayoutObject

from src.global_value import FONT_RATIO
from src.layout.abstract import LayoutObject

if TYPE_CHECKING:
    from src.draw import Draw
    from src.text import HTMLNode


class LineLayout(
    LayoutObject[LayoutObject, Union[LayoutObject, None], ChildLayoutObject]
):
    def __init__(
        self,
        node: HTMLNode,
        parent: LayoutObject,
        previous: Union[LayoutObject, None],
        font_ratio: float = FONT_RATIO,
    ):
        super().__init__(node, parent, previous, font_ratio)

    def layout(self):
        self.width = self.parent.width
        self.x = self.parent.x

        if self.previous:
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y

        for word in self.children:
            word.layout()

        if not self.children:
            self.height = 0
            return

        max_ascent = max([-word.font.getMetrics().fAscent for word in self.children])

        baseline = self.y + 1.25 * max_ascent
        for word in self.children:
            word.y = baseline + word.font.getMetrics().fAscent

        max_descent = max([word.font.getMetrics().fDescent for word in self.children])

        self.height = 1.25 * (max_ascent + max_descent)

    def paint(self, display_list: List[Draw]) -> None:
        for child in self.children:
            child.paint(display_list)

    def __repr__(self):
        return "LineLayout(x={}, y={}, width={}, height={})".format(
            self.x, self.y, self.width, self.height
        )
