def test_cssparser1():
    from src.cssparser import CSSParser
    from src.selector import TagSelector

    selector = CSSParser("div { foo: bar }").parse()
    print(selector)
    assert len(selector) == 1
    assert isinstance(selector[0][0], TagSelector)
    assert selector[0][0].tag == "div"
    assert selector[0][1]["foo"] == "bar"


def test_cssparser2():
    from src.cssparser import CSSParser
    from src.selector import DesendantSelector, TagSelector

    selector = CSSParser("div span { foo: bar }").parse()
    assert isinstance(selector[0][0], DesendantSelector)
    assert isinstance(selector[0][0].ancestor, TagSelector)
    assert isinstance(selector[0][0].descendant, TagSelector)
    assert selector[0][0].ancestor.tag == "div"
    assert selector[0][0].descendant.tag == "span"
    assert selector[0][1]["foo"] == "bar"

    CSSParser("div span h1 { foo: bar }").parse()


def test_cssparser3():
    from src.cssparser import CSSParser
    from src.selector import DesendantSelector, TagSelector

    selector = CSSParser("div span h1 { foo: bar }").parse()
    print(selector)
    assert isinstance(selector[0][0], DesendantSelector)
    assert isinstance(selector[0][0].ancestor, DesendantSelector)
    assert isinstance(selector[0][0].ancestor.ancestor, TagSelector)
    assert isinstance(selector[0][0].ancestor.descendant, TagSelector)
    assert isinstance(selector[0][0].descendant, TagSelector)
    assert selector[0][0].ancestor.ancestor.tag == "div"
    assert selector[0][0].ancestor.descendant.tag == "span"
    assert selector[0][0].descendant.tag == "h1"
    assert selector[0][1]["foo"] == "bar"


def test_cssparser4():
    from src.cssparser import CSSParser
    from src.selector import TagSelector

    selector = CSSParser("div { foo: bar } span { baz : baz2 }").parse()
    print(selector)
    assert len(selector) == 2
    assert isinstance(selector[0][0], TagSelector)
    assert selector[0][0].tag == "div"
    assert selector[0][1]["foo"] == "bar"
    assert isinstance(selector[1][0], TagSelector)
    assert selector[1][0].tag == "span"
    assert selector[1][1]["baz"] == "baz2"


def test_unknown_cssparser():
    from src.cssparser import CSSParser
    from src.selector import TagSelector

    selector = CSSParser("a;").parse()
    assert len(selector) == 0
    selector = CSSParser("a {;}").parse()
    assert isinstance(selector[0][0], TagSelector)
    assert selector[0][0].tag == "a"
    assert len(selector[0][1]) == 0
    selector = CSSParser("{} a;").parse()
    assert len(selector) == 0
    selector = CSSParser("a { p }").parse()
    assert isinstance(selector[0][0], TagSelector)
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
        body_layout = browser.tabs[0].document.children[0].children[0]
        div_layout = body_layout.children[0]
        assert str(div_layout.node) == "<div>"
        assert div_layout.node.style["color"] == "blue"


def test_resolve_url():
    from src.util.url import resolve_url

    assert resolve_url("http://foo.com", "http://bar.com/") == "http://foo.com"
    assert resolve_url("/url", "http://bar.com/") == "http://bar.com/url"
    assert resolve_url("url2", "http://bar.com/url1") == "http://bar.com/url2"
    assert resolve_url("url2", "http://bar.com/url1/") == "http://bar.com/url1/url2"
