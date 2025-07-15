"""
Информационная вкладка для графического интерфейса распознавания речи.
"""

import os
import sys
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QTextEdit, QGroupBox)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QFont, QDesktopServices



# Настраиваем логирование
# Настраиваем логирование через глобальную конфигурацию
try:
    from logging_config import configure_logging
    configure_logging()
except ImportError:
    # Fallback на базовую настройку, если глобальная конфигурация недоступна
    logging.basicConfig(level=logging.INFO, 
                      format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)


class InfoTab(QWidget):
    """Информационная вкладка для распознавания речи."""
    
    def __init__(self, parent=None):
        """
        Инициализация информационной вкладки.
        
        Args:
            parent: Родительский виджет
        """
        super().__init__(parent)
        
        self.recognizer = None
        # Инициализация компонентов
        self.init_ui()

    def retranslate_ui(self):
        self.info_group.setTitle(self.tr("О технологиях распознавания"))
        self.info_text.setHtml(self.tr("""
        <h2>Технологии распознавания речи</h2>
        <p>Это приложение поддерживает несколько движков распознавания речи, включая Yandex SpeechKit, Google Cloud Speech-to-Text и офлайн-распознавание с помощью Vosk.</p>

        <h3>Yandex SpeechKit</h3>
        <ul>
            <li><b>Описание:</b> Облачный сервис от Яндекса для распознавания и синтеза речи.</li>
            <li><b>Требования:</b> API-ключ от Яндекс.Облака.</li>
            <li><b>Особенности:</b> Поддержка нескольких языков, специализированные модели.</li>
        </ul>

        <h3>Google Cloud Speech-to-Text</h3>
        <ul>
            <li><b>Описание:</b> Сервис от Google для преобразования речи в текст.</li>
            <li><b>Требования:</b> JSON-ключ сервисного аккаунта Google Cloud.</li>
            <li><b>Особенности:</b> Высокая точность, поддержка множества языков и диалектов.</li>
        </ul>

        <h3>Vosk</h3>
        <ul>
            <li><b>Описание:</b> Офлайн-библиотека для распознавания речи.</li>
            <li><b>Требования:</b> Предварительно загруженная модель для нужного языка.</li>
            <li><b>Особенности:</b> Работает без подключения к интернету, что обеспечивает приватность данных.</li>
        </ul>

        <h3>Рекомендации по качеству аудио</h3>
        <ul>
            <li>Используйте качественный микрофон.</li>
            <li>Минимизируйте фоновый шум.</li>
            <li>Говорите четко и не слишком быстро.</li>
            <li>Для лучшего результата используйте частоту дискретизации 16000 Гц.</li>
        </ul>
        """))
        self.docs_button.setText(self.tr("Открыть документацию"))
        self.recognizer_info_group.setTitle(self.tr("Текущий распознаватель"))
        self.update_recognizer_info(self.recognizer) # Обновляем информацию с новым переводом

    def init_ui(self):
        """Инициализация пользовательского интерфейса."""
        # Макет вкладки
        layout = QVBoxLayout(self)
        
        # Группа информации о технологиях
        self.info_group = QGroupBox()
        info_layout = QVBoxLayout(self.info_group)
        
        # Текст информации
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        
        info_layout.addWidget(self.info_text)
        
        # Кнопка для открытия документации
        self.docs_button = QPushButton()
        self.docs_button.clicked.connect(lambda: QDesktopServices.openUrl(
            QUrl("https://cloud.yandex.ru/docs/speechkit/") # Можно сделать динамической
        ))
        
        info_layout.addWidget(self.docs_button)
        
        layout.addWidget(self.info_group)

        # Группа информации о текущем распознаватеle
        self.recognizer_info_group = QGroupBox()
        recognizer_info_layout = QVBoxLayout(self.recognizer_info_group)
        self.recognizer_info_text = QTextEdit()
        self.recognizer_info_text.setReadOnly(True)
        recognizer_info_layout.addWidget(self.recognizer_info_text)
        layout.addWidget(self.recognizer_info_group)

        self.retranslate_ui()
        # Инициализируем текст пустым значением при создании вкладки
        self.update_recognizer_info(None)

    def update_recognizer_info(self, recognizer: Optional[Any]):
        """
        Обновляет информацию о текущем распознавателе.

        Args:
            recognizer: Объект текущего распознавателя или None.
        """
        self.recognizer = recognizer # Сохраняем распознаватель
        if not hasattr(self, 'recognizer_info_text'): # Проверка, что UI инициализирован
            logger.warning("InfoTab: Попытка обновить информацию о распознавателе до инициализации UI.")
            return

        if recognizer:
            recognizer_name = recognizer.__class__.__name__
            config = getattr(recognizer, 'config', {})
            if not isinstance(config, dict):
                config = {}

            config_details = "<br>".join([f"&nbsp;&nbsp;{k}: {v}" for k, v in config.items()])
            info_str = f"<b>{self.tr('Тип')}:</b> {recognizer_name}<br>"
            info_str += f"<b>{self.tr('Конфигурация')}:</b><br>{config_details}"

            if hasattr(recognizer, 'model_path') and getattr(recognizer, 'model_path', None):
                info_str += f"<br><b>{self.tr('Путь к модели (Vosk)')}:</b> {recognizer.model_path}"

            api_key = getattr(recognizer, 'api_key', None)
            if api_key:
                info_str += f"<br><b>{self.tr('API ключ (Yandex/Google)')}:</b> {'*' * (len(api_key) - 4) + api_key[-4:]}"
            elif hasattr(recognizer, 'service_account_json') and getattr(recognizer, 'service_account_json', None):
                info_str += f"<br><b>{self.tr('JSON ключ (Google)')}:</b> {self.tr('Указан')}"

            self.recognizer_info_text.setHtml(info_str.replace('\n', '<br>'))
            logger.info(f"InfoTab: Информация о распознавателе обновлена: {recognizer_name}")
        else:
            self.recognizer_info_text.setHtml(self.tr("Распознаватель не выбран или не инициализирован."))
            logger.info("InfoTab: Распознаватель не определен.")