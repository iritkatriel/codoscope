import tokenize
from token import tok_name
from typing import Iterable


from base_widget import BaseWidget, Detail


class TokenWidget(BaseWidget):

    def format_token(self, token: tokenize.TokenInfo, current_line: int) -> Detail:
        line = token.start[0]
        end_line = token.end[0]
        if end_line != line:
            line_marker = f"{line:4d}-{end_line}: "
        elif line != current_line:
            line_marker = f"{line:4d}: "
        else:
            line_marker = "      "

        return (
            f"{line_marker}{tok_name[token.exact_type]:10} {token.string!r} start={token.start} end={token.end}",
            line,
            end_line + 1,
        )

    def set_tokens(self, tokens: Iterable[tokenize.TokenInfo]) -> None:
        details: list[Detail] = []
        current_line = 0
        for t in tokens:
            d = self.format_token(t, current_line)
            details.append(d)
            current_line = d[1]

        self.update(details)
