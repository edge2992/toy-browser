from __future__ import annotations

import ctypes
import math
import sys
from enum import Enum, auto
from typing import List

import sdl2
import skia

from src.cssparser import CSSParser
from src.global_value import CHROME_PX, HEIGHT, HSTEP, VSTEP, WIDTH
from src.graphics.tab import Tab
from src.util.draw_skia import draw_line, draw_rect, draw_text, parse_color


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
        self.active_tab: int
        self.forcus: Forcus = Forcus.NONE
        self.address_bar = ""
        self.chrome_surface = skia.Surface(self.width, CHROME_PX)
        self.tab_surface: skia.Surface

        if sdl2.SDL_BYTEORDER == sdl2.SDL_BIG_ENDIAN:
            self.RED_MASK = 0xFF000000
            self.GREEN_MASK = 0x00FF0000
            self.BLUE_MASK = 0x0000FF00
            self.ALPHA_MASK = 0x000000FF
        else:
            self.RED_MASK = 0x000000FF
            self.GREEN_MASK = 0x0000FF00
            self.BLUE_MASK = 0x00FF0000
            self.ALPHA_MASK = 0xFF000000

        self.root_surface = skia.Surface.MakeRaster(
            skia.ImageInfo.Make(
                self.width,
                self.height,
                ct=skia.kRGBA_8888_ColorType,
                at=skia.kPremul_AlphaType,
            )
        )
        self.sdl_window = sdl2.SDL_CreateWindow(
            b"Browser",
            sdl2.SDL_WINDOWPOS_CENTERED,
            sdl2.SDL_WINDOWPOS_CENTERED,
            self.width,
            self.height,
            sdl2.SDL_WINDOW_SHOWN,
        )
        with open("src/browser.css") as f:
            self.default_style_sheet = CSSParser(f.read()).parse()

    def load(self, url: str):
        print("browser load")
        new_tab = Tab(self.width, self.height)
        new_tab.load(url)
        self.active_tab = len(self.tabs)
        self.tabs.append(new_tab)
        self.raster_chrome()
        self.raster_tab()
        self.draw()

    def raster_tab(self):
        active_tab = self.tabs[self.active_tab]
        tab_height = math.ceil(active_tab.document.height)

        if not hasattr(self, "tab_surface") or tab_height != self.tab_surface.height():
            self.tab_surface = skia.Surface(self.width, tab_height)

        canvas = self.tab_surface.getCanvas()
        canvas.clear(skia.ColorWHITE)
        active_tab.raster(canvas)

    def raster_chrome(self):
        canvas = self.chrome_surface.getCanvas()
        canvas.clear(skia.ColorWHITE)

        self.__raster_tab_bar(canvas)
        self.__raster_address_bar(canvas)
        self.__raster_back_button(canvas)
        self.__raster_forward_button(canvas)

    def draw(self):
        canvas = self.root_surface.getCanvas()
        canvas.clear(skia.ColorWHITE)

        tab_rect = skia.Rect.MakeLTRB(0, CHROME_PX, self.width, self.height)
        tab_offset = CHROME_PX - self.tabs[self.active_tab].scroll
        canvas.save()
        canvas.clipRect(tab_rect)
        canvas.translate(0, tab_offset)
        self.tab_surface.draw(canvas, 0, 0)
        canvas.restore()

        chrome_rect = skia.Rect.MakeLTRB(0, 0, self.width, CHROME_PX)
        canvas.save()
        canvas.clipRect(chrome_rect)
        self.chrome_surface.draw(canvas, 0, 0)
        canvas.restore()

        # This makes an image interface to the Skia surface, but
        # doesn't copy the data.
        skia_image = self.root_surface.makeImageSnapshot()
        skia_bytes = skia_image.tobytes()

        depth = 32
        pitch = 4 * self.width
        sdl_surface = sdl2.SDL_CreateRGBSurfaceFrom(
            skia_bytes,
            self.width,
            self.height,
            depth,
            pitch,
            self.RED_MASK,
            self.GREEN_MASK,
            self.BLUE_MASK,
            self.ALPHA_MASK,
        )
        rect = sdl2.SDL_Rect(0, 0, self.width, self.height)
        window_surface = sdl2.SDL_GetWindowSurface(self.sdl_window)
        # SDL_BlitSurface its what actually does the copy
        sdl2.SDL_BlitSurface(sdl_surface, rect, window_surface, rect)
        sdl2.SDL_UpdateWindowSurface(self.sdl_window)

    def __raster_tab_bar(self, canvas):
        # タブバーの描画
        tabfont = skia.Font(skia.Typeface("Arial"), 20)
        buttonfont = skia.Font(skia.Typeface("Arial"), 30)

        for i, tab in enumerate(self.tabs):
            name = "Tab {}".format(i)
            x1, x2 = 40 + 80 * i, 120 + 80 * i
            draw_line(canvas, x1, 0, x1, 40)
            draw_line(canvas, x2, 0, x2, 40)
            draw_text(canvas, x1 + 10, 10, name, tabfont)
            if i == self.active_tab:
                draw_line(canvas, 0, 40, x1, 40)
                draw_line(canvas, x2, 40, self.width, 40)

        draw_rect(canvas, 10, 10, 30, 30)
        draw_text(canvas, 11, 4, "+", buttonfont)

    def __raster_back_button(self, canvas):
        # 戻るボタンの描画
        draw_rect(canvas, 10, 50, 35, 90)
        fill = "black" if self.tabs[self.active_tab].history.has_previous() else "gray"
        path = skia.Path().moveTo(15, 70).lineTo(30, 55).lineTo(30, 85)
        paint = skia.Paint(Color=parse_color(fill), Style=skia.Paint.kFill_Style)
        canvas.drawPath(path, paint)

    def __raster_forward_button(self, canvas):
        # 進むボタンの描画
        draw_rect(canvas, 40, 50, 65, 90)
        fill = "black" if self.tabs[self.active_tab].history.has_next() else "gray"
        path = skia.Path().moveTo(45, 55).lineTo(59, 70).lineTo(45, 85)
        paint = skia.Paint(Color=parse_color(fill), Style=skia.Paint.kFill_Style)
        canvas.drawPath(path, paint)

    def __raster_address_bar(self, canvas):
        # アドレスバーの描画
        buttonfont = skia.Font(skia.Typeface("Arial"), 30)

        draw_rect(canvas, 70, 50, self.width - 10, 90)
        if self.forcus == Forcus.ADDRESS_BAR:
            draw_text(
                canvas,
                85,
                55,
                self.address_bar,
                buttonfont,
            )
            w = buttonfont.measureText(self.address_bar)
            draw_line(canvas, 85 + w, 55, 85 + w, 90)
        else:
            url = self.tabs[self.active_tab].url
            draw_text(canvas, 85, 55, url, buttonfont)

    def handle_click(self, e: sdl2.events.SDL_MouseButtonEvent):
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
            self.raster_chrome()
        else:
            assert self.active_tab is not None
            self.forcus = Forcus.CONTENT
            self.tabs[self.active_tab].click(e.x, e.y - CHROME_PX)
            self.raster_tab()
        self.draw()

    def handle_middle_click(self, e: sdl2.events.SDL_MouseButtonEvent):
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
            self.raster_chrome()
        else:
            assert self.active_tab is not None
            url = self.tabs[self.active_tab].click(e.x, e.y - CHROME_PX)
            if url is not None:
                self.load(url)
            self.raster_tab()
        self.draw()

    def handle_key(self, key: str):
        if len(key) == 0:
            return
        if not (0x20 <= ord(key) < 0x7F):
            return

        if self.forcus == Forcus.ADDRESS_BAR:
            self.address_bar += key
            self.draw()
        elif self.forcus == Forcus.CONTENT:
            assert self.active_tab is not None
            self.tabs[self.active_tab].keypress(key)
            self.draw()

    def handle_backspace(self, e):
        if self.forcus == Forcus.ADDRESS_BAR:
            self.address_bar = self.address_bar[:-1]
            self.draw()
        elif self.forcus == Forcus.CONTENT:
            assert self.active_tab is not None
            self.tabs[self.active_tab].backspace()
            self.draw()

    def handle_return(self, e):
        if self.forcus == Forcus.ADDRESS_BAR:
            assert self.active_tab is not None
            self.tabs[self.active_tab].load(self.address_bar)
            self.forcus = Forcus.NONE
            self.draw()

    def handle_down(self, e):
        assert self.active_tab is not None
        self.tabs[self.active_tab].scrolldown()
        self.draw()

    def handle_up(self, e):
        assert self.active_tab is not None
        self.tabs[self.active_tab].scrollup()
        self.draw()

    def handle_scroll(self, delta: float):
        if delta > 0:
            self.handle_up(delta)
        else:
            self.handle_down(delta)

    def handle_resize(self, e):
        print("resize")
        if e.width > 1 and (self.width != e.width or self.height != e.height):
            self.width = e.width
            self.height = e.height
            # layout -> paint -> draw
            for tab in self.tabs:
                # TODO: 全てのタブのレイアウトを再計算する。再計算を非同期にして、アクティブタブのレイアウトの再計算が終了したらdrawする
                tab.resize(self.width, self.height)
            self.draw()

    def handle_fontup(self, e):
        print("fontup")
        assert self.active_tab is not None
        self.tabs[self.active_tab].fontup()
        self.draw()

    def handle_fontdown(self, e):
        print("fontdown")
        assert self.active_tab is not None
        self.tabs[self.active_tab].fontdown()
        self.draw()

    def handle_quit(self):
        sdl2.SDL_DestroyWindow(self.sdl_window)


