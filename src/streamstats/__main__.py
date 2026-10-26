import argparse
import logging
from pathlib import Path

from streamstats.analysis import Analyzer
from streamstats.errors import StreamStatsError
from streamstats.parsers import parse_csv_file, parse_jsonl_file
from streamstats.report import save_report

logger = (logging
          .getLogger(__name__))


def main() -> int:
    """Запуск потокового анализатора файлов"""

    parser = argparse.ArgumentParser(description="Потоковый анализатор файлов CSV и JSONL")
    subparsers = parser.add_subparsers(dest="command", required=True)
    analyze_parser = subparsers.add_parser("analyze", help="Анализирует входные файлы")
    analyze_parser.add_argument("inputs", nargs="+", type=Path, help="Входные файлы")
    analyze_parser.add_argument("--format", choices=("csv", "jsonl"),
                                required=True, help="Формат входных файлов")
    analyze_parser.add_argument("--output", type=Path, required=True, help="Путь к JSON-отчету")
    analyze_parser.add_argument("--skip-invalid", action="store_true", help="Пропускает некорректные данные")

    args = parser.parse_args()
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
    if args.format == "csv":
        parse_file = parse_csv_file
    else:
        parse_file = parse_jsonl_file

    try:
        analyzer = Analyzer()
        for input_path in args.inputs:
            for event in parse_file(input_path, skip_invalid=args.skip_invalid):
                if event is None:
                    analyzer.add_skipped_record()
                    continue

                analyzer.add_event(event)

        save_report(analyzer.get_report(), args.output)
        return 0
    except StreamStatsError as error:
        logger.error("%s", error)
        return 2
    except OSError as error:
        logger.error("Ошибка работы с файлом: %s", error)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())