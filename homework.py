import os

from dotenv import load_dotenv

import logging
import requests
import sys
import telegram
import time

from http import HTTPStatus

from exceptions import (ValuesMissingErr, IncorrectCode, WrongResponse)

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


def check_tokens():
    """Проверяем, что все токены на месте."""
    logging.info('Проверка всех токенов')
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def send_message(bot, message):
    """Отправление сообщения."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.info('Сообщение отправлено')
        logging.debug('Успешно')
    except Exception as error:
        logging.error(f'Сообщение не было отправлено {error}')


def get_api_answer(timestamp):
    """Запрос к API домашки."""
    timestamp = int(time.time())
    params_request = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': {'from_date': timestamp},
    }
    message = ('Инициация запроса API').format(**params_request)
    logging.info(message)
    try:
        response = requests.get(**params_request)
        if response.status_code != HTTPStatus.OK:
            raise IncorrectCode
        return response.json()
    except Exception as error:
        message = ('Status not 200').format(**params_request)
        raise IncorrectCode(message, error)


def check_response(response):
    """Проверка респонса апишки."""
    logging.info('API correct check')
    if not isinstance(response, dict):
        raise TypeError('APIs not dict')
    if 'homeworks' not in response or 'current_date' not in response:
        raise WrongResponse('No homeworks key')
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise TypeError('homework is not a list')
    return homeworks


def parse_status(homework):
    """Получаем статус домашки."""
    logging.info('just checking')
    if 'homework_name' not in homework:
        raise KeyError('No homework_name key found')
    homework_name = homework.get('homework_name')
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
    prevoius_message = ''
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
            if message != prevoius_message:
                send_message(bot, message)
                prevoius_message = message
            else:
                logging.info(message)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message, exc_info=True)
            if message != prevoius_message:
                send_message(bot, message)
                prevoius_message = message
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.ERROR,
        format='%(asctime)s, %(levelname)s, %(message)s, %(name)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    main()
