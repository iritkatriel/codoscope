from __future__ import annotations

import ast
import dis
import html
import io
import json
import re
import sys
import tokenize
import traceback
import types
from token import tok_name
from typing import Any, Iterator

from _testinternalcapi import compiler_codegen, optimize_cfg


def view_tokens(code: str) -> dict[str, Any]:
    if color := sys.version_info >= (3, 15):
        import _colorize

        theme = _colorize.get_theme(force_color=True)
        syntax = theme.syntax
        token_colors = tokenize._get_token_colors(syntax, theme.tokenize)
        reset = syntax.reset

    toks = list(tokenize.tokenize(io.BytesIO(code.encode("utf-8")).readline))
    html_lines = []
    src_lines = []
    current_line = 0
    for tok in toks:
        line, end = tok.start[0], tok.end[0]
        if end != line:
            marker = f"{line:4d}-{end}: "
        elif line != current_line:
            marker = f"{line:4d}: "
        else:
            marker = "      "
        if color:
            ansi = (
                f"{theme.tokenize.position}{marker}{reset}"
                f"{token_colors.get(tok.type, reset)}{tok_name[tok.exact_type]:10}{reset} "
                f"{tok.string!r}"
            )
            html_lines.append(_ansi_to_html(ansi))
        else:
            plain = f"{marker}{tok_name[tok.exact_type]:10} {tok.string!r}"
            html_lines.append(html.escape(plain))
        src_lines.append(line if line > 0 else None)
        current_line = line
    return {
        "text": "\n".join(html_lines),
        "lines": src_lines,
        "html": True,
    }


_ANSI_RE = re.compile(r"\x1b\[([0-9;]*)m")
_LINENO_RE = re.compile(r"\blineno=(\d+)")
_ATTR_ROW_RE = re.compile(r"^\s*(?:lineno|col_offset|end_lineno|end_col_offset)=\d+")
_ANSI_CLASS = {
    "31": "ansi-red",
    "32": "ansi-green",
    "33": "ansi-yellow",
    "34": "ansi-blue",
    "36": "ansi-cyan",
    "90": "ansi-grey",
    "1;31": "ansi-bold-red",
    "1;34": "ansi-bold-blue",
}


def _ansi_to_html(s: str) -> str:
    out: list[str] = []
    pos = 0
    open_span = False
    for m in _ANSI_RE.finditer(s):
        out.append(html.escape(s[pos : m.start()]))
        if open_span:
            out.append("</span>")
            open_span = False
        code = m.group(1)
        cls = _ANSI_CLASS.get(code) if code and code != "0" else None
        if cls:
            out.append(f'<span class="{cls}">')
            open_span = True
        pos = m.end()
    out.append(html.escape(s[pos:]))
    if open_span:
        out.append("</span>")
    return "".join(out)


def _attach_linenos(plain_lines: list[str]) -> list[int | None]:
    n = len(plain_lines)
    result: list[int | None] = [None] * n
    indents = [len(line) - len(line.lstrip(" ")) for line in plain_lines]

    for i, line in enumerate(plain_lines):
        m = _LINENO_RE.search(line)
        if m:
            result[i] = int(m.group(1))

    for i in range(n - 1, -1, -1):
        if result[i] is not None:
            continue
        my_indent = indents[i]
        for j in range(i + 1, n):
            if indents[j] <= my_indent:
                break
            if indents[j] == my_indent + 4 and result[j] is not None:
                result[i] = result[j]
                break

    for i in range(n):
        if result[i] is not None:
            continue
        for j in range(i - 1, -1, -1):
            if indents[j] < indents[i] and result[j] is not None:
                result[i] = result[j]
                break

    return result


_END_COL_RE = re.compile(r"^\s*end_col_offset=\d+([)\]]*)(,?)\s*$")


def _strip_attribute_rows(
    plain_lines: list[str],
    html_lines: list[str],
    lineno_map: list[int | None],
) -> tuple[list[str], list[str], list[int | None]]:
    n = len(plain_lines)
    keep = [True] * n
    plain_lines = list(plain_lines)
    html_lines = list(html_lines)

    i = 0
    while i < n:
        if not _ATTR_ROW_RE.match(plain_lines[i]):
            i += 1
            continue
        start = i
        struct = ""
        trailing_comma = False
        while i < n and _ATTR_ROW_RE.match(plain_lines[i]):
            keep[i] = False
            m = _END_COL_RE.match(plain_lines[i])
            if m:
                struct += m.group(1)
                trailing_comma = bool(m.group(2))
            i += 1
        tail = struct + ("," if trailing_comma else "")
        prev = start - 1
        if prev >= 0 and tail:
            plain_lines[prev] = _replace_trailing_comma(plain_lines[prev], tail)
            html_lines[prev] = _replace_trailing_comma(html_lines[prev], tail)

    new_plain = [line for i, line in enumerate(plain_lines) if keep[i]]
    new_html = [line for i, line in enumerate(html_lines) if keep[i]]
    new_lineno = [ln for i, ln in enumerate(lineno_map) if keep[i]]
    return new_plain, new_html, new_lineno


