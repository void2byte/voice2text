"""Конфигурация для модуля привязок окон"""

import os
from dataclasses import dataclass
from typing import Tuple


@dataclass
class WidgetConfig:
    """Конфигурация виджетов привязок"""
    default_width: int = 100
    default_height: int = 50
    default_pos_x: int = 50
    default_pos_y: int = 50
    min_size: Tuple[int, int] = (50, 30)
    max_size: Tuple[int, int] = (200, 100)
    opacity: float = 0.8
    always_on_top: bool = True


@dataclass
class ValidationConfig:
    """Конфигурация валидации"""
    min_app_name_length: int = 2
    max_app_name_length: int = 100
    max_coordinate_value: int = 10000
    max_position_offset: int = 5000
    validate_window_existence: bool = True
    validate_screen_bounds: bool = True


@dataclass
class StorageConfig:
    """Конфигурация хранения данных"""
    bindings_file: str = os.path.join("settings", "bindings.json")
    backup_enabled: bool = True
    backup_count: int = 5
    auto_save: bool = True
    save_on_change: bool = True


@dataclass
class UIConfig:
    """Конфигурация пользовательского интерфейса"""
    show_success_messages: bool = True
    show_error_dialogs: bool = True
    show_warning_dialogs: bool = True
    dialog_timeout: int = 5000  # миллисекунды
    auto_close_dialogs: bool = False


@dataclass
class DialogConfig:
    """Конфигурация диалогов"""
    last_identification_method: str = "TITLE_PARTIAL"
    show_all_windows: bool = False
    case_sensitive: bool = False
    use_regex: bool = False
    remember_settings: bool = True


@dataclass
class LoggingConfig:
    """Конфигурация логирования"""
    log_level: str = "INFO"
    log_to_file: bool = True
    log_file: str = os.path.join("logs", "window_binder.log")
    max_log_size: int = 10 * 1024 * 1024  # 10 MB
    backup_count: int = 3
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


@dataclass
class PerformanceConfig:
    """Конфигурация производительности"""
    window_search_timeout: float = 2.0  # секунды
    widget_update_interval: int = 100  # миллисекунды
    batch_operations: bool = True
    lazy_loading: bool = True


class WindowBinderConfig:
    """Главный класс конфигурации"""
    
    def __init__(self):
        self.widget = WidgetConfig()
        self.validation = ValidationConfig()
        self.storage = StorageConfig()
        self.ui = UIConfig()
        self.dialog = DialogConfig()
        self.logging = LoggingConfig()
        self.performance = PerformanceConfig()
    
    def update_from_dict(self, config_dict: dict) -> None:
        """Обновить конфигурацию из словаря"""
        for section_name, section_config in config_dict.items():
            if hasattr(self, section_name):
                section = getattr(self, section_name)
                for key, value in section_config.items():
                    if hasattr(section, key):
                        setattr(section, key, value)
    
    def to_dict(self) -> dict:
        """Преобразовать конфигурацию в словарь"""
        return {
            'widget': self.widget.__dict__,
            'validation': self.validation.__dict__,
            'storage': self.storage.__dict__,
            'ui': self.ui.__dict__,
            'dialog': self.dialog.__dict__,
            'logging': self.logging.__dict__,
            'performance': self.performance.__dict__
        }
    
    def save_to_file(self, file_path: str) -> bool:
        """Сохранить конфигурацию в файл"""
        try:
            import json
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, indent=4, ensure_ascii=False)
            
            return True
        except Exception:
            return False
    
    def load_from_file(self, file_path: str) -> bool:
        """Загрузить конфигурацию из файла"""
        try:
            import json
            
            if not os.path.exists(file_path):
                return False
            
            with open(file_path, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)
            
            self.update_from_dict(config_dict)
            return True
        except Exception:
            return False


# Глобальный экземпляр конфигурации
config = WindowBinderConfig()

# Попытка загрузить конфигурацию из файла
config_file = os.path.join("settings", "window_binder_config.json")
config.load_from_file(config_file)