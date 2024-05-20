import io
import pprint
import tokenize
from rich.syntax import Syntax

from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll
from textual.reactive import var
from textual.widgets import Header, Footer, Static, TextArea

SAMPLE_CODE = """try:
    if x:
        y = 12
    else:
        y = 14
except:
    y = 16
"""


class SourceWidget(Container):

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield TextArea.code_editor("", language="python", classes="editor")

    def update_code(self, code: str) -> None:
        source = self.query_one(".editor", TextArea)
        source.text = code
        # To use a Static display
        # source.udpate(
        #     Syntax(
        #         code, "python", line_numbers=True, word_wrap=False, indent_guides=True
        #     )
        # )

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
        ("ctrl+1", "toggle_source", "Source"),
        ("ctrl+2", "toggle_tokens", "Tokens"),
        ("ctrl+3", "toggle_ast", "AST"),
        ("ctrl+4", "toggle_opt_ast", "AST(opt.)"),
        ("ctrl+5", "toggle_pseudo_bc", "Pseudo BC"),
        ("ctrl+6", "toggle_opt_pseudo_bc", "Opt. BC"),
        ("ctrl+7", "toggle_code_obj", "Final BC"),
    ]

    show_source = var(True)
    show_tokens = var(True)
    show_ast = var(True)
    show_opt_ast = var(True)
    show_pseudo_bc = var(True)
    show_opt_pseudo_bc = var(True)
    show_code_obj = var(True)

    def compose(self) -> ComposeResult:
        yield Header()
        yield SourceWidget(id="source")
        yield TokenWidget(id="tokens")
        yield Footer()

    def _set_code(self, code: str) -> None:
        source = self.query_one("#source", SourceWidget)
        source.update_code(code)
        tokens = list(tokenize.tokenize(
            io.BytesIO(code.encode('utf-8')).readline)
        )        
        self.query_one("#tokens", TokenWidget).update(pprint.pformat(tokens))

    def on_mount(self) -> None:
        self._set_code(SAMPLE_CODE)
        self.query_one(".editor").focus()


if __name__ == "__main__":
    app = CodeViewer()
    app.run()
