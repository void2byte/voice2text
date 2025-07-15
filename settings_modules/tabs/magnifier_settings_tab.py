"""
Модуль с виджетом настроек лупы.
"""

import logging
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QSpinBox, QDoubleSpinBox, QGroupBox, QCheckBox,
    QSlider
)

from settings_modules.tabs.base_settings_tab import BaseSettingsTab

logger = logging.getLogger(__name__)

class MagnifierSettingsTab(BaseSettingsTab):
    """Вкладка настроек лупы"""
    
    def __init__(self, settings_manager, parent=None):
        """
        Инициализация вкладки настроек лупы
        
        Args:
            settings_manager: Менеджер настроек
            parent: Родительский виджет
        """
        super().__init__(settings_manager, parent)
        self._init_ui()
        self._load_settings()
    
    def _init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Группа основных настроек лупы
        self.magnifier_group = QGroupBox(self.tr("Настройки лупы"))
        magnifier_layout = QVBoxLayout()
        self.magnifier_group.setLayout(magnifier_layout)
        
        # Включение/выключение лупы
        self.enable_magnifier = QCheckBox(self.tr("Включить лупу"))
        magnifier_layout.addWidget(self.enable_magnifier)
        
        # Размер лупы
        size_layout = QHBoxLayout()
        self.size_label = QLabel(self.tr("Размер лупы (px):"))
        self.size_spin = QSpinBox()
        self.size_spin.setRange(50, 500)
        self.size_spin.setSingleStep(10)
        
        size_layout.addWidget(self.size_label)
        size_layout.addWidget(self.size_spin)
        magnifier_layout.addLayout(size_layout)
        
        # Коэффициент увеличения
        zoom_layout = QHBoxLayout()
        self.zoom_label = QLabel(self.tr("Коэффициент увеличения:"))
        self.zoom_spin = QDoubleSpinBox()
        self.zoom_spin.setRange(1.0, 10.0)
        self.zoom_spin.setSingleStep(0.5)
        self.zoom_spin.setDecimals(1)
        
        zoom_layout.addWidget(self.zoom_label)
        zoom_layout.addWidget(self.zoom_spin)
        magnifier_layout.addLayout(zoom_layout)
        
        # Включение/выключение сетки
        self.enable_grid = QCheckBox(self.tr("Показывать сетку в лупе"))
        magnifier_layout.addWidget(self.enable_grid)
        
        layout.addWidget(self.magnifier_group)
        layout.addStretch()
        
        # Подключаем сигналы
        self.enable_magnifier.toggled.connect(self._on_settings_changed)
        self.size_spin.valueChanged.connect(self._on_settings_changed)
        self.zoom_spin.valueChanged.connect(self._on_settings_changed)
        self.enable_grid.toggled.connect(self._on_settings_changed)
        
        # Вызываем метод локализации
        self.retranslate_ui()
    
    def _load_settings(self):
        """Загрузка настроек"""
        self.enable_magnifier.setChecked(
            self.settings_manager.get_setting("magnifier/enabled", True)
        )
        self.size_spin.setValue(
            self.settings_manager.get_setting("magnifier/size", 200)
        )
        self.zoom_spin.setValue(
            self.settings_manager.get_setting("magnifier/zoom_factor", 2.0)
        )
        self.enable_grid.setChecked(
            self.settings_manager.get_setting("magnifier/grid_enabled", True)
        )
    
    def _on_settings_changed(self):
        """Обработчик изменения настроек"""
        settings = {
            "magnifier": {
                "enabled": self.enable_magnifier.isChecked(),
                "size": self.size_spin.value(),
                "zoom_factor": self.zoom_spin.value(),
                "grid_enabled": self.enable_grid.isChecked()
            }
        }
        self.settings_changed.emit(settings)
    
    def get_settings(self) -> dict:
        """Получение текущих настроек вкладки"""
        return {
            "magnifier": {
                "enabled": self.enable_magnifier.isChecked(),
                "size": self.size_spin.value(),
                "zoom_factor": self.zoom_spin.value(),
                "grid_enabled": self.enable_grid.isChecked()
            }
        }
    
    def retranslate_ui(self):
        """Обновление локализации интерфейса"""
        self.magnifier_group.setTitle(self.tr("Настройки лупы"))
        self.enable_magnifier.setText(self.tr("Включить лупу"))
        self.size_label.setText(self.tr("Размер лупы (px):"))
        self.zoom_label.setText(self.tr("Коэффициент увеличения:"))
        self.enable_grid.setText(self.tr("Показывать сетку в лупе"))
