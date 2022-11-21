from abc import ABC
from typing import Dict, Tuple
from src.text import Element, HTMLNode


class Selector(ABC):
    def __init__(self, priority: int):
        self.priority: int = priority

    def matches(self, node: HTMLNode) -> bool:
        raise NotImplementedError


class TagSelector(Selector):
    def __init__(self, tag):
        super().__init__(1)
        self.tag = tag

    def matches(self, node: HTMLNode) -> bool:
        return isinstance(node, Element) and self.tag == node.tag

    def __repr__(self) -> str:
        return f"TagSelector({self.tag})"


class DesendantSelector(Selector):
    def __init__(self, ancestor: Selector, descendant: Selector):
        super().__init__(ancestor.priority + descendant.priority)
        self.ancestor = ancestor
        self.descendant = descendant

    def matches(self, node):
        if not self.descendant.matches(node):
            return False
        while node.parent:
            if self.ancestor.matches(node.parent):
                return True
            node = node.parent
        return False

    def __repr__(self) -> str:
        return (
            f"DesendantSelector(ancestor={self.ancestor}, descendant={self.descendant})"
        )


def cascade_priority(rule: Tuple[Selector, Dict]):
    selector, body = rule
    return selector.priority
