# Этот файл будет содержать основную логику управления монетизацией в приложении Screph.

import logging
# Предполагается, что api_client.py находится в ../backend_integration/
# Для корректного импорта может потребоваться настройка PYTHONPATH или использование относительных импортов, если это модуль
from monetization.in_app_monetization.backend_integration.api_client import MonetizationApiClient

logger = logging.getLogger(__name__)

# Глобальный экземпляр клиента API. Может быть инициализирован при старте приложения.
# или передаваться/создаваться по необходимости.
# Для простоты, предположим, что токен пользователя получается каким-то образом
# и передается при инициализации сервиса.

class MonetizationService:
    def __init__(self, user_token):
        """
        Инициализирует сервис монетизации.
        :param user_token: Токен аутентификации пользователя.
        """
        if not user_token:
            raise ValueError("User token must be provided to MonetizationService")
        self.api_client = MonetizationApiClient(user_token=user_token)
        self.current_balance_minutes = 0
        self.active_packages_info = [] # Для хранения информации о пакетах
        self._load_balance()

    def _load_balance(self):
        """
        Загружает (или обновляет) текущий баланс пользователя с бэкенда.
        """
        logger.info("Loading user balance...")
        balance_data = self.api_client.get_user_balance()
        if balance_data and 'error' not in balance_data:
            self.current_balance_minutes = balance_data.get('total_minutes_remaining', 0)
            self.active_packages_info = balance_data.get('active_packages', [])
            logger.info(f"Balance loaded: {self.current_balance_minutes} minutes.")
        else:
            logger.error(f"Failed to load balance: {balance_data.get('error', 'Unknown error')}")
            # В случае ошибки можно оставить старый баланс или сбросить
            self.current_balance_minutes = 0 
            self.active_packages_info = []

    def get_current_balance(self):
        """
        Возвращает текущий известный баланс минут.
        Для получения актуального баланса может потребоваться вызов refresh_balance().
        """
        return self.current_balance_minutes

    def get_active_packages_info(self):
        """
        Возвращает информацию об активных пакетах.
        """
        return self.active_packages_info

    def refresh_balance(self):
        """
        Принудительно обновляет баланс с бэкенда.
        """
        self._load_balance()

    def has_sufficient_minutes(self, minutes_required):
        """
        Проверяет, достаточно ли у пользователя минут для выполнения операции.
        :param minutes_required: Количество требуемых минут (int).
        :return: True, если минут достаточно, иначе False.
        """
        if not isinstance(minutes_required, int) or minutes_required < 0:
            logger.warning(f"Invalid minutes_required value: {minutes_required}")
            return False # или True, если 0 минут это валидный запрос без списания
        return self.current_balance_minutes >= minutes_required

    def consume_minutes(self, minutes_to_consume):
        """
        Регистрирует использование минут и обновляет локальный баланс.
        :param minutes_to_consume: Количество списываемых минут (int).
        :return: True, если списание успешно зарегистрировано на бэкенде и локальный баланс обновлен, иначе False.
        """
        if not isinstance(minutes_to_consume, int) or minutes_to_consume <= 0:
            logger.error(f"Invalid minutes_to_consume value: {minutes_to_consume}")
            return False

        if not self.has_sufficient_minutes(minutes_to_consume):
            logger.warning(f"Attempted to consume {minutes_to_consume} minutes, but only {self.current_balance_minutes} available.")
            return False

        logger.info(f"Attempting to consume {minutes_to_consume} minutes.")
        response = self.api_client.record_usage(minutes_spent=minutes_to_consume)

        if response and 'error' not in response:
            # Бэкенд подтвердил списание. Обновим локальный баланс.
            # В идеале, бэкенд должен вернуть новый баланс, чтобы избежать рассинхронизации.
            # Но если он этого не делает, мы можем обновить его принудительно или вычесть локально.
            # Для простоты, вычтем локально и затем обновим с сервера.
            logger.info(f"Successfully recorded usage of {minutes_to_consume} minutes. Response: {response}")
            # self.current_balance_minutes -= minutes_to_consume # Оптимистичное обновление
            self.refresh_balance() # Запросить актуальный баланс с сервера
            return True
        else:
            logger.error(f"Failed to record usage of {minutes_to_consume} minutes. Error: {response.get('error', 'Unknown error')}")
            # Можно попробовать обновить баланс, чтобы синхронизироваться, если причина была во временной ошибке
            self.refresh_balance()
            return False

# Пример использования (потребует интеграции в основное приложение Screph):
if __name__ == '__main__':
    # Это демонстрационный код. В реальном приложении токен будет получен иначе.
    test_user_token = "your_actual_user_token_here" # ЗАМЕНИТЬ!

    if test_user_token == "your_actual_user_token_here":
        print("Please replace 'your_actual_user_token_here' with a real token for testing MonetizationService.")
    else:
        try:
            monetization_service = MonetizationService(user_token=test_user_token)
            print(f"Initial balance: {monetization_service.get_current_balance()} minutes.")
            print(f"Active packages: {monetization_service.get_active_packages_info()}")

            minutes_for_feature = 5
            if monetization_service.has_sufficient_minutes(minutes_for_feature):
                print(f"User has enough minutes for a feature requiring {minutes_for_feature} minutes.")
                if monetization_service.consume_minutes(minutes_for_feature):
                    print(f"Successfully consumed {minutes_for_feature} minutes.")
                    print(f"New balance: {monetization_service.get_current_balance()} minutes.")
                else:
                    print(f"Failed to consume {minutes_for_feature} minutes.")
            else:
                print(f"User does not have enough minutes for a feature requiring {minutes_for_feature} minutes.")
            
            # Обновление баланса
            print("Refreshing balance...")
            monetization_service.refresh_balance()
            print(f"Balance after refresh: {monetization_service.get_current_balance()} minutes.")

        except ValueError as e:
            print(f"Error initializing MonetizationService: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")