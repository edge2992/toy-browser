from typing import TYPE_CHECKING, List, Union
from src.global_value import FONT_RATIO
from src.layout.abstract import LayoutObject

from src.text import HTMLNode
from src.draw import Draw
from src.util.draw_skia import linespace

if TYPE_CHECKING:
    import skia
    from src.layout.line import LineLayout


class ChildLayoutObject(
    LayoutObject["LineLayout", Union["ChildLayoutObject", None], LayoutObject]
):
    """InputLayoutとTextLayoutの共通の親クラス"""

    def __init__(
        self,
        node: HTMLNode,
        parent: "LineLayout",
        previous: Union["ChildLayoutObject", None],
        font_ratio: float = FONT_RATIO,
    ):
        super().__init__(node, parent, previous, font_ratio)
        self.word: str
        self.font: skia.Font

    def layout(self):
        self.font = self.get_font(self.node)
        # self.width = self.font.meatureText(self.word)
        if self.previous:
            space = self.previous.font.measureText(" ")
            self.x = self.previous.x + space + self.previous.width
        else:
            self.x = self.parent.x

        self.height = linespace(self.font)

    def paint(self, display_list: List[Draw]):
        raise NotImplementedError
