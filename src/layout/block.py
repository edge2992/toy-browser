from __future__ import annotations

from typing import TYPE_CHECKING, List, Union

import skia

from src.draw import DrawRRect
from src.global_value import FONT_RATIO
from src.layout.abstract import LayoutObject
from src.layout.inline import InlineLayout
from src.text import LAYOUT_MODE, Element

if TYPE_CHECKING:
    from src.draw import Draw
    from src.text import HTMLNode


class BlockLayout(LayoutObject[LayoutObject, Union[LayoutObject, None], LayoutObject]):
    def __init__(
        self,
        node: HTMLNode,
        parent: LayoutObject,
        previous: Union[LayoutObject, None],
        font_ratio: float = FONT_RATIO,
    ):
        super().__init__(node, parent, previous, font_ratio)

    def layout(self) -> None:
        previous: Union[InlineLayout, BlockLayout, None] = None
        # create child layout object
        for child in self.node.children:
            if isinstance(child, Element) and child.tag == "head":
                continue  # headを飛ばす
            next: Union[InlineLayout, BlockLayout]
            if child.display == LAYOUT_MODE.INLINE:
                next = InlineLayout(child, self, previous, self.font_ratio)
            elif child.display == LAYOUT_MODE.BLOCK:
                next = BlockLayout(child, self, previous, self.font_ratio)
            else:
                raise ValueError("Unknown display mode")
            self.children.append(next)
            previous = next
        # width, x, yをparentとpreviousを参考に計算する
        self.width = self.parent.width
        self.x = self.parent.x

        if self.previous:
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y
        # childrenで再帰的にlayoutを実行する
        for child_layout in self.children:
            child_layout.layout()
        # childrenを全て読んでheightを計算
        self.height = sum([child.height for child in self.children])

    def paint(self, display_list: List[Draw]) -> None:
        cmds = []

        rect = skia.Rect.MakeLTRB(
            self.x, self.y, self.x + self.width, self.y + self.height
        )
        bgcolor = self.node.style.get("background-color", "transparent")
        if bgcolor != "transparent":
            radius = float(self.node.style.get("border-radius", "0px")[:-2])
            cmds.append(DrawRRect(rect, radius, bgcolor))

        for child in self.children:
            child.paint(cmds)

        cmds = self.paint_visual_effects(self.node, cmds, rect)
        display_list.extend(cmds)

    def __repr__(self):
        return "BlockLayout(x={}, y={}, width={}, height={}, node={})".format(
            self.x, self.y, self.width, self.height, self.node
        )
