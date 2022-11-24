from __future__ import annotations
import sys
import tkinter
import tkinter.font
import urllib.parse
from typing import List, Union
import dukpy

from src.cssparser import CSSParser, style
from src.draw import Draw
from src.jscontext import JSContext
from src.layout import DocumentLayout, InputLayout, LayoutObject, get_font
from src.network import request
from src.selector import cascade_priority
from src.text import Element, HTMLParser, Text
from src.util.node import tree_to_list
from src.util.url import resolve_url

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100
CHROME_PX = 100
FONT_RATIO: float = 0.75


class History:
    def __init__(self):
        self._history: List[str] = []
        self.index: int = -1

    def append(self, url: str) -> None:
        self.index += 1
        if self.index < len(self._history) and self._history[self.index] == url:
            pass
        else:
            self._history = self._history[: self.index]
            self._history.append(url)

    def next(self) -> Union[str, None]:
        if self.has_next():
            return self._history[self.index + 1]
        return None

    def previous(self) -> Union[str, None]:
        if self.has_previous():
            self.index -= 2
            return self._history[self.index + 1]
        return None

    def get_next(self) -> Union[str, None]:
        if self.has_next():
            return self._history[self.index + 1]
        return None

    def get_previous(self) -> Union[str, None]:
        if self.has_previous():
            return self._history[self.index - 1]
        return None

    def has_next(self) -> bool:
        return self.index < len(self._history) - 1

    def has_previous(self) -> bool:
        return self.index > 0


class Tab:
    def __init__(self, width: int, height: int):
        self.scroll = 0
        with open("src/browser.css") as f:
            self.default_style_sheet = CSSParser(f.read()).parse()
        self.history = History()
        self.width = width
        self.height = height
        self.url = None
        self.font_ratio = FONT_RATIO
        self.forcus: Union[Element, None] = None

    def load(self, url: str, body: Union[str, None] = None):
        self.history.append(url)
        header, body, _ = request(url, self.url, payload=body)
        print("header\n", header)
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
            try:
                _, body, _ = request(resolve_url(link, self.url), self.url)
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


