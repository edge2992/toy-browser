# Section5のLayoutのテスト


def test_layout_mode():
    from src.text import HTMLParser, print_tree
    from src.layout import layout_mode

    parser = HTMLParser("text")
    document_tree = parser.parse()
    print_tree(document_tree)
    assert layout_mode(document_tree) == "block"  # html
    assert layout_mode(document_tree.children[0]) == "inline"  # body
    assert layout_mode(document_tree.children[0].children[0]) == "inline"  # text


def test_bigger_parser():
    from src.text import HTMLParser, print_tree
    from src.layout import layout_mode

    sample_html = "<div></div><div>text</div><div><div></div>text</div><span></span><span>text</span>"
    parser = HTMLParser(sample_html)
    document_tree = parser.parse()
    print_tree(document_tree)
    assert len(document_tree.children[0].children) == 5
    assert layout_mode(document_tree.children[0].children[0]) == "block"  # div no child
    assert (
        layout_mode(document_tree.children[0].children[1]) == "inline"
    )  # div one text child
    assert (
        layout_mode(document_tree.children[0].children[2]) == "block"
    )  # div one text child and one div child


def test_layout_tree(mocker):
    from src.graphics import Browser
    from src.text import print_tree
    from src.layout import BlockLayout

    sample_html = "<div></div><div>text</div><div><div></div>text</div><span></span><span>text</span>"
    url = "http://test.test/example1"
    with mocker.patch(
        "src.browser._get_headers_and_body", return_value=("", sample_html)
    ):
        browser = Browser()
        browser.load(url)
        print_tree(browser.tabs[0].nodes)
        print_tree(browser.tabs[0].document)
        print(browser.tabs[0].display_list)
        body_layout = browser.tabs[0].document.children[0].children[0]
        assert isinstance(body_layout, BlockLayout)
        assert str(body_layout.node) == "<body>"
        assert len(body_layout.children) == 5


def test_layout_mode2():
    from src.text import print_tree, HTMLParser
    from src.layout import layout_mode

    sample_html = "<div></div><div>text</div><div><div></div>text</div><span></span><span>text</span>"
    parser = HTMLParser(sample_html)
    document_tree = parser.parse()
    print_tree(document_tree)
    assert layout_mode(document_tree.children[0]) == "block"
    assert layout_mode(document_tree.children[0].children[0]) == "block"
    assert layout_mode(document_tree.children[0].children[1]) == "inline"
    assert layout_mode(document_tree.children[0].children[2]) == "block"
    assert layout_mode(document_tree.children[0].children[3]) == "block"
    assert layout_mode(document_tree.children[0].children[4]) == "inline"


def test_layout_tree_head(example_org_body, sorted_default_rules):
    print()
    from src.text import HTMLParser, print_tree
    from src.layout import DocumentLayout
    from src.cssparser import style
    import tkinter

    # dummy tkinter canvas
    _ = tkinter.Canvas(tkinter.Tk(), width=800, height=600)
    nodes = HTMLParser(example_org_body).parse()
    style(nodes, sorted_default_rules)
    # print_tree(nodes)
    document = DocumentLayout(nodes)
    document.layout()
    body = document.children[0].children[0]
    assert body.node.tag == "body"
    print_tree(document)
