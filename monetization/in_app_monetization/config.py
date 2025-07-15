# Файл конфигурации для модуля монетизации в приложении Screph.

import os

# URL API бэкенда монетизации
# Рекомендуется использовать переменные окружения для таких настроек.
# Пример: os.environ.get('Screph_MONETIZATION_BACKEND_URL', 'http://localhost:8000/api/v1/')
# Для простоты здесь будет значение по умолчанию, но его следует переопределять в реальном окружении.
MONETIZATION_BACKEND_API_URL = "http://localhost:8000/api/v1/"

# Порог для предупреждения о низком балансе (в минутах)
LOW_BALANCE_WARNING_THRESHOLD_MINUTES = 15

# Настройки логирования (могут быть переопределены глобальной конфигурацией логирования Screph)
LOG_LEVEL = "INFO" # Например, DEBUG, INFO, WARNING, ERROR
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Настройки для UI (если применимо)
# Например, ссылки на страницы покупки, помощи и т.д.
PURCHASE_MINUTES_URL = "https://Screph.example.com/purchase" # Заменить на реальный URL
FAQ_MONETIZATION_URL = "https://Screph.example.com/faq#monetization"

# Другие специфичные для монетизации настройки
# Например, частота проверки баланса, если она автоматическая
AUTOMATIC_BALANCE_CHECK_INTERVAL_SECONDS = 300 # 5 минут

# Ключи API или другие чувствительные данные НИКОГДА не должны храниться здесь в открытом виде.
# Используйте переменные окружения или защищенные хранилища.

# Функция для получения конфигурационного значения с возможностью переопределения через переменные окружения
def get_config_value(key, default_value=None):
    """
    Получает значение конфигурации. Сначала ищет в переменных окружения,
    затем использует значение из этого файла.
    Переменные окружения должны иметь префикс 'Screph_MONETIZATION_'.
    Например, для MONETIZATION_BACKEND_API_URL переменная будет Screph_MONETIZATION_MONETIZATION_BACKEND_API_URL.
    """
    env_var_name = f"Screph_MONETIZATION_{key.upper()}"
    value = os.environ.get(env_var_name)
    if value is not None:
        return value
    
    # Если не найдено в env, ищем в globals() этого модуля
    if key in globals():
        return globals()[key]
    
    return default_value

# Пример того, как можно использовать get_config_value для получения настроек:
# CURRENT_BACKEND_URL = get_config_value('MONETIZATION_BACKEND_API_URL', 'http://fallback-url.com/api')
# LOW_BALANCE_THRESHOLD = int(get_config_value('LOW_BALANCE_WARNING_THRESHOLD_MINUTES', 10))

if __name__ == '__main__':
    print("Monetization Configuration:")
    print(f"Backend API URL: {get_config_value('MONETIZATION_BACKEND_API_URL')}")
    print(f"Low Balance Warning Threshold: {get_config_value('LOW_BALANCE_WARNING_THRESHOLD_MINUTES')} minutes")
    print(f"Log Level: {get_config_value('LOG_LEVEL')}")
    # Установка переменной окружения для теста
    # os.environ['Screph_MONETIZATION_TEST_SETTING'] = 'test_value_from_env'
    # print(f"Test Setting (from env if set): {get_config_value('TEST_SETTING', 'default_test_value')}")