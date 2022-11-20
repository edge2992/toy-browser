import pytest


@pytest.fixture
def example_org_body():
    with open("tests/data/example.html", "r") as f:
        body = f.read()
    return body


@pytest.fixture
def sorted_default_rules():
    from src.cssparser import CSSParser

    with open("src/browser.css") as f:
        default_style_sheet = CSSParser(f.read()).parse()
    return default_style_sheet
