from __future__ import annotations

import sys
import tkinter
import tkinter.font
from enum import Enum, auto
from typing import List, Union

from src.cssparser import CSSParser
from src.layout import get_font
from src.graphics.tab import Tab
from src.global_value import (
    WIDTH,
    HEIGHT,
    HSTEP,
    VSTEP,
    CHROME_PX,
)


class Forcus(Enum):
    ADDRESS_BAR = auto()
    CONTENT = auto()
    NONE = auto()


class Browser:
    def __init__(self):
        self.width = WIDTH
        self.height = HEIGHT
        self.hstep = HSTEP
        self.vstep = VSTEP
        self.tabs: List[Tab] = []  # type: ignore
        self.active_tab: Union[None, int] = None  # type: ignore
        self.forcus: Forcus = Forcus.NONE
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
        if self.forcus == Forcus.ADDRESS_BAR:
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
        self.forcus = Forcus.NONE
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
                self.forcus = Forcus.ADDRESS_BAR
                self.address_bar = ""
        else:
            assert self.active_tab is not None
            self.forcus = Forcus.CONTENT
            self.tabs[self.active_tab].click(e.x, e.y - CHROME_PX)
        self.draw()

    def handle_middle_click(self, e: tkinter.Event):
        self.forcus = Forcus.NONE
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

        if self.forcus == Forcus.ADDRESS_BAR:
            self.address_bar += e.char
            self.draw()
        elif self.forcus == Forcus.CONTENT:
            assert self.active_tab is not None
            self.tabs[self.active_tab].keypress(e.char)
            self.draw()

    def handle_backspace(self, e: tkinter.Event):
        if self.forcus == Forcus.ADDRESS_BAR:
            self.address_bar = self.address_bar[:-1]
            self.draw()
        elif self.forcus == Forcus.CONTENT:
            assert self.active_tab is not None
            self.tabs[self.active_tab].backspace()
            self.draw()

    def handle_return(self, e: tkinter.Event):
        if self.forcus == Forcus.ADDRESS_BAR:
            assert self.active_tab is not None
            self.tabs[self.active_tab].load(self.address_bar)
            self.forcus = Forcus.NONE
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
        if e.width > 1 and (self.width != e.width or self.height != e.height):
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
