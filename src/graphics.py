import tkinter
import tkinter.font
import sys
from typing import List

from src.layout import DocumentLayout
from src.browser import request
from src.text import Element, HTMLParser
from src.draw import Draw
from src.cssparser import style, CSSParser
from src.util.node import tree_to_list
from src.util.url import resolve_url
from src.selector import cascade_priority

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100


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
        self.window = tkinter.Tk()
        self.window.bind("<Down>", self.scrolldown)
        self.window.bind("<Up>", self.scrollup)
        self.window.bind("<Right>", self.fontup)
        self.window.bind("<Left>", self.fontdown)
        self.window.bind("<Button-5>", self.scrolldown)
        self.window.bind("<Button-4>", self.scrollup)
        # self.window.bind(
        #     "<Configure>", self.resize
        # )  # TODO: キャンバス生成時に3回呼ばれてレンダリングし直してしまう
        self.canvas = tkinter.Canvas(
            self.window, width=self.width, height=self.height, bg="white"
        )
        self.canvas.pack(fill=tkinter.BOTH, expand=True)
        with open("src/browser.css") as f:
            self.default_style_sheet = CSSParser(f.read()).parse()

    def load(self, url: str):
        _, body, _ = request(url)
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
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        for cmd in self.display_list:
            if cmd.top > self.scroll + self.height:
                continue
            if cmd.bottom < self.scroll:
                continue
            cmd.execute(self.scroll, self.canvas)

    def scrolldown(self, e):
        print("scrolldown")
        max_y = self.document.height - self.height
        self.scroll = min(self.scroll + SCROLL_STEP, max_y)
        self.draw()

    def scrollup(self, e):
        print("scrollup")
        self.scroll -= SCROLL_STEP
        self.scroll = max(self.scroll, self.min_scroll)
        self.draw()

    def resize(self, e):
        self.width = e.width
        self.height = e.height
        print("resize")
        self.document.layout()
        self.display_list = []
        self.document.paint(self.display_list)
        self.draw()

    def fontup(self, e):
        # TODO: Layoutクラスにhstepとvstepを渡す
        self.font = self.font + 1
        self.hstep += 2
        self.vstep += 2
        print("fontup")
        self.document.layout()
        self.display_list = []
        self.document.paint(self.display_list)
        self.draw()

    def fontdown(self, e):
        # TODO: Layoutクラスにhstepとvstepを渡す
        self.font = self.font - 1
        self.hstep -= 2
        self.vstep -= 2
        print("fontdown")
        self.document.layout()
        self.display_list = []
        self.document.paint(self.display_list)
        self.draw()


if __name__ == "__main__":
    browser = Browser()
    browser.load(sys.argv[1])
    tkinter.mainloop()
