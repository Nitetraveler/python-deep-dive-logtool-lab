"""Command-line interface for logtool (stub - replaced in Task 6)."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from logtool import __version__


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="logtool")
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.parse_args(argv)
    print("logtool is installed - sub-commands arrive in Task 6")
    return 0