if __name__ == "__main__":
    sdl2.SDL_Init(sdl2.SDL_INIT_EVENTS)
    browser = Browser()
    browser.load(sys.argv[1])
    event = sdl2.SDL_Event()
    while True:
        while sdl2.SDL_PollEvent(ctypes.byref(event)) != 0:
            if event.type == sdl2.SDL_QUIT:
                browser.handle_quit()
                sdl2.SDL_Quit()
                sys.exit()
            elif event.type == sdl2.SDL_MOUSEBUTTONUP:
                if event.button.button == sdl2.SDL_BUTTON_LEFT:
                    browser.handle_click(event.button)
                elif event.button.button == sdl2.SDL_BUTTON_MIDDLE:
                    browser.handle_middle_click(event.button)
            elif event.type == sdl2.SDL_MOUSEWHEEL:
                browser.handle_scroll(event.wheel.preciseY)
            elif event.type == sdl2.SDL_KEYDOWN:
                if event.key.keysym.sym == sdl2.SDLK_RETURN:
                    browser.handle_return(event.key)
                elif event.key.keysym.sym == sdl2.SDLK_BACKSPACE:
                    browser.handle_backspace(event.key)
                elif event.key.keysym.sym == sdl2.SDLK_DOWN:
                    browser.handle_down(event.key)
                elif event.key.keysym.sym == sdl2.SDLK_UP:
                    browser.handle_up(event.key)
                elif event.key.keysym.sym == sdl2.SDLK_RIGHT:
                    browser.handle_fontup(event.key)
                elif event.key.keysym.sym == sdl2.SDLK_LEFT:
                    browser.handle_fontdown(event.key)
            elif event.type == sdl2.SDL_TEXTINPUT:
                browser.handle_key(event.text.text.decode("utf8"))
