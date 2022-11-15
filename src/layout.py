import tkinter
import tkinter.font
from typing import Dict, List, Tuple, Union
from src.text import Tag, Text
from tqdm import tqdm
import time

HSTEP, VSTEP = 13, 18
FONTS: Dict[Tuple[int, str, str], tkinter.font.Font] = {}  # font cache
FONT_METRICS: Dict[Tuple[int, str, str], dict] = {}


def get_font(size: int, weight: str, slant: str) -> tkinter.font.Font:
    key = (size, weight, slant)
    if key not in FONTS:
        FONTS[key] = tkinter.font.Font(size=size, weight=weight, slant=slant)  # type: ignore
    return FONTS[key]


def get_font_metric(size: int, weight: str, slant: str) -> dict:
    key = (size, weight, slant)
    if key not in FONT_METRICS:
        FONT_METRICS[key] = get_font(size, weight, slant).metrics()  # type: ignore
    return FONT_METRICS[key]


class Layout:
    def __init__(self, tokens: List[Union[Text, Tag]], width: int, hstep: int):
        self.display_list: List[Tuple[int, int, str, tkinter.font.Font]] = []
        self.line: List[Tuple[int, str, tkinter.font.Font]] = []
        self.font_metrics: List[dict] = []
        self.cursor_x = HSTEP
        self.cursor_y = VSTEP
        self.weight = "normal"
        self.style = "roman"
        self.size = 16
        self.width = width
        self.hstep = hstep
        self.max_scroll = 0
        for tok in tqdm(tokens):
            self.token(tok)

    def token(self, tok):
        if isinstance(tok, Text):
            self.text(tok)
        elif tok.tag == "i":
            self.style = "italic"
        elif tok.tag == "/i":
            self.style = "roman"
        elif tok.tag == "b":
            self.weight = "bold"
        elif tok.tag == "/b":
            self.weight = "normal"
        elif tok.tag == "small":
            self.size -= 2
        elif tok.tag == "/small":
            self.size += 2
        elif tok.tag == "big":
            self.size += 2
        elif tok.tag == "/big":
            self.size -= 2
        elif tok.tag == "br":
            self.flush()
        elif tok.tag == "/p":
            self.flush()
            self.cursor_y += VSTEP

    def text(self, tok):
        # English
        font = get_font(self.size, self.weight, self.style)
        metric = get_font_metric(self.size, self.weight, self.style)
        for word in tok.text.split():
            self.max_scroll = max(self.max_scroll, self.cursor_y)
            w = font.measure(word)
            if self.cursor_x + w > self.width - self.hstep:
                self.flush()
            self.line.append((self.cursor_x, word, font))
            self.font_metrics.append(metric)
            self.cursor_x += w + font.measure(" ")

        # Chinese
        # font = get_font(self.size, self.weight, self.style)
        # for c in tok.text:
        #     self.max_scroll = max(self.max_scroll, self.cursor_y)
        #     w = font.measure(c)
        #     if self.cursor_x >= self.width - self.hstep:
        #         self.flush()
        #     self.line.append((self.cursor_x, c, font))
        #     self.cursor_x += w

    def flush(self):
        if not self.line:
            return
        # metrics = [font.metrics() for _, _, font in self.line]

        max_ascent = max([metric["ascent"] for metric in self.font_metrics])
        baseline = self.cursor_y + 1.25 * max_ascent
        assert len(self.line) == len(self.font_metrics)
        for (x, word, font), metric in zip(self.line, self.font_metrics):
            y = int(baseline - metric["ascent"])
            self.display_list.append((x, y, word, font))

        max_descent = max([metric["descent"] for metric in self.font_metrics])
        self.cursor_x = HSTEP
        self.cursor_y = baseline + 1.25 * max_descent
        self.line = []
        self.font_metrics = []
