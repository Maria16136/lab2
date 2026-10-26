class StreamStatsError(Exception):
    """Базовая ошибка приложения"""


class InvalidEventError(StreamStatsError):
    """Ошибка структуры или содержимого события"""


class InvalidTimestampError(InvalidEventError):
    """Ошибка записи времени"""


class UnsupportedFormatError(StreamStatsError):
    """Неподдерживаемый формат входного файла"""


class CLIConfigurationError(StreamStatsError):
    """Ошибка параметров командной строки"""