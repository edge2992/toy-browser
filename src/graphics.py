import tkinter
import tkinter.font
import sys
from layout import Layout

from src.browser import request
from src.text import HTMLParser

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
        self.canvas = tkinter.Canvas(self.window, width=self.width, height=self.height)
        self.canvas.pack(fill=tkinter.BOTH, expand=True)

    def load(self, url: str):
        _, body, _ = request(url)
        self.nodes = HTMLParser(body).parse()
        layout = Layout(self.nodes, self.width, self.hstep)
        self.display_list = layout.display_list
        self.max_scroll = layout.max_scroll
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        for x, y, c, f in self.display_list:
            if y > self.scroll + self.height:
                continue
            if y + self.vstep < self.scroll:
                continue
            self.canvas.create_text(x, y - self.scroll, text=c, font=f, anchor="nw")

    def scrolldown(self, e):
        print("scrolldown")
        self.scroll += SCROLL_STEP
        self.scroll = min(self.max_scroll, self.scroll)
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
        self.display_list = Layout(self.nodes, self.width, self.hstep).display_list
        self.draw()

    def fontup(self, e):
        # TODO: Layoutクラスにhstepとvstepを渡す
        self.font = self.font + 1
        self.hstep += 2
        self.vstep += 2
        print("fontup")
        self.display_list = Layout(self.nodes, self.width, self.hstep).display_list
        self.draw()

    def fontdown(self, e):
        # TODO: Layoutクラスにhstepとvstepを渡す
        self.font = self.font - 1
        self.hstep -= 2
        self.vstep -= 2
        print("fontdown")
        self.display_list = Layout(self.nodes, self.width, self.hstep).display_list
        self.draw()


if __name__ == "__main__":
    browser = Browser()
    browser.load(sys.argv[1])
    tkinter.mainloop()
