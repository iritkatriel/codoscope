from collections import defaultdict
import tokenize
from token import tok_name
from typing import Iterable


from textual.app import ComposeResult
from textual.containers import ScrollableContainer
from textual import events
from textual.geometry import Region
from textual.widgets import Static
from rich.syntax import Syntax

from events import HoverLine
from styles import HIGHLIGHT


class TokenWidget(ScrollableContainer):

    # lineno_map maps code line numbers, to the indices of all tokens in that line
    lineno_map: defaultdict[int, set[int]]
    token_positions: list[int]

    def __init__(self, id: str) -> None:
        super().__init__(id=id)
        self.lineno_map = defaultdict(set)
        self.token_positions = []

    def compose(self) -> ComposeResult:
        yield Static(classes="tokens", expand=True)

    def format_token(
        self, token: tokenize.TokenInfo, current_line: int
    ) -> tuple[str, int, int]:
        line = token.start[0]
        end_line = token.end[0]
        if end_line != line:
            line_marker = f"{line:4d}-{end_line}: "
        elif line != current_line:
            line_marker = f"{line:4d}: "
        else:
            line_marker = "      "

        return (
            (
                line_marker
                + f"{tok_name[token.exact_type]:10} {token.string!r} start={token.start} end={token.end}"
            ),
            line,
            end_line + 1,
        )

    def update(self, tokens: Iterable[tokenize.TokenInfo]) -> None:
        token_lines: list[str] = []
        self.lineno_map.clear()
        self.token_positions = []
        width = 0
        current_line = 0
        for token_idx, token in enumerate(tokens):
            formatted_token, current_line, token_end_line = self.format_token(
                token, current_line
            )
            for lineno in range(current_line, token_end_line):
                self.lineno_map[lineno].add(token_idx + 1)
            self.token_positions.append(current_line)
            token_lines.append(formatted_token)
            width = max(width, len(formatted_token))

        static = self.query_one(".tokens", Static)
        self._prerendered = Syntax(
            "\n".join(token_lines),
            "text",
            word_wrap=False,
        )
        static.update(self._prerendered)
        static.styles.width = width

    def on_mouse_move(self, event: events.MouseMove) -> None:
        line = self.token_positions[event.y]
        self.post_message(HoverLine(line))

    def highlight(self, line: int) -> None:
        body = self.query_one(".tokens", Static)
        self._prerendered._stylized_ranges.clear()  # No public API for this?
        for highlight_line in self.lineno_map[line]:
            self._prerendered.stylize_range(
                HIGHLIGHT, (highlight_line, 0), (highlight_line + 1, 0)
            )
        body.update(self._prerendered)

        # Ensure it's visible
        if self.lineno_map[line]:
            min_line = min(self.lineno_map[line]) - 1
            max_line = max(self.lineno_map[line]) - 1
            self.scroll_to_region(Region(0, min_line, 1, max_line - min_line + 1))
