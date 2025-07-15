"""
Вкладка настроек для графического интерфейса распознавания речи.
"""

import os
import sys
import logging
from typing import Dict, Any, List, Optional, Tuple, Union, Callable

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QComboBox, QLineEdit, QTextEdit, QGroupBox, 
                            QFormLayout, QRadioButton, QButtonGroup, QMessageBox, QStackedWidget, QFileDialog)
from PySide6.QtCore import Qt, Signal, QSettings
from voice_control.recognizers.vosk_recognizer import VOSK_AVAILABLE



# Настраиваем логирование через глобальную конфигурацию
try:
    from logging_config import configure_logging
    configure_logging()
except ImportError:
    # Fallback на базовую настройку, если глобальная конфигурация недоступна
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

from voice_control.recognizers.base_recognizer import BaseRecognizer
from voice_control.recognizers.yandex_recognizer import YandexSpeechRecognizer
from voice_control.recognizers.vosk_recognizer import VoskSpeechRecognizer
from voice_control.recognizers.google_recognizer import GoogleSpeechRecognizer
from voice_control.ui.settings_tabs.google_settings_tab import GoogleSettingsTab
from voice_control.ui.settings_tabs.yandex_settings_tab import YandexSettingsTab
from voice_control.ui.settings_tabs.vosk_settings_tab import VoskSettingsTab

