# logtool

Streaming analysis of Apache/Nginx combined-format access logs (plain or gzip).

    logtool summary data/access.log
    logtool top data/access.log --by path -n 3
    logtool errors data/access.log --min-status 500 -f json

## Installation

Requires Python 3.12 or later.

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -e ".[dev]"

## Generate reproducible sample data

    python scripts/gen_logs.py --out data/access.log
    python scripts/gen_logs.py --lines 2000 --start 2024-10-09T00:00:00 --out data/access.log.1.gz
    python scripts/gen_logs.py --lines 200000 --out data/big.log

## CLI usage

    logtool summary data/access.log
    logtool summary data/access.log data/access.log.1.gz -f json
    logtool top data/access.log --by ip -n 5
    logtool top data/access.log --by path -n 5
    logtool errors data/access.log --min-status 500
    logtool -vv summary data/access.log
    logtool summary data/access.log --fail-on-error-rate 0.15

## Challenge extension

The challenge adds inclusive date-range filtering, hourly
aggregation, decorator-based reporter registration and CSV output.

    logtool hourly data/access.log -f json
    logtool hourly data/access.log --since 2024-10-10T02:00:00 --until 2024-10-10T03:59:59 -f json
    logtool top data/access.log --by ip -n 2 -f csv

Hourly aggregation uses itertools.groupby and expects
chronologically ordered records. Naive ISO timestamps are
interpreted as UTC. Explicit timezone offsets are supported.

Supported output formats: text, JSON and CSV.

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Successful execution |
| 1 | Missing input file |
| 2 | Invalid command-line arguments |
| 3 | Error-rate threshold exceeded |
| 130 | Interrupted execution |

## Architecture

| Module | Responsibility |
|--------|----------------|
| models.py | Immutable LogRecord and ParseError |
| timeparse.py | Optimised timestamp parsing |
| utils.py | Context managers and decorators |
| reader.py | Lazy generators and filtering |
| analyzer.py | Single-pass aggregation and hourly counts |
| reporters.py | Polymorphic reporters and registration |
| cli.py | Argument parsing, dispatch and exit codes |

## Verification

    ruff check .
    black --check .
    mypy
    pytest -q --cov=logtool --cov-report=term-missing --cov-fail-under=85

## Performance profiling

    python scripts/bench.py data/big.log
    python -m cProfile -o profile.out -m logtool summary data/big.log

## Expected deterministic results

| Metric | Expected |
|--------|----------|
| Plain input lines | 20000 |
| Valid records | 19980 |
| Malformed records | 20 |
| Total bytes | 17972000 |
| Unique IPs | 4 |
| Error records | 3980 |
| Error rate | 19.92% |
| Combined valid records | 21978 |
| Combined malformed records | 22 |
| Combined total bytes | 19769200 |

## Release history

- v0.1.0: Completed and verified main lab, Tasks 1-8.
- v0.2.0: Challenge extension with hourly analysis, date filtering,
  reporter registration and CSV output.

The package metadata retains the lab-specified version 0.1.0.
Git tags identify the main lab and challenge milestones.

## Evidence

The evidence directory contains environment verification,
task-level validation, regression exercises, coverage reports,
performance benchmarks, release checksums and challenge results.

Generated datasets can be recreated using scripts/gen_logs.py.
Virtual environments and temporary caches are excluded from Git.


## Author and lab completion

- Author: nitetraveler
- GitHub: Nitetraveler
- Training provider: Alnafi
- Programme: DCCS
- Lab: Python Deep Dive
- Main tasks: 8 of 8 completed
- Challenge extension: Completed
- Automated tests: 97 passed
- Statement coverage: 100%
- Branch coverage: 100%
- Timestamp parser speedup: 4.52x
- Main release: v0.1.0
- Challenge release: v0.2.0
- Comprehensive final validation: PASS

All implementation, verification reports and grading evidence
are preserved in this project.
