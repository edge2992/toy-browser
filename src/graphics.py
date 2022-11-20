from __future__ import annotations
import tkinter
import tkinter.font
import sys
from typing import List, Union

from src.layout import DocumentLayout, get_font
from src.browser import request
from src.text import Element, HTMLParser, Text
from src.draw import Draw
from src.cssparser import style, CSSParser
from src.util.node import tree_to_list
from src.util.url import resolve_url
from src.selector import cascade_priority

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100
CHROME_PX = 100
FONT_RATIO: float = 0.75


class Tab:
    def __init__(self, width: int, height: int):
        self.scroll = 0
        with open("src/browser.css") as f:
            self.default_style_sheet = CSSParser(f.read()).parse()
        self.history: List[str] = []
        self.width = width
        self.height = height
        self.font_ratio = FONT_RATIO

    def load(self, url: str):
        self.history.append(url)
        header, body, _ = request(url)
        print("header\n", header)
        self.scroll = 0
        self.url = url
        self.nodes = HTMLParser(body).parse()
        links = [
            node.attributes["href"]
            for node in tree_to_list(self.nodes, [])
            if isinstance(node, Element)
            and node.tag == "link"
            and "href" in node.attributes
            and node.attributes.get("rel") == "stylesheet"
        ]
        rules = self.default_style_sheet.copy()
        for link in links:
            try:
                _, body, _ = request(resolve_url(link, url))
            except Exception as e:
                print(e)
                continue
            rules.extend(CSSParser(body).parse())
        style(self.nodes, sorted(rules, key=cascade_priority))
        self._layout()

    def _layout(self):
        # layout -> paint
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

    def click(self, x, y):
        y += self.scroll
        objs = [
            obj
            for obj in tree_to_list(self.document, [])
            if obj.x <= x < obj.x + obj.width and obj.y <= y < obj.y + obj.height
        ]
        if not objs:
            return
        elt = objs[-1].node
        while elt:
            if isinstance(elt, Text):
                pass
            elif isinstance(elt, Element) and "href" in elt.attributes:
                url = resolve_url(elt.attributes["href"], self.url)
                print("tab click", url)
                return self.load(url)

            elt = elt.parent

    def go_back(self):
        if len(self.history) > 1:
            self.history.pop()
            self.load(self.history.pop())

    def scrolldown(self):
        max_y = self.document.height - (self.height - CHROME_PX)
        self.scroll = min(self.scroll + SCROLL_STEP, max_y)

    def scrollup(self):
        self.scroll -= SCROLL_STEP
        self.scroll = max(self.scroll, 0)

    def fontup(self):
        self.font_ratio += 0.1
        self._layout()

    def fontdown(self):
        self.font_ratio -= 0.1
        self._layout()

    def resize(self, width, height):
        print("resizing tag...", width, height)
        if self.width != width:
            # widthを変更した場合には再レイアウトが必要
            self.width = width
            self._layout()

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
        self.window.bind("<Key>", self.handle_key)
        self.window.bind("<Enter>", self.handle_return)
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

        tabfont = get_font(20, "normal", "roman")
        buttonfont = get_font(30, "normal", "roman")
        self._draw_tab()
        self._draw_tab_bar(tabfont, buttonfont)
        self._draw_back_button()
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
        self.canvas.create_rectangle(10, 50, 35, 90, outline="black", width=1)
        self.canvas.create_polygon(16, 70, 30, 55, 30, 85, fill="black")

    def _draw_address_bar(self, buttonfont):
        # アドレスバーの描画
        self.canvas.create_rectangle(
            40, 50, self.width - 10, 90, outline="black", width=1
        )
        if self.forcus == "address bar":
            self.canvas.create_text(
                55,
                55,
                anchor="nw",
                text=self.address_bar,
                font=buttonfont,
                fill="black",
            )
            w = buttonfont.measure(self.address_bar)
            self.canvas.create_line(55 + w, 55, 55 + w, 90, fill="black")
        else:
            assert self.active_tab is not None
            url = self.tabs[self.active_tab].url
            self.canvas.create_text(
                55, 55, anchor="nw", text=url, font=buttonfont, fill="black"
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
            elif 50 <= e.x < WIDTH - 10 and 40 <= e.y < 90:
                print("address bar click", e.x, e.y)
                self.forcus = "address_bar"
                self.address_bar = ""
        else:
            assert self.active_tab is not None
            self.tabs[self.active_tab].click(e.x, e.y - CHROME_PX)
        self.draw()

    def handle_key(self, e: tkinter.Event):
        if len(e.char) == 0:
            return
        if not (0x20 <= ord(e.char) < 0x7F):
            return

        if self.forcus == "address bar":
            self.address_bar += e.char
            self.draw()

    def handle_return(self, e: tkinter.Event):
        if self.forcus == "address bar":
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
