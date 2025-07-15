"""
Упрощенная конфигурация логирования для проекта BotEye.
Настраивает базовое логирование для всех модулей проекта.
"""

import logging
import sys

def configure_logging():
    """
    Простая настройка логирования для всего приложения.
    Устанавливает уровень DEBUG для всех модулей и настраивает вывод в консоль.
    
    Returns:
        logging.Logger: Корневой логгер
    """
    # Сброс всех предыдущих настроек логирования
    logging.root.handlers = []
    
    # Настраиваем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Настраиваем кодировку консоли для Windows
    if sys.platform == 'win32':
        import codecs
        try:
            if sys.stdout:
                sys.stdout.reconfigure(encoding='utf-8')
            if sys.stderr:
                sys.stderr.reconfigure(encoding='utf-8')
        except (AttributeError, TypeError):
            if sys.stdout:
                sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
            if sys.stderr:
                sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

    # Создаем обработчик для вывода в консоль, если она доступна
    if sys.stdout:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # Отключаем логи от внешних библиотек
    for lib in ['PIL', 'matplotlib', 'PySide6']:
        logging.getLogger(lib).setLevel(logging.WARNING)
    
    # Особый акцент на модули селектора элементов
    modules_to_monitor = [
        # Основной модуль управления элементами
        'screen_selector.simplified_selector.core.selection_manager',
        # Оригинальные модули селектора
        'screen_selector.selector_modules.selection.selection_manager',
        'screen_selector.selector_modules.selection.selection_state',
        'screen_selector.selector_modules.selection.hierarchy_integration',
    ]
    
    for module in modules_to_monitor:
        module_logger = logging.getLogger(module)
        module_logger.setLevel(logging.DEBUG)
        # Гарантируем, что сообщения от этих модулей будут отображаться
        module_logger.propagate = True
    
    return root_logger

if __name__ == "__main__":
    logger = configure_logging()
    logger.info("Логирование настроено")
    logger.debug("Уровень отладки активирован")
