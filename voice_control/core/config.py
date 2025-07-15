"""Конфигурация модуля голосового управления."""

import os
import json
import logging
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path


class AudioFormat(Enum):
    """Форматы аудио."""
    WAV = "wav"
    MP3 = "mp3"
    FLAC = "flac"
    OGG = "ogg"


class RecognitionEngine(Enum):
    """Движки распознавания речи."""
    GOOGLE = "google"
    AZURE = "azure"
    AWS = "aws"
    YANDEX = "yandex"
    WHISPER = "whisper"
    VOSK = "vosk"


class TTSEngine(Enum):
    """Движки синтеза речи."""
    GOOGLE = "google"
    AZURE = "azure"
    AWS = "aws"
    YANDEX = "yandex"
    ESPEAK = "espeak"
    FESTIVAL = "festival"


class LogLevel(Enum):
    """Уровни логирования."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class AudioConfig:
    """Конфигурация аудио."""
    sample_rate: int = 16000
    channels: int = 1
    chunk_size: int = 1024
    format: AudioFormat = AudioFormat.WAV
    input_device_index: Optional[int] = None
    output_device_index: Optional[int] = None
    noise_reduction: bool = True
    auto_gain_control: bool = True
    echo_cancellation: bool = True
    volume_threshold: float = 0.01
    silence_timeout: float = 2.0
    max_recording_duration: float = 30.0
    buffer_size: int = 4096


@dataclass
class RecognitionConfig:
    """Конфигурация распознавания речи."""
    engine: RecognitionEngine = RecognitionEngine.GOOGLE
    language: str = "ru-RU"
    alternative_languages: List[str] = field(default_factory=lambda: ["en-US"])
    confidence_threshold: float = 0.7
    timeout: float = 5.0
    phrase_time_limit: Optional[float] = None
    energy_threshold: int = 300
    dynamic_energy_threshold: bool = True
    pause_threshold: float = 0.8
    non_speaking_duration: float = 0.5
    api_key: Optional[str] = None
    api_url: Optional[str] = None
    model_path: Optional[str] = None
    enable_profanity_filter: bool = False
    enable_automatic_punctuation: bool = True
    enable_word_time_offsets: bool = False
    max_alternatives: int = 1


@dataclass
class TTSConfig:
    """Конфигурация синтеза речи."""
    engine: TTSEngine = TTSEngine.GOOGLE
    language: str = "ru"
    voice: Optional[str] = None
    speed: float = 1.0
    pitch: float = 0.0
    volume: float = 1.0
    api_key: Optional[str] = None
    api_url: Optional[str] = None
    cache_enabled: bool = True
    cache_dir: str = "cache/tts"
    max_cache_size: int = 100  # MB
    audio_format: AudioFormat = AudioFormat.MP3
    quality: str = "high"


@dataclass
class CommandConfig:
    """Конфигурация обработки команд."""
    enable_fuzzy_matching: bool = True
    fuzzy_threshold: float = 0.8
    enable_context_awareness: bool = True
    max_command_history: int = 100
    command_timeout: float = 30.0
    enable_confirmation: bool = False
    confirmation_threshold: float = 0.9
    enable_undo: bool = True
    max_undo_stack: int = 10
    enable_macros: bool = True
    custom_commands_file: Optional[str] = None
    enable_learning: bool = True
    learning_threshold: int = 3


@dataclass
class SecurityConfig:
    """Конфигурация безопасности."""
    enable_user_authentication: bool = False
    enable_voice_biometrics: bool = False
    enable_command_filtering: bool = True
    allowed_commands: Optional[List[str]] = None
    blocked_commands: Optional[List[str]] = None
    enable_audit_log: bool = True
    audit_log_file: str = "logs/audit.log"
    max_failed_attempts: int = 3
    lockout_duration: int = 300  # секунды
    enable_encryption: bool = False
    encryption_key: Optional[str] = None


@dataclass
class PerformanceConfig:
    """Конфигурация производительности."""
    enable_multithreading: bool = True
    max_worker_threads: int = 4
    enable_gpu_acceleration: bool = False
    gpu_device_id: int = 0
    enable_caching: bool = True
    cache_size: int = 50  # MB
    enable_preloading: bool = True
    preload_models: bool = False
    memory_limit: Optional[int] = None  # MB
    cpu_limit: Optional[float] = None  # процент
    enable_profiling: bool = False
    profiling_output_dir: str = "profiling"


@dataclass
class UIConfig:
    """Конфигурация пользовательского интерфейса."""
    enable_visual_feedback: bool = True
    enable_audio_feedback: bool = True
    enable_haptic_feedback: bool = False
    show_confidence_scores: bool = True
    show_processing_time: bool = False
    enable_waveform_display: bool = True
    enable_command_suggestions: bool = True
    theme: str = "default"
    language: str = "ru"
    font_size: int = 12
    enable_notifications: bool = True
    notification_duration: int = 3000  # миллисекунды


@dataclass
class LoggingConfig:
    """Конфигурация логирования."""
    level: LogLevel = LogLevel.INFO
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = "logs/voice_control.log"
    max_file_size: int = 10  # MB
    backup_count: int = 5
    enable_console_output: bool = True
    enable_file_output: bool = True
    enable_structured_logging: bool = False
    log_audio_data: bool = False
    log_recognition_results: bool = True
    log_command_execution: bool = True
    log_performance_metrics: bool = True


@dataclass
class VoiceControlConfig:
    """Главная конфигурация модуля голосового управления."""
    # Основные настройки
    enabled: bool = True
    debug_mode: bool = False
    config_version: str = "1.0.0"
    
    # Конфигурации компонентов
    audio: AudioConfig = field(default_factory=AudioConfig)
    recognition: RecognitionConfig = field(default_factory=RecognitionConfig)
    tts: TTSConfig = field(default_factory=TTSConfig)
    commands: CommandConfig = field(default_factory=CommandConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    # Дополнительные настройки
    data_dir: str = "data"
    temp_dir: str = "temp"
    plugins_dir: str = "plugins"
    models_dir: str = "models"
    
    # Настройки автосохранения
    auto_save_config: bool = True
    auto_save_interval: int = 300  # секунды
    
    # Экспериментальные функции
    experimental_features: Dict[str, bool] = field(default_factory=dict)
    
    # Пользовательские настройки
    custom_settings: Dict[str, Any] = field(default_factory=dict)


class ConfigManager:
    """Менеджер конфигурации."""
    
    def __init__(self, config_file: Optional[Union[str, Path]] = None):
        self.config_file = Path(config_file) if config_file else Path("config/voice_control.json")
        self.logger = logging.getLogger(self.__class__.__name__)
        self._config: Optional[VoiceControlConfig] = None
        self._watchers: List[callable] = []
        
        # Создание директории конфигурации
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
    
    def load_config(self) -> VoiceControlConfig:
        """Загрузка конфигурации из файла."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Преобразование данных в конфигурацию
                self._config = self._dict_to_config(data)
                self.logger.info(f"Конфигурация загружена из {self.config_file}")
            else:
                # Создание конфигурации по умолчанию
                self._config = VoiceControlConfig()
                self.save_config()
                self.logger.info("Создана конфигурация по умолчанию")
            
            # Применение переменных окружения
            self._apply_environment_variables()
            
            return self._config
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки конфигурации: {e}")
            # Возврат конфигурации по умолчанию в случае ошибки
            self._config = VoiceControlConfig()
            return self._config
    
    def save_config(self, config: Optional[VoiceControlConfig] = None) -> bool:
        """Сохранение конфигурации в файл."""
        try:
            config_to_save = config or self._config
            if not config_to_save:
                return False
            
            # Преобразование конфигурации в словарь
            data = self._config_to_dict(config_to_save)
            
            # Создание резервной копии
            if self.config_file.exists():
                backup_file = self.config_file.with_suffix('.json.bak')
                self.config_file.rename(backup_file)
            
            # Сохранение конфигурации
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Конфигурация сохранена в {self.config_file}")
            
            # Уведомление наблюдателей
            self._notify_watchers()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка сохранения конфигурации: {e}")
            return False
    
    def get_config(self) -> VoiceControlConfig:
        """Получение текущей конфигурации."""
        if self._config is None:
            return self.load_config()
        return self._config
    
    def update_config(self, updates: Dict[str, Any]) -> bool:
        """Обновление конфигурации."""
        try:
            if self._config is None:
                self.load_config()
            
            # Применение обновлений
            self._apply_updates(self._config, updates)
            
            # Сохранение обновленной конфигурации
            return self.save_config()
            
        except Exception as e:
            self.logger.error(f"Ошибка обновления конфигурации: {e}")
            return False
    
    def reset_to_defaults(self) -> bool:
        """Сброс конфигурации к значениям по умолчанию."""
        try:
            self._config = VoiceControlConfig()
            return self.save_config()
        except Exception as e:
            self.logger.error(f"Ошибка сброса конфигурации: {e}")
            return False
    
    def validate_config(self, config: Optional[VoiceControlConfig] = None) -> List[str]:
        """Валидация конфигурации."""
        config_to_validate = config or self._config
        if not config_to_validate:
            return ["Конфигурация не загружена"]
        
        errors = []
        
        # Валидация аудио настроек
        if config_to_validate.audio.sample_rate <= 0:
            errors.append("Частота дискретизации должна быть положительной")
        
        if config_to_validate.audio.channels not in [1, 2]:
            errors.append("Количество каналов должно быть 1 или 2")
        
        # Валидация распознавания
        if config_to_validate.recognition.confidence_threshold < 0 or config_to_validate.recognition.confidence_threshold > 1:
            errors.append("Порог уверенности должен быть от 0 до 1")
        
        # Валидация TTS
        if config_to_validate.tts.speed <= 0:
            errors.append("Скорость речи должна быть положительной")
        
        if config_to_validate.tts.volume < 0 or config_to_validate.tts.volume > 1:
            errors.append("Громкость должна быть от 0 до 1")
        
        # Валидация производительности
        if config_to_validate.performance.max_worker_threads <= 0:
            errors.append("Количество рабочих потоков должно быть положительным")
        
        return errors
    
    def add_watcher(self, callback: callable):
        """Добавление наблюдателя за изменениями конфигурации."""
        self._watchers.append(callback)
    
    def remove_watcher(self, callback: callable):
        """Удаление наблюдателя."""
        if callback in self._watchers:
            self._watchers.remove(callback)
    
    def _notify_watchers(self):
        """Уведомление наблюдателей об изменениях."""
        for watcher in self._watchers:
            try:
                watcher(self._config)
            except Exception as e:
                self.logger.error(f"Ошибка в наблюдателе конфигурации: {e}")
    
    def _dict_to_config(self, data: Dict[str, Any]) -> VoiceControlConfig:
        """Преобразование словаря в конфигурацию."""
        # Создание конфигурации по умолчанию
        config = VoiceControlConfig()
        
        # Применение данных из словаря
        self._apply_updates(config, data)
        
        return config
    
    def _config_to_dict(self, config: VoiceControlConfig) -> Dict[str, Any]:
        """Преобразование конфигурации в словарь."""
        return asdict(config)
    
    def _apply_updates(self, config: VoiceControlConfig, updates: Dict[str, Any]):
        """Применение обновлений к конфигурации."""
        for key, value in updates.items():
            if hasattr(config, key):
                current_value = getattr(config, key)
                
                if isinstance(current_value, dict) and isinstance(value, dict):
                    current_value.update(value)
                elif hasattr(current_value, '__dict__') and isinstance(value, dict):
                    # Обновление вложенных конфигураций
                    self._apply_updates(current_value, value)
                else:
                    setattr(config, key, value)
    
    def _apply_environment_variables(self):
        """Применение переменных окружения."""
        if not self._config:
            return
        
        # Применение основных переменных
        env_mappings = {
            'VOICE_CONTROL_DEBUG': ('debug_mode', bool),
            'VOICE_CONTROL_LANGUAGE': ('recognition.language', str),
            'VOICE_CONTROL_API_KEY': ('recognition.api_key', str),
            'VOICE_CONTROL_SAMPLE_RATE': ('audio.sample_rate', int),
            'VOICE_CONTROL_CONFIDENCE_THRESHOLD': ('recognition.confidence_threshold', float),
        }
        
        for env_var, (config_path, value_type) in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                try:
                    # Преобразование типа
                    if value_type == bool:
                        converted_value = env_value.lower() in ('true', '1', 'yes', 'on')
                    elif value_type == int:
                        converted_value = int(env_value)
                    elif value_type == float:
                        converted_value = float(env_value)
                    else:
                        converted_value = env_value
                    
                    # Установка значения по пути
                    self._set_nested_value(self._config, config_path, converted_value)
                    
                except (ValueError, TypeError) as e:
                    self.logger.warning(f"Ошибка применения переменной окружения {env_var}: {e}")
    
    def _set_nested_value(self, obj: Any, path: str, value: Any):
        """Установка значения по вложенному пути."""
        parts = path.split('.')
        current = obj
        
        for part in parts[:-1]:
            if hasattr(current, part):
                current = getattr(current, part)
            else:
                return
        
        if hasattr(current, parts[-1]):
            setattr(current, parts[-1], value)


# Глобальный менеджер конфигурации
_global_config_manager: Optional[ConfigManager] = None


def get_config_manager(config_file: Optional[Union[str, Path]] = None) -> ConfigManager:
    """Получение глобального менеджера конфигурации."""
    global _global_config_manager
    if _global_config_manager is None:
        _global_config_manager = ConfigManager(config_file)
    return _global_config_manager


def get_config() -> VoiceControlConfig:
    """Получение текущей конфигурации."""
    return get_config_manager().get_config()


def save_config(config: Optional[VoiceControlConfig] = None) -> bool:
    """Сохранение конфигурации."""
    return get_config_manager().save_config(config)


def update_config(updates: Dict[str, Any]) -> bool:
    """Обновление конфигурации."""
    return get_config_manager().update_config(updates)