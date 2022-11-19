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


def test_compute_style():
    from src.text import Element
    from src.cssparser import compute_style

    html = Element("html", {}, None)
    body = Element("body", {}, html)
    div = Element("div", {}, body)
    v = compute_style(body, "property", "value")
    assert v == "value"
    v = compute_style(body, "font-size", "12px")
    assert v == "12px"
    html.style = {"font-size": "30px"}
    assert compute_style(body, "font-size", "100%") == "30.0px"
    assert compute_style(body, "font-size", "80%") == "24.0px"
    body.style = {"font-size": "10px"}
    assert compute_style(div, "font-size", "100%") == "10.0px"
    assert compute_style(div, "font-size", "80%") == "8.0px"


def test_style1():
    from src.text import Element
    from src.cssparser import style

    html = Element("html", {}, None)
    body = Element("body", {}, html)
    div = Element("div", {}, body)
    style(html, [])
    style(body, [])
    style(div, [])
    assert html.style == body.style
    assert body.style == div.style
    print(html.style)
    print(body.style)
    print(div.style)


def test_style2():
    from src.text import Element
    from src.cssparser import style, CSSParser

    html = Element("html", {}, None)
    body = Element("body", {}, html)
    div = Element("div", {}, body)

    rules = CSSParser(
        "html { font-size: 10px} body { font-size: 90% } div { font-size: 90% } "
    ).parse()
    style(html, rules)
    style(body, rules)
    style(div, rules)
    assert html.style["font-size"] == "10px"
    assert body.style["font-size"] == "9.0px"
    assert div.style["font-size"] == "8.1px"


def test_priority(mocker):
    from src.graphics import Browser

    with mocker.patch(
        "src.browser._get_headers_and_body",
        return_value=("", '<div style="color:blue">Test</div>'),
    ):
        browser = Browser()
        browser.load("http://bar.com/")
        assert (
            browser.document.children[0].children[0].children[0].node.style["color"]
            == "blue"
        )
