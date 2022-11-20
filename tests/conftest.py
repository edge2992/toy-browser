import pytest


@pytest.fixture
def example_org_body():
    with open("tests/data/example.html", "r") as f:
        body = f.read()
    return body
