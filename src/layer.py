import skia


class SaveLayer:
    def __init__(self, sk_paint, children):
        self.sk_paint = sk_paint
        self.children = children
        self.rect = skia.Rect.MakeEmpty()
        for cmd in self.children:
            self.rect.join(cmd.rect)

    def execute(self, scroll, canvas):
        canvas.saveLayer(paint=self.sk_paint)
        for cmd in self.children:
            cmd.execute(scroll, canvas)
        canvas.restore()