class Browser:
    def __init__(self):
        self.width = WIDTH
        self.height = HEIGHT
        self.hstep = HSTEP
        self.vstep = VSTEP
        self.tabs: List[Tab] = []  # type: ignore
        self.active_tab: Union[None, int] = None  # type: ignore
        self.forcus = None
        self.address_bar = ""

        self.window = tkinter.Tk()
        self.window.bind("<Down>", self.handle_down)
        self.window.bind("<Up>", self.handle_up)
        self.window.bind("<Right>", self.handle_fontup)
        self.window.bind("<Left>", self.handle_fontdown)
        self.window.bind("<MouseWheel>", self.handle_scroll)
        self.window.bind("<Button-1>", self.handle_click)
        self.window.bind("<Button-3>", self.handle_middle_click)
        self.window.bind("<Key>", self.handle_key)
        self.window.bind("<BackSpace>", self.handle_backspace)
        self.window.bind("<Return>", self.handle_return)
        self.window.bind("<Configure>", self.handle_resize)
        # For Linux
        # self.window.bind("<Button-5>", self.scrolldown)
        # self.window.bind("<Button-4>", self.scrollup)
        self.canvas = tkinter.Canvas(
            self.window, width=self.width, height=self.height, bg="white"
        )
        self.canvas.pack(fill=tkinter.BOTH, expand=True)
        with open("src/browser.css") as f:
            self.default_style_sheet = CSSParser(f.read()).parse()

    def load(self, url: str):
        print("browser load")
        new_tab = Tab(self.width, self.height)
        new_tab.load(url)
        self.active_tab = len(self.tabs)
        self.tabs.append(new_tab)
        self.draw()

    def draw(self):
        self.canvas.delete("all")

        tabfont = get_font(None, 20, "normal", "roman")
        buttonfont = get_font(None, 30, "normal", "roman")
        self._draw_tab()
        self._draw_tab_bar(tabfont, buttonfont)
        self._draw_back_button()
        self._draw_forward_button()
        self._draw_address_bar(buttonfont)

    def _draw_tab(self):
        # タブの描画
        assert self.active_tab is not None
        self.tabs[self.active_tab].draw(self.canvas)
        self.canvas.create_rectangle(
            0, 0, self.width, CHROME_PX, fill="white", outline="white"
        )

    def _draw_tab_bar(self, tabfont, buttonfont):
        # タブバーの描画
        for i, tab in enumerate(self.tabs):
            name = "Tab {}".format(i)
            x1, x2 = 40 + 80 * i, 120 + 80 * i
            self.canvas.create_line(x1, 0, x1, 40, fill="black")
            self.canvas.create_line(x2, 0, x2, 40, fill="black")
            self.canvas.create_text(
                x1 + 10, 10, anchor="nw", text=name, font=tabfont, fill="black"
            )
            if i == self.active_tab:
                self.canvas.create_line(0, 40, x1, 40, fill="black")
                self.canvas.create_line(x2, 40, self.width, 40, fill="black")
        self.canvas.create_rectangle(10, 10, 30, 30, outline="black", width=1)
        self.canvas.create_text(
            11, 0, anchor="nw", text="+", font=buttonfont, fill="black"
        )

    def _draw_back_button(self):
        # 戻るボタンの描画
        assert self.active_tab is not None
        self.canvas.create_rectangle(10, 50, 35, 90, outline="black", width=1)
        fill = "black" if self.tabs[self.active_tab].history.has_previous() else "gray"
        self.canvas.create_polygon(16, 70, 30, 55, 30, 85, fill=fill)

    def _draw_forward_button(self):
        # 進むボタンの描画
        assert self.active_tab is not None
        self.canvas.create_rectangle(40, 50, 65, 90, outline="black", width=1)
        fill = "black" if self.tabs[self.active_tab].history.has_next() else "gray"
        self.canvas.create_polygon(45, 55, 59, 70, 45, 85, fill=fill)

    def _draw_address_bar(self, buttonfont):
        # アドレスバーの描画
        self.canvas.create_rectangle(
            70, 50, self.width - 10, 90, outline="black", width=1
        )
        if self.forcus == "address_bar":
            self.canvas.create_text(
                85,
                55,
                anchor="nw",
                text=self.address_bar,
                font=buttonfont,
                fill="black",
            )
            w = buttonfont.measure(self.address_bar)
            self.canvas.create_line(85 + w, 55, 85 + w, 90, fill="black")
        else:
            assert self.active_tab is not None
            url = self.tabs[self.active_tab].url
            assert url is not None
            self.canvas.create_text(
                85, 55, anchor="nw", text=url, font=buttonfont, fill="black"
            )

    def handle_click(self, e: tkinter.Event):
        self.forcus = None
        if e.y < CHROME_PX:
            if 40 <= e.x < 40 + 80 * len(self.tabs) and 0 <= e.y < 40:
                print("active tab click", e.x, e.y)
                self.active_tab = (e.x - 40) // 80
            elif 10 <= e.x < 35 and 10 <= e.y < 30:
                print("new tab click", e.x, e.y)
                self.load("https://browser.engineering/")
            elif 10 <= e.x < 35 and 40 <= e.y < 90:
                print("back click", e.x, e.y)
                assert self.active_tab is not None
                self.tabs[self.active_tab].go_back()
            elif 40 <= e.x < 65 and 40 <= e.y < 90:
                print("forward click", e.x, e.y)
                assert self.active_tab is not None
                self.tabs[self.active_tab].go_forward()
            elif 80 <= e.x < WIDTH - 10 and 40 <= e.y < 90:
                print("address bar click", e.x, e.y)
                self.forcus = "address_bar"
                self.address_bar = ""
        else:
            assert self.active_tab is not None
            self.forcus = "content"
            self.tabs[self.active_tab].click(e.x, e.y - CHROME_PX)
        self.draw()

    def handle_middle_click(self, e: tkinter.Event):
        self.forcus = None
        if e.y < CHROME_PX:
            if 40 <= e.x < 40 + 80 * len(self.tabs) and 0 <= e.y < 40:
                # TODO: delete tab
                self.active_tab = (e.x - 40) // 80
            elif 10 <= e.x < 35 and 10 <= e.y < 30:
                # TODO: delete tab
                print("new tab click", e.x, e.y)
                pass
            elif 10 <= e.x < 35 and 40 <= e.y < 90:
                assert self.active_tab is not None
                url = self.tabs[self.active_tab].history.get_previous()
                if url:
                    self.load(url)
            elif 40 <= e.x < 65 and 40 <= e.y < 90:
                assert self.active_tab is not None
                url = self.tabs[self.active_tab].history.get_next()
                if url:
                    self.load(url)
            elif 80 <= e.x < WIDTH - 10 and 40 <= e.y < 90:
                pass
        else:
            assert self.active_tab is not None
            url = self.tabs[self.active_tab].click(e.x, e.y - CHROME_PX)
            if url is not None:
                self.load(url)
        self.draw()

    def handle_key(self, e: tkinter.Event):
        if len(e.char) == 0:
            return
        if not (0x20 <= ord(e.char) < 0x7F):
            return

        if self.forcus == "address_bar":
            self.address_bar += e.char
            self.draw()
        elif self.forcus == "content":
            assert self.active_tab is not None
            self.tabs[self.active_tab].keypress(e.char)
            self.draw()

    def handle_backspace(self, e: tkinter.Event):
        if self.forcus == "address_bar":
            self.address_bar = self.address_bar[:-1]
            self.draw()
        elif self.forcus == "content":
            assert self.active_tab is not None
            self.tabs[self.active_tab].backspace()
            self.draw()

    def handle_return(self, e: tkinter.Event):
        if self.forcus == "address_bar":
            assert self.active_tab is not None
            self.tabs[self.active_tab].load(self.address_bar)
            self.forcus = None
            self.draw()

    def handle_down(self, e: tkinter.Event):
        assert self.active_tab is not None
        self.tabs[self.active_tab].scrolldown()
        self.draw()

    def handle_up(self, e: tkinter.Event):
        assert self.active_tab is not None
        self.tabs[self.active_tab].scrollup()
        self.draw()

    def handle_scroll(self, e: tkinter.Event):
        if e.delta > 0:
            self.handle_up(e)
        else:
            self.handle_down(e)

    def handle_resize(self, e: tkinter.Event):
        print("resize")
        if e.width > 1:
            self.width = e.width
            self.height = e.height
            # layout -> paint -> draw
            for tab in self.tabs:
                # TODO: 全てのタブのレイアウトを再計算する。再計算を非同期にして、アクティブタブのレイアウトの再計算が終了したらdrawする
                tab.resize(self.width, self.height)
            self.draw()

    def handle_fontup(self, e: tkinter.Event):
        print("fontup")
        assert self.active_tab is not None
        self.tabs[self.active_tab].fontup()
        self.draw()

    def handle_fontdown(self, e: tkinter.Event):
        print("fontdown")
        assert self.active_tab is not None
        self.tabs[self.active_tab].fontdown()
        self.draw()


if __name__ == "__main__":
    browser = Browser()
    browser.load(sys.argv[1])
    tkinter.mainloop()
