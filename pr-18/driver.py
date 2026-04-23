from __future__ import annotations

import ast
import dis
import io
import json
import sys
import tokenize
import traceback
from token import tok_name

from _testinternalcapi import compiler_codegen, optimize_cfg


def view_tokens(code: str) -> str:
    out = []
    toks = tokenize.tokenize(io.BytesIO(code.encode("utf-8")).readline)
    current_line = 0
    for t in toks:
        line, end = t.start[0], t.end[0]
        if end != line:
            marker = f"{line:4d}-{end}: "
        elif line != current_line:
            marker = f"{line:4d}: "
        else:
            marker = "      "
        out.append(f"{marker}{tok_name[t.exact_type]:10} {t.string!r}")
        current_line = line
    return "\n".join(out)


def view_ast(code: str, *, optimize: bool = False) -> str:
    tree = ast.parse(code, optimize=1) if optimize else ast.parse(code)
    return ast.dump(tree, indent=4)


class _PseudoArgResolver(dis.ArgResolver):
    def offset_from_jump_arg(self, op, arg, offset):
        if op in dis.hasjump or op in dis.hasexc:
            return arg
        return super().offset_from_jump_arg(op, arg, offset)


class _CaptureStream:
    def __init__(self):
        self.lines = []

    def write(self, line):
        if line.strip():
            self.lines.append(line)


def _iter_instructions(insts, resolver):
    prev_line = None
    for offset, inst in enumerate(insts):
        if isinstance(inst, dis.Instruction):
            yield inst
            continue
        op, arg = inst[:2]
        positions = dis.Positions(*inst[2:6])
        lineno = positions.lineno if (positions.lineno or 0) > 0 else None
        starts_line = lineno != prev_line
        prev_line = lineno
        label = resolver.labels_map.get(offset, None)
        argval, argrepr = resolver.get_argval_argrepr(op, arg, offset)
        yield dis.Instruction(
            dis._all_opname[op],
            op,
            arg,
            argval,
            argrepr,
            offset,
            0,
            starts_line,
            lineno,
            label,
            positions,
        )


def _disassemble(insts_list, co_consts) -> str:
    stream = _CaptureStream()
    jump_targets = [
        t for op, t, *_ in insts_list if op in dis.hasjump or op in dis.hasexc
    ]
    labels_map = {o: i for i, o in enumerate(jump_targets, start=1)}
    resolver = _PseudoArgResolver(co_consts=co_consts, labels_map=labels_map)
    fmt = dis.Formatter(
        file=stream,
        lineno_width=4,
        label_width=4 + len(str(len(labels_map))),
    )
    dis.print_instructions(_iter_instructions(insts_list, resolver), None, fmt)
    return "\n".join(stream.lines)


class _ConstPlaceholder:
    __slots__ = ("idx",)

    def __init__(self, idx):
        self.idx = idx

    def __repr__(self):
        return f"<const#{self.idx}>"


class _InternalConstPlaceholder:
    def __repr__(self):
        return "<internal const>"


def _max_const_arg(items):
    max_arg = -1
    for inst in items:
        if isinstance(inst, dis.Instruction):
            op, arg = inst.opcode, inst.arg
        else:
            op, arg = inst[0], inst[1]
        if op in dis.hasconst and arg is not None and arg > max_arg:
            max_arg = arg
    return max_arg


def _placeholder_consts(items):
    return [_ConstPlaceholder(i) for i in range(_max_const_arg(items) + 1)]


def _co_consts_from_metadata(metadata):
    if not metadata:
        return None
    consts = metadata.get("consts")
    if not isinstance(consts, dict) or not consts:
        return None
    # compiler metadata stores const->index and indices may be sparse.
    max_idx = max(consts.values())
    resolved = [_ConstPlaceholder(i) for i in range(max_idx + 1)]
    for value, idx in consts.items():
        resolved[idx] = value
    return resolved


