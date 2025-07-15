"""Configuration Helper for voice control system.

Помощник для управления конфигурацией системы голосового управления
с поддержкой различных форматов, валидации и динамического обновления.
"""

import os
import json
import yaml
import toml
from typing import Any, Dict, List, Optional, Union, Callable, Type
from pathlib import Path
from dataclasses import dataclass, asdict, fields
from enum import Enum
import threading
import time
from copy import deepcopy
import configparser


class ConfigFormat(Enum):
    """Поддерживаемые форматы конфигурации."""
    JSON = "json"
    YAML = "yaml"
    TOML = "toml"
    INI = "ini"
    ENV = "env"


class ConfigError(Exception):
    """Исключение конфигурации."""
    pass


@dataclass
class ConfigSchema:
    """Схема конфигурации."""
    name: str
    type: Type
    default: Any = None
    required: bool = False
    description: str = ""
    validator: Optional[Callable[[Any], bool]] = None
    choices: Optional[List[Any]] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None


@dataclass
class ConfigChangeEvent:
    """Событие изменения конфигурации."""
    key: str
    old_value: Any
    new_value: Any
    timestamp: float
    source: str


class ConfigHelper:
    """Помощник для управления конфигурацией системы.
    
    Обеспечивает загрузку, сохранение, валидацию и мониторинг
    конфигурации с поддержкой различных форматов.
    """
    
    def __init__(self, 
                 config_path: Optional[str] = None,
                 format: Optional[ConfigFormat] = None,
                 auto_reload: bool = False,
                 backup_count: int = 5):
        """Инициализация помощника конфигурации.
        
        Args:
            config_path: Путь к файлу конфигурации
            format: Формат конфигурации
            auto_reload: Автоматическая перезагрузка при изменении файла
            backup_count: Количество резервных копий
        """
        self._config_path = config_path
        self._format = format
        self._auto_reload = auto_reload
        self._backup_count = backup_count
        
        # Данные конфигурации
        self._config_data: Dict[str, Any] = {}
        self._schema: Dict[str, ConfigSchema] = {}
        self._defaults: Dict[str, Any] = {}
        
        # Мониторинг изменений
        self._change_listeners: List[Callable[[ConfigChangeEvent], None]] = []
        self._last_modified: Optional[float] = None
        self._lock = threading.RLock()
        
        # Автоматическое определение формата
        if self._config_path and not self._format:
            self._format = self._detect_format(self._config_path)
        
        # Загрузка конфигурации
        if self._config_path and os.path.exists(self._config_path):
            self.load_config()
        
        # Запуск мониторинга файла
        if self._auto_reload and self._config_path:
            self._start_file_monitoring()
    
    def _detect_format(self, file_path: str) -> ConfigFormat:
        """Автоматическое определение формата конфигурации.
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            Формат конфигурации
        """
        ext = Path(file_path).suffix.lower()
        
        format_mapping = {
            '.json': ConfigFormat.JSON,
            '.yaml': ConfigFormat.YAML,
            '.yml': ConfigFormat.YAML,
            '.toml': ConfigFormat.TOML,
            '.ini': ConfigFormat.INI,
            '.cfg': ConfigFormat.INI,
            '.conf': ConfigFormat.INI,
            '.env': ConfigFormat.ENV
        }
        
        return format_mapping.get(ext, ConfigFormat.JSON)
    
    def _start_file_monitoring(self) -> None:
        """Запуск мониторинга изменений файла конфигурации."""
        def monitor_file():
            while True:
                try:
                    if os.path.exists(self._config_path):
                        current_modified = os.path.getmtime(self._config_path)
                        
                        if (self._last_modified is not None and 
                            current_modified > self._last_modified):
                            
                            # Файл изменился, перезагружаем конфигурацию
                            old_config = deepcopy(self._config_data)
                            self.load_config()
                            
                            # Уведомление о изменениях
                            self._notify_changes(old_config, self._config_data, "file_reload")
                        
                        self._last_modified = current_modified
                    
                    time.sleep(1)  # Проверка каждую секунду
                    
                except Exception:
                    time.sleep(5)  # При ошибке ждем дольше
        
        monitor_thread = threading.Thread(target=monitor_file, daemon=True)
        monitor_thread.start()
    
    def define_schema(self, schema: Dict[str, ConfigSchema]) -> None:
        """Определение схемы конфигурации.
        
        Args:
            schema: Словарь схем конфигурации
        """
        with self._lock:
            self._schema.update(schema)
            
            # Обновление значений по умолчанию
            for key, config_schema in schema.items():
                if config_schema.default is not None:
                    self._defaults[key] = config_schema.default
    
    def add_schema_field(self, key: str, schema: ConfigSchema) -> None:
        """Добавление поля схемы.
        
        Args:
            key: Ключ конфигурации
            schema: Схема поля
        """
        with self._lock:
            self._schema[key] = schema
            if schema.default is not None:
                self._defaults[key] = schema.default
    
    def load_config(self, file_path: Optional[str] = None) -> None:
        """Загрузка конфигурации из файла.
        
        Args:
            file_path: Путь к файлу (если не указан, используется self._config_path)
        """
        config_file = file_path or self._config_path
        
        if not config_file:
            raise ConfigError("No configuration file specified")
        
        if not os.path.exists(config_file):
            raise ConfigError(f"Configuration file not found: {config_file}")
        
        try:
            with self._lock:
                # Определение формата
                format_to_use = self._format or self._detect_format(config_file)
                
                # Загрузка данных
                with open(config_file, 'r', encoding='utf-8') as f:
                    if format_to_use == ConfigFormat.JSON:
                        data = json.load(f)
                    elif format_to_use == ConfigFormat.YAML:
                        data = yaml.safe_load(f)
                    elif format_to_use == ConfigFormat.TOML:
                        data = toml.load(f)
                    elif format_to_use == ConfigFormat.INI:
                        parser = configparser.ConfigParser()
                        parser.read(config_file)
                        data = {section: dict(parser[section]) for section in parser.sections()}
                    elif format_to_use == ConfigFormat.ENV:
                        data = self._load_env_file(config_file)
                    else:
                        raise ConfigError(f"Unsupported format: {format_to_use}")
                
                # Применение значений по умолчанию
                merged_data = deepcopy(self._defaults)
                self._deep_merge(merged_data, data)
                
                # Валидация
                self._validate_config(merged_data)
                
                # Обновление конфигурации
                self._config_data = merged_data
                
                # Обновление времени модификации
                self._last_modified = os.path.getmtime(config_file)
                
        except Exception as e:
            raise ConfigError(f"Failed to load configuration: {str(e)}")
    
    def _load_env_file(self, file_path: str) -> Dict[str, Any]:
        """Загрузка переменных окружения из .env файла.
        
        Args:
            file_path: Путь к .env файлу
            
        Returns:
            Словарь переменных
        """
        data = {}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"\'')
                        
                        # Попытка конвертации типов
                        if value.lower() in ('true', 'false'):
                            value = value.lower() == 'true'
                        elif value.isdigit():
                            value = int(value)
                        elif value.replace('.', '').isdigit():
                            value = float(value)
                        
                        data[key] = value
        
        return data
    
    def save_config(self, file_path: Optional[str] = None, 
                   create_backup: bool = True) -> None:
        """Сохранение конфигурации в файл.
        
        Args:
            file_path: Путь к файлу (если не указан, используется self._config_path)
            create_backup: Создать резервную копию
        """
        config_file = file_path or self._config_path
        
        if not config_file:
            raise ConfigError("No configuration file specified")
        
        try:
            with self._lock:
                # Создание резервной копии
                if create_backup and os.path.exists(config_file):
                    self._create_backup(config_file)
                
                # Создание директории если не существует
                os.makedirs(os.path.dirname(config_file), exist_ok=True)
                
                # Определение формата
                format_to_use = self._format or self._detect_format(config_file)
                
                # Сохранение данных
                with open(config_file, 'w', encoding='utf-8') as f:
                    if format_to_use == ConfigFormat.JSON:
                        json.dump(self._config_data, f, indent=2, ensure_ascii=False)
                    elif format_to_use == ConfigFormat.YAML:
                        yaml.dump(self._config_data, f, default_flow_style=False, allow_unicode=True)
                    elif format_to_use == ConfigFormat.TOML:
                        toml.dump(self._config_data, f)
                    elif format_to_use == ConfigFormat.INI:
                        parser = configparser.ConfigParser()
                        for section, values in self._config_data.items():
                            if isinstance(values, dict):
                                parser[section] = {k: str(v) for k, v in values.items()}
                        parser.write(f)
                    elif format_to_use == ConfigFormat.ENV:
                        self._save_env_file(f, self._config_data)
                    else:
                        raise ConfigError(f"Unsupported format: {format_to_use}")
                
                # Обновление времени модификации
                self._last_modified = os.path.getmtime(config_file)
                
        except Exception as e:
            raise ConfigError(f"Failed to save configuration: {str(e)}")
    
    def _save_env_file(self, file_handle, data: Dict[str, Any]) -> None:
        """Сохранение данных в формате .env файла.
        
        Args:
            file_handle: Файловый дескриптор
            data: Данные для сохранения
        """
        def write_value(key: str, value: Any, prefix: str = ""):
            full_key = f"{prefix}{key}".upper()
            
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    write_value(sub_key, sub_value, f"{full_key}_")
            else:
                if isinstance(value, str) and (' ' in value or '=' in value):
                    value = f'"{value}"'
                file_handle.write(f"{full_key}={value}\n")
        
        for key, value in data.items():
            write_value(key, value)
    
    def _create_backup(self, file_path: str) -> None:
        """Создание резервной копии файла конфигурации.
        
        Args:
            file_path: Путь к файлу
        """
        try:
            backup_dir = Path(file_path).parent / "backups"
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = int(time.time())
            backup_name = f"{Path(file_path).stem}_{timestamp}{Path(file_path).suffix}"
            backup_path = backup_dir / backup_name
            
            # Копирование файла
            import shutil
            shutil.copy2(file_path, backup_path)
            
            # Удаление старых резервных копий
            self._cleanup_old_backups(backup_dir, Path(file_path).stem)
            
        except Exception:
            pass  # Игнорируем ошибки создания резервных копий
    
    def _cleanup_old_backups(self, backup_dir: Path, file_stem: str) -> None:
        """Очистка старых резервных копий.
        
        Args:
            backup_dir: Директория резервных копий
            file_stem: Базовое имя файла
        """
        try:
            backups = []
            for backup_file in backup_dir.glob(f"{file_stem}_*"):
                if backup_file.is_file():
                    backups.append((backup_file.stat().st_mtime, backup_file))
            
            # Сортировка по времени (новые первыми)
            backups.sort(reverse=True)
            
            # Удаление старых копий
            for _, backup_file in backups[self._backup_count:]:
                backup_file.unlink()
                
        except Exception:
            pass
    
    def _validate_config(self, data: Dict[str, Any]) -> None:
        """Валидация конфигурации по схеме.
        
        Args:
            data: Данные для валидации
        """
        errors = []
        
        # Проверка обязательных полей
        for key, schema in self._schema.items():
            if schema.required and key not in data:
                errors.append(f"Required field '{key}' is missing")
                continue
            
            if key in data:
                value = data[key]
                
                # Проверка типа
                if not isinstance(value, schema.type):
                    try:
                        # Попытка конвертации
                        data[key] = schema.type(value)
                        value = data[key]
                    except (ValueError, TypeError):
                        errors.append(f"Field '{key}' must be of type {schema.type.__name__}")
                        continue
                
                # Проверка выбора из списка
                if schema.choices and value not in schema.choices:
                    errors.append(f"Field '{key}' must be one of: {schema.choices}")
                
                # Проверка диапазона
                if isinstance(value, (int, float)):
                    if schema.min_value is not None and value < schema.min_value:
                        errors.append(f"Field '{key}' must be >= {schema.min_value}")
                    
                    if schema.max_value is not None and value > schema.max_value:
                        errors.append(f"Field '{key}' must be <= {schema.max_value}")
                
                # Пользовательский валидатор
                if schema.validator and not schema.validator(value):
                    errors.append(f"Field '{key}' failed custom validation")
        
        if errors:
            raise ConfigError(f"Configuration validation failed: {'; '.join(errors)}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Получение значения конфигурации.
        
        Args:
            key: Ключ конфигурации (поддерживает точечную нотацию)
            default: Значение по умолчанию
            
        Returns:
            Значение конфигурации
        """
        with self._lock:
            return self._get_nested_value(self._config_data, key, default)
    
    def set(self, key: str, value: Any, source: str = "manual") -> None:
        """Установка значения конфигурации.
        
        Args:
            key: Ключ конфигурации (поддерживает точечную нотацию)
            value: Новое значение
            source: Источник изменения
        """
        with self._lock:
            old_value = self._get_nested_value(self._config_data, key)
            self._set_nested_value(self._config_data, key, value)
            
            # Валидация после изменения
            try:
                self._validate_config(self._config_data)
            except ConfigError:
                # Откат изменений при ошибке валидации
                self._set_nested_value(self._config_data, key, old_value)
                raise
            
            # Уведомление об изменении
            event = ConfigChangeEvent(
                key=key,
                old_value=old_value,
                new_value=value,
                timestamp=time.time(),
                source=source
            )
            
            for listener in self._change_listeners:
                try:
                    listener(event)
                except Exception:
                    pass
    
    def _get_nested_value(self, data: Dict[str, Any], key: str, default: Any = None) -> Any:
        """Получение вложенного значения по точечной нотации.
        
        Args:
            data: Данные
            key: Ключ (может содержать точки)
            default: Значение по умолчанию
            
        Returns:
            Значение
        """
        keys = key.split('.')
        current = data
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        
        return current
    
    def _set_nested_value(self, data: Dict[str, Any], key: str, value: Any) -> None:
        """Установка вложенного значения по точечной нотации.
        
        Args:
            data: Данные
            key: Ключ (может содержать точки)
            value: Значение
        """
        keys = key.split('.')
        current = data
        
        for k in keys[:-1]:
            if k not in current or not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def _deep_merge(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """Глубокое слияние словарей.
        
        Args:
            target: Целевой словарь
            source: Исходный словарь
        """
        for key, value in source.items():
            if (key in target and 
                isinstance(target[key], dict) and 
                isinstance(value, dict)):
                self._deep_merge(target[key], value)
            else:
                target[key] = value
    
    def _notify_changes(self, old_config: Dict[str, Any], 
                       new_config: Dict[str, Any], 
                       source: str) -> None:
        """Уведомление об изменениях конфигурации.
        
        Args:
            old_config: Старая конфигурация
            new_config: Новая конфигурация
            source: Источник изменений
        """
        def find_changes(old_data: Dict[str, Any], 
                        new_data: Dict[str, Any], 
                        prefix: str = ""):
            changes = []
            
            # Проверка измененных и новых ключей
            for key, new_value in new_data.items():
                full_key = f"{prefix}.{key}" if prefix else key
                old_value = old_data.get(key)
                
                if isinstance(new_value, dict) and isinstance(old_value, dict):
                    changes.extend(find_changes(old_value, new_value, full_key))
                elif old_value != new_value:
                    changes.append(ConfigChangeEvent(
                        key=full_key,
                        old_value=old_value,
                        new_value=new_value,
                        timestamp=time.time(),
                        source=source
                    ))
            
            # Проверка удаленных ключей
            for key, old_value in old_data.items():
                if key not in new_data:
                    full_key = f"{prefix}.{key}" if prefix else key
                    changes.append(ConfigChangeEvent(
                        key=full_key,
                        old_value=old_value,
                        new_value=None,
                        timestamp=time.time(),
                        source=source
                    ))
            
            return changes
        
        changes = find_changes(old_config, new_config)
        
        for change in changes:
            for listener in self._change_listeners:
                try:
                    listener(change)
                except Exception:
                    pass
    
    def add_change_listener(self, listener: Callable[[ConfigChangeEvent], None]) -> None:
        """Добавление слушателя изменений конфигурации.
        
        Args:
            listener: Функция-слушатель
        """
        with self._lock:
            self._change_listeners.append(listener)
    
    def remove_change_listener(self, listener: Callable[[ConfigChangeEvent], None]) -> None:
        """Удаление слушателя изменений конфигурации.
        
        Args:
            listener: Функция-слушатель
        """
        with self._lock:
            if listener in self._change_listeners:
                self._change_listeners.remove(listener)
    
    def get_all(self) -> Dict[str, Any]:
        """Получение всей конфигурации.
        
        Returns:
            Копия всей конфигурации
        """
        with self._lock:
            return deepcopy(self._config_data)
    
    def update(self, data: Dict[str, Any], source: str = "bulk_update") -> None:
        """Массовое обновление конфигурации.
        
        Args:
            data: Новые данные
            source: Источник изменений
        """
        with self._lock:
            old_config = deepcopy(self._config_data)
            
            # Слияние данных
            self._deep_merge(self._config_data, data)
            
            # Валидация
            try:
                self._validate_config(self._config_data)
            except ConfigError:
                # Откат при ошибке
                self._config_data = old_config
                raise
            
            # Уведомление об изменениях
            self._notify_changes(old_config, self._config_data, source)
    
    def reset_to_defaults(self) -> None:
        """Сброс конфигурации к значениям по умолчанию."""
        with self._lock:
            old_config = deepcopy(self._config_data)
            self._config_data = deepcopy(self._defaults)
            self._notify_changes(old_config, self._config_data, "reset_defaults")
    
    def export_config(self, file_path: str, format: Optional[ConfigFormat] = None) -> None:
        """Экспорт конфигурации в файл.
        
        Args:
            file_path: Путь к файлу
            format: Формат экспорта
        """
        export_format = format or self._detect_format(file_path)
        
        # Временно изменяем формат для сохранения
        original_format = self._format
        original_path = self._config_path
        
        try:
            self._format = export_format
            self._config_path = file_path
            self.save_config(create_backup=False)
        finally:
            self._format = original_format
            self._config_path = original_path
    
    def get_schema_info(self) -> Dict[str, Dict[str, Any]]:
        """Получение информации о схеме конфигурации.
        
        Returns:
            Информация о схеме
        """
        with self._lock:
            schema_info = {}
            
            for key, schema in self._schema.items():
                schema_info[key] = {
                    'type': schema.type.__name__,
                    'default': schema.default,
                    'required': schema.required,
                    'description': schema.description,
                    'choices': schema.choices,
                    'min_value': schema.min_value,
                    'max_value': schema.max_value,
                    'current_value': self.get(key)
                }
            
            return schema_info