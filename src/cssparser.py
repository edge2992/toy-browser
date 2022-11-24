from typing import List, Tuple, Union
from src.text import HTMLNode, Element
from src.selector import (
    CSSRule,
    ClassSelector,
    Declaration,
    IdSelector,
    Selector,
    SequenceSelector,
    TagSelector,
    DesendantSelector,
)


INHERITED_PROPERTIES = {
    "font-size": "16px",
    "font-style": "normal",
    "font-weight": "normal",
    "font-family": "Times",
    "color": "black",
}


def compute_style(node: HTMLNode, property: str, value: str) -> Union[str, None]:
    if property == "font-size":
        if value.endswith("px"):
            return value
        elif value.endswith("%"):
            if node.parent:
                parent_font_size = node.parent.style["font-size"]
            else:
                parent_font_size = INHERITED_PROPERTIES["font-size"]
            node_pct = float(value[:-1]) / 100
            parent_px = float(parent_font_size[:-2])
            return str(node_pct * parent_px) + "px"
        else:
            return None
    else:
        return value


def style(node: HTMLNode, rules: List[CSSRule]) -> None:
    node.style = {}
    for property, default_value in INHERITED_PROPERTIES.items():
        if node.parent:
            node.style[property] = node.parent.style[property]
        else:
            node.style[property] = default_value
    for selector, body in rules:
        if not selector.matches(node):
            continue
        for property, value in body.items():
            computed_value = compute_style(node, property, value)
            if not computed_value:
                continue
            node.style[property] = computed_value
    if isinstance(node, Element) and "style" in node.attributes:
        pairs = CSSParser(node.attributes["style"]).body()
        for property, value in pairs.items():
            node.style[property] = value
    for child in node.children:
        style(child, rules)


class CSSParser:
    def __init__(self, s: str):
        self.s = s
        self.i = 0

    def whitespace(self) -> None:
        while self.i < len(self.s) and self.s[self.i].isspace():
            self.i += 1

    def literal(self, literal: str) -> None:
        assert self.i < len(self.s) and self.s[self.i] == literal
        self.i += 1

    def word(self) -> str:
        start = self.i
        while self.i < len(self.s):
            if self.s[self.i].isalnum() or self.s[self.i] in "#-.%":
                self.i += 1
            else:
                break
        assert self.i > start
        return self.s[start : self.i]

    def pair(self) -> Tuple[str, str]:
        # <div style="background-color:lightblue"></div> -> ("background-color", "lightblue")
        prop = self.word()
        self.whitespace()
        self.literal(":")
        self.whitespace()
        val = self.word()
        return prop.lower(), val

    def ignore_until(self, chars):
        # skip developers error
        while self.i < len(self.s):
            if self.s[self.i] in chars:
                return self.s[self.i]
            else:
                self.i += 1

    def body(self) -> Declaration:
        pairs: Declaration = {}
        while self.i < len(self.s) and self.s[self.i] != "}":
            try:
                prop, val = self.pair()
                pairs[prop] = val
                self.whitespace()
                self.literal(";")
                self.whitespace()
            except AssertionError:
                why = self.ignore_until([";", "}"])
                if why == ";":
                    self.literal(";")
                    self.whitespace()
                else:
                    break

        return pairs

    def simple_selector(self) -> Selector:
        # impl: .class, #id, tag
        word = self.word().lower()
        if word.startswith("."):
            return ClassSelector(word[1:])
        elif word.startswith("#"):
            return IdSelector(word[1:])
        else:
            # impl: tag.class, tag#id
            # TODO: impl: tag.class#id, tag.class.class, tag#id#id
            if "." in word:
                tag, cls = word.split(".", 1)
                if "#" in cls or "." in cls or "#" in tag or "." in tag:
                    print("[warning] invalid selector: ", word)
                return SequenceSelector(TagSelector(tag), ClassSelector(cls))
            if "#" in word:
                tag, id_ = word.split("#", 1)
                if "#" in id_ or "." in id_ or "#" in tag or "." in tag:
                    print("[warning] invalid selector: ", word)
                return SequenceSelector(TagSelector(tag), IdSelector(id_))
            return TagSelector(word)

    def selector(self) -> Selector:
        out: Selector = self.simple_selector()
        self.whitespace()
        while self.i < len(self.s) and self.s[self.i] != "{":
            desendant = self.simple_selector()
            out = DesendantSelector(out, desendant)
            self.whitespace()
        return out

    def parse(self) -> List[CSSRule]:
        rules: List[CSSRule] = []  # type: ignore
        while self.i < len(self.s):
            try:
                self.whitespace()
                selector = self.selector()
                self.literal("{")
                self.whitespace()
                body = self.body()
                self.literal("}")
                rules.append((selector, body))
            except AssertionError:
                why = self.ignore_until(["}"])
                if why == "}":
                    self.literal("}")
                    self.whitespace()
                else:
                    break
        return rules
