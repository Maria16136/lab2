import json
from pathlib import Path


def save_report(report: dict, output_path: Path) -> None:
    """Сохраняет отчёт со статистикой в JSON-файл"""

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=4)