"""
Базовый класс для всех вкладок настроек.
"""

import logging
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget

logger = logging.getLogger(__name__)

class BaseSettingsTab(QWidget):
    """Базовый класс для всех вкладок настроек"""
    
    settings_changed = Signal(dict)
    
    def __init__(self, settings_manager, parent=None):
        """
        Инициализация базового класса вкладки настроек
        
        Args:
            settings_manager: Менеджер настроек
            parent: Родительский виджет
        """
        super().__init__(parent)
        self.settings_manager = settings_manager
    
    def _init_ui(self):
        """
        Инициализация пользовательского интерфейса.
        Должна быть переопределена в наследниках.
        """
        raise NotImplementedError("Метод _init_ui должен быть переопределен")
    
    def _load_settings(self):
        """
        Загрузка настроек.
        Должна быть переопределена в наследниках.
        """
        raise NotImplementedError("Метод _load_settings должен быть переопределен")
    
    def _on_settings_changed(self):
        """
        Обработчик изменения настроек.
        Должен быть переопределен в наследниках.
        """
        raise NotImplementedError("Метод _on_settings_changed должен быть переопределен")
    
    def get_settings(self) -> dict:
        """
        Получение текущих настроек вкладки.
        Должен быть переопределен в наследниках.
        
        Returns:
            dict: Словарь с текущими настройками вкладки
        """
        raise NotImplementedError("Метод get_settings должен быть переопределен")
    
    def retranslate_ui(self):
        """
        Обновление переводов интерфейса.
        Должен быть переопределен в наследниках.
        """
        raise NotImplementedError("Метод retranslate_ui должен быть переопределен")
