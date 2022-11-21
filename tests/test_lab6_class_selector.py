def parse_test(css: str):
    from src.cssparser import CSSParser

    rules = CSSParser(css).parse()
    print()
    for sel, pairs in sorted(rules, key=lambda sp: sp[0].priority):
        print(sel)
        for key in sorted(pairs):
            val = pairs[key]
            print(f" {key}: {val}")


def test_class_parse1():
    from src.cssparser import CSSParser
    from src.selector import ClassSelector

    css_text = ".main { font-size: 100px; }"
    parse_test(css_text)
    rules = CSSParser(css_text).parse()
    assert isinstance(rules[0][0], ClassSelector)
    assert rules[0][0].class_name == "main"
    assert isinstance(rules[0][1], dict)


def test_class_parse2():
    from src.cssparser import CSSParser
    from src.selector import ClassSelector, DesendantSelector, TagSelector

    css_text = ".a p { font-size:10px ;}"
    parse_test(css_text)
    rules = CSSParser(css_text).parse()
    assert isinstance(rules[0][0], DesendantSelector)
    assert isinstance(rules[0][0].ancestor, ClassSelector)
    assert isinstance(rules[0][0].descendant, TagSelector)
    assert rules[0][0].priority == 11
    assert rules[0][0].ancestor.priority == 10
    assert rules[0][0].descendant.priority == 1


def test_class_parse3():
    from src.cssparser import CSSParser
    from src.selector import ClassSelector, DesendantSelector, TagSelector

    css_text = "p .a { color:blue ;}"

    parse_test(css_text)
    rules = CSSParser(css_text).parse()
    assert isinstance(rules[0][0], DesendantSelector)
    assert isinstance(rules[0][0].ancestor, TagSelector)
    assert isinstance(rules[0][0].descendant, ClassSelector)
    assert rules[0][0].priority == 11
    assert rules[0][0].ancestor.priority == 1
    assert rules[0][0].descendant.priority == 10


def test_class_parse4():
    from src.cssparser import CSSParser
    from src.selector import ClassSelector, DesendantSelector

    css_text = ".a .b { font-weight:bold ;}"
    parse_test(css_text)
    rules = CSSParser(css_text).parse()
    assert isinstance(rules[0][0], DesendantSelector)
    assert isinstance(rules[0][0].ancestor, ClassSelector)
    assert isinstance(rules[0][0].descendant, ClassSelector)
    assert rules[0][0].priority == 20
    assert rules[0][0].ancestor.priority == 10
    assert rules[0][0].descendant.priority == 10


def test_class_match():
    from src.selector import ClassSelector
    from src.text import Element

    assert ClassSelector("b").matches(Element("p", {"class": "b"}, None))
    assert not ClassSelector("b").matches(Element("p", {"class": "a"}, None))
    assert ClassSelector("b").matches(Element("p", {"class": "a b"}, None))
    assert ClassSelector("b").matches(Element("p", {"class": "b a"}, None))
    assert not ClassSelector("b").matches(Element("p", {"class": "bat"}, None))


def test_priority():
    from src.cssparser import CSSParser
    from src.selector import (
        ClassSelector,
        DesendantSelector,
        TagSelector,
        cascade_priority,
    )

    css_text = (
        "h1 b { color:orange ;}"
        + ".foo { color:yellow ;}"
        + "p { color:red ;}"
        + " .foo p { color:green ;}"
    )
    parse_test(css_text)
    rules = sorted(CSSParser(css_text).parse(), key=cascade_priority)
    assert isinstance(rules[0][0], TagSelector)
    assert isinstance(rules[1][0], DesendantSelector)
    assert isinstance(rules[2][0], ClassSelector)
    assert isinstance(rules[3][0], DesendantSelector)
    assert rules[0][1]["color"] == "red"
    assert rules[1][1]["color"] == "orange"
    assert rules[2][1]["color"] == "yellow"
    assert rules[3][1]["color"] == "green"
