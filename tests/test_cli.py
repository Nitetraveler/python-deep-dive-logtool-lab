"""Tests for the command-line interface."""

import json
import subprocess
import sys

import pytest

from logtool.cli import main


def run_json(capsys, args):
    assert main([*args, "--format", "json"]) == 0
    return json.loads(capsys.readouterr().out)


def test_summary_json(log_file, capsys):
    data = run_json(capsys, ["summary", str(log_file)])
    assert data["records"] == 5
    assert data["malformed"] == 1
    assert data["files"] == 1
    assert data["total_bytes"] == 3030
    assert data["error_rate"] == 0.6


def test_summary_text(log_file, capsys):
    assert main(["summary", str(log_file)]) == 0
    out = capsys.readouterr().out
    assert "60.00%" in out
    assert "records" in out


def test_summary_multiple_files(log_file, gz_log_file, capsys):
    data = run_json(capsys, ["summary", str(log_file), str(gz_log_file)])
    assert data["files"] == 2
    assert data["records"] == 10
    assert data["malformed"] == 2


def test_top_path(log_file, capsys):
    data = run_json(capsys, ["top", str(log_file), "--by", "path", "-n", "2"])
    assert data["top_path"] == [
        ["/index.html", 2],
        ["/api/v1/items", 2],
    ]


def test_top_default(log_file, capsys):
    data = run_json(capsys, ["top", str(log_file)])
    assert data["top_ip"][0] == ["10.0.0.1", 3]


def test_errors_500(log_file, capsys):
    data = run_json(capsys, ["errors", str(log_file), "--min-status", "500"])
    assert data["error_records"] == 1
    assert data["by_status"] == {"500": 1}
    assert data["top_error_paths"] == [["/api/v1/items", 1]]


def test_errors_default(log_file, capsys):
    data = run_json(capsys, ["errors", str(log_file)])
    assert data["min_status"] == 400
    assert data["error_records"] == 3


@pytest.mark.parametrize(
    "threshold,expected",
    [("0.5", 3), ("0.7", 0), ("0.6", 0)],
)
def test_error_threshold(log_file, capsys, threshold, expected):
    assert (
        main(
            [
                "summary",
                str(log_file),
                "--fail-on-error-rate",
                threshold,
            ]
        )
        == expected
    )
    captured = capsys.readouterr()
    if expected == 3:
        assert "exceeds threshold" in captured.err
    else:
        assert "exceeds threshold" not in captured.err


def test_missing_file(tmp_path, capsys):
    assert main(["summary", str(tmp_path / "missing.log")]) == 1
    assert "log file not found" in capsys.readouterr().err


@pytest.mark.parametrize(
    "args",
    [
        ["top", "x.log", "--by", "user"],
        ["top", "x.log", "-n", "0"],
        ["summary", "x.log", "--fail-on-error-rate", "1.5"],
        ["summary", "x.log", "--fail-on-error-rate", "-0.1"],
        ["summary", "x.log", "-f", "invalid"],
        [],
    ],
)
def test_bad_arguments(args):
    with pytest.raises(SystemExit) as caught:
        main(args)
    assert caught.value.code == 2


def test_version(capsys):
    with pytest.raises(SystemExit) as caught:
        main(["--version"])
    assert caught.value.code == 0
    assert "logtool 0.1.0" in capsys.readouterr().out


def test_keyboard_interrupt(monkeypatch, capsys):
    def interrupt(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr("logtool.cli.analyze", interrupt)
    assert main(["summary", "x.log"]) == 130
    assert "interrupted" in capsys.readouterr().err


@pytest.mark.parametrize("flag", ["-v", "-vv"])
def test_verbose(log_file, flag, capsys):
    assert main([flag, "summary", str(log_file)]) == 0
    assert "records" in capsys.readouterr().out


def test_module_entrypoint(log_file):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "logtool",
            "summary",
            str(log_file),
            "-f",
            "json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(result.stdout)["records"] == 5
