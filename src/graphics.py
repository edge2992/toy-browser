import tkinter
import sys
from typing import List, Tuple

from src.browser import lex, request

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100


class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        self.window.bind("<Down>", self.scrolldown)
        self.window.bind("<Up>", self.scrollup)
        self.window.bind("<Button-5>", self.scrolldown)
        self.window.bind("<Button-4>", self.scrollup)
        self.canvas = tkinter.Canvas(self.window, width=WIDTH, height=HEIGHT)
        self.canvas.pack()
        self.scroll = 0
        self.min_scroll = 0
        self.max_scroll = 0

    def load(self, url: str):
        _, body, _ = request(url)
        text = lex(body)
        self.display_list = self.layout(text)
        self.draw()

    def layout(self, text: str) -> List[Tuple[int, int, str]]:
        display_list: List[Tuple[int, int, str]] = []
        cursor_x, cursor_y = HSTEP, VSTEP
        for c in text:
            self.max_scroll = max(self.max_scroll, cursor_y)
            display_list.append((cursor_x, cursor_y, c))
            cursor_x += HSTEP
            if cursor_x >= WIDTH - HSTEP:
                cursor_y += VSTEP
                cursor_x = HSTEP
        return display_list

    def draw(self):
        self.canvas.delete("all")
        for x, y, c in self.display_list:
            if y > self.scroll + HEIGHT:
                continue
            if y + VSTEP < self.scroll:
                continue
            self.canvas.create_text(x, y - self.scroll, text=c)

    def scrolldown(self, e):
        self.scroll += SCROLL_STEP
        self.scroll = min(self.max_scroll, self.scroll)
        self.draw()

    def scrollup(self, e):
        self.scroll -= SCROLL_STEP
        self.scroll = max(self.scroll, self.min_scroll)
        self.draw()


if __name__ == "__main__":
    browser = Browser()
    browser.load(sys.argv[1])
    tkinter.mainloop()
