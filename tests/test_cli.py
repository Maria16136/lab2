import json
import subprocess
import sys
from pathlib import Path

import streamstats.__main__ as cli
from streamstats.__main__ import main
from streamstats.errors import StreamStatsError


def run_cli(*args: str) -> subprocess.CompletedProcess:
    import os

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    return subprocess.run([sys.executable, "-m", "streamstats", *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=env, check=False)


def test_cli_help() -> None:
    result = run_cli("--help")

    assert result.returncode == 0
    assert "analyze" in result.stdout


def test_cli_analyzes_jsonl_file(tmp_path: Path) -> None:
    input_path = tmp_path / "events.jsonl"
    output_path = tmp_path / "report.json"
    input_path.write_text('{"timestamp":"2026-10-20T12:00:00",'
                          '"level":"INFO","source":"auth","message":"Вход"}\n', encoding="utf-8")

    result = run_cli("analyze", str(input_path), "--format", "jsonl", "--output", str(output_path))

    assert result.returncode == 0
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["total_events"] == 1
    assert report["level_counts"] == {"INFO": 1}


def test_cli_analyzes_csv_file(tmp_path: Path) -> None:
    input_path = tmp_path / "events.csv"
    output_path = tmp_path / "report.json"
    input_path.write_text("timestamp,level,source,message\n" "2026-10-20T12:00:00,ERROR,database,Ошибка\n", encoding="utf-8")

    result = run_cli("analyze", str(input_path), "--format", "csv", "--output", str(output_path))

    assert result.returncode == 0
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["total_events"] == 1
    assert report["source_counts"] == {"database": 1}


def test_cli_combines_multiple_files(tmp_path: Path) -> None:
    first_input = tmp_path / "first.jsonl"
    second_input = tmp_path / "second.jsonl"
    output_path = tmp_path / "report.json"

    first_input.write_text('{"timestamp":"2026-10-20T12:00:00",'
                           '"level":"INFO","source":"auth","message":"Вход"}\n', encoding="utf-8")
    second_input.write_text('{"timestamp":"2026-10-20T12:01:00",'
                            '"level":"ERROR","source":"database","message":"Сбой"}\n', encoding="utf-8")

    result = run_cli("analyze", str(first_input), str(second_input), "--format", "jsonl", "--output", str(output_path))

    assert result.returncode == 0
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["total_events"] == 2
    assert report["level_counts"] == {"INFO": 1, "ERROR": 1}


def test_cli_invalid_record_returns_error(tmp_path: Path) -> None:
    input_path = tmp_path / "events.jsonl"
    output_path = tmp_path / "report.json"
    input_path.write_text("это не JSON\n", encoding="utf-8")

    result = run_cli("analyze", str(input_path), "--format", "jsonl", "--output", str(output_path))

    assert result.returncode == 2
    assert "events.jsonl" in result.stderr
    assert "строка 1" in result.stderr


def test_cli_skip_invalid_records(tmp_path: Path) -> None:
    input_path = tmp_path / "events.jsonl"
    output_path = tmp_path / "report.json"
    input_path.write_text("это не JSON\n" '{"timestamp":"2026-10-20T12:00:00",'
                          '"level":"INFO","source":"auth","message":"Вход"}\n', encoding="utf-8")

    result = run_cli("analyze", str(input_path), "--format", "jsonl", "--output", str(output_path), "--skip-invalid")

    assert result.returncode == 0
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["total_events"] == 1
    assert report["skipped_records"] == 1
    assert "WARNING" in result.stderr


def test_cli_missing_input_file_returns_error(tmp_path: Path) -> None:
    input_path = tmp_path / "missing.jsonl"
    output_path = tmp_path / "report.json"

    result = run_cli("analyze", str(input_path), "--format", "jsonl", "--output", str(output_path))

    assert result.returncode == 2
    assert "Ошибка работы с файлом" in result.stderr


def test_main_analyzes_jsonl_file(tmp_path: Path, monkeypatch) -> None:
    input_path = tmp_path / "events.jsonl"
    output_path = tmp_path / "report.json"

    input_path.write_text('{"timestamp":"2026-10-20T12:00:00",'
                          '"level":"INFO","source":"auth","message":"Login"}\n', encoding="utf-8")

    monkeypatch.setattr(sys, "argv", ["streamstats", "analyze", str(input_path), "--format",
                                      "jsonl", "--output", str(output_path)])

    assert main() == 0
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["total_events"] == 1


def test_main_returns_two_for_missing_file(tmp_path: Path, monkeypatch) -> None:
    output_path = tmp_path / "report.json"

    monkeypatch.setattr(sys, "argv", ["streamstats", "analyze", str(tmp_path / "missing.jsonl"),
                                      "--format", "jsonl", "--output", str(output_path)])

    assert main() == 2


def test_main_handles_streamstats_error(tmp_path: Path, monkeypatch, caplog) -> None:
    input_path = tmp_path / "events.jsonl"
    output_path = tmp_path / "report.json"
    input_path.write_text("{}", encoding="utf-8")

    def failing_parser(*args, **kwargs):
        raise StreamStatsError("Тестовая ошибка")
        yield

    monkeypatch.setattr(cli, "parse_jsonl_file", failing_parser)
    monkeypatch.setattr(sys, "argv", ["streamstats", "analyze", str(input_path),
                                      "--format", "jsonl", "--output", str(output_path)])

    assert main() == 2
    assert "Тестовая ошибка" in caplog.text


def test_main_handles_output_error(tmp_path: Path, monkeypatch, caplog) -> None:
    input_path = tmp_path / "events.jsonl"
    input_path.write_text("", encoding="utf-8")

    def failing_save_report(*args, **kwargs) -> None:
        raise OSError("Не удалось сохранить отчёт")

    monkeypatch.setattr(cli, "save_report", failing_save_report)
    monkeypatch.setattr(sys, "argv", ["streamstats", "analyze", str(input_path), "--format", "jsonl",
                                      "--output", str(tmp_path / "report.json")])

    assert main() == 2
    assert "Ошибка работы с файлом" in caplog.text