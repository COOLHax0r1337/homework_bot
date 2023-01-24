class ValuesMissingErr(Exception):
    """Отсутствие обязательных переменных окружения во время запуска бота."""

    pass


class IncorrectCode(Exception):
    """Wrong API answer."""

    pass


class WrongResponse(Exception):
    """Wrong response API homework."""
