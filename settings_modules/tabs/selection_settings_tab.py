"""
Модуль с виджетом настроек выделения элементов.
"""

import logging
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QSpinBox, QDoubleSpinBox, QGroupBox, QSlider,
    QColorDialog
)
from PySide6.QtGui import QColor

from settings_modules.tabs.base_settings_tab import BaseSettingsTab

logger = logging.getLogger(__name__)

class SelectionSettingsTab(BaseSettingsTab):
    """Вкладка настроек выделения элементов"""
    
    def __init__(self, settings_manager, parent=None):
        """
        Инициализация вкладки настроек выделения элементов
        
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
        
        # Группа настроек минимальных размеров выделения
        self.size_group = QGroupBox(self.tr("Минимальные размеры выделения"))
        size_layout = QVBoxLayout()
        self.size_group.setLayout(size_layout)
        
        # Настройка минимальной ширины
        width_layout = QHBoxLayout()
        self.width_label = QLabel(self.tr("Минимальная ширина (px):"))
        self.min_width_spin = QSpinBox()
        self.min_width_spin.setRange(1, 100)
        self.min_width_spin.setSingleStep(1)
        
        width_layout.addWidget(self.width_label)
        width_layout.addWidget(self.min_width_spin)
        size_layout.addLayout(width_layout)
        
        # Настройка минимальной высоты
        height_layout = QHBoxLayout()
        self.height_label = QLabel(self.tr("Минимальная высота (px):"))
        self.min_height_spin = QSpinBox()
        self.min_height_spin.setRange(1, 100)
        self.min_height_spin.setSingleStep(1)
        
        height_layout.addWidget(self.height_label)
        height_layout.addWidget(self.min_height_spin)
        size_layout.addLayout(height_layout)
        
        layout.addWidget(self.size_group)
        
        # Группа настроек затемнения фона
        self.darkening_group = QGroupBox(self.tr("Затемнение фона"))
        darkening_layout = QVBoxLayout()
        self.darkening_group.setLayout(darkening_layout)
        
        # Настройка коэффициента затемнения
        darkening_layout_slider = QHBoxLayout()
        self.darkening_label = QLabel(self.tr("Степень затемнения:"))
        self.darkening_slider = QSlider(Qt.Orientation.Horizontal)
        self.darkening_slider.setRange(0, 100)
        self.darkening_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.darkening_slider.setTickInterval(10)
        
        self.darkening_value_label = QLabel("50%")
        self.darkening_slider.valueChanged.connect(
            lambda v: self.darkening_value_label.setText(f"{v}%")
        )
        
        darkening_layout_slider.addWidget(self.darkening_label)
        darkening_layout_slider.addWidget(self.darkening_slider)
        darkening_layout_slider.addWidget(self.darkening_value_label)
        darkening_layout.addLayout(darkening_layout_slider)
        
        self.darkening_info = QLabel(self.tr("0% - без затемнения, 100% - полностью темный"))
        self.darkening_info.setStyleSheet("color: gray;")
        darkening_layout.addWidget(self.darkening_info)
        
        layout.addWidget(self.darkening_group)
        layout.addStretch()
        
        # Подключаем сигналы
        self.min_width_spin.valueChanged.connect(self._on_settings_changed)
        self.min_height_spin.valueChanged.connect(self._on_settings_changed)
        self.darkening_slider.valueChanged.connect(self._on_settings_changed)
        
        self.retranslate_ui()
    
    def _load_settings(self):
        """Загрузка настроек"""
        self.min_width_spin.setValue(
            self.settings_manager.get_setting("selection/min_width", 10)
        )
        self.min_height_spin.setValue(
            self.settings_manager.get_setting("selection/min_height", 10)
        )
        
        # Преобразуем коэффициент затемнения (0-1) в значение для слайдера (0-100)
        darkening_factor = self.settings_manager.get_setting("selection/darkening_factor", 0.5)
        self.darkening_slider.setValue(int(darkening_factor * 100))
    
    def _on_settings_changed(self):
        """Обработчик изменения настроек"""
        settings = {
            "selection": {
                "min_width": self.min_width_spin.value(),
                "min_height": self.min_height_spin.value(),
                "darkening_factor": self.darkening_slider.value() / 100.0
            }
        }
    
    def retranslate_ui(self):
        """Обновляет переводы интерфейса"""
        # Обновляем тексты групп
        self.size_group.setTitle(self.tr("Минимальные размеры выделения"))
        self.darkening_group.setTitle(self.tr("Затемнение фона"))
        
        # Обновляем метки
        self.width_label.setText(self.tr("Минимальная ширина (px):"))
        self.height_label.setText(self.tr("Минимальная высота (px):"))
        self.darkening_label.setText(self.tr("Степень затемнения:"))
        self.darkening_info.setText(self.tr("0% - без затемнения, 100% - полностью темный"))
        self.settings_changed.emit(settings)
    
    def get_settings(self) -> dict:
        """Получение текущих настроек вкладки"""
        return {
            "selection": {
                "min_width": self.min_width_spin.value(),
                "min_height": self.min_height_spin.value(),
                "darkening_factor": self.darkening_slider.value() / 100.0
            }
        }
