class ValuesMissingErr(Exception):
    """Отсутствие обязательных переменных окружения во время запуска бота."""


class IncorrectCode(Exception):
    """Wrong API answer."""


class ProgramErr(Exception):
    """Program stopped working."""
