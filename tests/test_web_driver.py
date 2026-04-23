from __future__ import annotations

import dis
import io
from pathlib import Path
import sys
from unittest import mock
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from web import driver  # noqa: E402


class WebDriverTests(unittest.TestCase):
    def test_view_tokens_includes_token_names(self) -> None:
        rendered = driver.view_tokens("x = 1\n")
        self.assertIn("NAME", rendered)
        self.assertIn("NUMBER", rendered)

    def test_view_ast_returns_module_dump(self) -> None:
        rendered = driver.view_ast("x = 1\n", optimize=False)
        self.assertIn("Module(", rendered)
        self.assertIn("Assign(", rendered)

    def test_view_pseudo_smoke(self) -> None:
        rendered = driver.view_pseudo("def f(x):\n    return x\n\nprint(f(42))\n")
        self.assertIn("LOAD_CONST", rendered)

    def test_view_compiled_smoke(self) -> None:
        rendered = driver.view_compiled("x = 1\n")
        self.assertIn("LOAD_CONST", rendered)

    def test_instruction_items_supports_list_and_get_instructions(self) -> None:
        inst = dis.Instruction(
            "LOAD_CONST", dis.opmap["LOAD_CONST"], 0, 1, "1", 0, 0, True, 1, None, None
        )
        from_list = driver._instruction_items([inst])
        self.assertEqual(len(from_list), 1)
        self.assertEqual(from_list[0].opname, "LOAD_CONST")

        class FakeInsts:
            def get_instructions(self):
                return [inst]

        from_method = driver._instruction_items(FakeInsts())
        self.assertEqual(len(from_method), 1)
        self.assertEqual(from_method[0].opname, "LOAD_CONST")

    def test_co_consts_from_metadata_preserves_sparse_indices(self) -> None:
        resolved = driver._co_consts_from_metadata({"consts": {"a": 0, "z": 2}})
        assert resolved is not None
        self.assertEqual(repr(resolved[1]), "<const#1>")
        self.assertEqual(resolved[0], "a")
        self.assertEqual(resolved[2], "z")

    def test_merge_co_consts_fills_placeholders_from_compiled_consts(self) -> None:
        merged = driver._merge_co_consts(
            ["a", driver._ConstPlaceholder(1)], ["a", "b", "c"]
        )
        self.assertEqual(merged[1], "b")
        self.assertEqual(merged[2], "c")

    def test_apply_annotations_workaround_inserts_internal_const(self) -> None:
        pseudo_items = [
            dis.Instruction(
                "ANNOTATIONS_PLACEHOLDER", 0, 0, None, "", 0, 0, False, None, None, None
            ),
            dis.Instruction(
                "LOAD_CONST",
                dis.opmap["LOAD_CONST"],
                1,
                None,
                "",
                1,
                0,
                False,
                None,
                None,
                None,
            ),
        ]
        adjusted = driver._apply_annotations_const_workaround(
            pseudo_items, ["codeobj", None]
        )
        self.assertIn("<internal const>", [repr(v) for v in adjusted])

    def test_main_outputs_json_with_all_views(self) -> None:
        with mock.patch("builtins.open", mock.mock_open(read_data="x = 1\n")):
            fake_stdout = io.StringIO()
            with mock.patch.object(driver.sys, "stdout", fake_stdout):
                rc = driver.main()

        self.assertEqual(rc, 0)
        rendered = fake_stdout.getvalue()
        self.assertIn('"python_version"', rendered)
        self.assertIn('"tokens"', rendered)
        self.assertIn('"compiled"', rendered)


if __name__ == "__main__":
    unittest.main()
