"""Графический интерфейс для распознавания речи с использованием Яндекс SpeechKit.
"""

import os
import sys
import logging
from typing import Dict, Any, List, Optional, Tuple, Union

from PySide6.QtWidgets import QApplication

# Добавляем корневую директорию проекта в sys.path, если она еще не добавлена
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Импортируем наши модули
from voice_control.ui.main_window import SpeechRecognitionWindow

# Настройка логирования
logger = logging.getLogger(__name__)


# Запуск приложения
def main():
    """Основная функция для запуска приложения."""
    # Настройка логирования через глобальную конфигурацию
    try:
        from logging_config import configure_logging
        configure_logging()
        logger.info("Использована глобальная конфигурация логирования")
    except ImportError:
        # Fallback на базовую настройку, если глобальная конфигурация недоступна
        logging.basicConfig(level=logging.INFO)
        logger.warning("Глобальная конфигурация логирования недоступна, используется базовая настройка")
    
    # Проверяем, существует ли уже экземпляр QApplication
    app = QApplication.instance()
    standalone_mode = app is None
    
    # Создаем приложение Qt, только если его еще нет
    if app is None:
        app = QApplication(sys.argv)
    
    # Устанавливаем стиль
    app.setStyle("Fusion")
    
    # Создаем и показываем окно
    window = SpeechRecognitionWindow()
    window.show()
    
    # Запускаем цикл обработки событий только если мы в standalone режиме
    if standalone_mode:
        sys.exit(app.exec())
    else:
        # Если запущены из другого приложения, просто возвращаем окно
        return window


def run_speech_recognition_app(settings_manager=None):
    """Функция для запуска приложения распознавания речи из других модулей."""
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    window = SpeechRecognitionWindow(settings_manager=settings_manager)
    window.show()
    return window


if __name__ == "__main__":
    main()