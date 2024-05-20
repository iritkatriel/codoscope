import io
import pprint
import tokenize
from rich.syntax import Syntax

from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll
from textual.reactive import var
from textual.widgets import Header, Footer, Static

# Enable editing
# from textual.widgets import TextArea

SAMPLE_CODE = (
    """try:
    if x:
        y = 12
    else:
        y = 14
except:
    y = 16
"""
    * 8
)


class SourceWidget(Container):

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            # To use an editor
            # yield TextArea.code_editor("", language="python", classes="editor")
            yield Static(classes="editor", expand=True)

    def update_code(self, code: str) -> None:
        # To use an editor
        # source = self.query_one(".editor", TextArea)
        # source.text = code
        source = self.query_one(".editor", Static)
        source.update(
            Syntax(
                code, "python", line_numbers=True, word_wrap=False, indent_guides=True
            )
        )


class TokenWidget(Container):

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Static(classes="tokens", expand=True)

    def update(self, code: str) -> None:
        static = self.query_one(".tokens", Static)
        static.update(code)


class CodeViewer(App[None]):

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
        yield SourceWidget(id="source")
        yield TokenWidget(id="tokens")
        yield Footer()

    def _set_code(self, code: str) -> None:
        source = self.query_one("#source", SourceWidget)
        source.update_code(code)
        tokens = list(tokenize.tokenize(io.BytesIO(code.encode("utf-8")).readline))
        self.query_one("#tokens", TokenWidget).update(pprint.pformat(tokens))

    def on_mount(self) -> None:
        self._set_code(SAMPLE_CODE)
        self.query_one(".editor").focus()

    def action_toggle_tokens(self):
        self.show_tokens = not self.show_tokens


if __name__ == "__main__":
    app = CodeViewer()
    app.run()
