"""
Модуль с виджетом основных настроек.
"""

import logging
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QComboBox, QLabel, QHBoxLayout
)

from settings_modules.tabs.base_settings_tab import BaseSettingsTab
from translation_manager import get_translation_manager

logger = logging.getLogger(__name__)

class MainSettingsTab(BaseSettingsTab):
    """Вкладка основных настроек"""

    def __init__(self, settings_manager, parent=None):
        """
        Инициализация вкладки основных настроек

        Args:
            settings_manager: Менеджер настроек
            parent: Родительский виджет
        """
        super().__init__(settings_manager, parent)
        self.translation_manager = get_translation_manager(self.settings_manager)
        self._init_ui()
        self._load_settings()

    def _init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Группа настроек языка
        self.language_group = QGroupBox(self.tr("Язык"))
        language_layout = QHBoxLayout()
        self.language_group.setLayout(language_layout)

        self.language_label = QLabel(self.tr("Язык интерфейса:"))
        self.language_combo = QComboBox()
        self.language_combo.addItems(["English", "Русский"])

        language_layout.addWidget(self.language_label)
        language_layout.addWidget(self.language_combo)
        language_layout.addStretch()

        layout.addWidget(self.language_group)

        # Группа настроек режима работы
        self.mode_group = QGroupBox(self.tr("Режим работы"))
        mode_layout = QHBoxLayout()
        self.mode_group.setLayout(mode_layout)

        self.mode_label = QLabel(self.tr("Режим после распознавания:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            self.tr("Обычный режим"),
            self.tr("Копировать и скрыть"),
            self.tr("Копировать, очистить и скрыть")
        ])

        mode_layout.addWidget(self.mode_label)
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()

        layout.addWidget(self.mode_group)

        layout.addStretch()

        # Подключаем сигналы
        self.language_combo.currentTextChanged.connect(self._on_settings_changed)
        self.mode_combo.currentIndexChanged.connect(self._on_settings_changed)

        self.retranslate_ui()

    def _load_settings(self):
        """Загрузка настроек"""
        # Язык
        lang = self.settings_manager.get_setting("main/language", "ru_RU")
        if lang == "en_US":
            self.language_combo.setCurrentText("English")
        else:
            self.language_combo.setCurrentText("Русский")

        # Режим работы
        mode = self.settings_manager.get_setting("main/recognition_mode", 0)
        self.mode_combo.setCurrentIndex(mode)

    def _on_settings_changed(self):
        """Обработчик изменения настроек"""
        settings = self.get_settings()
        self.settings_changed.emit(settings)
        # При смене языка, меняем его в translation_manager
        if self.sender() == self.language_combo:
            lang_text = self.language_combo.currentText()
            if lang_text == "English":
                self.translation_manager.set_language("en_US")
            else:
                self.translation_manager.change_language("ru_RU")

    def get_settings(self) -> dict:
        """Получение текущих настроек вкладки"""
        lang_text = self.language_combo.currentText()
        lang_code = "en_US" if lang_text == "English" else "ru_RU"
        return {
            "main": {
                "language": lang_code,
                "recognition_mode": self.mode_combo.currentIndex()
            }
        }

    def retranslate_ui(self):
        """Обновляет переводы интерфейса"""
        self.language_group.setTitle(self.tr("Язык"))
        self.language_label.setText(self.tr("Язык интерфейса:"))
        self.mode_group.setTitle(self.tr("Режим работы"))
        self.mode_label.setText(self.tr("Режим после распознавания:"))
        self.mode_combo.setItemText(0, self.tr("Обычный режим"))
        self.mode_combo.setItemText(1, self.tr("Копировать и скрыть"))
        self.mode_combo.setItemText(2, self.tr("Копировать, очистить и скрыть"))