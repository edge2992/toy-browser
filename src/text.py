from __future__ import annotations
from abc import ABC
from enum import Enum, auto
from typing import Dict, Tuple, Union, List

from src.entities import ENTITIES_DICT


class LAYOUT_MODE(Enum):
    INLINE = auto()
    BLOCK = auto()


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


class HTMLNode(ABC):
    def __init__(self, parent: Union["HTMLNode", None]):
        self.parent: Union[HTMLNode, None] = parent
        self.children: List[HTMLNode] = []
        self.style: Dict[str, str] = {}

    @property
    def display(self) -> LAYOUT_MODE:
        raise NotImplementedError


class Text(HTMLNode):
    def __init__(self, text: str, parent: Union[HTMLNode, None]):
        super().__init__(parent)
        for c in ENTITIES_DICT:
            text = text.replace(c, ENTITIES_DICT[c])
        self.text = text

    @property
    def display(self) -> LAYOUT_MODE:
        return LAYOUT_MODE.INLINE

    def __repr__(self):
        return repr(self.text)


class Element(HTMLNode):
    def __init__(
        self, tag: str, attributes: Dict[str, str], parent: Union[HTMLNode, None]
    ):
        super().__init__(parent)
        self.tag = tag
        self.attributes = attributes

    @property
    def display(self) -> LAYOUT_MODE:
        if self.children:
            for child in self.children:
                if isinstance(child, Text):
                    continue
                elif isinstance(child, Element) and child.tag in BLOCK_ELEMENTS:
                    return LAYOUT_MODE.BLOCK
            return LAYOUT_MODE.INLINE
        elif self.tag == "input":
            return LAYOUT_MODE.INLINE
        else:
            return LAYOUT_MODE.BLOCK

    def __repr__(self):
        return "<" + self.tag + ">"


SELF_CLOSING_TAGS = [
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
]


class HTMLParser:
    HEAD_TAGS = [
        "base",
        "basefont",
        "bgsound",
        "noscript",
        "link",
        "meta",
        "title",
        "style",
        "script",
    ]

    def __init__(self, body: str):
        self.body = body
        self.unfinished: List[Element] = []

    def implicit_tags(self, tag: Union[str, None]) -> None:
        while True:
            open_tags = [node.tag for node in self.unfinished]
            if open_tags == [] and tag != "html":
                self.add_tag("html")
            elif open_tags == ["html"] and tag not in ["head", "body", "/html"]:
                if tag in self.HEAD_TAGS:
                    self.add_tag("head")
                else:
                    self.add_tag("body")
            elif (
                open_tags == ["html", "head"] and tag not in ["/head"] + self.HEAD_TAGS
            ):
                self.add_tag("/head")
            else:
                break

    def add_text(self, text: str) -> None:
        if text.isspace():
            return
        self.implicit_tags(None)
        parent = self.unfinished[-1]
        node = Text(text, parent)
        parent.children.append(node)

    def add_tag(self, tag: str) -> None:
        tag, attributes = self.get_attributes(tag)
        if tag.startswith("!"):
            return  # doctype
        self.implicit_tags(tag)
        parent: Union[Element, None]
        if tag.startswith("/"):
            if len(self.unfinished) == 1:
                return
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        elif tag in SELF_CLOSING_TAGS:
            parent = self.unfinished[-1]
            node = Element(tag, attributes, parent)
            parent.children.append(node)
        else:
            parent = self.unfinished[-1] if self.unfinished else None
            node = Element(tag, attributes, parent)
            self.unfinished.append(node)

    def finish(self) -> HTMLNode:
        if len(self.unfinished) == 0:
            self.add_tag("html")
        while len(self.unfinished) > 1:
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        return self.unfinished.pop()

    def parse(self) -> HTMLNode:
        text = ""
        in_tag = False
        for c in self.body:
            if c == "<":
                in_tag = True
                if text:
                    self.add_text(text)
                text = ""
            elif c == ">":
                in_tag = False
                self.add_tag(text)
                text = ""
            else:
                text += c
        if not in_tag and text:
            self.add_text(text)
        return self.finish()

    def get_attributes(self, text: str) -> Tuple[str, dict]:
        parts = text.split()
        tag = parts[0].lower()
        attributes = {}
        for attrpair in parts[1:]:
            if "=" in attrpair:
                key, value = attrpair.split("=", 1)
                if len(value) > 2 and value[0] in ["'", '"']:
                    value = value[1:-1]
                attributes[key.lower()] = value
            else:
                attributes[attrpair.lower()] = ""
        return tag, attributes


def print_tree(node, indent: int = 0):
    print(" " * indent, node)
    for child in node.children:
        print_tree(child, indent + 2)


if __name__ == "__main__":
    from src.network import request
    import sys

    headers, body, _ = request(sys.argv[1], sys.argv[1])
    print(body)
    nodes = HTMLParser(body).parse()
    print_tree(nodes)
