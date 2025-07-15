#!/usr/bin/env python3
"""
Скрипт для запуска графического интерфейса распознавания речи с использованием Яндекс SpeechKit.
"""

import sys
import os
import logging

# Добавляем корневую директорию проекта в sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Импортируем глобальную конфигурацию логирования
from logging_config import configure_logging

# Импортируем функцию запуска из модуля
from voice_control.ui.speech_recognition_gui import main

if __name__ == "__main__":
    # Настройка логирования через глобальную конфигурацию
    logger = configure_logging()
    logger.info("Запуск приложения распознавания речи")
    
    # Запускаем приложение
    main()
