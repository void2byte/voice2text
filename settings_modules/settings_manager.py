"""
Модуль для управления настройками приложения.
Обеспечивает загрузку и сохранение настроек в JSON-формате.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, Type

# Настройка логгера
logger = logging.getLogger(__name__)

# Путь к файлу настроек
DEFAULT_SETTINGS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")

# Настройки по умолчанию
DEFAULT_SETTINGS = {
    "hotkeys": {
        "start_selection": "Ctrl+Alt+S",
        "minimize_dialog": "S",
        "voice_annotation": "V"
    },
    "selection": {
        "min_width": 10,
        "min_height": 10,
        "darkening_factor": 0.5  # 0 - без затемнения, 1 - полностью темный
    },
    "magnifier": {
        "enabled": True,
        "zoom_factor": 2.0,
        "size": 200,
        "grid_enabled": True
    },
    "voice_annotation": {
        "max_duration": 60,  # Максимальная длительность аудио в секундах
        "auto_recognition": True,  # Автоматическое распознавание речи
        "audio_quality": "medium"  # Качество записи (low, medium, high)
    },
    "notifications": {
        "show_on_startup": True,  # Показывать уведомление при запуске
        "show_on_capture": True,  # Показывать уведомление при захвате экрана
        "show_on_save": True,  # Показывать уведомление при сохранении
        "sound_enabled": True  # Включить звуковые уведомления
    },
    "files": {
        "add_timestamp": True,  # Добавлять время в имя файла
        "timestamp_format": "%Y%m%d_%H%M%S",  # Формат времени
        "image_format": "png",  # Формат изображений (png, jpg)
        "jpg_quality": 90,  # Качество JPEG при сохранении (0-100)
        "create_subdirs_by_date": False  # Создавать подпапки по дате
    },
    "ui": {
        "highlight_color": "#FF0000",
        "selection_border_width": 2,
        "auto_save_path": "",
        "remember_last_save_location": True
    }
}


class SettingsManager:
    """Класс для управления настройками приложения"""
    
    def __init__(self, settings_path: str = DEFAULT_SETTINGS_PATH):
        """
        Инициализация менеджера настроек
        
        Args:
            settings_path: Путь к файлу настроек
        """
        self.settings_path = settings_path
        self.settings = self.load_settings()
    
    def load_settings(self) -> Dict[str, Any]:
        """
        Загружает настройки из файла. Если файл не существует, создает его с настройками по умолчанию.
        
        Returns:
            Dict[str, Any]: Словарь с настройками
        """
        try:
            if os.path.exists(self.settings_path):
                with open(self.settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                # Обновляем настройки, если в файле отсутствуют какие-то ключи из DEFAULT_SETTINGS
                self._update_missing_settings(settings)
                logger.info(f"Настройки успешно загружены из {self.settings_path}")
                return settings
            else:
                # Файл не существует, создаем его с настройками по умолчанию
                self.save_settings(DEFAULT_SETTINGS)
                logger.info(f"Создан новый файл настроек по пути {self.settings_path}")
                return DEFAULT_SETTINGS.copy()
        except Exception as e:
            logger.error(f"Ошибка при загрузке настроек: {e}")
            return DEFAULT_SETTINGS.copy()
    
    def _update_missing_settings(self, settings: Dict[str, Any]) -> None:
        """
        Обновляет настройки недостающими ключами из DEFAULT_SETTINGS
        
        Args:
            settings: Текущие настройки
        """
        modified = False
        
        def update_dict(target, source):
            nonlocal modified
            for key, value in source.items():
                if key not in target:
                    target[key] = value
                    modified = True
                elif isinstance(value, dict) and isinstance(target[key], dict):
                    update_dict(target[key], value)
        
        update_dict(settings, DEFAULT_SETTINGS)
        
        if modified:
            self.save_settings(settings)
            logger.info("Настройки обновлены недостающими значениями по умолчанию")
    
    def update_settings(self, new_settings: Dict[str, Any]) -> bool:
        """
        Обновляет текущие настройки новыми значениями
        
        Args:
            new_settings: Словарь с новыми значениями настроек
        
        Returns:
            bool: True если обновление прошло успешно, иначе False
        """
        try:
            # Загружаем текущие настройки, если они не загружены
            if not self.settings:
                self.load_settings()
            
            # Рекурсивно обновляем текущие настройки новыми значениями
            def update_dict(target, source):
                for key, value in source.items():
                    if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                        update_dict(target[key], value)
                    else:
                        target[key] = value
            
            update_dict(self.settings, new_settings)
            logger.info(f"Обновление настроек: {new_settings}")
            
            # Сохраняем обновленные настройки
            return self.save_settings(self.settings)
        except Exception as e:
            logger.error(f"Ошибка при обновлении настроек: {e}")
            return False
    
    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """
        Сохраняет настройки в файл
        
        Args:
            settings: Словарь с настройками
        
        Returns:
            bool: True если сохранение прошло успешно, иначе False
        """
        try:
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
            
            self.settings = settings
            logger.info(f"Настройки успешно сохранены в {self.settings_path}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении настроек: {e}")
            return False

    def get_setting(self, key: str, default: Optional[Any] = None, expected_type: Optional[Type[Any]] = None) -> Optional[Any]:
        """
        Получает значение настройки по ключу.
        Ключ может быть вложенным, разделенным '/'.

        Args:
            key: Ключ настройки (например, "voice_annotation/max_duration").
            default: Значение по умолчанию, если ключ не найден.
            expected_type: Ожидаемый тип значения. Если указан, будет попытка преобразования.

        Returns:
            Значение настройки или значение по умолчанию.
        """
        try:
            keys = key.split('/')
            value = self.settings
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    logger.warning(f"Ключ '{key}' не найден в настройках. Используется значение по умолчанию: {default}")
                    return default
            
            if expected_type is not None:
                try:
                    if expected_type is bool and isinstance(value, str):
                        if value.lower() == 'true':
                            return True 
                        elif value.lower() == 'false':
                            return False 
                        else:
                            raise ValueError(f"Невозможно преобразовать строку '{value}' в bool для ключа '{key}'")
                    return expected_type(value)
                except (ValueError, TypeError) as e:
                    logger.error(f"Ошибка преобразования типа для ключа '{key}': значение '{value}' не может быть преобразовано в {expected_type}. Ошибка: {e}. Используется значение по умолчанию: {default}")
                    return default
            return value 
        except Exception as e:
            logger.error(f"Общая ошибка при получении настройки '{key}': {e}. Используется значение по умолчанию: {default}")
            return default

    def get_all_settings(self) -> Dict[str, Any]:
        """Возвращает все текущие настройки."""
        return self.settings.copy()

    def set_setting(self, key: str, value: Any) -> bool:
        """
        Устанавливает значение для указанной настройки и сохраняет все настройки.
        Ключ может быть вложенным, разделенным '/'.

        Args:
            key: Ключ настройки (например, "voice_annotation/max_duration").
            value: Новое значение для настройки.

        Returns:
            bool: True, если настройка успешно установлена и сохранена, иначе False.
        """
        try:
            keys = key.split('/')
            current_level = self.settings
            for i, k_part in enumerate(keys[:-1]):
                if k_part not in current_level or not isinstance(current_level[k_part], dict):
                    current_level[k_part] = {}  # Создаем вложенный словарь, если его нет
                current_level = current_level[k_part]
            
            current_level[keys[-1]] = value
            
            return self.save_settings(self.settings)
        except Exception as e:
            logger.error(f"Ошибка при установке настройки '{key}': {e}")
            return False
    
    def reset_to_defaults(self) -> bool:
        """
        Сбрасывает все настройки к значениям по умолчанию
        
        Returns:
            bool: True если сброс прошел успешно, иначе False
        """
        return self.save_settings(DEFAULT_SETTINGS.copy())
