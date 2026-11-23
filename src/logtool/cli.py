"""Command-line interface for logtool."""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Callable, Sequence
from datetime import UTC, datetime

from logtool import __version__
from logtool.analyzer import LogAnalyzer, hourly_counts
from logtool.reader import (
    ParseStats,
    between,
    filter_records,
    parse_records,
    read_lines,
)
from logtool.reporters import REPORTERS, get_reporter
from logtool.utils import timed

Handler = Callable[[argparse.Namespace], int]

EXIT_OK = 0
EXIT_IO_ERROR = 1
EXIT_THRESHOLD = 3


@timed
def analyze(
    paths: Sequence[str], min_status: int | None = None
) -> tuple[LogAnalyzer, ParseStats]:
    """Build and consume the streaming analysis pipeline."""
    stats = ParseStats()
    records = parse_records(read_lines(paths), stats)

    if min_status is not None:
        records = filter_records(records, min_status=min_status)

    return LogAnalyzer(records), stats


def emit(data: dict[str, object], fmt: str) -> None:
    """Render and print a report."""
    print(get_reporter(fmt).render(data))


def cmd_summary(args: argparse.Namespace) -> int:
    analyzer, stats = analyze(args.files)

    data: dict[str, object] = {
        "files": len(args.files),
        "malformed": stats.malformed,
        **analyzer.summary(),
    }

    emit(data, args.format)

    threshold = args.fail_on_error_rate

    if threshold is not None and analyzer.error_rate > threshold:
        print(
            f"logtool: error rate {analyzer.error_rate:.2%} "
            f"exceeds threshold {threshold:.2%}",
            file=sys.stderr,
        )
        return EXIT_THRESHOLD

    return EXIT_OK


def cmd_top(args: argparse.Namespace) -> int:
    analyzer, _ = analyze(args.files)

    emit(
        {f"top_{args.by}": analyzer.top(args.by, args.n)},
        args.format,
    )

    return EXIT_OK


def cmd_errors(args: argparse.Namespace) -> int:
    analyzer, _ = analyze(args.files, min_status=args.min_status)

    data: dict[str, object] = {
        "min_status": args.min_status,
        "error_records": len(analyzer),
        "by_status": {
            str(status): count
            for status, count in sorted(analyzer.status_counts.items())
        },
        "top_error_paths": analyzer.top("path", args.n),
    }

    emit(data, args.format)

    return EXIT_OK


def positive_int(value: str) -> int:
    number = int(value)

    if number < 1:
        raise argparse.ArgumentTypeError(f"must be >= 1, got {value}")

    return number


def ratio(value: str) -> float:
    number = float(value)

    if not 0.0 <= number <= 1.0:
        raise argparse.ArgumentTypeError(f"must be between 0 and 1, got {value}")

    return number


def iso_datetime(value: str) -> datetime:
    """Parse ISO-8601 timestamps, treating naive values as UTC."""
    try:
        result = datetime.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"invalid ISO-8601 timestamp: {value!r}"
        ) from exc

    if result.tzinfo is None:
        result = result.replace(tzinfo=UTC)

    return result


def cmd_hourly(args: argparse.Namespace) -> int:
    """Report hourly counts within optional inclusive date bounds."""
    records = parse_records(read_lines(args.files))

    selected = between(
        records,
        since=args.since,
        until=args.until,
    )

    emit({"hourly": hourly_counts(selected)}, args.format)
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logtool",
        description="Streaming access-log analysis CLI",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="-v for INFO, -vv for DEBUG",
    )

    common = argparse.ArgumentParser(add_help=False)

    common.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="plain or gzip access-log files",
    )

    common.add_argument(
        "-f",
        "--format",
        choices=sorted(REPORTERS),
        default="text",
        help="report output format",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        metavar="COMMAND",
    )

    summary = subparsers.add_parser(
        "summary",
        parents=[common],
        help="summarize access logs",
    )

    summary.add_argument(
        "--fail-on-error-rate",
        type=ratio,
        metavar="RATIO",
        help="exit 3 if the error rate exceeds this ratio",
    )

    summary.set_defaults(func=cmd_summary)

    top = subparsers.add_parser(
        "top",
        parents=[common],
        help="show most frequent values",
    )

    top.add_argument(
        "--by",
        choices=["ip", "path", "status"],
        default="ip",
    )

    top.add_argument("-n", type=positive_int, default=5)
    top.set_defaults(func=cmd_top)

    errors = subparsers.add_parser(
        "errors",
        parents=[common],
        help="analyze HTTP errors",
    )

    errors.add_argument("--min-status", type=int, default=400)
    errors.add_argument("-n", type=positive_int, default=5)
    errors.set_defaults(func=cmd_errors)

    hourly = subparsers.add_parser(
        "hourly",
        parents=[common],
        help="Count records per hour",
    )
    hourly.add_argument("--since", type=iso_datetime)
    hourly.add_argument("--until", type=iso_datetime)
    hourly.set_defaults(func=cmd_hourly)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    level = {
        0: logging.WARNING,
        1: logging.INFO,
    }.get(args.verbose, logging.DEBUG)

    logging.basicConfig(
        level=level,
        stream=sys.stderr,
        format="%(levelname)s %(name)s: %(message)s",
    )

    try:
        handler: Handler = args.func
        return handler(args)
    except FileNotFoundError as exc:
        print(f"logtool: error: {exc}", file=sys.stderr)
        return EXIT_IO_ERROR
    except KeyboardInterrupt:
        print("logtool: interrupted", file=sys.stderr)
        return 130
