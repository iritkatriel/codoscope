from __future__ import annotations

import dis
import sys
from pathlib import Path
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bytecode_widget import _disassemble, _get_instructions, PseudoInstrsArgResolver


class BytecodeHelpersTests(unittest.TestCase):
    def test_get_instructions_accepts_dis_instruction(self) -> None:
        insts = list(dis.Bytecode(compile("x = 1", "<source>", "exec")))
        resolver = PseudoInstrsArgResolver(co_consts=(), labels_map={})

        converted = list(_get_instructions(insts[:1], resolver))
        self.assertEqual(len(converted), 1)
        self.assertIsInstance(converted[0], dis.Instruction)

    def test_get_instructions_converts_pseudo_tuple(self) -> None:
        pseudo = [(dis.opmap["LOAD_CONST"], 0, 1, 1, 0, 1)]
        resolver = PseudoInstrsArgResolver(co_consts=(123,), labels_map={})

        converted = list(_get_instructions(pseudo, resolver))
        self.assertEqual(len(converted), 1)
        self.assertEqual(converted[0].opname, "LOAD_CONST")
        self.assertEqual(converted[0].argval, 123)

    def test_disassemble_formats_bytecode_lines(self) -> None:
        insts = list(dis.Bytecode(compile("x = 1", "<source>", "exec")))
        result = list(_disassemble(insts, (1,), "<compiled bytecode>"))

        self.assertGreater(len(result), 0)
        rendered_lines = [line for line, _, _ in result]
        self.assertTrue(any("LOAD_CONST" in line for line in rendered_lines))
        self.assertTrue(all(isinstance(start, int) and isinstance(end, int) for _, start, end in result))


if __name__ == "__main__":
    unittest.main()
