"""
Модуль с виджетом настроек голосовой аннотации.
"""

import logging
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QSpinBox, QComboBox, QGroupBox, QRadioButton,
    QButtonGroup
)

from settings_modules.tabs.base_settings_tab import BaseSettingsTab

logger = logging.getLogger(__name__)

class VoiceSettingsTab(BaseSettingsTab):
    """Вкладка настроек голосовой аннотации"""
    
    def __init__(self, settings_manager, parent=None):
        super().__init__(settings_manager, parent)
        self._init_ui()
        self._load_settings()
    
    def _init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Группа настроек записи
        self.recording_group = QGroupBox(self.tr("Настройки записи"))
        recording_layout = QVBoxLayout()
        self.recording_group.setLayout(recording_layout)
        
        # Максимальная длительность
        duration_layout = QHBoxLayout()
        self.duration_label = QLabel(self.tr("Максимальная длительность (секунд):"))
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(10, 300)
        self.duration_spin.setSingleStep(10)
        duration_layout.addWidget(self.duration_label)
        duration_layout.addWidget(self.duration_spin)
        recording_layout.addLayout(duration_layout)
        
        # Качество аудио
        quality_layout = QHBoxLayout()
        self.quality_label = QLabel(self.tr("Качество записи:"))
        self.quality_combo = QComboBox()
        self.quality_combo.addItems([self.tr("Низкое"), self.tr("Среднее"), self.tr("Высокое")])
        quality_layout.addWidget(self.quality_label)
        quality_layout.addWidget(self.quality_combo)
        recording_layout.addLayout(quality_layout)
        
        layout.addWidget(self.recording_group)
        
        # Группа настроек распознавания
        self.recognition_group_widget = QGroupBox(self.tr("Распознавание речи"))
        recognition_layout = QVBoxLayout()
        self.recognition_group_widget.setLayout(recognition_layout)
        
        # Режим распознавания
        self.recognition_group = QButtonGroup(self)
        
        self.auto_recognition = QRadioButton(self.tr("Автоматическое распознавание"))
        self.manual_recognition = QRadioButton(self.tr("Отложенное распознавание"))
        
        recognition_layout.addWidget(self.auto_recognition)
        recognition_layout.addWidget(self.manual_recognition)
        
        self.recognition_group.addButton(self.auto_recognition)
        self.recognition_group.addButton(self.manual_recognition)
        
        layout.addWidget(self.recognition_group_widget)
        layout.addStretch()
        
        # Подключение сигналов
        self.duration_spin.valueChanged.connect(self._on_settings_changed)
        self.quality_combo.currentIndexChanged.connect(self._on_settings_changed)
        self.auto_recognition.toggled.connect(self._on_settings_changed)
        
        self.retranslate_ui()
    
    def _load_settings(self):
        """Загрузка настроек"""
        # Длительность
        duration = self.settings_manager.get_setting("voice_annotation/max_duration", 60)
        self.duration_spin.setValue(duration)
        
        # Качество
        quality_map = {"low": 0, "medium": 1, "high": 2}
        quality = self.settings_manager.get_setting("voice_annotation/audio_quality", "medium")
        self.quality_combo.setCurrentIndex(quality_map.get(quality, 1))
        
        # Режим распознавания
        auto_recognition = self.settings_manager.get_setting("voice_annotation/auto_recognition", True)
        if auto_recognition:
            self.auto_recognition.setChecked(True)
        else:
            self.manual_recognition.setChecked(True)
    
    def _on_settings_changed(self):
        """Обработчик изменения настроек"""
        settings = {
            "voice_annotation": {
                "max_duration": self.duration_spin.value(),
                "audio_quality": ["low", "medium", "high"][self.quality_combo.currentIndex()],
                "auto_recognition": self.auto_recognition.isChecked()
            }
        }
        self.settings_changed.emit(settings)
    
    def get_settings(self) -> dict:
        """Получение текущих настроек вкладки"""
        return {
            "voice_annotation": {
                "max_duration": self.duration_spin.value(),
                "audio_quality": ["low", "medium", "high"][self.quality_combo.currentIndex()],
                "auto_recognition": self.auto_recognition.isChecked()
            }
        }
    
    def retranslate_ui(self):
        """Обновляет переводы интерфейса"""
        # Обновляем тексты групп
        self.recording_group.setTitle(self.tr("Настройки записи"))
        self.recognition_group_widget.setTitle(self.tr("Распознавание речи"))
        
        # Обновляем метки
        self.duration_label.setText(self.tr("Максимальная длительность (секунд):"))
        self.quality_label.setText(self.tr("Качество записи:"))
        
        # Обновляем элементы комбобокса
        current_quality = self.quality_combo.currentIndex()
        self.quality_combo.clear()
        self.quality_combo.addItems([self.tr("Низкое"), self.tr("Среднее"), self.tr("Высокое")])
        self.quality_combo.setCurrentIndex(current_quality)
        
        # Обновляем радиокнопки
        self.auto_recognition.setText(self.tr("Автоматическое распознавание"))
        self.manual_recognition.setText(self.tr("Отложенное распознавание"))