def _replace_trailing_comma(line: str, tail: str) -> str:
    rstripped = line.rstrip()
    if rstripped.endswith(","):
        rstripped = rstripped[:-1]
    return rstripped + tail


def view_ast(code: str, *, optimize: bool = False) -> dict[str, Any]:
    tree = ast.parse(code, optimize=1) if optimize else ast.parse(code)
    dump_kwargs: dict[str, Any] = dict(
        indent=4, include_attributes=True, show_empty=True
    )
    if sys.version_info >= (3, 15):
        dump_kwargs["color"] = True
    colored = ast.dump(tree, **dump_kwargs)
    plain_lines = _ANSI_RE.sub("", colored).split("\n")
    html_lines = [_ansi_to_html(line) for line in colored.split("\n")]
    lineno_map = _attach_linenos(plain_lines)
    _, html_lines, lineno_map = _strip_attribute_rows(
        plain_lines, html_lines, lineno_map
    )
    return {
        "text": "\n".join(html_lines),
        "lines": lineno_map,
        "html": True,
    }


class _PseudoArgResolver(dis.ArgResolver):
    def offset_from_jump_arg(self, op, arg, offset):
        if op in dis.hasjump or op in dis.hasexc:
            return arg
        return super().offset_from_jump_arg(op, arg, offset)


class _CaptureStream:
    def __init__(self):
        self.lines = []
        self.src_lines = []
        self.current_line = None

    def write(self, line):
        if line.strip():
            self.lines.append(line)
            self.src_lines.append(self.current_line)


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


class _LineTrackingFormatter(dis.Formatter):
    def print_instruction(self, instr, mark_as_current=False):
        line = getattr(instr, "line_number", None)
        if line:
            self.file.current_line = line
        super().print_instruction(instr, mark_as_current=mark_as_current)


def _disassemble(insts_list, co_consts) -> dict[str, Any]:
    stream = _CaptureStream()
    jump_targets = [
        t for op, t, *_ in insts_list if op in dis.hasjump or op in dis.hasexc
    ]
    labels_map = {o: i for i, o in enumerate(jump_targets, start=1)}
    resolver = _PseudoArgResolver(co_consts=co_consts, labels_map=labels_map)
    fmt = _LineTrackingFormatter(
        file=stream,
        lineno_width=4,
        label_width=4 + len(str(len(labels_map))),
    )
    dis.print_instructions(_iter_instructions(insts_list, resolver), None, fmt)
    return {"text": "\n".join(stream.lines), "lines": list(stream.src_lines)}


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
    if isinstance(consts, list):
        return list(consts) if consts else None
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
                adjusted.extend(
                    _ConstPlaceholder(k) for k in range(len(adjusted), insert_at)
                )
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


def _iter_nested_code_objects(co: types.CodeType) -> Iterator[types.CodeType]:
    for const in co.co_consts:
        if isinstance(const, types.CodeType):
            yield const
            yield from _iter_nested_code_objects(const)


def _heading_view(co: types.CodeType) -> dict[str, Any]:
    name = getattr(co, "co_qualname", None) or co.co_name
    text = f"\nDisassembly of <code object {name} at line {co.co_firstlineno}>:"
    return {"text": text, "lines": [None] * (text.count("\n") + 1)}


def _combine_views(*parts: dict[str, Any]) -> dict[str, Any]:
    text_segs = []
    src_lines = []
    for p in parts:
        text_segs.append(p["text"])
        src_lines.extend(p["lines"])
    return {"text": "\n".join(text_segs), "lines": src_lines}


def _nested_compiled_views(co: types.CodeType) -> Iterator[dict[str, Any]]:
    for nested in _iter_nested_code_objects(co):
        yield _heading_view(nested)
        yield _disassemble(list(dis.Bytecode(nested)), list(nested.co_consts))


def view_pseudo(code: str, *, optimize: bool = False) -> dict[str, Any]:
    insts, metadata = compiler_codegen(ast.parse(code, optimize=1), "<source>", 0)
    co_consts = _merge_co_consts(
        _co_consts_from_metadata(metadata), _compiled_co_consts(code)
    )
    if optimize:
        insts = optimize_cfg(insts, co_consts, 0)
    items = _instruction_items(insts)
    adjusted_consts = _apply_annotations_const_workaround(items, co_consts)
    top = _disassemble(items, _fit_co_consts(items, adjusted_consts))
    co = compile(code, "<source>", "exec", optimize=1)
    return _combine_views(top, *_nested_compiled_views(co))


def view_compiled(code: str) -> dict[str, Any]:
    # assemble_code_object requires metadata["consts"] that compiler_codegen
    # no longer emits. Fall back to the public compile() API which yields an
    # equivalent final code object (with real consts).
    co = compile(code, "<source>", "exec", optimize=1)
    top = _disassemble(list(dis.Bytecode(co)), list(co.co_consts))
    return _combine_views(top, *_nested_compiled_views(co))


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
            view = fn(code)
        except Exception:
            text = traceback.format_exc()
            view = {"text": text, "lines": [None] * len(text.splitlines())}
        result[name] = view
    json.dump(result, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
