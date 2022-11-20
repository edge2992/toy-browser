from __future__ import annotations
import tkinter
import tkinter.font
from typing import Dict, Generic, List, Tuple, TypeVar, Union
from src.draw import Draw, DrawRect, DrawText
from src.text import Element, HTMLNode, Text

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
FONTS: Dict[Tuple[int, str, str], tkinter.font.Font] = {}  # font cache
FONT_METRICS: Dict[Tuple[int, str, str], dict] = {}
FONT_RATIO: float = 0.75


def get_font(size: int, weight: str, slant: str) -> tkinter.font.Font:
    key = (size, weight, slant)
    if key not in FONTS:
        FONTS[key] = tkinter.font.Font(size=size, weight=weight, slant=slant)  # type: ignore
    return FONTS[key]


def get_font_metric(size: int, weight: str, slant: str) -> dict:
    key = (size, weight, slant)
    if key not in FONT_METRICS:
        FONT_METRICS[key] = get_font(size, weight, slant).metrics()  # type: ignore
    return FONT_METRICS[key]


BLOCK_ELEMENTS = [
    "html",
    "body",
    "article",
    "section",
    "nav",
    "aside",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hgroup",
    "header",
    "footer",
    "address",
    "p",
    "hr",
    "pre",
    "blockquote",
    "ol",
    "ul",
    "menu",
    "li",
    "dl",
    "dt",
    "dd",
    "figure",
    "figcaption",
    "main",
    "div",
    "table",
    "form",
    "fieldset",
    "legend",
    "details",
    "summary",
]


def layout_mode(node: HTMLNode) -> str:
    if isinstance(node, Text):
        return "inline"
    elif node.children:
        for child in node.children:
            if isinstance(child, Text):
                continue
            if isinstance(child, Element) and child.tag in BLOCK_ELEMENTS:
                return "block"
        return "inline"
    else:
        return "block"


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

    def layout(self):
        """レイアウトツリーを作成する"""
        raise NotImplementedError

    def paint(self, display_list: List[Draw]):
        """描画するdisplay_listを作成する"""
        raise NotImplementedError


class InlineLayout(LayoutObject[LayoutObject, Union[LayoutObject, None], LayoutObject]):
    def __init__(
        self,
        node: HTMLNode,
        parent: LayoutObject,
        previous: Union[LayoutObject, None],
        font_ratio: float = FONT_RATIO,
    ):
        super().__init__(node, parent, previous, font_ratio)
        self.font_metrics: List[dict] = []
        self.previous_word: Union[TextLayout, None] = None

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
            for child in node.children:
                self.recurse(child)
        else:
            raise ValueError("Unknown node type")

    def text(self, node: Text) -> None:
        # English
        weight = node.style["font-weight"]
        style = node.style["font-style"]

        if style == "normal":
            style = "roman"
        size = int(float(node.style["font-size"][:-2]) * self.font_ratio)
        font = get_font(size, weight, style)
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

    def paint(self, display_list: List[Draw]) -> None:
        bgcolor = self.node.style.get("background-color", "transparent")
        if bgcolor != "transparent":
            x2, y2 = self.x + self.width, self.y + self.height
            display_list.append(DrawRect(self.x, self.y, x2, y2, bgcolor))
        for child in self.children:
            child.paint(display_list)

    def __repr__(self) -> str:
        return "InlineLayout(x={}, y={}, width={}, height={}, node={})".format(
            self.x, self.y, self.width, self.height, self.node
        )


class BlockLayout(LayoutObject[LayoutObject, Union[LayoutObject, None], LayoutObject]):
    def __init__(
        self,
        node: HTMLNode,
        parent: LayoutObject,
        previous: Union[LayoutObject, None],
        font_ratio: float = FONT_RATIO,
    ):
        super().__init__(node, parent, previous, font_ratio)

    def layout(self) -> None:
        previous: Union[InlineLayout, BlockLayout, None] = None
        # create child layout object
        for child in self.node.children:
            next: Union[InlineLayout, BlockLayout]
            if layout_mode(child) == "inline":
                next = InlineLayout(child, self, previous, self.font_ratio)
            else:
                next = BlockLayout(child, self, previous, self.font_ratio)
            self.children.append(next)
            previous = next
        # width, x, yをparentとpreviousを参考に計算する
        self.width = self.parent.width
        self.x = self.parent.x
        if self.previous:
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y
        # childrenで再帰的にlayoutを実行する
        for child_layout in self.children:
            child_layout.layout()
        # childrenを全て読んでheightを計算
        self.height = sum([child.height for child in self.children])

    def paint(self, display_list: List[Draw]) -> None:
        for child in self.children:
            child.paint(display_list)

    def __repr__(self):
        return "BlockLayout(x={}, y={}, width={}, height={}, node={})".format(
            self.x, self.y, self.width, self.height, self.node
        )


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


class LineLayout(LayoutObject[LayoutObject, Union[LayoutObject, None], "TextLayout"]):
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

        max_ascent = max(word.font.metrics("ascent") for word in self.children)

        baseline = self.y + 1.25 * max_ascent
        for word in self.children:
            word.y = int(baseline - word.font.metrics("ascent"))

        max_descent = max([word.font.metrics("descent") for word in self.children])
        self.height = int(1.25 * (max_ascent + max_descent))

    def paint(self, display_list: List[Draw]) -> None:
        for child in self.children:
            child.paint(display_list)

    def __repr__(self):
        return "LineLayout(x={}, y={}, width={}, height={})".format(
            self.x, self.y, self.width, self.height
        )


class TextLayout(LayoutObject[LineLayout, Union["TextLayout", None], LayoutObject]):
    def __init__(
        self,
        node: HTMLNode,
        word: str,
        parent: LineLayout,
        previous: Union[TextLayout, None],
        font_ratio: float = FONT_RATIO,
    ):
        super().__init__(node, parent, previous, font_ratio)
        self.word = word
        self.font: tkinter.font.Font

    def layout(self):
        weight = self.node.style["font-weight"]
        style = self.node.style["font-style"]
        if style == "normal":
            style = "roman"
        size = int(float(self.node.style["font-size"][:-2]) * self.font_ratio)
        self.font = get_font(size, weight, style)
        self.width = self.font.measure(self.word)
        if self.previous:
            space = self.previous.font.measure(" ")
            self.x = self.previous.x + space + self.previous.width
        else:
            self.x = self.parent.x

        self.height = self.font.metrics("linespace")

    def paint(self, display_list: List[Draw]) -> None:
        color = self.node.style["color"]
        display_list.append(DrawText(self.x, self.y, self.word, self.font, color))

    def __repr__(self) -> str:
        return ("TextLayout(x={}, y={}, width={}, height={}, node={}, word={})").format(
            self.x, self.y, self.width, self.height, self.node, self.word
        )
