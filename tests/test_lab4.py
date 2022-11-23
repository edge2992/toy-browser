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


def test_layout(mocker):
    from src.graphics import Browser
    from src.draw import DrawText

    with mocker.patch(
        "src.network._get_headers_and_body", return_value=("", "<p>text</p>")
    ):
        browser = Browser()
        browser.load("http://test.test/example1")
        print(browser.tabs[0].display_list)
        assert isinstance(browser.tabs[0].display_list[0], DrawText)
