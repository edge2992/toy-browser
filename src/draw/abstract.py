import skia


class Draw:
    def __init__(
        self,
        top: float,
        left: float,
        right: float,
        bottom: float,
        rect: skia.Rect,
        color: str,
    ):
        self.top: float = top
        self.left: float = left
        self.right: float = right
        self.bottom: float = bottom
        self.rect: skia.Rect = rect
        self.color: str = color

    def execute(self, canvas):
        raise NotImplementedError
