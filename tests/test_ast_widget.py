import ast
import sys
from pathlib import Path
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ast_widget import _attr_repr, _has_children, dump_iter


class ASTWidgetHelpersTests(unittest.TestCase):
    def test_has_children_false_for_name(self) -> None:
        self.assertFalse(_has_children(ast.Name(id="x", ctx=ast.Load())))

    def test_has_children_true_for_binop(self) -> None:
        node = ast.parse("x + 1", mode="eval").body
        self.assertTrue(_has_children(node))

    def test_attr_repr_for_context(self) -> None:
        node = ast.Name(id="x", ctx=ast.Load())
        self.assertEqual(_attr_repr(node, "ctx"), "Load")

    def test_dump_iter_includes_key_nodes(self) -> None:
        tree = ast.parse("x = 1\ny = x + 2\n")
        dumped = list(dump_iter(tree))
        lines = [line for line, _, _ in dumped]

        self.assertIn("Module()", lines[0])
        self.assertTrue(any("Assign()" in line for line in lines))
        self.assertTrue(any("Name(id='x', ctx=Store)" in line for line in lines))
        self.assertTrue(any("Constant(value=1, kind=None)" in line for line in lines))

    def test_dump_iter_tracks_source_line_ranges(self) -> None:
        tree = ast.parse("x = 1\ny = 2\n")
        dumped = list(dump_iter(tree))
        assign_entries = [entry for entry in dumped if entry[0].strip() == "Assign()"]

        self.assertEqual(len(assign_entries), 2)
        self.assertEqual(assign_entries[0][1:], (1, 2))
        self.assertEqual(assign_entries[1][1:], (2, 3))


if __name__ == "__main__":
    unittest.main()
