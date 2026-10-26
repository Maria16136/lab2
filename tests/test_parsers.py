import pytest

from streamstats.errors import InvalidEventError, InvalidTimestampError
from streamstats.models import Event
from streamstats.parsers import (
    parse_csv_file,
    parse_csv_row,
    parse_jsonl_file,
    parse_jsonl_line,
)


def test_parse_jsonl_line() -> None:
    line = '{"timestamp": "2026-10-20T12:00:00", "level": "INFO", "source": "auth", "message": "User logged in"}'

    event = parse_jsonl_line(line)

    assert isinstance(event, Event)
    assert event.level == "INFO"
    assert event.source == "auth"
    assert event.message == "User logged in"


def test_parse_csv_row() -> None:
    row = {"timestamp": "2026-10-20T12:00:00", "level": "INFO", "source": "auth", "message": "User logged in"}

    event = parse_csv_row(row)

    assert isinstance(event, Event)
    assert event.timestamp == "2026-10-20T12:00:00"
    assert event.level == "INFO"
    assert event.source == "auth"
    assert event.message == "User logged in"


def test_invalid_json() -> None:
    with pytest.raises(InvalidEventError):
        parse_jsonl_line("это не JSON")


def test_missing_source() -> None:
    line = '{"timestamp": "2026-10-20T12:00:00", "level": "INFO", "message": "Hello"}'

    with pytest.raises(InvalidEventError):
        parse_jsonl_line(line)


def test_invalid_timestamp() -> None:
    line = '{"timestamp": "вчера", "level": "INFO", "source": "auth", "message": "Hello"}'

    with pytest.raises(InvalidTimestampError):
        parse_jsonl_line(line)


def test_invalid_level() -> None:
    line = '{"timestamp": "2026-10-20T12:00:00", "level": "UNKNOWN", "source": "auth", "message": "Hello"}'

    with pytest.raises(InvalidEventError):
        parse_jsonl_line(line)


def test_empty_source() -> None:
    line = '{"timestamp": "2026-10-20T12:00:00", "level": "INFO", "source": "   ", "message": "Hello"}'

    with pytest.raises(InvalidEventError):
        parse_jsonl_line(line)


def test_missing_timestamp() -> None:
    line = '{"level": "INFO", "source": "auth", "message": "Hello"}'

    with pytest.raises(InvalidEventError):
        parse_jsonl_line(line)


def test_wrong_level_type() -> None:
    line = '{"timestamp": "2026-10-20T12:00:00", "level": 123, "source": "auth", "message": "Hello"}'

    with pytest.raises(InvalidEventError):
        parse_jsonl_line(line)


def test_empty_jsonl_file(tmp_path) -> None:
    file_path = tmp_path / "events.jsonl"
    file_path.write_text("", encoding="utf-8")

    events = list(parse_jsonl_file(file_path))

    assert events == []


def test_empty_csv_file(tmp_path) -> None:
    file_path = tmp_path / "events.csv"
    file_path.write_text("timestamp,level,source,message\n", encoding="utf-8")

    events = list(parse_csv_file(file_path))

    assert events == []


def test_invalid_jsonl_file_stops_reading(tmp_path) -> None:
    file_path = tmp_path / "events.jsonl"
    file_path.write_text('{"timestamp": "2026-10-20T12:00:00", '
                         '"level": "INFO", "source": "auth", "message": "Hello"}\n' 'это не JSON\n', encoding="utf-8")

    with pytest.raises(InvalidEventError, match=r"events\.jsonl: строка 2"):
        list(parse_jsonl_file(file_path))


def test_skip_invalid_jsonl_record(tmp_path, caplog) -> None:
    file_path = tmp_path / "events.jsonl"
    file_path.write_text('{"timestamp": "2026-10-20T12:00:00", ' '"level": "INFO", "source": "auth", "message": "Hello"}\n'
                         'это не JSON\n' '{"timestamp": "2026-10-20T12:01:00", '
                         '"level": "ERROR", "source": "database", "message": "Failed"}\n', encoding="utf-8")

    events = list(parse_jsonl_file(file_path, skip_invalid=True))

    assert len(events) == 3
    assert events[0].source == "auth"
    assert events[1] is None
    assert events[2].source == "database"
    assert "строка 2 пропущена" in caplog.text


def test_json_array_is_invalid() -> None:
    with pytest.raises(InvalidEventError):
        parse_jsonl_line('["not", "an", "event"]')


def test_wrong_timestamp_type() -> None:
    line = ('{"timestamp": 123, "level": "INFO", ' '"source": "auth", "message": "Hello"}')

    with pytest.raises(InvalidTimestampError):
        parse_jsonl_line(line)


def test_wrong_source_type() -> None:
    line = ('{"timestamp": "2026-10-20T12:00:00", ' '"level": "INFO", "source": 123, "message": "Hello"}')

    with pytest.raises(InvalidEventError):
        parse_jsonl_line(line)


def test_wrong_message_type() -> None:
    line = ('{"timestamp": "2026-10-20T12:00:00", ' '"level": "INFO", "source": "auth", "message": 123}')

    with pytest.raises(InvalidEventError):
        parse_jsonl_line(line)


def test_invalid_csv_record_stops_reading(tmp_path) -> None:
    file_path = tmp_path / "events.csv"
    file_path.write_text("timestamp,level,source,message\n" "2026-10-20T12:00:00,UNKNOWN,auth,Hello\n", encoding="utf-8")

    with pytest.raises(InvalidEventError, match=r"events\.csv: строка 2"):
        list(parse_csv_file(file_path))


def test_skip_invalid_csv_record(tmp_path, caplog) -> None:
    file_path = tmp_path / "events.csv"
    file_path.write_text("timestamp,level,source,message\n" "2026-10-20T12:00:00,UNKNOWN,auth,Hello\n"
                         "2026-10-20T12:01:00,INFO,database,Connected\n", encoding="utf-8")

    events = list(parse_csv_file(file_path, skip_invalid=True))

    assert len(events) == 2
    assert events[0] is None
    assert events[1].source == "database"
    assert "строка 2 пропущена" in caplog.text