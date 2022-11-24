from __future__ import annotations

import tkinter
import tkinter.font
import urllib.parse
from typing import List, Union

import dukpy

from src.graphics.history import History
from src.cssparser import CSSParser, style
from src.draw import Draw
from src.jscontext import JSContext
from src.layout import DocumentLayout, InputLayout, LayoutObject
from src.network import request
from src.selector import cascade_priority
from src.text import Element, HTMLParser, Text
from src.util.node import tree_to_list
from src.util.url import resolve_url, url_origin
from src.global_value import CHROME_PX, FONT_RATIO, SCROLL_STEP


class Tab:
    def __init__(self, width: int, height: int):
        self.scroll = 0
        with open("src/browser.css") as f:
            self.default_style_sheet = CSSParser(f.read()).parse()
        self.history = History()
        self.width = width
        self.height = height
        self.url = None
        self.allowed_origins: Union[List[str], None] = None
        self.font_ratio = FONT_RATIO
        self.forcus: Union[Element, None] = None

    def load(self, url: str, body: Union[str, None] = None):
        self.history.append(url)
        headers, body, _ = request(url, self.url, payload=body)
        print("header\n", headers)
        self.allowed_origins = None
        if "content-security-policy" in headers:
            csp = headers["content-security-policy"].split()
            if len(csp) > 0 and csp[0] == "default-src":
                self.allowed_origins = csp[1:]
        self.scroll = 0
        self.url = url
        self.nodes = HTMLParser(body).parse()
        self.rules = self._rules()

        scripts = [
            node.attributes["src"]
            for node in tree_to_list(self.nodes, [])
            if isinstance(node, Element)
            and node.tag == "script"
            and "src" in node.attributes
        ]
        self.js = JSContext(self)
        for script in scripts:
            script_url = resolve_url(script, self.url)
            if not self.allowed_request(script_url):
                print("Blocked script", script, "due to CSP")
                continue
            header, body, _ = request(resolve_url(script, self.url), self.url)
            try:
                self.js.run(body)
            except dukpy.JSRuntimeError as e:
                print("Script", script, "crashed", e)
        self.render()

    def _rules(self):
        rules = self.default_style_sheet.copy()
        node_list = tree_to_list(self.nodes, [])

        links = [
            node.attributes["href"]
            for node in node_list
            if isinstance(node, Element)
            and node.tag == "link"
            and "href" in node.attributes
            and node.attributes.get("rel") == "stylesheet"
        ]
        for link in links:
            script_url = resolve_url(link, self.url)
            if not self.allowed_request(script_url):
                print("Blocked script", link, "due to CSP")
                continue
            try:
                _, body, _ = request(script_url, self.url)
            except Exception as e:
                print(e)
                continue
            rules.extend(CSSParser(body).parse())

        inline_styles = [
            node
            for node in node_list
            if isinstance(node, Element) and node.tag == "style"
        ]
        for inline_style_node in inline_styles:
            assert isinstance(inline_style_node.children[0], Text)
            body = inline_style_node.children[0].text
            rules.extend(CSSParser(body).parse())

        return rules

    def render(self) -> None:
        # layout -> paint
        style(self.nodes, sorted(self.rules, key=cascade_priority))
        self.document = DocumentLayout(
            self.nodes, width=self.width, font_ratio=self.font_ratio
        )
        self.document.layout()
        self.display_list: List[Draw] = []  # type: ignore
        self.document.paint(self.display_list)

    def draw(self, canvas: tkinter.Canvas):
        for cmd in self.display_list:
            if cmd.top > self.scroll + self.height - CHROME_PX:
                continue
            if cmd.bottom < self.scroll:
                continue
            cmd.execute(self.scroll - CHROME_PX, canvas)

        if self.forcus:
            obj = [
                obj
                for obj in tree_to_list(self.document, [])
                if isinstance(obj, InputLayout) and obj.node == self.forcus
            ][0]
            text = self.forcus.attributes.get("value", "")
            x = obj.x + obj.font.measure(text)
            y = obj.y - self.scroll + CHROME_PX
            canvas.create_line(x, y, x, y + obj.height)

    def allowed_request(self, url: str):
        return self.allowed_origins == None or url_origin(url) in self.allowed_origins

    def submit_form(self, elt: Element):
        if self.js.dispatch_event("submit", elt):
            return
        inputs: List[Element] = [
            node
            for node in tree_to_list(elt, [])
            if isinstance(node, Element)
            and node.tag == "input"
            and "name" in node.attributes
        ]
        body = ""
        for input in inputs:
            name = urllib.parse.quote(input.attributes["name"])
            value = urllib.parse.quote(input.attributes.get("value", ""))
            body += "&" + name + "=" + value
        body = body[1:]
        url = resolve_url(elt.attributes["action"], self.url)
        self.load(url, body)

    def click(self, x, y):
        self.forcus = None
        y += self.scroll
        objs: List[LayoutObject] = [
            obj
            for obj in tree_to_list(self.document, [])
            if obj.x <= x < obj.x + obj.width and obj.y <= y < obj.y + obj.height
        ]
        if not objs:
            return None
        elt = objs[-1].node
        while elt:
            if isinstance(elt, Text):
                pass
            elif isinstance(elt, Element):
                if elt.tag == "a" and "href" in elt.attributes:
                    if self.js.dispatch_event("click", elt):
                        return
                    url = resolve_url(elt.attributes["href"], self.url)
                    return self.load(url)
                elif elt.tag == "input":
                    if self.js.dispatch_event("click", elt):
                        return
                    self.forcus = elt
                    elt.attributes["value"] = ""
                    return self.render()
                elif elt.tag == "button":
                    if self.js.dispatch_event("click", elt):
                        return
                    while elt:
                        if (
                            isinstance(elt, Element)
                            and elt.tag == "form"
                            and "action" in elt.attributes
                        ):
                            return self.submit_form(elt)
                        elt = elt.parent
            assert elt
            elt = elt.parent
        return None

    def keypress(self, char: str):
        if self.forcus:
            if self.js.dispatch_event("keydown", self.forcus):
                return
            self.forcus.attributes["value"] += char
            self.render()

    def backspace(self):
        if self.forcus:
            self.forcus.attributes["value"] = self.forcus.attributes["value"][:-1]
            self.render()

    def go_back(self):
        url = self.history.previous()
        if url:
            self.load(url)

    def go_forward(self):
        url = self.history.next()
        if url:
            self.load(url)

    def scrolldown(self):
        max_y = self.document.height - (self.height - CHROME_PX)
        self.scroll = min(self.scroll + SCROLL_STEP, max_y)

    def scrollup(self):
        self.scroll -= SCROLL_STEP
        self.scroll = max(self.scroll, 0)

    def fontup(self):
        self.font_ratio += 0.1
        self.render()

    def fontdown(self):
        self.font_ratio -= 0.1
        self.render()

    def resize(self, width, height):
        print("resizing tag...", width, height)
        if self.width != width:
            # widthを変更した場合には再レイアウトが必要
            self.width = width
            self.render()

        self.height = height
        self.width = width

    def __repr__(self) -> str:
        return "Tab"
