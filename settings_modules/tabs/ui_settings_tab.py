"""
Модуль с виджетом настроек пользовательского интерфейса.
"""

import logging
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QSpinBox, QLineEdit, QGroupBox, QCheckBox,
    QPushButton, QFileDialog, QColorDialog
)
from PySide6.QtGui import QColor

from settings_modules.tabs.base_settings_tab import BaseSettingsTab

logger = logging.getLogger(__name__)

class UISettingsTab(BaseSettingsTab):
    """Вкладка настроек пользовательского интерфейса"""
    
    def __init__(self, settings_manager, parent=None):
        """
        Инициализация вкладки настроек пользовательского интерфейса
        
        Args:
            settings_manager: Менеджер настроек
            parent: Родительский виджет
        """
        super().__init__(settings_manager, parent)
        self.highlight_color = QColor("#FF0000")  # Красный по умолчанию
        self._init_ui()
        self._load_settings()
    
    def _init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Группа настроек выделения
        self.highlight_group = QGroupBox(self.tr("Настройки выделения"))
        highlight_layout = QVBoxLayout()
        self.highlight_group.setLayout(highlight_layout)
        
        # Цвет выделения
        color_layout = QHBoxLayout()
        self.color_label = QLabel(self.tr("Цвет выделения:"))
        self.color_button = QPushButton()
        self.color_button.setFixedSize(24, 24)
        self.color_button.setStyleSheet(f"background-color: {self.highlight_color.name()}; border: 1px solid gray;")
        self.color_button.clicked.connect(self._select_color)
        
        self.color_value = QLabel(self.highlight_color.name())
        
        color_layout.addWidget(self.color_label)
        color_layout.addWidget(self.color_button)
        color_layout.addWidget(self.color_value)
        color_layout.addStretch()
        highlight_layout.addLayout(color_layout)
        
        # Настройка ширины границы выделения
        border_layout = QHBoxLayout()
        self.border_label = QLabel(self.tr("Ширина границы (px):"))
        self.border_spin = QSpinBox()
        self.border_spin.setRange(1, 10)
        self.border_spin.setSingleStep(1)
        
        border_layout.addWidget(self.border_label)
        border_layout.addWidget(self.border_spin)
        highlight_layout.addLayout(border_layout)
        
        layout.addWidget(self.highlight_group)
        
        # Группа настроек сохранения
        self.save_group = QGroupBox(self.tr("Настройки сохранения"))
        save_layout = QVBoxLayout()
        self.save_group.setLayout(save_layout)
        
        # Каталог для автоматического сохранения
        path_layout = QHBoxLayout()
        self.path_label = QLabel(self.tr("Каталог автосохранения:"))
        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        self.browse_button = QPushButton(self.tr("Обзор..."))
        self.browse_button.clicked.connect(self._browse_save_path)
        
        path_layout.addWidget(self.path_label)
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(self.browse_button)
        save_layout.addLayout(path_layout)
        
        # Запоминать последний каталог сохранения
        self.remember_path = QCheckBox(self.tr("Запоминать последний каталог сохранения"))
        save_layout.addWidget(self.remember_path)
        
        layout.addWidget(self.save_group)
        layout.addStretch()
        
        # Подключаем сигналы
        self.border_spin.valueChanged.connect(self._on_settings_changed)
        self.path_edit.textChanged.connect(self._on_settings_changed)
        self.remember_path.toggled.connect(self._on_settings_changed)
        
        self.retranslate_ui()
    
    def _load_settings(self):
        """Загрузка настроек"""
        # Цвет выделения
        color_str = self.settings_manager.get_setting("ui/highlight_color", "#FF0000")
        self.highlight_color = QColor(color_str)
        self.color_button.setStyleSheet(f"background-color: {self.highlight_color.name()}; border: 1px solid gray;")
        self.color_value.setText(self.highlight_color.name())
        
        # Ширина границы
        self.border_spin.setValue(
            self.settings_manager.get_setting("ui/selection_border_width", 2)
        )
        
        # Путь автосохранения
        self.path_edit.setText(
            self.settings_manager.get_setting("ui/auto_save_path", "")
        )
        
        # Запоминать путь
        self.remember_path.setChecked(
            self.settings_manager.get_setting("ui/remember_last_save_location", True)
        )
    
    def _select_color(self):
        """Открывает диалог выбора цвета"""
        color = QColorDialog.getColor(self.highlight_color, self, self.tr("Выберите цвет выделения"))
        if color.isValid():
            self.highlight_color = color
            self.color_button.setStyleSheet(f"background-color: {color.name()}; border: 1px solid gray;")
            self.color_value.setText(color.name())
            self._on_settings_changed()
    
    def _browse_save_path(self):
        """Открывает диалог выбора каталога для автосохранения"""
        dir_path = QFileDialog.getExistingDirectory(
            self, self.tr("Выберите каталог для автосохранения"), self.path_edit.text()
        )
        if dir_path:
            self.path_edit.setText(dir_path)
    
    def _on_settings_changed(self):
        """Обработчик изменения настроек"""
        settings = {
            "ui": {
                "highlight_color": self.highlight_color.name(),
                "selection_border_width": self.border_spin.value(),
                "auto_save_path": self.path_edit.text(),
                "remember_last_save_location": self.remember_path.isChecked()
            }
        }
    
    def retranslate_ui(self):
        """Обновляет переводы интерфейса"""
        # Обновляем тексты групп
        self.highlight_group.setTitle(self.tr("Настройки выделения"))
        self.save_group.setTitle(self.tr("Настройки сохранения"))
        
        # Обновляем метки
        self.color_label.setText(self.tr("Цвет выделения:"))
        self.border_label.setText(self.tr("Ширина границы (px):"))
        self.path_label.setText(self.tr("Каталог автосохранения:"))
        
        # Обновляем кнопки
        self.browse_button.setText(self.tr("Обзор..."))
        
        # Обновляем чекбокс
        self.remember_path.setText(self.tr("Запоминать последний каталог сохранения"))
        self.settings_changed.emit(settings)
    
    def get_settings(self) -> dict:
        """Получение текущих настроек вкладки"""
        return {
            "ui": {
                "highlight_color": self.highlight_color.name(),
                "selection_border_width": self.border_spin.value(),
                "auto_save_path": self.path_edit.text(),
                "remember_last_save_location": self.remember_path.isChecked()
            }
        }
