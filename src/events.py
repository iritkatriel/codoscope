from typing import Any

from textual.message import Message


class HoverLine(Message):

    def __init__(self, lineno: int, *args: Any, **kwargs: Any) -> None:
        self.lineno = lineno
        super().__init__(*args, **kwargs)
