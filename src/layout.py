import tkinter
import tkinter.font
from typing import Dict, List, Tuple, Union
from src.draw import DrawRect, DrawText
from src.text import Element, Text

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


def layout_mode(node):
    if isinstance(node, Text):
        return "inline"
    elif node.children:
        for child in node.children:
            if isinstance(child, Text):
                continue
            if child.tag in BLOCK_ELEMENTS:
                return "block"
        return "inline"
    else:
        return "block"


class InlineLayout:
    x: int
    y: int
    width: int
    height: int
    display_list: list = []
    font_metrics: list = []

    def __init__(self, node, parent, previous):
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children = []

    def layout(self):
        self.width = self.parent.width
        self.x = self.parent.x

        if self.previous:
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y

        self.display_list = []
        self.weight = "normal"
        self.style = "roman"
        self.size = 16

        self.cursor_x = self.x
        self.cursor_y = self.y

        self.line = []
        self.recurse(self.node)
        self.flush()

        self.height = self.cursor_y - self.y

    def recurse(self, node):
        if isinstance(node, Text):
            self.text(node)
        else:
            self.open_tag(node.tag)
            for child in node.children:
                self.recurse(child)
            self.close_tag(node.tag)

    def open_tag(self, tag):
        if tag == "i":
            self.style = "italic"
        elif tag == "b":
            self.weight = "bold"
        elif tag == "small":
            self.size -= 2
        elif tag == "big":
            self.size += 2
        elif tag == "br":
            self.flush()

    def close_tag(self, tag):
        if tag == "i":
            self.style = "roman"
        elif tag == "b":
            self.weight = "normal"
        elif tag == "small":
            self.size += 2
        elif tag == "big":
            self.size -= 2
        elif tag == "p":
            self.flush()
            self.cursor_y += VSTEP

    def text(self, tok):
        # English
        font = get_font(self.size, self.weight, self.style)
        metric = get_font_metric(self.size, self.weight, self.style)
        for word in tok.text.split():
            # self.max_scroll = max(self.max_scroll, self.cursor_y)
            w = font.measure(word)
            assert self.cursor_x
            assert self.width
            if self.cursor_x + w > self.width - HSTEP:
                self.flush()
            self.line.append((self.cursor_x, word, font))
            self.font_metrics.append(metric)
            self.cursor_x += w + font.measure(" ")

        # Chinese
        # font = get_font(self.size, self.weight, self.style)
        # for c in tok.text:
        #     self.max_scroll = max(self.max_scroll, self.cursor_y)
        #     w = font.measure(c)
        #     if self.cursor_x >= self.width - self.hstep:
        #         self.flush()
        #     self.line.append((self.cursor_x, c, font))
        #     self.cursor_x += w

    def flush(self):
        if not self.line:
            return
        # metrics = [font.metrics() for _, _, font in self.line]

        max_ascent = max([metric["ascent"] for metric in self.font_metrics])
        baseline = self.cursor_y + 1.25 * max_ascent
        assert len(self.line) == len(self.font_metrics)
        for (x, word, font), metric in zip(self.line, self.font_metrics):
            y = int(baseline - metric["ascent"])
            assert isinstance(self.display_list, list)
            self.display_list.append((x, y, word, font))

        self.cursor_x = self.x
        max_descent = max([metric["descent"] for metric in self.font_metrics])
        self.line = []
        self.font_metrics = []
        # self.cursor_x = HSTEP
        self.cursor_y = baseline + 1.25 * max_descent

    def paint(self, display_list):
        if isinstance(self.node, Element) and self.node.tag == "pre":
            x2, y2 = self.x + self.width, self.y + self.height
            display_list.append(DrawRect(self.x, self.y, x2, y2, "gray"))
        assert isinstance(self.display_list, list)
        for x, y, word, font in self.display_list:
            display_list.append(DrawText(x, y, word, font))

    def __repr__(self) -> str:
        return "InlineLayout(x={}, y={}, width={}, height={}, node={})".format(
            self.x, self.y, self.width, self.height, self.node
        )


class BlockLayout:
    def __init__(self, node, parent, previous):
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children = []
        self.x = None
        self.y = None
        self.width = None
        self.height = None

    def layout(self):
        previous = None
        # create child layout object
        for child in self.node.children:
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
        for child in self.children:
            child.layout()
        # childrenを全て読んでheightを計算
        self.height = sum([child.height for child in self.children])

    def paint(self, display_list):
        for child in self.children:
            child.paint(display_list)

    def __repr__(self):
        return "BlockLayout(x={}, y={}, width={}, height={}, node={})".format(
            self.x, self.y, self.width, self.height, self.node
        )


class DocumentLayout:
    def __init__(self, node):
        self.node = node
        self.parent = None
        self.children = []

    def layout(self):
        child = BlockLayout(self.node, self, None)
        self.children.append(child)
        self.width = WIDTH - 2 * HSTEP
        self.x = HSTEP
        self.y = VSTEP
        child.layout()
        assert child.height
        self.height = child.height + 2 * VSTEP

    def paint(self, display_list):
        self.children[0].paint(display_list)

    def __repr__(self):
        return "DocumentLayout()"
