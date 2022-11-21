from abc import ABC
from typing import Dict, List, Tuple
from src.text import Element, HTMLNode


class Selector(ABC):
    def __init__(self, priority: int):
        self.priority: int = priority

    def matches(self, node: HTMLNode) -> bool:
        raise NotImplementedError


Declaration = Dict[str, str]
CSSRule = Tuple[Selector, Declaration]


class TagSelector(Selector):
    def __init__(self, tag):
        super().__init__(1)
        self.tag = tag

    def matches(self, node: HTMLNode) -> bool:
        return isinstance(node, Element) and self.tag == node.tag

    def __repr__(self) -> str:
        return f"TagSelector({self.tag}, priority={self.priority})"


class ClassSelector(Selector):
    def __init__(self, class_name: str):
        super().__init__(10)
        self.class_name = class_name

    def matches(self, node: HTMLNode) -> bool:
        return (
            isinstance(node, Element)
            and self.class_name in node.attributes.get("class", "").split()
        )

    def __repr__(self) -> str:
        return f"ClassSelector({self.class_name}, priority={self.priority})"


class IdSelector(Selector):
    def __init__(self, id_name: str):
        super().__init__(10)
        self.id_name = id_name

    def matches(self, node: HTMLNode) -> bool:
        return (
            isinstance(node, Element)
            and self.id_name in node.attributes.get("id", "").split()
        )

    def __repr__(self) -> str:
        return f"IdSelector({self.id_name}, priority={self.priority})"


class DesendantSelector(Selector):
    def __init__(self, ancestor: Selector, descendant: Selector):
        super().__init__(ancestor.priority + descendant.priority)
        self.ancestor = ancestor
        self.descendant = descendant

    def matches(self, node: HTMLNode) -> bool:
        if not self.descendant.matches(node):
            return False
        while node.parent:
            if self.ancestor.matches(node.parent):
                return True
            node = node.parent
        return False

    def __repr__(self) -> str:
        return f"DesendantSelector(ancestor={self.ancestor}, descendant={self.descendant}, priority={self.priority})"


class GroupSelector(Selector):
    def __init__(self, groups: List[Selector]):
        super().__init__(1)
        self.groups = groups

    def matches(self, node: HTMLNode) -> bool:
        for elem in self.groups:
            if elem.matches(node):
                return True
        return False

    def __repr__(self) -> str:
        return f"GrouptSelector(groups={self.groups}, priority={self.priority})"


def cascade_priority(rule: CSSRule):
    selector, _ = rule
    return selector.priority
