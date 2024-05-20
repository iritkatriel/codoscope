import io
import tokenize
from rich.syntax import Syntax

from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll
from textual import events
from textual.geometry import Region
from textual import log
from textual.reactive import var
from textual.widgets import Header, Footer, Static

from events import HoverLine
from styles import HIGHLIGHT
from token_widget import TokenWidget

# Enable editing
# from textual.widgets import TextArea

import bisect
from pathlib import Path

SAMPLE_CODE = Path(bisect.__file__).read_text()


class SourceWidget(Container):

    def compose(self) -> ComposeResult:
        with VerticalScroll(classes="scroller"):
            # To use an editor
            # yield TextArea.code_editor("", language="python", classes="editor")
            yield Static(classes="editor", expand=True)

    def update_code(self, code: str, highlight_lines: set[int]) -> None:
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
            highlight_lines=highlight_lines,
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


class CodeViewer(App[None]):

    TITLE = "Compile Pipeline Explorer"
    CSS_PATH = "viewer.tcss"

    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("f2", "toggle_source", "Source"),
        ("f3", "toggle_tokens", "Tokens"),
        ("f4", "toggle_ast", "AST"),
        ("f5", "toggle_opt_ast", "AST(opt.)"),
        ("f6", "toggle_pseudo_bc", "Pseudo BC"),
        ("f7", "toggle_opt_pseudo_bc", "Opt. BC"),
        ("f8", "toggle_code_obj", "Final BC"),
    ]

    show_source = var(True)
    show_tokens = var(True)
    show_ast = var(False)
    show_opt_ast = var(False)
    show_pseudo_bc = var(False)
    show_opt_pseudo_bc = var(False)
    show_code_obj = var(False)

    def watch_show_tokens(self, show_tokens: bool) -> None:
        self.query_one("#tokens").styles.display = "block" if show_tokens else "none"

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="body"):
            yield SourceWidget(id="source")
            yield TokenWidget(id="tokens")
        yield Footer()

    def _set_code(self, code: str) -> None:
        source = self.query_one("#source", SourceWidget)
        source.update_code(code, set())
        tokens = tokenize.tokenize(io.BytesIO(code.encode("utf-8")).readline)
        self.query_one("#tokens", TokenWidget).set_tokens(tokens)

    def on_mount(self) -> None:
        self._set_code(SAMPLE_CODE)
        self.query_one(".editor").focus()

    def action_toggle_tokens(self) -> None:
        self.show_tokens = not self.show_tokens

    def on_hover_line(self, message: HoverLine) -> None:
        log(f"hover: {message.lineno}")
        source = self.query_one("#source", SourceWidget)
        source.highlight(message.lineno)
        tokens = self.query_one("#tokens", TokenWidget)
        tokens.highlight(message.lineno)


if __name__ == "__main__":
    app = CodeViewer()
    app.run()
