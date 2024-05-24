from rich.syntax import Syntax

from textual.app import ComposeResult
from textual import events
from textual.containers import Container, VerticalScroll
from textual.geometry import Region
from textual.widgets import TextArea, Static
from styles import HIGHLIGHT

from events import HoverLine


class SourceWidget(Container):

    def compose(self) -> ComposeResult:
        with VerticalScroll(classes="scroller"):
            # To use an editor
            # yield TextArea.code_editor("", language="python", classes="editor")
            yield Static(classes="editor", expand=True)

    def set_code(self, code: str) -> None:
        # To use an editor
        # source = self.query_one(".editor", TextArea)
        # source.text = code
        source = self.query_one(".editor", Static)
        self._prerendered = Syntax(
            code,
            "python",
            line_numbers=True,
            word_wrap=False,
            indent_guides=True,
        )
        source.update(self._prerendered)

    def on_mouse_move(self, event: events.MouseMove) -> None:
        self.post_message(HoverLine(event.y + 1))

    def highlight(self, line: int) -> None:
        self.query_one(".scroller", VerticalScroll).scroll_to_region(
            Region(0, line - 1, 0, 1)
        )
        source = self.query_one(".editor", Static)
        self._prerendered.highlight_lines = {line}
        self._prerendered._stylized_ranges.clear()
        self._prerendered.stylize_range(HIGHLIGHT, (line, 0), (line + 1, 0))
        source.update(self._prerendered)


class EditWidget(Container):

    def compose(self) -> ComposeResult:
        with VerticalScroll(classes="scroller"):
            yield TextArea.code_editor("", language="python", classes="editor")

    def set_code(self, code: str) -> None:
        # To use an editor
        source = self.query_one(".editor", TextArea)
        source.text = code

    def on_mouse_move(self, event: events.MouseMove) -> None:
        self.post_message(HoverLine(event.y + 1))

    def highlight(self, line: int) -> None:
        self.query_one(".scroller", VerticalScroll).scroll_to_region(
            Region(0, line - 1, 0, 1)
        )