class SettingsTabRecognizer(QWidget):
    """Вкладка настроек для распознавания речи."""
    
    settings_applied = Signal(YandexSpeechRecognizer)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.recognizer: Optional[BaseRecognizer] = None
        self.settings_widgets: Dict[str, QWidget] = {}
        self.init_ui()
        self.load_settings()

    def retranslate_ui(self):
        self.recognizer_type_group.setTitle(self.tr("Тип распознавателя"))
        self.recognizer_type_combo.setItemText(0, self.tr("Yandex SpeechKit"))
        if VOSK_AVAILABLE:
            self.recognizer_type_combo.setItemText(self.recognizer_type_combo.findData("vosk"), self.tr("Локальный (Vosk)"))
        self.recognizer_type_combo.setItemText(self.recognizer_type_combo.findData("google"), self.tr("Google Cloud Speech-to-Text"))

        self.apply_button.setText(self.tr("Применить и сохранить настройки"))

        # Retranslate child tabs
        for widget in self.settings_widgets.values():
            if hasattr(widget, 'retranslate_ui'):
                widget.retranslate_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)

        self.recognizer_type_group = QGroupBox()
        recognizer_type_layout = QHBoxLayout(self.recognizer_type_group)
        self.recognizer_type_combo = QComboBox()
        self.recognizer_type_combo.addItem("", "yandex") # Text will be set in retranslate_ui
        if VOSK_AVAILABLE:
            self.recognizer_type_combo.addItem("", "vosk") # Text will be set in retranslate_ui
        self.recognizer_type_combo.addItem("", "google") # Text will be set in retranslate_ui
        recognizer_type_layout.addWidget(self.recognizer_type_combo)
        layout.addWidget(self.recognizer_type_group)


        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)

        # Создаем и добавляем вкладки настроек
        self.yandex_settings_tab = YandexSettingsTab()
        self.stacked_widget.addWidget(self.yandex_settings_tab)
        self.settings_widgets["yandex"] = self.yandex_settings_tab

        if VOSK_AVAILABLE:
            self.vosk_settings_tab = VoskSettingsTab()
            self.stacked_widget.addWidget(self.vosk_settings_tab)
            self.settings_widgets["vosk"] = self.vosk_settings_tab

        self.google_settings_tab = GoogleSettingsTab()
        self.stacked_widget.addWidget(self.google_settings_tab)
        self.settings_widgets["google"] = self.google_settings_tab
        
        self.recognizer_type_combo.currentTextChanged.connect(self.on_recognizer_type_changed)

        self.apply_button = QPushButton()
        self.apply_button.clicked.connect(self.apply_settings)
        layout.addWidget(self.apply_button)
        
        layout.addStretch()

        self.retranslate_ui()

        # Инициализация текущей вкладки
        self.on_recognizer_type_changed(self.recognizer_type_combo.currentData())

    def on_recognizer_type_changed(self, recognizer_id_text: Optional[str] = None):
        # Если recognizer_id_text не передан (например, при первом вызове из init_ui до connect)
        # или если currentData() возвращает None (хотя не должно для QComboBox с элементами)
        # берем текущее значение из комбобокса.
        current_id = self.recognizer_type_combo.currentData()
        if not current_id:
            logger.warning("recognizer_type_combo.currentData() вернул None или пустую строку.")
            # Можно установить значение по умолчанию, если это необходимо
            # current_id = "yandex" # Например
            # self.recognizer_type_combo.setCurrentIndex(self.recognizer_type_combo.findData(current_id))
            return # Или просто выйти, если нет данных для обработки

        logger.debug(f"Смена типа распознавателя на: {current_id}")
        if current_id in self.settings_widgets:
            self.stacked_widget.setCurrentWidget(self.settings_widgets[current_id])
        else:
            logger.warning(f"Виджет настроек для '{current_id}' не найден.")
            # Можно скрыть QStackedWidget или показать пустую страницу
            # self.stacked_widget.setCurrentIndex(-1) # или какой-то индекс по умолчанию

    def apply_settings(self):
        recognizer_type = self.recognizer_type_combo.currentData()
        current_settings_widget = self.settings_widgets.get(recognizer_type)

        if not current_settings_widget:
            QMessageBox.warning(self, self.tr("Ошибка"), self.tr("Не найден виджет настроек для {}").format(recognizer_type))
            return

        if not hasattr(current_settings_widget, 'is_valid') or not hasattr(current_settings_widget, 'get_settings'):
            QMessageBox.warning(self, self.tr("Ошибка"), self.tr("Виджет настроек для {} не реализует необходимые методы.").format(recognizer_type))
            return

        if not current_settings_widget.is_valid():
            # Сообщение об ошибке должно отображаться внутри is_valid()
            return

        config = current_settings_widget.get_settings()
        logger.info(f"Применение настроек для {recognizer_type} с конфигурацией: {config}")

        try:
            if recognizer_type == "yandex":
                self.recognizer = YandexSpeechRecognizer(config=config)
            elif recognizer_type == "vosk" and VOSK_AVAILABLE:
                self.recognizer = VoskSpeechRecognizer(config=config)
            elif recognizer_type == "google":
                self.recognizer = GoogleSpeechRecognizer(config=config)
            else:
                QMessageBox.warning(self, self.tr("Ошибка"), self.tr("Неизвестный тип распознавателя: {}").format(recognizer_type))
                return
            
            self.settings_applied.emit(self.recognizer)
            self.save_settings() # Сохраняем настройки после успешного применения
            QMessageBox.information(self, self.tr("Успех"), self.tr("Настройки успешно применены и сохранены."))
            logger.info(f"Настройки для {recognizer_type} успешно применены.")

        except Exception as e:
            logger.error(f"Ошибка при создании или применении распознавателя {recognizer_type}: {e}")
            QMessageBox.critical(self, self.tr("Ошибка применения настроек"), 
                                 self.tr("Не удалось применить настройки для {}:\n{}").format(recognizer_type, e))


    def save_settings(self):
        """Сохранение настроек в QSettings."""
        settings = QSettings("Screph", "SpeechRecognition")
        current_recognizer_type = self.recognizer_type_combo.currentData()
        settings.setValue("recognizer_type", current_recognizer_type)

        active_widget = self.settings_widgets.get(current_recognizer_type)
        if active_widget and hasattr(active_widget, 'save_specific_settings'):
            active_widget.save_specific_settings(settings)
            logger.info(f"Специфичные настройки для типа '{current_recognizer_type}' сохранены виджетом.")
        elif active_widget:
            logger.warning(f"Виджет для '{current_recognizer_type}' не имеет метода save_specific_settings.")
        else:
            logger.warning(f"Виджет для '{current_recognizer_type}' не найден при сохранении настроек.")
        
        logger.info(f"Общие настройки сохранены. Текущий тип распознавателя: '{current_recognizer_type}'.")

    def load_settings(self):
        """Загрузка настроек из QSettings."""
        settings = QSettings("Screph", "SpeechRecognition")
        
        default_recognizer_type = "yandex" 
        if self.recognizer_type_combo.count() > 0:
            if self.recognizer_type_combo.findData(default_recognizer_type) == -1:
                default_recognizer_type = self.recognizer_type_combo.itemData(0)

        recognizer_type = settings.value("recognizer_type", default_recognizer_type)
        
        index = self.recognizer_type_combo.findData(recognizer_type)
        if index != -1:
            self.recognizer_type_combo.setCurrentIndex(index)
        elif self.recognizer_type_combo.count() > 0:
            self.recognizer_type_combo.setCurrentIndex(0)
            recognizer_type = self.recognizer_type_combo.currentData()
            logger.warning(f"Сохраненный тип распознавателя '{settings.value('recognizer_type')}' не найден. Установлен первый доступный: '{recognizer_type}'.")
        else:
            logger.warning("Нет доступных типов распознавателей. Загрузка настроек невозможна.")
            return

        for r_type, widget in self.settings_widgets.items():
            if hasattr(widget, 'load_specific_settings'):
                try:
                    widget.load_specific_settings(settings)
                    logger.info(f"Специфичные настройки для '{r_type}' загружены виджетом.")
                except Exception as e:
                    logger.error(f"Ошибка при загрузке специфичных настроек для '{r_type}': {e}", exc_info=True)
            else:
                logger.warning(f"Виджет для '{r_type}' не имеет метода load_specific_settings.")

        self.on_recognizer_type_changed(self.recognizer_type_combo.currentData())
        logger.info(f"Настройки загружены. Активный тип распознавателя: '{self.recognizer_type_combo.currentData()}'.")

    def get_recognizer(self) -> Optional[BaseRecognizer]:
        """
        Получение текущего экземпляра распознавателя речи.
        Экземпляр создается или обновляется при вызове apply_settings.
        
        Returns:
            Распознаватель речи (экземпляр BaseRecognizer или его наследника) 
            или None, если он не был успешно инициализирован.
        """
        return self.recognizer
