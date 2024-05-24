import ast
from typing import Any, Iterable


from base_widget import BaseWidget, Detail


def _has_children(node: ast.AST) -> bool:
    SENTINEL = object()
    if isinstance(node, ast.Name):
        return False
    for name in node._fields:
        value = getattr(node, name, SENTINEL)
        if isinstance(value, list | ast.AST):
            return True
    return False


def _attr_repr(node: ast.AST, attr: str) -> str:
    value = getattr(node, attr, ...)
    match value:
        case ast.Load() | ast.Store():
            return value.__class__.__name__
        case ast.AST:
            raise ValueError("Should not get an AST node here of type {node.__class__}")
        case _:
            return repr(value)


def dump_iter(node: ast.AST) -> Iterable[Detail]:
    SENTINEL = object()
    indent = "    "

    def _format(
        node: Any, level: int = 0, last_line: int = 0, prepend: str = ""
    ) -> Iterable[Detail]:
        prefix = f"{indent*level}{prepend}"
        match node:
            case ast.AST(_fields=fields):
                start = getattr(node, "lineno", last_line)
                end = getattr(node, "end_lineno", start) + 1
                if not _has_children(node):
                    args = (f"{name}={_attr_repr(node, name)}" for name in fields)
                    yield f"{prefix}{node.__class__.__name__}({', '.join(args)})", start, end
                else:
                    yield f"{prefix}{node.__class__.__name__}()", start, end
                    for name in fields:
                        value = getattr(node, name, SENTINEL)
                        if value is SENTINEL:
                            continue
                        yield from _format(value, level + 1, start, f"{name}=")
            case [single_value] if not _has_children(single_value):
                dets = list(_format(single_value, level, last_line, prepend + "["))
                assert len(dets) == 1
                text, start, end = dets[0]
                yield text + "]", start, end
            case [*values]:
                yield f"{prefix}[]", last_line, last_line + 1
                for value in values:
                    yield from _format(value, level + 1, last_line)
            case otherwise:
                yield f"{prefix}{otherwise!r}", last_line, last_line + 1

    yield from _format(node)


class ASTWidget(BaseWidget):

    optimized: bool

    def __init__(self, *args: Any, optimized: bool = False, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.optimized = optimized

    def set_code(self, code: str) -> None:
        if not self.optimized:
            tree = ast.parse(code)
        else:
            tree = ast.parse(code, optimize=True)  # type: ignore
        self.update(dump_iter(tree))
