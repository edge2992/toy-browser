from __future__ import annotations

from typing import TYPE_CHECKING, List, Union

from src.global_value import FONT_RATIO
from src.layout.abstract import LayoutObject

if TYPE_CHECKING:
    from src.draw import Draw
    from src.layout.input import InputLayout
    from src.layout.text import TextLayout
    from src.text import HTMLNode


class LineLayout(
    LayoutObject[
        LayoutObject, Union[LayoutObject, None], Union["TextLayout", "InputLayout"]
    ]
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

        try:
            max_ascent = max(word.font.metrics("ascent") for word in self.children)
        except ValueError as e:
            print("[max_ascent warnings] ", e)
            print("self node", self.node)
            print("parent node", self.parent.node)
            max_ascent = 0

        baseline = self.y + 1.25 * max_ascent
        for word in self.children:
            word.y = int(baseline - word.font.metrics("ascent"))

        try:
            max_descent = max([word.font.metrics("descent") for word in self.children])
        except ValueError as e:
            print("[max_decent warnings] ", e)
            print("self node", self.node)
            print("parent node", self.parent.node)
            max_descent = 0

        self.height = int(1.25 * (max_ascent + max_descent))

    def paint(self, display_list: List[Draw]) -> None:
        for child in self.children:
            child.paint(display_list)

    def __repr__(self):
        return "LineLayout(x={}, y={}, width={}, height={})".format(
            self.x, self.y, self.width, self.height
        )
