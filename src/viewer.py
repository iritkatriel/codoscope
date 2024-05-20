from rich.syntax import Syntax

from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll
from textual.widgets import Header, Footer, Static

SAMPLE_CODE = """
try:
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
            yield Static(classes="source", expand=True)

    def update_code(self, code: str) -> None:
        source = self.query_one(".source", Static)
        source.update(
            Syntax(
                code, "python", line_numbers=True, word_wrap=False, indent_guides=True
            )
        )


class CodeViewer(App):

    BINDINGS = [("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield SourceWidget(id="source")
        yield Footer()

    def on_mount(self) -> None:
        code = self.query_one("#source", SourceWidget)
        code.update_code(SAMPLE_CODE)


if __name__ == "__main__":
    app = CodeViewer()
    app.run()
