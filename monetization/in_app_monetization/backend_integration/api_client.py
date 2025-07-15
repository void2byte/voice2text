# Этот файл будет содержать класс или функции для взаимодействия с API бэкенда монетизации.

import requests
import logging

# Предполагаемый URL бэкенда (должен быть в конфигурации)
BACKEND_API_URL = "http://localhost:8000/api/v1/" # Пример, заменить на реальный URL из настроек

logger = logging.getLogger(__name__)

class MonetizationApiClient:
    def __init__(self, user_token=None):
        """
        Инициализирует клиент API.
        :param user_token: Токен аутентификации пользователя (если требуется).
        """
        self.user_token = user_token
        self.headers = {}
        if self.user_token:
            self.headers['Authorization'] = f'Token {self.user_token}' # Или Bearer, в зависимости от бэкенда

    def _make_request(self, method, endpoint, params=None, data=None, json_data=None):
        """
        Внутренний метод для выполнения HTTP-запросов.
        """
        url = f"{BACKEND_API_URL.rstrip('/')}/{endpoint.lstrip('/')}"
        try:
            response = requests.request(method, url, headers=self.headers, params=params, data=data, json=json_data, timeout=10)
            response.raise_for_status() # Вызовет исключение для HTTP-ошибок 4xx/5xx
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error occurred: {e} - {e.response.text}")
            # Можно вернуть специфичную структуру ошибки или None
            return {'error': str(e), 'status_code': e.response.status_code, 'details': e.response.text if e.response else None}
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception occurred: {e}")
            return {'error': str(e), 'status_code': None, 'details': None}
        except ValueError: # Если ответ не JSON
            logger.error(f"Failed to decode JSON from response: {response.text}")
            return {'error': 'Invalid JSON response', 'status_code': response.status_code, 'details': response.text}

    def get_user_balance(self):
        """
        Получает текущий баланс минут пользователя и срок их действия.
        Предполагаемый эндпоинт: /api/v1/profile/ (согласно ранее созданной структуре бэкенда)
        """
        # Эндпоинт /api/v1/profile/ уже существует и возвращает 'total_minutes_remaining'
        # и 'active_packages' с информацией о датах.
        # Для простоты, будем считать, что этот эндпоинт подходит.
        # Если бэкенд требует аутентификации, self.user_token должен быть установлен.
        if not self.user_token:
            logger.warning("User token is not set. Cannot fetch user balance.")
            return {'error': 'User token not set', 'total_minutes_remaining': 0, 'active_packages': []}
        
        response_data = self._make_request('GET', 'profile/')
        if response_data and 'error' not in response_data:
            # Предполагаем, что 'total_minutes_remaining' есть в ответе
            # и 'active_packages' содержит список пакетов с 'expiry_date' или 'purchase_date' и 'package.duration_days'
            return {
                'total_minutes_remaining': response_data.get('total_minutes_remaining', 0),
                'active_packages': response_data.get('active_packages', [])
            }
        return {'error': response_data.get('error', 'Failed to fetch balance'), 'total_minutes_remaining': 0, 'active_packages': []}

    def record_usage(self, minutes_spent):
        """
        Отправляет информацию об использованных ресурсах (минутах).
        Предполагаемый эндпоинт: /api/v1/spend_minutes/
        :param minutes_spent: Количество потраченных минут (int).
        """
        if not self.user_token:
            logger.warning("User token is not set. Cannot record usage.")
            return {'error': 'User token not set'}
        if not isinstance(minutes_spent, int) or minutes_spent <= 0:
            logger.error("Invalid minutes_spent value.")
            return {'error': 'Invalid minutes_spent value'}

        payload = {'minutes_to_spend': minutes_spent}
        return self._make_request('POST', 'spend_minutes/', json_data=payload)

# Пример использования (для тестирования):
if __name__ == '__main__':
    # Нужен запущенный бэкенд и валидный токен пользователя
    # Для теста можно создать пользователя и токен через Django shell или админку
    # Например, если пользователь создан и есть токен:
    # from rest_framework.authtoken.models import Token
    # user = User.objects.get(username='testuser')
    # token = Token.objects.create(user=user)
    # print(token.key)
    
    # ЗАМЕНИТЬ НА РЕАЛЬНЫЙ ТОКЕН ПОЛЬЗОВАТЕЛЯ ДЛЯ ТЕСТА
    test_user_token = "your_actual_user_token_here" 
    
    if test_user_token == "your_actual_user_token_here":
        print("Please replace 'your_actual_user_token_here' with a real token for testing.")
    else:
        client = MonetizationApiClient(user_token=test_user_token)

        print("Fetching user balance...")
        balance_info = client.get_user_balance()
        print(f"Balance info: {balance_info}")

        if balance_info and balance_info.get('total_minutes_remaining', 0) > 0:
            minutes_to_log = 1
            if balance_info['total_minutes_remaining'] >= minutes_to_log:
                print(f"\nRecording usage of {minutes_to_log} minute(s)...")
                usage_response = client.record_usage(minutes_spent=minutes_to_log)
                print(f"Usage response: {usage_response}")

                print("\nFetching updated user balance...")
                updated_balance_info = client.get_user_balance()
                print(f"Updated balance info: {updated_balance_info}")
            else:
                print(f"Not enough minutes to log {minutes_to_log} minute(s).")
        else:
            print("\nNo minutes available to test usage recording or error fetching balance.")