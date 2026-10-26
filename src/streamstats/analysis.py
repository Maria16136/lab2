from collections import Counter
from datetime import datetime

from streamstats.models import Event


class Analyzer:
    """Собирает статистику по потоку событий"""

    def __init__(self) -> None:
        self.total_events = 0
        self.level_counts = Counter()
        self.source_counts = Counter()
        self.error_source_counts = Counter()
        self.first_timestamp = None
        self.last_timestamp = None
        self.skipped_records = 0


    def add_event(self, event: Event) -> None:
        """Добавляет событие в статистику"""

        self.total_events += 1
        self.level_counts[event.level] += 1
        self.source_counts[event.source] += 1
        if event.level in {"ERROR", "CRITICAL"}:
            self.error_source_counts[event.source] += 1

        current_timestamp = datetime.fromisoformat(event.timestamp)

        if self.first_timestamp is None or current_timestamp < self.first_timestamp:
            self.first_timestamp = current_timestamp

        if self.last_timestamp is None or current_timestamp > self.last_timestamp:
            self.last_timestamp = current_timestamp


    def add_skipped_record(self) -> None:
        """Учитывает пропущенную некорректную запись"""

        self.skipped_records += 1


    def get_top_error_sources(self) -> list[tuple[str, int]]:
        """Возвращает 5 источников с наибольшим числом ошибок"""

        return sorted(self.error_source_counts.items(), key=lambda item: (-item[1], item[0]))[:5]


    def get_report(self) -> dict:
        """Возвращает статистику в виде словаря"""

        return {
            "total_events": self.total_events,
            "level_counts": dict(self.level_counts),
            "source_counts": dict(self.source_counts),
            "top_error_sources": self.get_top_error_sources(),
            "first_timestamp": (self.first_timestamp.isoformat() if self.first_timestamp is not None else None),
            "last_timestamp": (self.last_timestamp.isoformat() if self.last_timestamp is not None else None),
            "skipped_records": self.skipped_records,
        }