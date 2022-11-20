def test_htmlParser():
    from src.text import HTMLParser
    from src.text import print_tree

    parser = HTMLParser("<html><body>test</body></html>")
    print_tree(parser.parse())


def test_htmlParser2():
    from src.text import HTMLParser
    from src.text import print_tree

    parser = HTMLParser("text")
    print_tree(parser.parse())


def test_htmlParser3():
    from src.text import HTMLParser
    from src.text import print_tree

    parser = HTMLParser("<body>text")
    print_tree(parser.parse())


def test_htmlParser4():
    from src.text import HTMLParser
    from src.text import print_tree

    parser = HTMLParser("<base><basefont></basefont><title></title><div></div>")
    print_tree(parser.parse())


def test_htmlParser5():
    from src.text import HTMLParser
    from src.text import print_tree

    parser = HTMLParser("<div>text")
    print_tree(parser.parse())


def test_htmlParser6():
    from src.text import HTMLParser
    from src.text import print_tree

    parser = HTMLParser("<div name1=value1 name2=value2>text</div>")
    print_tree(parser.parse())


def test_layout():
    from src.text import HTMLParser
    from src.layout import DocumentLayout
    import tkinter

    _ = tkinter.Canvas(tkinter.Tk(), width=800, height=600)
    parser = HTMLParser("<p>text</p>")
    tree = parser.parse()
    document = DocumentLayout(tree)
    document.layout()
    display_list = []
    document.paint(display_list)
    print(display_list)
