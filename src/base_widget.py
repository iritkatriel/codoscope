from collections import defaultdict
from typing import Iterable, TypeAlias

from textual.app import ComposeResult
from textual.containers import ScrollableContainer
from textual import events
from textual.geometry import Region
from textual.widgets import Static
from rich.syntax import Syntax

from events import HoverLine
from styles import HIGHLIGHT


Detail: TypeAlias = tuple[
    str, int, int
]  # data to show, start and end line. python-style range


class BaseWidget(ScrollableContainer):
    """
    Display "details" about a piece a code. Each "detail" is shown as a line, and
    corresponds to a segment of lines in the source.

    For example a detail can be a token, an AST node, or a bytecode instruction.
    """

    # lineno_map maps source line numbers, to the indices of all details in that line
    lineno_map: defaultdict[int, set[int]]
    # detail_poistions[i] indicate the position of the i-th detail shown.
    detail_positions: list[int]

    def __init__(self, id: str) -> None:
        super().__init__(id=id)
        self.lineno_map = defaultdict(set)
        self.detail_positions = []

    def compose(self) -> ComposeResult:
        yield Static(classes="display", expand=True)

    def update(self, details: Iterable[Detail]) -> None:
        output_lines: list[str] = []
        self.lineno_map.clear()
        self.detail_positions = []
        width = 0
        for detail_idx, detail in enumerate(details):
            formatted, start_line, end_line = detail
            for lineno in range(start_line, end_line):
                self.lineno_map[lineno].add(detail_idx + 1)
            self.detail_positions.append(start_line)
            output_lines.append(formatted)
            width = max(width, len(formatted))

        static = self.query_one(".display", Static)
        self._prerendered = Syntax(
            "\n".join(output_lines),
            "text",
            word_wrap=False,
        )
        static.update(self._prerendered)
        static.styles.width = width

    def on_mouse_move(self, event: events.MouseMove) -> None:
        line = self.detail_positions[event.y]
        self.post_message(HoverLine(line))

    def highlight(self, line: int) -> None:
        body = self.query_one(".display", Static)
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