def _merge_co_consts(metadata_consts, compiled_consts):
    if metadata_consts is None:
        return list(compiled_consts)
    merged = list(metadata_consts)
    limit = max(len(merged), len(compiled_consts))
    if len(merged) < limit:
        merged.extend(_ConstPlaceholder(i) for i in range(len(merged), limit))
    for i, value in enumerate(compiled_consts):
        if isinstance(merged[i], _ConstPlaceholder):
            merged[i] = value
    return merged


def _fit_co_consts(items, co_consts):
    max_arg = _max_const_arg(items)
    if max_arg < 0:
        return co_consts
    if len(co_consts) > max_arg:
        return co_consts
    fitted = list(co_consts)
    fitted.extend(_ConstPlaceholder(i) for i in range(len(fitted), max_arg + 1))
    return fitted


def _is_annotations_placeholder(inst) -> bool:
    if isinstance(inst, dis.Instruction):
        return inst.opname == "ANNOTATIONS_PLACEHOLDER"
    return dis._all_opname[inst[0]] == "ANNOTATIONS_PLACEHOLDER"


def _load_const_arg(inst):
    if isinstance(inst, dis.Instruction):
        if inst.opcode in dis.hasconst:
            return inst.arg
        return None
    op, arg = inst[0], inst[1]
    if op in dis.hasconst:
        return arg
    return None


def _apply_annotations_const_workaround(items, co_consts):
    """3.15+ pseudo code may use an internal const slot for annotations.

    Insert an explicit placeholder for that internal slot so subsequent
    LOAD_CONST values align with user-visible constants.
    """
    for i, inst in enumerate(items):
        if not _is_annotations_placeholder(inst):
            continue
        for nxt in items[i + 1 :]:
            const_arg = _load_const_arg(nxt)
            if const_arg is None:
                continue
            adjusted = list(co_consts)
            insert_at = const_arg
            if insert_at > len(adjusted):
                adjusted.extend(_ConstPlaceholder(k) for k in range(len(adjusted), insert_at))
            adjusted.insert(insert_at, _InternalConstPlaceholder())
            return adjusted
        break
    return co_consts


def _compiled_co_consts(code: str):
    # Fallback source for const values when compiler metadata omits "consts".
    return list(compile(code, "<source>", "exec", optimize=1).co_consts)


def _instruction_items(insts):
    if hasattr(insts, "get_instructions"):
        return list(insts.get_instructions())
    return list(insts)


def view_pseudo(code: str, *, optimize: bool = False) -> str:
    insts, metadata = compiler_codegen(ast.parse(code, optimize=1), "<source>", 0)
    co_consts = _merge_co_consts(_co_consts_from_metadata(metadata), _compiled_co_consts(code))
    # On some newer WASM builds (e.g. CPython 3.15 snapshots), optimize_cfg can
    # trap at runtime with low-level wasm errors. Prefer a stable pseudo view
    # there instead of crashing the whole worker process.
    if optimize and sys.version_info < (3, 15):
        insts = optimize_cfg(insts, co_consts, 0)
    items = _instruction_items(insts)
    adjusted_consts = _apply_annotations_const_workaround(items, co_consts)
    return _disassemble(items, _fit_co_consts(items, adjusted_consts))


def view_compiled(code: str) -> str:
    # assemble_code_object requires metadata["consts"] that compiler_codegen
    # no longer emits. Fall back to the public compile() API which yields an
    # equivalent final code object (with real consts).
    co = compile(code, "<source>", "exec", optimize=1)
    items = list(dis.Bytecode(co))
    return _disassemble(items, list(co.co_consts))


VIEWS = {
    "tokens": view_tokens,
    "ast": lambda c: view_ast(c, optimize=False),
    "ast-opt": lambda c: view_ast(c, optimize=True),
    "pseudo": lambda c: view_pseudo(c, optimize=False),
    "pseudo-opt": lambda c: view_pseudo(c, optimize=True),
    "compiled": view_compiled,
}


def main() -> int:
    try:
        code = open("user.py", encoding="utf-8").read()
    except FileNotFoundError:
        code = ""
    result = {"python_version": sys.version.split()[0]}
    for name, fn in VIEWS.items():
        try:
            result[name] = fn(code)
        except Exception:
            result[name] = traceback.format_exc()
    json.dump(result, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
