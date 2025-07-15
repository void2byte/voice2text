"""
Модуль для применения настроек к различным компонентам приложения.
"""

import logging
import os
import datetime
from typing import Optional

from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)

class SettingsApplicator(QObject):
    """Класс для применения настроек к компонентам приложения"""
    
    # Сигналы об изменении настроек для различных компонентов
    hotkeys_changed = Signal(dict)
    voice_settings_changed = Signal(dict)
    ui_settings_changed = Signal(dict)
    notification_settings_changed = Signal(dict)
    file_settings_changed = Signal(dict)
    magnifier_settings_changed = Signal(dict)
    
    def __init__(self, settings_manager):
        """
        Инициализация применителя настроек
        
        Args:
            settings_manager: Менеджер настроек
        """
        super().__init__()
        self.settings_manager = settings_manager
    
    def apply_all_settings(self, tray_app=None, element_selector=None, voice_widget=None, magnifier_widget=None):
        """
        Применяет все настройки ко всем компонентам приложения
        
        Args:
            tray_app: Экземпляр приложения в трее
            element_selector: Экземпляр селектора элементов
            voice_widget: Экземпляр виджета голосовой аннотации
            magnifier_widget: Экземпляр виджета лупы
        """
        if tray_app:
            self.apply_hotkey_settings(tray_app)
            self.apply_notification_settings(tray_app)
        
        if element_selector:
            self.apply_element_selector_settings(element_selector)
        
        if voice_widget:
            self.apply_voice_annotation_settings(voice_widget)
            
        if magnifier_widget:
            self.apply_magnifier_settings(magnifier_widget)
    
    def apply_hotkey_settings(self, tray_app):
        """
        Применяет настройки горячих клавиш
        
        Args:
            tray_app: Экземпляр приложения в трее
        """
        hotkeys = {
            "start_selection": self.settings_manager.get_setting("hotkeys", "start_selection"),
            "minimize_dialog": self.settings_manager.get_setting("hotkeys", "minimize_dialog"),
            "voice_annotation": self.settings_manager.get_setting("hotkeys", "voice_annotation")
        }
        
        self.hotkeys_changed.emit(hotkeys)
        logger.debug("Применены настройки горячих клавиш")
    
    def apply_element_selector_settings(self, element_selector):
        """
        Применяет настройки к селектору элементов
        
        Args:
            element_selector: Экземпляр селектора элементов
        """
        # Применяем настройки пользовательского интерфейса к селектору элементов
        self.apply_ui_settings(element_selector)
        
        # Если у селектора есть виджет лупы, применяем настройки к нему
        if hasattr(element_selector, 'magnifier'):
            self.apply_magnifier_settings(element_selector.magnifier)
        
        # Настройки выделения
        selection_settings = {
            "min_width": self.settings_manager.get_setting("selection", "min_width"),
            "min_height": self.settings_manager.get_setting("selection", "min_height"),
            "darkening_factor": self.settings_manager.get_setting("selection", "darkening_factor")
        }
        
        # Настройки лупы
        magnifier_settings = {
            "enabled": self.settings_manager.get_setting("magnifier", "enabled"),
            "zoom_factor": self.settings_manager.get_setting("magnifier", "zoom_factor"),
            "size": self.settings_manager.get_setting("magnifier", "size"),
            "grid_enabled": self.settings_manager.get_setting("magnifier", "grid_enabled")
        }
        
        # Настройки UI
        ui_settings = {
            "highlight_color": self.settings_manager.get_setting("ui", "highlight_color"),
            "selection_border_width": self.settings_manager.get_setting("ui", "selection_border_width")
        }
        
        # Отправляем сигналы с настройками
        self.ui_settings_changed.emit({
            "selection": selection_settings,
            "magnifier": magnifier_settings,
            "ui": ui_settings
        })
        
        logger.debug("Применены настройки селектора элементов")
    
    def apply_voice_annotation_settings(self, voice_widget):
        """
        Применяет настройки к виджету голосовой аннотации
        
        Args:
            voice_widget: Экземпляр виджета голосовой аннотации
        """
        voice_settings = {
            "max_duration": self.settings_manager.get_setting("voice_annotation", "max_duration"),
            "auto_recognition": self.settings_manager.get_setting("voice_annotation", "auto_recognition"),
            "audio_quality": self.settings_manager.get_setting("voice_annotation", "audio_quality")
        }
        
        self.voice_settings_changed.emit(voice_settings)
        
    def apply_magnifier_settings(self, magnifier_widget):
        """
        Применяет настройки к виджету лупы
        
        Args:
            magnifier_widget: Экземпляр виджета лупы
        """
        # Получаем настройки лупы из менеджера настроек
        magnifier_settings = {
            "zoom_factor": self.settings_manager.get_setting("magnifier/zoom_factor", 3.0),
            "size": self.settings_manager.get_setting("magnifier/size", 240),
            "grid_enabled": self.settings_manager.get_setting("magnifier/grid_enabled", True),
            "grid_size": self.settings_manager.get_setting("magnifier/grid_size", 20)
        }
        
        # Отправляем сигнал об изменении настроек
        self.magnifier_settings_changed.emit(magnifier_settings)
        
        # Прямое применение настроек к виджету, если он доступен
        if magnifier_widget:
            if hasattr(magnifier_widget, 'set_zoom_factor'):
                magnifier_widget.set_zoom_factor(magnifier_settings["zoom_factor"])
            
            if hasattr(magnifier_widget, 'set_size'):
                magnifier_widget.set_size(magnifier_settings["size"])
            
            if hasattr(magnifier_widget, 'set_grid_enabled'):
                magnifier_widget.set_grid_enabled(magnifier_settings["grid_enabled"])
            
            if hasattr(magnifier_widget, 'set_grid_size'):
                magnifier_widget.set_grid_size(magnifier_settings["grid_size"])
                
        logger.debug("Применены настройки лупы")
    
    def apply_notification_settings(self, tray_app):
        """
        Применяет настройки уведомлений
        
        Args:
            tray_app: Экземпляр приложения в трее
        """
        notification_settings = {
            "show_on_startup": self.settings_manager.get_setting("notifications", "show_on_startup"),
            "show_on_capture": self.settings_manager.get_setting("notifications", "show_on_capture"),
            "show_on_save": self.settings_manager.get_setting("notifications", "show_on_save"),
            "sound_enabled": self.settings_manager.get_setting("notifications", "sound_enabled")
        }
        
        self.notification_settings_changed.emit(notification_settings)
        logger.debug("Применены настройки уведомлений")
    
    def get_file_name(self, base_name: str, extension: Optional[str] = None) -> str:
        """
        Формирует имя файла согласно настройкам
        
        Args:
            base_name: Базовое имя файла
            extension: Расширение файла (если не указано, берется из настроек)
        
        Returns:
            str: Полное имя файла
        """
        # Получаем настройки файлов
        add_timestamp = self.settings_manager.get_setting("files/add_timestamp", True)
        timestamp_format = self.settings_manager.get_setting("files/timestamp_format", "%Y%m%d_%H%M%S")
        image_format = extension or self.settings_manager.get_setting("files/image_format", "png")
        
        # Формируем имя файла
        if add_timestamp:
            timestamp = datetime.datetime.now().strftime(timestamp_format)
            file_name = f"{base_name}_{timestamp}.{image_format}"
        else:
            file_name = f"{base_name}.{image_format}"
        
        # Проверяем необходимость создания подпапок по дате
        if self.settings_manager.get_setting("files/create_subdirs_by_date", False):
            date_dir = datetime.datetime.now().strftime("%Y-%m-%d")
            file_name = os.path.join(date_dir, file_name)
            
            # Создаем подпапку, если её нет
            if not os.path.exists(date_dir):
                os.makedirs(date_dir)
        
        return file_name
    
    def get_image_save_options(self) -> dict:
        """
        Получает параметры сохранения изображения согласно настройкам
        
        Returns:
            dict: Словарь с параметрами сохранения
        """
        image_format = self.settings_manager.get_setting("files/image_format", "png")
        options = {"format": image_format}
        
        if image_format == "jpg":
            quality = self.settings_manager.get_setting("files/jpg_quality", 90)
            options["quality"] = quality
        
        return options
