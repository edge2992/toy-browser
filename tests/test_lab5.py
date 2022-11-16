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
