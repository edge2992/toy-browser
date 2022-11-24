from __future__ import annotations
import tkinter
import tkinter.font
from typing import Dict, Generic, List, Tuple, TypeVar, Union, TYPE_CHECKING

from src.global_value import FONT_RATIO

if TYPE_CHECKING:
    from src.draw import Draw
    from src.text import HTMLNode

FONTS: Dict[
    Tuple[Union[str, None], int, str, str], tkinter.font.Font
] = {}  # font cache


def get_font(
    family: Union[str, None], size: int, weight: str, slant: str
) -> tkinter.font.Font:
    key = (family, size, weight, slant)
    if key not in FONTS:
        FONTS[key] = tkinter.font.Font(family=family, size=size, weight=weight, slant=slant)  # type: ignore
    return FONTS[key]


PN = TypeVar("PN", bound=Union["LayoutObject", None])  # parent layout node
PRN = TypeVar("PRN", bound=Union["LayoutObject", None])  # previous layout node
CN = TypeVar("CN", bound="LayoutObject")  # child layout node


class LayoutObject(Generic[PN, PRN, CN]):
    def __init__(
        self,
        node: HTMLNode,
        parent: PN,
        previous: PRN,
        font_ratio: float = FONT_RATIO,
    ):
        self.node: HTMLNode = node
        self.parent = parent
        self.previous = previous
        self.children: List[CN] = []
        self.x: int
        self.y: int
        self.width: int
        self.height: int
        self.font_ratio = font_ratio

    def get_font(self, node: HTMLNode) -> tkinter.font.Font:
        weight = node.style["font-weight"]
        style = node.style["font-style"]
        family = node.style["font-family"]

        if style == "normal":
            style = "roman"
        size = int(float(node.style["font-size"][:-2]) * self.font_ratio)

        try:
            font = get_font(family, size, weight, style)
        except tkinter.TclError as e:
            print("[warning]", e)
            font = get_font(None, size, weight, style)
        return font

    def layout(self):
        """レイアウトツリーを作成する"""
        raise NotImplementedError

    def paint(self, display_list: List[Draw]):
        """描画するdisplay_listを作成する"""
        raise NotImplementedError
