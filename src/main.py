import argparse
from pathlib import Path
import importlib
import sys

from viewer import CodeViewer

def main(args: list[str]) -> None:
    parser = argparse.ArgumentParser(
        prog="codoscope",
        description="An interactive explorer for Python's compiler pipeline",
    )
    parser.add_argument("filename", nargs="?")
    parser.add_argument("-c", dest="command")
    parser.add_argument("-m", dest="module")
    parsed = parser.parse_args()
    # Check that at least 2 of the 3 options weren't entered
    if (parsed.filename, parsed.command, parsed.module).count(None) < 2:
        parser.error("Ambiguous arguments. Choose either a file, a module or a command")

    if parsed.filename:
        code = Path(parsed.filename).read_text()
    elif parsed.command:
        code = parsed.command
    elif parsed.module:
        src_path = importlib.import_module(parsed.module).__file__
        code = Path(src_path).read_text()
    else:
        code = "# Enter code here"

    app = CodeViewer()
    app.startup_code = code
    app.run()


if __name__ == "__main__":
    main(sys.argv)
