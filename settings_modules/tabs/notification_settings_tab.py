"""
Модуль с виджетом настроек уведомлений.
"""

import logging
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, 
    QCheckBox, QGroupBox
)

logger = logging.getLogger(__name__)

class NotificationSettingsTab(QWidget):
    """Вкладка настроек уведомлений"""
    
    settings_changed = Signal(dict)
    
    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self._init_ui()
        self._load_settings()
    
    def _init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Группа основных настроек уведомлений
        self.notifications_group = QGroupBox(self.tr("Показывать уведомления"))
        notifications_layout = QVBoxLayout()
        self.notifications_group.setLayout(notifications_layout)
        
        # Уведомление при запуске
        self.startup_notify = QCheckBox(self.tr("При запуске приложения"))
        notifications_layout.addWidget(self.startup_notify)
        
        # Уведомление при захвате
        self.capture_notify = QCheckBox(self.tr("При захвате экрана"))
        notifications_layout.addWidget(self.capture_notify)
        
        # Уведомление при сохранении
        self.save_notify = QCheckBox(self.tr("При сохранении файла"))
        notifications_layout.addWidget(self.save_notify)
        
        layout.addWidget(self.notifications_group)
        
        # Группа дополнительных настроек
        self.sound_group = QGroupBox(self.tr("Звуковые эффекты"))
        sound_layout = QVBoxLayout()
        self.sound_group.setLayout(sound_layout)
        
        # Включение звуков
        self.sound_enabled = QCheckBox(self.tr("Включить звуковые уведомления"))
        sound_layout.addWidget(self.sound_enabled)
        
        layout.addWidget(self.sound_group)
        layout.addStretch()
        
        # Подключение сигналов
        self.startup_notify.toggled.connect(self._on_settings_changed)
        self.capture_notify.toggled.connect(self._on_settings_changed)
        self.save_notify.toggled.connect(self._on_settings_changed)
        self.sound_enabled.toggled.connect(self._on_settings_changed)
        
        self.retranslate_ui()
    
    def _load_settings(self):
        """Загрузка настроек"""
        # Загружаем состояния чекбоксов
        self.startup_notify.setChecked(
            self.settings_manager.get_setting("notifications/show_on_startup", True)
        )
        self.capture_notify.setChecked(
            self.settings_manager.get_setting("notifications/show_on_capture", True)
        )
        self.save_notify.setChecked(
            self.settings_manager.get_setting("notifications/show_on_save", True)
        )
        self.sound_enabled.setChecked(
            self.settings_manager.get_setting("notifications/sound_enabled", True)
        )
    
    def _on_settings_changed(self):
        """Обработчик изменения настроек"""
        settings = {
            "notifications": {
                "show_on_startup": self.startup_notify.isChecked(),
                "show_on_capture": self.capture_notify.isChecked(),
                "show_on_save": self.save_notify.isChecked(),
                "sound_enabled": self.sound_enabled.isChecked()
            }
        }
    
    def retranslate_ui(self):
        """Обновляет переводы интерфейса"""
        # Обновляем тексты групп
        self.notifications_group.setTitle(self.tr("Показывать уведомления"))
        self.sound_group.setTitle(self.tr("Звуковые эффекты"))
        
        # Обновляем чекбоксы
        self.startup_notify.setText(self.tr("При запуске приложения"))
        self.capture_notify.setText(self.tr("При захвате экрана"))
        self.save_notify.setText(self.tr("При сохранении файла"))
        self.sound_enabled.setText(self.tr("Включить звуковые уведомления"))
        self.settings_changed.emit(settings)
    
    def get_settings(self) -> dict:
        """Получение текущих настроек вкладки"""
        return {
            "notifications": {
                "show_on_startup": self.startup_notify.isChecked(),
                "show_on_capture": self.capture_notify.isChecked(),
                "show_on_save": self.save_notify.isChecked(),
                "sound_enabled": self.sound_enabled.isChecked()
            }
        }
