"""
Главное окно для графического интерфейса распознавания речи.
"""

import os
import sys
import logging
from typing import Dict, Any, List, Optional, Tuple, Union

from PySide6.QtWidgets import (QDialog, QWidget, QVBoxLayout, QHBoxLayout, 
                            QTabWidget, QStatusBar, QPushButton)
from PySide6.QtCore import Qt, Slot



# Импортируем наши модули
from settings_modules.tabs.main_settings_tab import MainSettingsTab
from voice_control.ui.settings_tab import SettingsTabRecognizer
from voice_control.ui.recognition_tab import RecognitionTab
from voice_control.ui.info_tab import InfoTab
from voice_control.recognizers.yandex_recognizer import YandexSpeechRecognizer
from translation_manager import get_translation_manager
from settings_modules.settings_manager import SettingsManager

# Настройка логирования
logger = logging.getLogger(__name__)


class SpeechRecognitionWidget(QWidget):
    """
    Виджет для распознавания речи с использованием Яндекс SpeechKit.
    """
    
    def __init__(self, settings_manager, parent=None):
        """
        Инициализация виджета распознавания речи.
        
        Args:
            settings_manager: Менеджер настроек
            parent: Родительский виджет (по умолчанию None)
        """
        super().__init__(parent)
        self.settings_manager = settings_manager
        
        # Инициализация компонентов
        self.init_ui()
    
    def init_ui(self):
        """Инициализация пользовательского интерфейса."""
        # Главный макет
        main_layout = QVBoxLayout(self)
        
        # Создаем вкладки
        self.tab_widget = QTabWidget()
        
        # Вкладка основных настроек
        self.main_settings_tab = MainSettingsTab(self.settings_manager)
        self.main_settings_tab.settings_changed.connect(self.on_main_settings_changed)

        # Вкладка настроек
        self.settings_tab = SettingsTabRecognizer()
        self.settings_tab.settings_applied.connect(self.on_settings_applied)
        
        # Вкладка распознавания
        self.recognition_tab = RecognitionTab(self.settings_manager)
        
        # Вкладка информации
        self.info_tab = InfoTab()
        
        self.tab_widget.addTab(self.main_settings_tab, "")
        self.tab_widget.addTab(self.settings_tab, "")
        self.tab_widget.addTab(self.recognition_tab, "")
        self.tab_widget.addTab(self.info_tab, "")
        
        main_layout.addWidget(self.tab_widget)
        
        self.retranslate_ui()

    def retranslate_ui(self):
        """Обновляет тексты вкладок и их содержимое."""
        self.tab_widget.setTabText(0, self.tr("Основные"))
        self.tab_widget.setTabText(1, self.tr("Настройки"))
        self.tab_widget.setTabText(2, self.tr("Распознавание"))
        self.tab_widget.setTabText(3, self.tr("Информация"))
        
        # Обновляем перевод в дочерних вкладках
        self.main_settings_tab.retranslate_ui()
        self.settings_tab.retranslate_ui()
        self.recognition_tab.retranslate_ui()
        self.info_tab.retranslate_ui()

    @Slot(dict)
    def on_main_settings_changed(self, settings):
        """
        Обработчик изменения настроек в основной вкладке.
        
        Args:
            settings: Словарь с измененными настройками
        """
        self.settings_manager.update_settings(settings)
        logger.debug(f"Основные настройки обновлены: {settings}")

    @Slot(YandexSpeechRecognizer)
    def on_settings_applied(self, recognizer: YandexSpeechRecognizer):
        """
        Обработчик применения настроек.
        
        Args:
            recognizer: Распознаватель речи
        """
        # Передаем распознаватель в вкладку распознавания
        self.recognition_tab.set_recognizer(recognizer)
        
        # Переключаемся на вкладку распознавания
        self.tab_widget.setCurrentIndex(1)


class SpeechRecognitionWindow(QDialog):
    """Главное окно для распознавания речи."""
    
    def __init__(self, settings_manager=None):
        """Инициализация главного окна."""
        super().__init__()
        
        # Инициализируем систему переводов
        if settings_manager:
            self.settings_manager = settings_manager
        else:
            self.settings_manager = SettingsManager()
        # Создаем виджет распознавания речи
        self.recognition_widget = SpeechRecognitionWidget(self.settings_manager)

        self.translation_manager = get_translation_manager(self.settings_manager)
        self.translation_manager.language_changed.connect(self.retranslate_ui)
        
        # Настройка окна
        self.setWindowTitle(self.tr("Распознавание речи - Яндекс SpeechKit"))
        self.setMinimumSize(800, 600)
        
        # Создаем кнопки управления
        self.close_button = QPushButton(self.tr("Закрыть"))
        self.close_button.clicked.connect(self.accept)

        # Основной макет
        layout = QVBoxLayout(self)
        layout.addWidget(self.recognition_widget)
        layout.addWidget(self.close_button)
        
        self.retranslate_ui()

    def retranslate_ui(self):
        """Обновляет все тексты в окне."""
        self.setWindowTitle(self.tr("Распознавание речи - Яндекс SpeechKit"))

        self.recognition_widget.retranslate_ui()
        logger.info(f"Язык интерфейса voice recognition изменен на {self.translation_manager.get_current_language()}")
