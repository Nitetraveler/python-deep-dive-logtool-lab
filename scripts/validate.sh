#!/usr/bin/env bash

set -euo pipefail

cd "$(dirname "$0")/.."

source .venv/bin/activate

echo "========== FINAL LAB VALIDATION =========="
date -u

echo
echo "========== ENVIRONMENT =========="

python --version
git --version
python -m pip check

echo
echo "========== PACKAGE ENTRY POINTS =========="

logtool --version
python -m logtool --version

echo
echo "========== DATASET INTEGRITY =========="

test "$(wc -l < data/access.log)" -eq 20000
test "$(gzip -cd data/access.log.1.gz | wc -l)" -eq 2000
test "$(wc -l < data/big.log)" -eq 200000

echo "PASS: All dataset sizes"

echo
echo "========== MAIN LAB SUMMARY =========="

logtool summary data/access.log -f json |
jq -e '
    .records == 19980 and
    .malformed == 20 and
    .total_bytes == 17972000 and
    .unique_ips == 4 and
    .error_rate == 0.1992 and
    .status_classes["5xx"] == 1980
'

echo
echo "========== COMBINED DATASET =========="

logtool summary data/access.log data/access.log.1.gz -f json |
jq -e '
    .records == 21978 and
    .malformed == 22 and
    .total_bytes == 19769200
'

echo
echo "========== TOP IP =========="

logtool top data/access.log --by ip -n 2 -f json |
jq -e '
    .top_ip == [
        ["203.0.113.10", 8563],
        ["198.51.100.23", 5708]
    ]
'

echo
echo "========== TOP PATH =========="

logtool top data/access.log --by path -n 3 -f json |
jq -e '
    .top_path == [
        ["/api/v1/items", 10000],
        ["/index.html", 5000],
        ["/login", 2500]
    ]
'

echo
echo "========== ERROR ANALYSIS =========="

logtool errors data/access.log --min-status 500 -f json |
jq -e '
    .error_records == 1980 and
    .by_status["500"] == 1000 and
    .by_status["503"] == 980
'

echo
echo "========== CHALLENGE HOURLY =========="

logtool hourly data/access.log \
    --since 2024-10-10T02:00:00 \
    --until 2024-10-10T03:59:59 -f json |
jq -e '
    .hourly == [
        ["2024-10-10 02:00", 3597],
        ["2024-10-10 03:00", 3596]
    ]
'

echo
echo "========== CHALLENGE CSV =========="

actual=$(logtool top data/access.log --by ip -n 2 -f csv)

expected=$(printf 'key,value\n203.0.113.10,8563\n198.51.100.23,5708')

test "$actual" = "$expected"

echo "PASS: CSV output"

echo
echo "========== EXIT CODE VERIFICATION =========="

check_exit() {
    local expected="$1"
    shift
    local actual=0

    "$@" >/dev/null 2>&1 || actual=$?

    printf 'Expected=%s Actual=%s Command=%s\n' \
        "$expected" "$actual" "$*"

    test "$actual" -eq "$expected"
}

check_exit 0 logtool summary data/access.log
check_exit 1 logtool summary data/nonexistent.log
check_exit 2 logtool top data/access.log --by invalid
check_exit 2 logtool top data/access.log -n 0
check_exit 2 logtool hourly data/access.log --since yesterday
check_exit 3 logtool summary data/access.log --fail-on-error-rate 0.15
check_exit 0 logtool summary data/access.log --fail-on-error-rate 0.25

echo
echo "========== LARGE DATASET =========="

logtool summary data/big.log -f json |
jq -e '
    .records == 199800 and
    .malformed == 200 and
    .total_bytes == 179720000
'

echo
echo "========== CODE QUALITY =========="

ruff check .
black --check -q .
mypy

echo
echo "========== COMPLETE AUTOMATED TESTS =========="

pytest -q \
    --cov=logtool \
    --cov-report=term-missing \
    --cov-fail-under=100

echo
echo "========== OPTIMISED TIMESTAMP PARSER =========="

if grep -n 'strptime(' src/logtool/timeparse.py; then
    echo "FAIL: Slow timestamp parser remains"
    exit 1
fi

echo "PASS: Optimised timestamp parser"

echo
echo "========== RELEASE ARTIFACT =========="

sha256sum --check evidence/task-08-wheel.sha256

echo
echo "========== RELEASE TAGS =========="

git show-ref --verify refs/tags/v0.1.0
git show-ref --verify refs/tags/v0.2.0

git merge-base --is-ancestor v0.1.0 v0.2.0
git merge-base --is-ancestor v0.2.0 HEAD

echo
echo "========== REQUIRED PROJECT FILES =========="

for file in \
    README.md \
    pyproject.toml \
    scripts/gen_logs.py \
    scripts/bench.py \
    scripts/validate.sh \
    tests/test_challenge.py \
    evidence/task-07-regression.log \
    evidence/task-08-final-validation.log \
    evidence/challenge-verification.log \
    evidence/challenge-final-coverage.log
do
    test -s "$file"
    echo "PASS: $file"
done

echo
echo "========== FINAL RESULT =========="

echo "PASS: ALL MAIN LAB REQUIREMENTS"
echo "PASS: ALL CHALLENGE REQUIREMENTS"
echo "PASS: ALL QUALITY GATES"
echo "PASS: RELEASE INTEGRITY"
echo "PASS: COMPREHENSIVE FINAL VALIDATION"
