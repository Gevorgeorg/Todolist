import requests
from django.conf import settings
from .dc import GetUpdatesResponse, SendMessageResponse


class TgClient:
    def __init__(self):
        self.base_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/"

    def _get(self, method: str, params: dict = None) -> dict[str]:
        req = requests.get(self.base_url + method, params=params, timeout=60)
        req.raise_for_status()
        return req.json()

    def _post(self, method: str, json: dict = None) -> dict[str]:
        req = requests.post(self.base_url + method, json=json, timeout=60)
        req.raise_for_status()
        return req.json()

    def get_updates(self, offset: int = 0, timeout: int = 60) -> GetUpdatesResponse:
        """Чтение сообщений ботом"""

        return GetUpdatesResponse.from_dict(
            self._get('getUpdates', {'offset': offset, 'timeout': timeout}))

    def send_message(self, chat_id: int, text: str) -> SendMessageResponse:
        """Отправка сообщений ботом - пользователю"""

        payload: dict = {'chat_id': chat_id, 'text': text}
        return SendMessageResponse.from_dict(self._post('sendMessage', payload))

    def get_me(self) -> dict[str]:
        """Получить информацию о боте"""

        return self._get('getMe')
