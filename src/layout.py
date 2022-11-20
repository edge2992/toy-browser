from __future__ import annotations
import tkinter
import tkinter.font
from typing import Dict, List, Tuple, Union
from src.draw import Draw, DrawRect, DrawText
from src.text import Element, HTMLNode, Text

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
FONTS: Dict[Tuple[int, str, str], tkinter.font.Font] = {}  # font cache
FONT_METRICS: Dict[Tuple[int, str, str], dict] = {}


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


class LayoutObject:
    def __init__(
        self,
        node: HTMLNode,
        parent: LayoutObject,
        previous: Union[LayoutObject, None],
    ):
        self.node: HTMLNode = node
        self.parent: Union[LayoutObject, None] = parent
        self.previous = previous
        self.children: List[LayoutObject] = []
        self.x: int
        self.y: int
        self.width: int
        self.height: int

    def paint(self, display_list: List[Draw]):
        raise NotImplementedError

    def layout(self):
        raise NotImplementedError


class InlineLayout(LayoutObject):
    def __init__(
        self,
        node: HTMLNode,
        parent: LayoutObject,
        previous: Union[LayoutObject, None],
    ):
        super().__init__(node, parent, previous)
        self.parent: LayoutObject = parent
        self.display_list: List[Tuple[int, int, str, tkinter.font.Font, str]] = []
        self.font_metrics: List[dict] = []
        self.line: List[Tuple[int, str, tkinter.font.Font, str]] = []

    def layout(self):
        self.width = self.parent.width
        self.x = self.parent.x

        if self.previous:
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y

        self.cursor_x = self.x
        self.cursor_y = self.y

        self.recurse(self.node)
        self.flush()

        self.height = self.cursor_y - self.y

    def recurse(self, node: HTMLNode):
        if isinstance(node, Text):
            self.text(node)
        elif isinstance(node, Element):
            if node.tag == "br":
                self.flush()
            for child in node.children:
                self.recurse(child)
        else:
            raise ValueError("Unknown node type")

    def text(self, node: Text) -> None:
        # English
        weight = node.style["font-weight"]
        style = node.style["font-style"]
        color = node.style["color"]
        if style == "normal":
            style = "roman"
        size = int(float(node.style["font-size"][:-2]) * 0.75)
        font = get_font(size, weight, style)
        metric = get_font_metric(size, weight, style)
        for word in node.text.split():
            w = font.measure(word)
            if self.cursor_x + w > self.width - HSTEP:
                self.flush()
            self.line.append((self.cursor_x, word, font, color))
            self.font_metrics.append(metric)
            self.cursor_x += w + font.measure(" ")

    def flush(self) -> None:
        if not self.line:
            return

        max_ascent = max([metric["ascent"] for metric in self.font_metrics])
        baseline = self.cursor_y + 1.25 * max_ascent
        assert len(self.line) == len(self.font_metrics), "{} != {}".format(
            len(self.line), len(self.font_metrics)
        )
        for (x, word, font, color), metric in zip(self.line, self.font_metrics):
            y = int(baseline - metric["ascent"])
            self.display_list.append((x, y, word, font, color))

        self.cursor_x = self.x
        max_descent = max([metric["descent"] for metric in self.font_metrics])
        self.line = []
        self.font_metrics = []
        # self.cursor_x = HSTEP
        self.cursor_y = baseline + 1.25 * max_descent

    def paint(self, display_list: List[Draw]) -> None:
        bgcolor = self.node.style.get("background-color", "transparent")
        if bgcolor != "transparent":
            x2, y2 = self.x + self.width, self.y + self.height
            display_list.append(DrawRect(self.x, self.y, x2, y2, bgcolor))
        assert isinstance(self.display_list, list)
        for x, y, word, font, color in self.display_list:
            display_list.append(DrawText(x, y, word, font, color))

    def __repr__(self) -> str:
        return "InlineLayout(x={}, y={}, width={}, height={}, node={})".format(
            self.x, self.y, self.width, self.height, self.node
        )


class BlockLayout(LayoutObject):
    def __init__(
        self,
        node: HTMLNode,
        parent: LayoutObject,
        previous: Union[LayoutObject, None],
    ):
        super().__init__(node, parent, previous)
        self.parent: LayoutObject = parent

    def layout(self) -> None:
        previous = None
        # create child layout object
        for child in self.node.children:
            next: LayoutObject
            if layout_mode(child) == "inline":
                next = InlineLayout(child, self, previous)
            else:
                next = BlockLayout(child, self, previous)
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
    def __init__(self, node: HTMLNode):
        self.node = node
        self.parent: Union[LayoutObject, None] = None
        self.children: List[LayoutObject] = []

    def layout(self) -> None:
        child = BlockLayout(self.node, self, None)
        self.children.append(child)
        self.width = WIDTH - 2 * HSTEP
        self.x = HSTEP
        self.y = VSTEP
        child.layout()
        self.height = child.height + 2 * VSTEP

    def paint(self, display_list: List[Draw]) -> None:
        self.children[0].paint(display_list)

    def __repr__(self):
        return "DocumentLayout()"
