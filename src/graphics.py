import tkinter
import sys
from typing import List, Tuple

from src.browser import lex, request

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
        self.window.bind("<Configure>", self.resize)
        self.canvas = tkinter.Canvas(self.window, width=self.width, height=self.height)
        self.canvas.pack(fill=tkinter.BOTH, expand=True)

    def load(self, url: str):
        _, body, _ = request(url)
        self.text = lex(body)
        self.display_list = self.layout(self.text)
        self.draw()

    def layout(self, text: str) -> List[Tuple[int, int, str]]:
        display_list: List[Tuple[int, int, str]] = []
        cursor_x, cursor_y = self.hstep, self.vstep
        for c in text:
            self.max_scroll = max(self.max_scroll, cursor_y)
            display_list.append((cursor_x, cursor_y, c))
            cursor_x += self.hstep
            if cursor_x >= self.width - self.hstep:
                cursor_y += self.vstep
                cursor_x = self.hstep
        return display_list

    def draw(self):
        self.canvas.delete("all")
        for x, y, c in self.display_list:
            if y > self.scroll + self.height:
                continue
            if y + self.vstep < self.scroll:
                continue
            self.canvas.create_text(
                x, y - self.scroll, text=c, font=("Times", self.font)
            )

    def scrolldown(self, e):
        self.scroll += SCROLL_STEP
        self.scroll = min(self.max_scroll, self.scroll)
        self.draw()

    def scrollup(self, e):
        self.scroll -= SCROLL_STEP
        self.scroll = max(self.scroll, self.min_scroll)
        self.draw()

    def resize(self, e):
        self.width = e.width
        self.height = e.height
        self.display_list = self.layout(self.text)
        self.draw()

    def fontup(self, e):
        self.font = self.font + 1
        self.hstep += 2
        self.vstep += 2
        self.display_list = self.layout(self.text)
        self.draw()

    def fontdown(self, e):
        self.font = self.font - 1
        self.hstep -= 2
        self.vstep -= 2
        self.display_list = self.layout(self.text)
        self.draw()


if __name__ == "__main__":
    browser = Browser()
    browser.load(sys.argv[1])
    tkinter.mainloop()
