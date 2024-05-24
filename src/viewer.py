import sys

from textual.app import App, ComposeResult
from textual.containers import Container
from textual import log
from textual.reactive import var
from textual.widgets import Header, Footer

from bytecode_widget import BytecodeWidget
from events import HoverLine
from ast_widget import ASTWidget
from token_widget import TokenWidget
from source_widgets import SourceWidget, EditWidget

SAMPLE_CODE = """
"Fibonacci Demo"

a, b = 0, 1
for _ in range(12):
    a, b = b, a+b
    print(a)

del a
del b
"""

# This controls 3.13 features
VERSION_3_13 = sys.version_info >= (3, 13)


class CodeViewer(App[None]):

    TITLE = "Compiler Pipeline Explorer"
    CSS_PATH = "viewer.tcss"

    if VERSION_3_13:
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
    else:
        BINDINGS = [
            ("ctrl+q", "quit", "Quit"),
            ("f2", "toggle_source", "Source"),
            ("f3", "toggle_tokens", "Tokens"),
            ("f4", "toggle_ast", "AST"),
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

    def watch_show_ast(self, show_ast: bool) -> None:
        self.query_one("#ast").styles.display = "block" if show_ast else "none"

    def watch_show_opt_ast(self, show_opt_ast: bool) -> None:
        if VERSION_3_13:
            self.query_one("#opt-ast").styles.display = (
                "block" if show_opt_ast else "none"
            )

    def watch_show_pseudo_bc(self, show_pseudo_bc: bool) -> None:
        if VERSION_3_13:
            self.query_one("#pseudo-bc").styles.display = (
                "block" if show_pseudo_bc else "none"
            )

    def watch_show_opt_pseudo_bc(self, show_opt_pseudo_bc: bool) -> None:
        if VERSION_3_13:
            self.query_one("#opt-pseudo-bc").styles.display = (
                "block" if show_opt_pseudo_bc else "none"
            )

    def watch_show_code_obj(self, show_code_obj: bool) -> None:
        self.query_one("#opt-code-obj").styles.display = (
            "block" if show_code_obj else "none"
        )

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="body"):
            yield SourceWidget(id="source")
            yield TokenWidget(id="tokens")
            yield ASTWidget(id="ast")
            if VERSION_3_13:
                yield ASTWidget(id="opt-ast", optimized=True)
                yield BytecodeWidget(id="pseudo-bc", mode="pseudo")
                yield BytecodeWidget(id="opt-pseudo-bc", mode="optimized")
            yield BytecodeWidget(id="opt-code-obj", mode="compiled")
        yield Footer()

    def _set_code(self, code: str) -> None:
        source = self.query_one("#source", SourceWidget)
        source.set_code(code)
        self.query_one("#tokens", TokenWidget).set_code(code)
        self.query_one("#ast", ASTWidget).set_code(code)
        if VERSION_3_13:
            self.query_one("#opt-ast", ASTWidget).set_code(code)
            self.query_one("#pseudo-bc", BytecodeWidget).set_code(code)
            self.query_one("#opt-pseudo-bc", BytecodeWidget).set_code(code)
        self.query_one("#opt-code-obj", BytecodeWidget).set_code(code)

    def on_mount(self) -> None:
        self._set_code(SAMPLE_CODE)
        self.query_one(".editor").focus()

    def action_toggle_tokens(self) -> None:
        self.show_tokens = not self.show_tokens

    def action_toggle_ast(self) -> None:
        self.show_ast = not self.show_ast

    def action_toggle_opt_ast(self) -> None:
        self.show_opt_ast = not self.show_opt_ast

    def action_toggle_pseudo_bc(self) -> None:
        self.show_pseudo_bc = not self.show_pseudo_bc

    def action_toggle_opt_pseudo_bc(self) -> None:
        self.show_opt_pseudo_bc = not self.show_opt_pseudo_bc

    def action_toggle_code_obj(self) -> None:
        self.show_code_obj = not self.show_code_obj

    def on_hover_line(self, message: HoverLine) -> None:
        log(f"hover: {message.lineno}")
        source = self.query_one("#source", SourceWidget)
        source.highlight(message.lineno)
        tokens = self.query_one("#tokens", TokenWidget)
        tokens.highlight(message.lineno)
        ast = self.query_one("#ast", ASTWidget)
        ast.highlight(message.lineno)
        if VERSION_3_13:
            opt_ast = self.query_one("#opt-ast", ASTWidget)
            opt_ast.highlight(message.lineno)
            pseudo_bc = self.query_one("#pseudo-bc", BytecodeWidget)
            pseudo_bc.highlight(message.lineno)
            opt_pseudo_bc = self.query_one("#opt-pseudo-bc", BytecodeWidget)
            opt_pseudo_bc.highlight(message.lineno)
        opt_code_obj = self.query_one("#opt-code-obj", BytecodeWidget)
        opt_code_obj.highlight(message.lineno)


if __name__ == "__main__":
    app = CodeViewer()
    app.run()
