#!/usr/bin/env python3
"""Benchmark the streaming log analysis pipeline."""

import logging
import sys

from logtool.analyzer import LogAnalyzer
from logtool.reader import parse_records, read_lines
from logtool.utils import Timer


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    paths = sys.argv[1:] or ["data/big.log"]

    with Timer(f"pipeline over {len(paths)} file(s)") as timer:
        analyzer = LogAnalyzer(parse_records(read_lines(paths)))

    print(repr(analyzer))

    if timer.elapsed:
        print(f"{len(analyzer) / timer.elapsed:,.0f} records/s")


if __name__ == "__main__":
    main()
