import ast
import dis
from typing import Any, Iterable, Literal, Sequence, TypeAlias
import sys

from base_widget import BaseWidget, Detail

# Conditional imports for 3.13
VERSION_3_13 = sys.version_info >= (3, 13)

if VERSION_3_13:
    compiler_codegen: Any
    optimize_cfg: Any
    from _testinternalcapi import compiler_codegen, optimize_cfg, assemble_code_object  # type: ignore
else:

    def _fail(*args: Any, **kwargs: Any) -> Any:
        raise Exception("This function should never been have called")

    compiler_codegen = optimize_cfg = assemble_code_object = _fail


BytecodeMode: TypeAlias = Literal["pseudo", "optimized", "compiled"]

PseudoInstruction: TypeAlias = tuple[
    int, int | None, int, int, int, int
]  # op, oparg, startline, endline, startcol, endcol


class PseudoInstrsArgResolver(dis.ArgResolver):
    def offset_from_jump_arg(self, op: int, arg: int, offset: int) -> int:
        if op in dis.hasjump or op in dis.hasexc:
            return arg
        return super().offset_from_jump_arg(op, arg, offset)


class AppendStream:
    def __init__(self, append_to: list[Detail]) -> None:
        self.target = append_to
        self.target_line = 0

    def write(self, line: str) -> None:
        if line.strip():
            self.target.append((line, self.target_line, self.target_line + 1))


class Formatter(dis.Formatter):
    file: AppendStream

    def print_instruction(
        self, instr: dis.Instruction, mark_as_current: bool = False
    ) -> None:
        if instr.line_number:
            self.file.target_line = instr.line_number
        super().print_instruction(instr, mark_as_current=mark_as_current)


def _get_instructions(
    insts: Iterable[PseudoInstruction | dis.Instruction],
    arg_resolver: PseudoInstrsArgResolver,
) -> Iterable[dis.Instruction]:
    prev_line = None
    for offset, inst in enumerate(insts):
        if isinstance(inst, dis.Instruction):
            yield inst
            continue
        op, arg = inst[:2]
        start_offset = 0
        positions = dis.Positions(*inst[2:6])
        line_number = positions.lineno if (positions.lineno or 0) > 0 else None
        starts_line = line_number != prev_line
        prev_line = line_number
        label = arg_resolver.labels_map.get(offset, None)
        argval, argrepr = arg_resolver.get_argval_argrepr(op, arg, offset)
        yield dis.Instruction(
            dis._all_opname[op],
            op,
            arg,
            argval,
            argrepr,
            offset,
            start_offset,
            starts_line,
            line_number,
            label,
            positions,
        )


def _disassemble(
    insts: Sequence[PseudoInstruction], co_consts: Sequence[object], title: str
) -> Iterable[Detail]:
    jump_targets = [
        target for op, target, *_ in insts if op in dis.hasjump or op in dis.hasexc
    ]
    labels_map = {offset: i for i, offset in enumerate(jump_targets, start=1)}

    # V1

    # resolver = PseudoInstrsArgResolver(co_consts=co_consts, labels_map=labels_map)

    # offset = 0
    # for opcode, oparg, sl, el, sc, ec in insts:
    #     argval, argrepr = resolver.get_argval_argrepr(opcode, oparg, offset)
    #     yield f"{dis.opname[opcode]:24} {argrepr}", sl, el+1
    #     offset += 2

    # V2
    label_width = 4 + len(str(len(labels_map)))
    arg_resolver = PseudoInstrsArgResolver(co_consts=co_consts, labels_map=labels_map)

    result: list[Detail] = []
    dis.print_instructions(
        _get_instructions(insts, arg_resolver),
        None,  # exception_entries
        Formatter(file=AppendStream(result), lineno_width=6, label_width=label_width),
    )
    yield title, -1, -1
    yield from result


class BytecodeWidget(BaseWidget):

    mode: BytecodeMode

    def __init__(self, *args: Any, mode: BytecodeMode, **kwargs: Any) -> None:
        if mode != "compiled" and not VERSION_3_13:
            raise ValueError(
                f"mode={mode!r} is not a supported format in Python < 3.13"
            )
        super().__init__(*args, **kwargs)
        self.mode = mode

    def set_code(self, code: str) -> None:
        if self.mode in ("pseudo", "optimized"):
            insts, metadata = compiler_codegen(
                ast.parse(code, optimize=1), "<source>", 0
            )
            co_consts = [
                p[1] for p in sorted([(v, k) for k, v in metadata["consts"].items()])
            ]

            if self.mode == "optimized":
                nlocals = 0
                insts = optimize_cfg(insts, co_consts, nlocals)

            self.update(
                _disassemble(
                    insts.get_instructions(), co_consts, f"<{self.mode} bytecode>"
                )
            )
        else:
            assert self.mode == "compiled"
            pass
