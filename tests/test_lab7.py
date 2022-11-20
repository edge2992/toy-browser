def test_line_text_layout1(sorted_default_rules):
    from src.text import HTMLParser, print_tree
    from src.layout import DocumentLayout, LineLayout, TextLayout
    from src.cssparser import style
    import tkinter

    example_html = "<div>This is a test<br>Also a test<br>And this too</div>"

    # dummy tkinter canvas
    _ = tkinter.Canvas(tkinter.Tk(), width=800, height=600)
    nodes = HTMLParser(example_html).parse()
    style(nodes, sorted_default_rules)
    print_tree(nodes)
    document = DocumentLayout(nodes)
    document.layout()
    div = document.children[0].children[0].children[0]
    assert type(div.children[0]) == LineLayout
    assert len(div.children[0].children) == 4
    assert len(div.children[1].children) == 3
    assert len(div.children[2].children) == 3
    assert type(div.children[0].children[0]) == TextLayout
    print_tree(document)
