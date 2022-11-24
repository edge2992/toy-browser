from __future__ import annotations
from typing import List, Union


class History:
    def __init__(self):
        self._history: List[str] = []
        self.index: int = -1

    def append(self, url: str) -> None:
        self.index += 1
        if self.index < len(self._history) and self._history[self.index] == url:
            pass
        else:
            self._history = self._history[: self.index]
            self._history.append(url)

    def next(self) -> Union[str, None]:
        if self.has_next():
            return self._history[self.index + 1]
        return None

    def previous(self) -> Union[str, None]:
        if self.has_previous():
            self.index -= 2
            return self._history[self.index + 1]
        return None

    def get_next(self) -> Union[str, None]:
        if self.has_next():
            return self._history[self.index + 1]
        return None

    def get_previous(self) -> Union[str, None]:
        if self.has_previous():
            return self._history[self.index - 1]
        return None

    def has_next(self) -> bool:
        return self.index < len(self._history) - 1

    def has_previous(self) -> bool:
        return self.index > 0
