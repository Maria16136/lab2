import json

from streamstats.report import save_report


def test_save_report_creates_file(tmp_path) -> None:
    output_path = tmp_path / "report.json"
    report = {"total_events": 3}

    save_report(report, output_path)

    assert output_path.exists()


def test_saved_report_contains_correct_data(tmp_path) -> None:
    output_path = tmp_path / "report.json"
    report = {"total_events": 2, "level_counts": {"INFO": 1, "ERROR": 1}, "source_counts": {"auth": 1, "database": 1}}

    save_report(report, output_path)

    with output_path.open("r", encoding="utf-8") as file:
        saved_report = json.load(file)

    assert saved_report == report


def test_saved_report_preserves_unicode(tmp_path) -> None:
    output_path = tmp_path / "report.json"
    report = {"message": "Ошибка авторизации"}

    save_report(report, output_path)

    content = output_path.read_text(encoding="utf-8")

    assert "Ошибка авторизации" in content


def test_saved_report_is_valid_json(tmp_path) -> None:
    output_path = tmp_path / "report.json"
    report = {"total_events": 5, "skipped_records": 1}

    save_report(report, output_path)

    content = output_path.read_text(encoding="utf-8")
    saved_report = json.loads(content)

    assert saved_report["total_events"] == 5
    assert saved_report["skipped_records"] == 1