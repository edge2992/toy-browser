from typing import List

import skia

from src.draw import Draw


class SaveLayer(Draw):
    def __init__(
        self,
        sk_paint: skia.Paint,
        children: List[Draw],
        should_save: bool = True,
        should_paint_cmds: bool = True,
    ):
        self.sk_paint = sk_paint
        self.children = children
        self.rect = skia.Rect.MakeEmpty()
        self.should_save = should_save
        self.should_paint_cmds = should_paint_cmds
        for cmd in self.children:
            self.rect.join(cmd.rect)

    def execute(self, canvas):
        if self.should_save:
            canvas.saveLayer(paint=self.sk_paint)
        if self.should_paint_cmds:
            for cmd in self.children:
                cmd.execute(canvas)
        if self.should_save:
            canvas.restore()
