from __future__ import annotations
import skia
from typing import Dict, Generic, List, Tuple, TypeVar, Union, TYPE_CHECKING

from src.global_value import FONT_RATIO

if TYPE_CHECKING:
    from src.draw import Draw
    from src.text import HTMLNode

FONTS: Dict[Tuple[Union[str, None], str, str], skia.Font] = {}  # font cache


def get_font(family: Union[str, None], size: int, weight: str, slant: str) -> skia.Font:
    key = (family, weight, slant)
    if key not in FONTS:
        if weight == "bold":
            skia_weight = skia.FontStyle.kBold_Weight
        else:
            skia_weight = skia.FontStyle.kNormal_Weight
        if slant == "italic":
            skia_style = skia.FontStyle.kItalic_Slant
        else:
            skia_style = skia.FontStyle.kUpright_Slant
        skia_width = skia.FontStyle.kNormal_Width
        style_info = skia.FontStyle(skia_weight, skia_width, skia_style)
        font = skia.Typeface("Arial", style_info)
        FONTS[key] = font
    return skia.Font(FONTS[key], size)


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

    def get_font(self, node: HTMLNode) -> skia.Font:
        weight = node.style["font-weight"]
        style = node.style["font-style"]
        family = node.style["font-family"]

        if style == "normal":
            style = "roman"
        size = int(float(node.style["font-size"][:-2]) * self.font_ratio)

        try:
            font = get_font(family, size, weight, style)
        except Exception as e:
            # except tkinter.TclError as e:
            print("[warning]", e)
            font = get_font(None, size, weight, style)
        return font

    def layout(self):
        """レイアウトツリーを作成する"""
        raise NotImplementedError

    def paint(self, display_list: List[Draw]):
        """描画するdisplay_listを作成する"""
        raise NotImplementedError
