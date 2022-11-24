def test_history_append():
    from src.graphics.history import History

    def go_forward(history: History):
        url = history.next()
        if url:
            history.append(url)
        return url

    def go_back(history: History):
        url = history.previous()
        if url:
            history.append(url)
        return url

    history = History()
    history.append("a1")
    history.append("a2")
    history.append("a3")
    assert history.has_previous() is True
    assert history.has_next() is False
    assert go_back(history) == "a2"
    assert history.has_previous() is True
    assert history.has_next() is True
    assert go_back(history) == "a1"
    assert history.has_previous() is False
    assert history.has_next() is True
    assert go_forward(history) == "a2"
    history.append("a4")
    assert history.has_previous() is True
    assert history.has_next() is False
    assert go_back(history) == "a2"
    assert go_back(history) == "a1"
