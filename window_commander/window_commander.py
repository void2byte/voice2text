#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
WindowCommander - приложение для взаимодействия с окнами Windows.
Позволяет выбирать окна и отправлять им команды и текст без активации.

Автор: Cascade AI
Дата: 2025-04-09
"""

import os
import sys
import logging
import datetime
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTranslator, QLocale

# Настройка путей для импорта
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Импорт наших модулей
from ui.main_window import MainWindow
from ui.settings_tab import SettingsTab
from core.window_manager import WindowManager
from core.window_selector import WindowSelector

# Настройка логирования
def setup_logging():
    # Создаем папку для логов, если её нет
    logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(logs_dir, exist_ok=True)

    # Формируем имя лог-файла с текущей датой
    log_filename = os.path.join(logs_dir, f"window_commander_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

    # Настраиваем логгер
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    # Создаем логгер для модуля
    logger = logging.getLogger('window_commander')
    logger.info(f"Запуск приложения WindowCommander. Лог будет сохранен в {log_filename}")
    return logger

def check_dependencies():
    """
    Проверка наличия зависимостей.
    
    Returns:
        tuple: (bool, str) - Результат проверки и сообщение
    """
    missing_deps = []
    
    try:
        import PySide6
    except ImportError:
        missing_deps.append("PySide6")
    
    try:
        import pyperclip
    except ImportError:
        missing_deps.append("pyperclip")
    
    try:
        import win32gui
    except ImportError:
        # win32gui не обязателен, но предпочтителен
        pass
    
    if missing_deps:
        return False, f"Отсутствуют необходимые библиотеки: {', '.join(missing_deps)}"
    
    return True, "Все зависимости установлены"

def main():
    """Главная функция запуска приложения"""
    # Настраиваем логирование
    logger = setup_logging()
    
    # Проверяем зависимости
    deps_ok, deps_message = check_dependencies()
    if not deps_ok:
        logger.error(f"Ошибка при проверке зависимостей: {deps_message}")
        print(f"Ошибка: {deps_message}")
        print("Установите недостающие библиотеки с помощью pip:")
        print("pip install PySide6 pyperclip pywin32")
        return
    
    logger.info(deps_message)
    
    try:
        # Запускаем Qt приложение
        app = QApplication(sys.argv)
        app.setApplicationName("Window Commander")
        
        # Настройка переводов (для будущего использования)
        translator = QTranslator()
        app.installTranslator(translator)
        
        # Инициализируем менеджер окон
        window_manager = WindowManager(logger)
        
        # Создаем главное окно
        window = MainWindow(logger)
        
        # Передаем ссылку на менеджер окон в главное окно
        # window.set_window_manager(window_manager)
        
        # Показываем главное окно
        window.show()
        
        # Выводим информацию о запуске
        logger.info("Приложение Window Commander успешно запущено")
        
        # Запускаем главный цикл приложения
        sys.exit(app.exec())
    except Exception as e:
        logger.error(f"Ошибка при запуске приложения: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()
