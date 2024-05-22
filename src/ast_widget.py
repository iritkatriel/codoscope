import ast
from typing import Any, Iterable


from base_widget import BaseWidget, Detail


def _has_children(node: ast.AST) -> bool:
    SENTINEL = object()
    for name in node._fields:
        value = getattr(node, name, SENTINEL)
        if isinstance(value, list | ast.AST):
            return True
    return False


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
                    args = (f"{name}={getattr(node, name, ...)!r}" for name in fields)
                    yield f"{prefix}{node.__class__.__name__}({', '.join(args)})", start, end
                else:
                    yield f"{prefix}{node.__class__.__name__}()", start, end
                    for name in fields:
                        value = getattr(node, name, SENTINEL)
                        if value is SENTINEL:
                            continue
                        yield from _format(value, level + 1, start, f"{name}=")
            case [*values]:
                yield f"{prefix}[]", last_line, last_line + 1
                for value in values:
                    yield from _format(value, level + 1, last_line)
            case otherwise:
                yield f"{prefix}{otherwise!r}", last_line, last_line + 1

    yield from _format(node)


class ASTWidget(BaseWidget):

    def set_code(self, code: str) -> None:
        tree = ast.parse(code)
        self.update(dump_iter(tree))
