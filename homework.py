import os
import logging
import requests
import sys
import time

from dotenv import load_dotenv
import telegram
from http import HTTPStatus

from exceptions import ValuesMissingErr, IncorrectCode

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens() -> bool:
    """Проверяем, что все токены на месте."""
    return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))


def send_message(bot, message) -> None:
    """Отправление сообщения."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.info('Сообщение отправлено')
        logging.debug('Успешно')
    except Exception:
        logging.error('Сообщение не было отправлено')


def get_api_answer(timestamp) -> dict:
    """Запрос к API домашки."""
    timestamp = int(time.time())
    params_request = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': {'from_date': timestamp},
    }
    try:
        response = requests.get(**params_request)
        if response.status_code != HTTPStatus.OK:
            raise IncorrectCode('Wrong API answer')
        return response.json()
    except Exception:
        raise IncorrectCode('Wrong status code')


def check_response(response: dict) -> list:
    """Проверка респонса апишки."""
    try:
        homework = response['homeworks']
    except KeyError:
        logging.error('No homeworks key found')
    if not isinstance(homework, list):
        logging.error('Homeworks is not a list')
        raise TypeError('Homeworks is not a list')
    return homework


def parse_status(homework) -> str:
    """Получаем статус домашки."""
    try:
        homework_name = homework['homework_name']
    except KeyError:
        logging.error('Wrong server response')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_VERDICTS:
        raise ValuesMissingErr(f'Неизвестный статус - {homework_status}')
    return ('Изменился статус проверки работы "{homework_name}". {verdict}'
            ).format(homework_name=homework_name,
                     verdict=HOMEWORK_VERDICTS[homework_status]
                     )


def main():
    """Основная логика бота."""
    if not check_tokens():
        message = 'Токен отсутствует'
        logging.critical(message)
        sys.exit(message)
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    start_message = 'Бот активирован'
    send_message(bot, start_message)
    logging.info(start_message)
    previous_message = ''
    while True:
        try:
            response = get_api_answer(timestamp)
            timestamp = response.get(
                'current_date', int(time.time())
            )
            homeworks = check_response(response)
            if homeworks:
                message = parse_status(homeworks[0])
            else:
                message = 'Обновлений нет'
            if message != previous_message:
                send_message(bot, message)
                previous_message = message
            else:
                logging.info(message)
        except Exception:
            message = 'Сбой в работе программы'
            send_message(bot, message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.ERROR,
        format='%(asctime)s, %(levelname)s, %(message)s, %(name)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    main()
