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


class Tab:
    def __init__(self):
        self.scroll = 0
        with open("src/browser.css") as f:
            self.default_style_sheet = CSSParser(f.read()).parse()
        self.history: List[str] = []

    def load(self, url: str):
        self.history.append(url)
        _, body, _ = request(url)
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

        self.document = DocumentLayout(self.nodes)
        self.document.layout()
        self.display_list: List[Draw] = []
        self.document.paint(self.display_list)

    def draw(self, canvas: tkinter.Canvas):
        for cmd in self.display_list:
            if cmd.top > self.scroll + HEIGHT - CHROME_PX:
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
                return self.load(url)

            elt = elt.parent

    def go_back(self):
        if len(self.history) > 1:
            self.history.pop()
            self.load(self.history.pop())

    def scrolldown(self):
        max_y = self.document.height - (HEIGHT - CHROME_PX)
        self.scroll = min(self.scroll + SCROLL_STEP, max_y)

    def scrollup(self):
        self.scroll -= SCROLL_STEP
        self.scroll = max(self.scroll, 0)

    def __repr__(self) -> str:
        return "Tab"


class Browser:
    def __init__(self):
        self.scroll = 0
        self.min_scroll = 0
        self.max_scroll = 0
        self.font = 12
        self.width = WIDTH
        self.height = HEIGHT
        self.hstep = HSTEP
        self.vstep = VSTEP
        self.url: Union[str, None] = None
        self.window = tkinter.Tk()
        self.window.bind("<Down>", self.handle_down)
        self.window.bind("<Up>", self.handle_up)
        self.window.bind("<Button-1>", self.handle_click)
        # self.window.bind("<Button-5>", self.scrolldown)
        # self.window.bind("<Button-4>", self.scrollup)
        # self.window.bind("<Right>", self.fontup)
        # self.window.bind("<Left>", self.fontdown)
        # self.window.bind(
        #     "<Configure>", self.resize
        # )  # TODO: キャンバス生成時に3回呼ばれてレンダリングし直してしまう
        self.canvas = tkinter.Canvas(
            self.window, width=self.width, height=self.height, bg="white"
        )
        self.canvas.pack(fill=tkinter.BOTH, expand=True)
        with open("src/browser.css") as f:
            self.default_style_sheet = CSSParser(f.read()).parse()
        self.tabs = []
        self.active_tab = None

    def load(self, url: str):
        new_tab = Tab()
        new_tab.load(url)
        self.active_tab = len(self.tabs)
        self.tabs.append(new_tab)
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        assert self.active_tab is not None
        # タブ描画
        self.tabs[self.active_tab].draw(self.canvas)
        self.canvas.create_rectangle(
            0, 0, WIDTH, CHROME_PX, fill="white", outline="white"
        )
        tabfont = get_font(20, "normal", "roman")
        # タブバー描画
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
                self.canvas.create_line(x2, 40, WIDTH, 40, fill="black")
        buttonfont = get_font(30, "normal", "roman")
        self.canvas.create_rectangle(10, 10, 30, 30, outline="black", width=1)
        self.canvas.create_text(
            11, 0, anchor="nw", text="+", font=buttonfont, fill="black"
        )
        # URL表示
        self.canvas.create_rectangle(40, 50, WIDTH - 10, 90, outline="black", width=1)
        url = self.tabs[self.active_tab].url
        self.canvas.create_text(
            55, 55, anchor="nw", text=url, font=buttonfont, fill="black"
        )
        # 戻るボタン
        self.canvas.create_rectangle(10, 50, 35, 90, outline="black", width=1)
        self.canvas.create_polygon(16, 70, 30, 55, 30, 85, fill="black")

    def handle_click(self, e: tkinter.Event):
        if e.y < CHROME_PX:
            if 40 <= e.x < 40 + 80 * len(self.tabs) and 0 <= e.y < 40:
                self.active_tab = (e.x - 40) // 80
            elif 10 <= e.x < 30 and 10 <= e.y < 30:
                self.load("https://browser.engineering/")
            elif 10 <= e.x < 35 and 40 <= e.y < 90:
                assert self.active_tab is not None
                self.tabs[self.active_tab].go_back()
        else:
            assert self.active_tab is not None
            self.tabs[self.active_tab].click(e.x, e.y - CHROME_PX)
        self.draw()

    def handle_down(self, e: tkinter.Event):
        assert self.active_tab is not None
        self.tabs[self.active_tab].scrolldown()
        self.draw()

    def handle_up(self, e: tkinter.Event):
        assert self.active_tab is not None
        self.tabs[self.active_tab].scrollup()
        self.draw()

    # def resize(self, e: tkinter.Event):
    #     self.width = e.width
    #     self.height = e.height
    #     print("resize")
    #     self.document.layout()
    #     self.display_list = []
    #     self.document.paint(self.display_list)
    #     self.draw()

    # def fontup(self, e: tkinter.Event):
    #     # TODO: Layoutクラスにhstepとvstepを渡す
    #     self.font = self.font + 1
    #     self.hstep += 2
    #     self.vstep += 2
    #     print("fontup")
    #     self.document.layout()
    #     self.display_list = []
    #     self.document.paint(self.display_list)
    #     self.draw()

    # def fontdown(self, e: tkinter.Event):
    #     # TODO: Layoutクラスにhstepとvstepを渡す
    #     self.font = self.font - 1
    #     self.hstep -= 2
    #     self.vstep -= 2
    #     print("fontdown")
    #     self.document.layout()
    #     self.display_list = []
    #     self.document.paint(self.display_list)
    #     self.draw()


if __name__ == "__main__":
    browser = Browser()
    browser.load(sys.argv[1])
    tkinter.mainloop()
