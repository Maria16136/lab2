from streamstats.analysis import Analyzer
from streamstats.models import Event


def test_count_total_events() -> None:
    analyzer = Analyzer()

    analyzer.add_event(Event("2026-10-20T12:00:00", "INFO", "auth", "Login"))
    analyzer.add_event(Event("2026-10-20T12:01:00", "ERROR", "database", "Failed"))

    assert analyzer.total_events == 2


def test_count_events_by_level() -> None:
    analyzer = Analyzer()

    analyzer.add_event(Event("2026-10-20T12:00:00", "INFO", "auth", "Login"))
    analyzer.add_event(Event("2026-10-20T12:01:00", "ERROR", "database", "Failed"))
    analyzer.add_event(Event("2026-10-20T12:02:00", "INFO", "auth", "Logout"))

    assert analyzer.level_counts == {"INFO": 2, "ERROR": 1}


def test_count_events_by_source() -> None:
    analyzer = Analyzer()

    analyzer.add_event(Event("2026-10-20T12:00:00", "INFO", "auth", "Login"))
    analyzer.add_event(Event("2026-10-20T12:01:00", "ERROR", "database", "Failed"))
    analyzer.add_event(Event("2026-10-20T12:02:00", "INFO", "auth", "Logout"))

    assert analyzer.source_counts == {"auth": 2, "database": 1}


def test_count_only_error_and_critical_sources() -> None:
    analyzer = Analyzer()

    analyzer.add_event(Event("2026-10-20T12:00:00", "INFO", "auth", "Login"))
    analyzer.add_event(Event("2026-10-20T12:01:00", "ERROR", "database", "Failed"))
    analyzer.add_event(Event("2026-10-20T12:02:00", "CRITICAL", "database", "Crash"))

    assert analyzer.error_source_counts == {"database": 2}


def test_find_first_and_last_timestamps() -> None:
    analyzer = Analyzer()

    analyzer.add_event(Event("2026-10-20T12:05:00", "INFO", "auth", "Third"))
    analyzer.add_event(Event("2026-10-20T12:00:00", "INFO", "auth", "First"))
    analyzer.add_event(Event("2026-10-20T12:10:00", "INFO", "auth", "Last"))

    report = analyzer.get_report()

    assert report["first_timestamp"] == "2026-10-20T12:00:00"
    assert report["last_timestamp"] == "2026-10-20T12:10:00"


def test_top_error_sources_limited_to_five() -> None:
    analyzer = Analyzer()

    for number in range(6):
        analyzer.add_event(Event(f"2026-10-20T12:{number:02}:00", "ERROR", f"source{number}", "Failed"))

    assert len(analyzer.get_top_error_sources()) == 5


def test_top_error_sources_sorted_by_count_and_name() -> None:
    analyzer = Analyzer()

    analyzer.add_event(Event("2026-10-20T12:00:00", "ERROR", "b", "Failed"))
    analyzer.add_event(Event("2026-10-20T12:01:00", "ERROR", "a", "Failed"))

    assert analyzer.get_top_error_sources() == [("a", 1), ("b", 1)]


def test_count_skipped_records() -> None:
    analyzer = Analyzer()

    analyzer.add_skipped_record()
    analyzer.add_skipped_record()

    assert analyzer.skipped_records == 2


def test_empty_analyzer_report() -> None:
    analyzer = Analyzer()

    report = analyzer.get_report()

    assert report["total_events"] == 0
    assert report["level_counts"] == {}
    assert report["source_counts"] == {}
    assert report["top_error_sources"] == []
    assert report["first_timestamp"] is None
    assert report["last_timestamp"] is None
    assert report["skipped_records"] == 0