"""Utilities package for voice control system.

Пакет утилит для системы голосового управления,
включающий логирование, валидацию, аудио помощники и другие инструменты.
"""

from .logger import PerformanceLogger
from .validator import InputValidator, ValidationLevel, ValidationResult
from .audio_helper import AudioHelper, AudioFormat, AudioBackend
from .config_helper import ConfigHelper, ConfigFormat, ConfigSchema, ConfigChangeEvent, ConfigError
from .file_helper import FileHelper, FileOperation, CompressionFormat, FileInfo, FileOperationResult, FileError

__all__ = [
    # Main classes
    'PerformanceLogger',
    'InputValidator', 
    'AudioHelper',
    'ConfigHelper',
    'FileHelper',
    
    # Validator types
    'ValidationLevel',
    'ValidationResult',
    
    # Audio types
    'AudioFormat',
    'AudioBackend',
    
    # Config types
    'ConfigFormat',
    'ConfigSchema',
    'ConfigChangeEvent',
    'ConfigError',
    
    # File types
    'FileOperation',
    'CompressionFormat',
    'FileInfo',
    'FileOperationResult',
    'FileError'
]

__version__ = "1.0.0"
__author__ = "Voice Control Team"
__description__ = "Utilities for voice control system"