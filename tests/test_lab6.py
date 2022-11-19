def test_cssparser1():
    from src.cssparser import CSSParser

    selector = CSSParser("div { foo: bar }").parse()
    assert len(selector) == 1
    assert selector[0][0].tag == "div"
    assert selector[0][1]["foo"] == "bar"


def test_cssparser2():
    from src.cssparser import CSSParser

    selector = CSSParser("div span { foo: bar }").parse()
    assert selector[0][0].ancestor.tag == "div"
    assert selector[0][0].descendant.tag == "span"
    assert selector[0][1]["foo"] == "bar"

    CSSParser("div span h1 { foo: bar }").parse()


def test_cssparser3():
    from src.cssparser import CSSParser

    selector = CSSParser("div span h1 { foo: bar }").parse()
    assert selector[0][0].ancestor.ancestor.tag == "div"
    assert selector[0][0].ancestor.descendant.tag == "span"
    assert selector[0][0].descendant.tag == "h1"
    assert selector[0][1]["foo"] == "bar"


def test_cssparser4():
    from src.cssparser import CSSParser

    selector = CSSParser("div { foo: bar } span { baz : baz2 }").parse()
    assert len(selector) == 2
    assert selector[0][0].tag == "div"
    assert selector[0][1]["foo"] == "bar"
    assert selector[1][0].tag == "span"
    assert selector[1][1]["baz"] == "baz2"


def test_unknown_cssparser():
    from src.cssparser import CSSParser

    selector = CSSParser("a;").parse()
    assert len(selector) == 0
    selector = CSSParser("a {;}").parse()
    assert selector[0][0].tag == "a"
    assert len(selector[0][1]) == 0
    selector = CSSParser("{} a;").parse()
    assert len(selector) == 0
    selector = CSSParser("a { p }").parse()
    assert selector[0][0].tag == "a"
    assert len(selector[0][1]) == 0
    selector = CSSParser("a { p: v }").parse()
    print(selector)
    selector = CSSParser("a { p: ^ }").parse()
    print(selector)
    selector = CSSParser("a { p: ; }").parse()
    print(selector)
    selector = CSSParser("a { p: v; q }").parse()
    print(selector)
    selector = CSSParser("a { p: v; ; q: u }").parse()
    print(selector)
    selector = CSSParser("a { p: v; q:: u }").parse()
    print(selector)
