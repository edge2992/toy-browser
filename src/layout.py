from __future__ import annotations
import tkinter
import tkinter.font
from typing import Dict, Generic, List, Tuple, TypeVar, Union
from src.draw import Draw, DrawRect, DrawText
from src.text import LAYOUT_MODE, Element, HTMLNode, Text

from src.global_value import FONT_RATIO, VSTEP, HSTEP, WIDTH, INPUT_WIDTH_PX

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


class InlineLayout(LayoutObject[LayoutObject, Union[LayoutObject, None], "LineLayout"]):
    def __init__(
        self,
        node: HTMLNode,
        parent: LayoutObject,
        previous: Union[LayoutObject, None],
        font_ratio: float = FONT_RATIO,
    ):
        super().__init__(node, parent, previous, font_ratio)
        self.previous_word: Union[TextLayout, InputLayout, None] = None

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
            elif node.tag == "input" or node.tag == "button":
                self.input(node)
            else:
                for child in node.children:
                    self.recurse(child)
        else:
            raise ValueError("Unknown node type")

    def text(self, node: Text) -> None:
        font = self.get_font(node)

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

    def input(self, node: Element):
        w = INPUT_WIDTH_PX
        if self.cursor_x + w > self.x + self.width:
            self.new_line()
        line = self.children[-1]
        input = InputLayout(node, line, self.previous_word, self.font_ratio)
        line.children.append(input)
        self.previous_word = input
        font = self.get_font(node)
        self.cursor_x += w + font.measure(" ")

    def paint(self, display_list: List[Draw]) -> None:
        bgcolor = self.node.style.get("background-color", "transparent")
        is_atomic = not isinstance(self.node, Text) and (
            isinstance(self.node, Element)
            and self.node.tag
            in [
                "input",
                "button",
            ]
        )

        if not is_atomic:
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
            mode = child.display
            if mode == LAYOUT_MODE.INLINE:
                next = InlineLayout(child, self, previous, self.font_ratio)
            elif mode == LAYOUT_MODE.BLOCK:
                next = BlockLayout(child, self, previous, self.font_ratio)
            else:
                # headを飛ばす
                continue
            self.children.append(next)
            previous = next
        # width, x, yをparentとpreviousを参考に計算する
        self.width = self.parent.width
        if "width" in self.node.style:
            if self.node.style["width"].endswith("px"):
                # responsiveにする必要があるか?
                self.width = min(int(self.node.style["width"][:-2]), self.parent.width)
            elif self.node.style["width"] == "auto":
                pass
            else:
                print("[warning] unknown width", self.node.style["width"])

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
        if "height" in self.node.style:
            if self.node.style["height"].endswith("px"):
                self.height = int(self.node.style["height"][:-2])
            elif self.node.style["height"] == "auto":
                pass
            else:
                print("[warning] unknown height", self.node.style["height"])

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


class TextLayout(
    LayoutObject[LineLayout, Union["TextLayout", "InputLayout", None], LayoutObject]
):
    def __init__(
        self,
        node: HTMLNode,
        word: str,
        parent: LineLayout,
        previous: Union[TextLayout, InputLayout, None],
        font_ratio: float = FONT_RATIO,
    ):
        super().__init__(node, parent, previous, font_ratio)
        self.word = word
        self.font: tkinter.font.Font

    def layout(self):
        self.font = self.get_font(self.node)
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


class InputLayout(
    LayoutObject[
        LineLayout,
        Union[TextLayout, "InputLayout", None],
        Union[TextLayout, "InputLayout"],
    ]
):
    def __init__(
        self,
        node: HTMLNode,
        parent: LineLayout,
        previous: Union[TextLayout, "InputLayout", None],
        font_ratio: float = FONT_RATIO,
    ):
        super().__init__(node, parent, previous, font_ratio)
        # self.word = word
        self.font: tkinter.font.Font

    def layout(self):
        self.font = self.get_font(self.node)

        self.width = INPUT_WIDTH_PX
        if self.previous:
            space = self.previous.font.measure(" ")
            self.x = self.previous.x + space + self.previous.width
        else:
            self.x = self.parent.x

        self.height = self.font.metrics("linespace")

    def paint(self, display_list: List[Draw]) -> None:
        bgcolor = self.node.style.get("background-color", "transparent")
        if bgcolor != "transparent":
            x2, y2 = self.x + self.width, self.y + self.height
            rect = DrawRect(self.x, self.y, x2, y2, bgcolor)
            display_list.append(rect)

        assert isinstance(self.node, Element)

        if self.node.tag == "input":
            text = self.node.attributes.get("value", "")
        elif self.node.tag == "button":
            assert isinstance(self.node.children[0], Text)
            text = self.node.children[0].text
        else:
            raise ValueError("Invalid tag for InputLayout")

        color = self.node.style["color"]
        display_list.append(DrawText(self.x, self.y, text, self.font, color))

        color = self.node.style["color"]
        display_list.append(DrawText(self.x, self.y, text, self.font, color))

    def __repr__(self) -> str:
        return ("InputLayout(x={}, y={}, width={}, height={}, node={})").format(
            self.x, self.y, self.width, self.height, self.node
        )
