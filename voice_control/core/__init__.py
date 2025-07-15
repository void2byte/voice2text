"""Core module for voice control functionality."""

"""Ядро модуля голосового управления.

Этот модуль содержит основные компоненты для голосового управления:
- VoiceController - главный контроллер
- DIContainer - контейнер зависимостей
- ErrorHandler - обработчик ошибок
- ProgressManager - менеджер прогресса
- ConfigManager - менеджер конфигурации
"""

from voice_control.core.audio_manager import AudioManager
from voice_control.core.recognition_factory import RecognitionFactory
from voice_control.core.audio_capture_pool import AudioCapturePool
from voice_control.core.progress_manager import ProgressManager
from voice_control.core.voice_recognizer import VoiceRecognizer
from voice_control.core.command_processor import CommandProcessor
from voice_control.core.response_generator import ResponseGenerator

# Новые модули
from voice_control.core.voice_controller import (
    VoiceController,
    VoiceControllerState,
    VoiceControllerMode,
    VoiceControllerConfig,
    VoiceSession,
    VoiceControllerEventType,
    VoiceControllerEvent,
    create_voice_controller
)

from voice_control.core.di_container import (
    DIContainer,
    DIScope,
    ScopeContext,
    LifetimeScope,
    DependencyInfo,
    DIException,
    CircularDependencyException,
    DependencyNotRegisteredException,
    get_container,
    register_singleton,
    register_transient,
    register_scoped,
    register_instance,
    resolve
)

from voice_control.core.error_handler import (
    ErrorHandler,
    BaseErrorHandler,
    LoggingErrorHandler,
    RetryErrorHandler,
    FallbackErrorHandler,
    NotificationErrorHandler,
    ErrorSeverity,
    ErrorCategory,
    ErrorAction,
    ErrorContext,
    ErrorInfo,
    handle_errors,
    get_error_handler
)

from voice_control.core.config import (
    VoiceControlConfig,
    AudioConfig,
    RecognitionConfig,
    TTSConfig,
    CommandConfig,
    SecurityConfig,
    PerformanceConfig,
    UIConfig,
    LoggingConfig,
    ConfigManager,
    AudioFormat,
    RecognitionEngine,
    TTSEngine,
    LogLevel,
    get_config_manager,
    get_config,
    save_config,
    update_config
)

__version__ = "1.0.0"
__author__ = "Voice Control Team"

__all__ = [
    # Существующие модули
    "AudioManager",
    "RecognitionFactory",
    "AudioCapturePool",
    "ProgressManager",
    
    # Voice Controller
    "VoiceController",
    "VoiceControllerState",
    "VoiceControllerMode",
    "VoiceControllerConfig",
    "VoiceSession",
    "VoiceControllerEventType",
    "VoiceControllerEvent",
    "create_voice_controller",
    
    # Dependency Injection
    "DIContainer",
    "DIScope",
    "ScopeContext",
    "LifetimeScope",
    "DependencyInfo",
    "DIException",
    "CircularDependencyException",
    "DependencyNotRegisteredException",
    "injectable",
    "singleton",
    "transient",
    "scoped",
    "auto_register",
    "get_container",
    "register",
    "resolve",
    "create_scope",
    
    # Error Handling
    "ErrorHandler",
    "BaseErrorHandler",
    "LoggingErrorHandler",
    "RetryErrorHandler",
    "FallbackErrorHandler",
    "NotificationErrorHandler",
    "ErrorSeverity",
    "ErrorCategory",
    "ErrorAction",
    "ErrorContext",
    "ErrorInfo",
    "handle_errors",
    "get_error_handler",
    
    # Configuration
    "VoiceControlConfig",
    "AudioConfig",
    "RecognitionConfig",
    "TTSConfig",
    "CommandConfig",
    "SecurityConfig",
    "PerformanceConfig",
    "UIConfig",
    "LoggingConfig",
    "ConfigManager",
    "AudioFormat",
    "RecognitionEngine",
    "TTSEngine",
    "LogLevel",
    "get_config_manager",
    "get_config",
    "save_config",
    "update_config",
]


def initialize_core(config_file: str = None) -> VoiceController:
    """Инициализация ядра голосового управления.
    
    Args:
        config_file: Путь к файлу конфигурации
        
    Returns:
        Инициализированный контроллер голосового управления
    """
    # Загрузка конфигурации
    config_manager = get_config_manager(config_file)
    config = config_manager.get_config()
    
    # Создание контроллера
    controller = create_voice_controller(config)
    
    return controller


def get_version() -> str:
    """Получение версии модуля."""
    return __version__