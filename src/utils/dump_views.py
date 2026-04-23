from __future__ import annotations

import argparse
import importlib
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from web.driver import VIEWS  # noqa: E402


def _load_code(parsed: argparse.Namespace) -> str:
    if parsed.filename:
        return Path(parsed.filename).read_text()
    if parsed.command:
        return parsed.command
    if parsed.module:
        src_path = importlib.import_module(parsed.module).__file__
        if src_path:
            return Path(src_path).read_text()
        raise ValueError(f"module {parsed.module} has no source")
    return ""


def _print_section(title: str, body: str) -> None:
    bar = "=" * 20
    print(f"\n{bar} {title} {bar}")
    print(body if body else "<empty>")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="dump_views",
        description="Print compiler pipeline views without the Textual UI",
    )
    parser.add_argument("filename", nargs="?")
    parser.add_argument("-c", dest="command")
    parser.add_argument("-m", dest="module")
    parsed = parser.parse_args(argv)

    if (parsed.filename, parsed.command, parsed.module).count(None) < 2:
        parser.error("Ambiguous arguments. Choose either a file, a module or a command")

    code = _load_code(parsed)

    _print_section("SOURCE", code)
    _print_section("TOKENS", VIEWS["tokens"](code))
    _print_section("AST", VIEWS["ast"](code))
    _print_section("OPTIMIZED AST", VIEWS["ast-opt"](code))
    _print_section("PSEUDO BYTECODE", VIEWS["pseudo"](code))
    _print_section("OPTIMIZED PSEUDO BYTECODE", VIEWS["pseudo-opt"](code))
    _print_section("CODE OBJECT", VIEWS["compiled"](code))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
