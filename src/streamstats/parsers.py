import csv
import json
import logging
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

from streamstats.errors import InvalidEventError, InvalidTimestampError
from streamstats.models import Event

logger = logging.getLogger(__name__)


def validate_event(data: dict[str, str]) -> None:
    """Проверяет, является ли сообщение корректным событием"""

    if not isinstance(data, dict):
        raise InvalidEventError("Событие должно быть JSON-объектом")

    required_fields = {"timestamp", "level", "source", "message"}
    missing_fields = required_fields - data.keys()
    if missing_fields:
        fields = ", ".join(sorted(missing_fields))
        raise InvalidEventError(f"Отсутствуют обязательные поля: {fields}")

    if not isinstance(data["timestamp"], str):
        raise InvalidTimestampError("Поле timestamp должно быть строкой")
    try:
        datetime.fromisoformat(data["timestamp"])
    except ValueError as error:
        raise InvalidTimestampError("Поле timestamp содержит некорректную дату и время") from error

    if not isinstance(data["level"], str):
        raise InvalidEventError("Поле level должно быть строкой")
    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    if data['level'] not in valid_levels:
        raise InvalidEventError("Недопустимый уровень события")

    if not isinstance(data["source"], str) or not data["source"].strip():
        raise InvalidEventError("Поле source должно быть непустой строкой")

    if not isinstance(data["message"], str):
        raise InvalidEventError("Поле message должно быть строкой")


def parse_jsonl_line(line: str) -> Event:
    """Преобразует одну строку JSONL в объект Event"""

    try:
        data = json.loads(line)
    except json.JSONDecodeError as error:
        raise InvalidEventError("Некорректный JSON") from error

    validate_event(data)

    return Event(timestamp=data["timestamp"], level=data["level"], source=data["source"], message=data["message"])


def parse_csv_row(data: dict[str, str]) -> Event:
    """Преобразует одну строку CSV в объект Event"""

    validate_event(data)

    return Event(timestamp=data["timestamp"], level=data["level"], source=data["source"], message=data["message"])


def parse_csv_file(file_path: Path, skip_invalid: bool = False) -> Iterator[Event | None]:
    """Читает CSV-файл и обрабатывает его записи"""

    with file_path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)

        for line_number, row in enumerate(reader, start=2):
            try:
                yield parse_csv_row(row)
            except InvalidEventError as error:
                if not skip_invalid:
                    raise InvalidEventError(f"{file_path}: строка {line_number}: {error}") from error

                logger.warning("%s: строка %d пропущена: %s", file_path, line_number, error)
                yield None


def parse_jsonl_file(file_path: Path, skip_invalid: bool = False) -> Iterator[Event | None]:
    """Читает JSONL-файл и обрабатывает его записи"""

    with file_path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            try:
                yield parse_jsonl_line(line)
            except InvalidEventError as error:
                if not skip_invalid:
                    raise InvalidEventError(f"{file_path}: строка {line_number}: {error}") from error

                logger.warning("%s: строка %d пропущена: %s", file_path, line_number, error)
                yield None