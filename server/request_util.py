import backoff
import requests
from loguru import logger


def on_backoff(details):
    exc_type = (
        type(details["exception"])
        if "exception" in details
        else "Неизвестное исключение"
    )  # Получаем тип исключения
    logger.warning(
        f"Ошибка: {exc_type}. Повторный запрос через {details['wait']:0.1f} секунд после {details['tries']} попыток вызова функции {details['target']}"
    )


def on_giveup(details):
    logger.error("Превышено количество попыток. Отказ от выполнения.")


@backoff.on_exception(
    backoff.expo,
    exception=requests.exceptions.RequestException,
    max_tries=3,
    on_backoff=on_backoff,
    on_giveup=on_giveup,
)
def send_request(method, url, timeout=10, **kwargs):
    response = requests.request(method, url, timeout=timeout, **kwargs)
    response.raise_for_status()
    return response
