"""Модели данных для привязок окон"""

import os
import uuid
import psutil
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum


class IdentificationMethod(Enum):
    """Методы идентификации окон"""
    TITLE_EXACT = "title_exact"  # Точное совпадение заголовка
    TITLE_PARTIAL = "title_partial"  # Частичное совпадение заголовка
    EXECUTABLE_PATH = "executable_path"  # Путь к исполняемому файлу
    EXECUTABLE_NAME = "executable_name"  # Имя исполняемого файла
    WINDOW_CLASS = "window_class"  # Класс окна
    PROCESS_ID = "process_id"  # ID процесса (не рекомендуется для постоянного хранения)
    COMBINED = "combined"  # Комбинированный метод


@dataclass
class SelectedWindowData:
    """Структура для передачи данных о выбранном окне."""
    identifier: 'WindowIdentifier'
    x: int
    y: int
    pos_x: int = 0
    pos_y: int = 0


@dataclass
class WindowIdentifier:
    """Идентификатор окна с различными методами распознавания"""
    
    # Основные методы идентификации
    title: Optional[str] = None
    executable_path: Optional[str] = None
    executable_name: Optional[str] = None
    window_class: Optional[str] = None
    
    # Настройки идентификации
    identification_methods: List[IdentificationMethod] = field(default_factory=lambda: [IdentificationMethod.EXECUTABLE_NAME, IdentificationMethod.TITLE_EXACT])
    
    # Дополнительные параметры
    case_sensitive: bool = False
    use_regex: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать в словарь для сериализации"""
        return {
            'title': self.title,
            'executable_path': self.executable_path,
            'executable_name': self.executable_name,
            'window_class': self.window_class,
            'identification_methods': [method.value for method in self.identification_methods],
            'case_sensitive': self.case_sensitive,
            'use_regex': self.use_regex
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WindowIdentifier':
        """Создать из словаря с поддержкой старого формата"""
        # Поддержка старого формата с primary_method и fallback_methods
        if 'primary_method' in data:
            methods = [IdentificationMethod(data['primary_method'])]
            if 'fallback_methods' in data:
                methods.extend([IdentificationMethod(m) for m in data['fallback_methods']])
            # Удаляем старые ключи, чтобы они не попали в конструктор
            data.pop('primary_method')
            data.pop('fallback_methods', None)
            data['identification_methods'] = [m.value for m in methods]

        return cls(
            title=data.get('title'),
            executable_path=data.get('executable_path'),
            executable_name=data.get('executable_name'),
            window_class=data.get('window_class'),
            identification_methods=[
                IdentificationMethod(method) 
                for method in data.get('identification_methods', [IdentificationMethod.EXECUTABLE_NAME.value, IdentificationMethod.TITLE_EXACT.value])
            ],
            case_sensitive=data.get('case_sensitive', False),
            use_regex=data.get('use_regex', False)
        )
    
    def get_display_name(self) -> str:
        """Получить отображаемое имя для идентификатора"""
        if self.title:
            return self.title
        elif self.executable_name:
            return f"[{self.executable_name}]"
        elif self.executable_path:
            return f"[{os.path.basename(self.executable_path)}]"
        else:
            return "Неизвестное окно"


@dataclass
class WindowBinding:
    """Расширенная модель привязки окна"""
    
    # Уникальный идентификатор
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Идентификатор окна
    window_identifier: WindowIdentifier = field(default_factory=WindowIdentifier)
    
    # Координаты клика
    x: int = 0
    y: int = 0
    
    # Позиция виджета
    pos_x: int = 0
    pos_y: int = 0
    
    # Дополнительные настройки
    enabled: bool = True
    description: Optional[str] = None
    hotkey: Optional[str] = None
    
    # Метаданные
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def __post_init__(self):
        """Инициализация после создания"""
        if self.created_at is None:
            from datetime import datetime
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать в словарь для сериализации"""
        return {
            'id': self.id,
            'window_identifier': self.window_identifier.to_dict(),
            'x': self.x,
            'y': self.y,
            'pos_x': self.pos_x,
            'pos_y': self.pos_y,
            'enabled': self.enabled,
            'description': self.description,
            'hotkey': self.hotkey,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WindowBinding':
        """Создать из словаря"""
        window_identifier_data = data.get('window_identifier', {})
        
        # Поддержка старого формата (только app_name)
        if 'app_name' in data and 'window_identifier' not in data:
            window_identifier_data = {
                'title': data['app_name'],
                'primary_method': 'title_exact'
            }
        
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            window_identifier=WindowIdentifier.from_dict(window_identifier_data),
            x=data.get('x', 0),
            y=data.get('y', 0),
            pos_x=data.get('pos_x', 0),
            pos_y=data.get('pos_y', 0),
            enabled=data.get('enabled', True),
            description=data.get('description'),
            hotkey=data.get('hotkey'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    @classmethod
    def from_legacy_format(cls, data: Dict[str, Any]) -> 'WindowBinding':
        """Создать из старого формата данных"""
        window_identifier = WindowIdentifier(
            title=data.get('app_name', ''),
            primary_method=IdentificationMethod.TITLE_EXACT,
            fallback_methods=[IdentificationMethod.TITLE_PARTIAL]
        )
        
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            window_identifier=window_identifier,
            x=data.get('x', 0),
            y=data.get('y', 0),
            pos_x=data.get('pos_x', 0),
            pos_y=data.get('pos_y', 0)
        )
    
    def get_display_name(self) -> str:
        """Получить отображаемое имя привязки"""
        if self.description:
            return self.description
        return self.window_identifier.get_display_name()
    
    def update_timestamp(self):
        """Обновить временную метку"""
        from datetime import datetime
        self.updated_at = datetime.now().isoformat()