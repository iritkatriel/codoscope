import io
import sys
import tokenize
from pathlib import Path
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from token_widget import TokenWidget


class TokenWidgetTests(unittest.TestCase):
    def _get_tokens(self, code: str):
        return list(tokenize.tokenize(io.BytesIO(code.encode("utf-8")).readline))

    def test_format_token_first_line_includes_number_marker(self) -> None:
        widget = TokenWidget(id="tok")
        tokens = self._get_tokens("x = 1\n")
        name_token = next(t for t in tokens if t.string == "x")

        rendered, start, end = widget.format_token(name_token, current_line=0)

        self.assertIn("   1: ", rendered)
        self.assertIn("NAME", rendered)
        self.assertEqual((start, end), (1, 2))

    def test_format_token_repeated_line_uses_padding_marker(self) -> None:
        widget = TokenWidget(id="tok")
        tokens = self._get_tokens("x = 1\n")
        equals_token = next(t for t in tokens if t.string == "=")

        rendered, _, _ = widget.format_token(equals_token, current_line=1)
        self.assertTrue(rendered.startswith("      "))


if __name__ == "__main__":
    unittest.main()
