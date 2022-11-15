class Text:
    def __init__(self, text: str):
        self.text = text


class Tag:
    def __init__(self, tag: str):
        self.tag = tag


def lex(body: str):
    out = []
    text = ""
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
            if text:
                out.append(Text(text))
            text = ""
        elif c == ">":
            in_tag = False
            out.append(Tag(text))
            text = ""
        else:
            text += c
    if not in_tag and text:
        out.append(Text(text))
    return out
