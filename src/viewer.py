from rich.syntax import Syntax

from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll
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
        # (
        #     Syntax(
        #         code, "python", line_numbers=True, word_wrap=False, indent_guides=True
        #     )
        # )


class CodeViewer(App):

    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("1", "toggle_source", "Toggle Source"),
        ("2", "toggle_tokens", "Toggle Tokens"),
        ("3", "toggle_tokens", "Toggle Tokens"),
        ("4", "toggle_tokens", "Toggle Tokens"),
        ("5", "toggle_tokens", "Toggle Tokens"),
        ("6", "toggle_tokens", "Toggle Tokens"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield SourceWidget(id="source")
        yield Footer()

    def on_mount(self) -> None:
        code = self.query_one("#source", SourceWidget)
        code.update_code(SAMPLE_CODE)
        self.query_one(".editor").focus()


if __name__ == "__main__":
    app = CodeViewer()
    app.run()
