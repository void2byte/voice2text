"""Модуль распознавания речи с поддержкой множественных движков."""

import asyncio
import logging
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Union, Callable, Any
from pathlib import Path
import numpy as np

try:
    import speech_recognition as sr
except ImportError:
    sr = None

try:
    import whisper
except ImportError:
    whisper = None

try:
    import openai
except ImportError:
    openai = None

try:
    from google.cloud import speech
except ImportError:
    speech = None

try:
    from .vosk_recognizer import VoskRecognizer, VOSK_AVAILABLE
except ImportError:
    VoskRecognizer = None
    VOSK_AVAILABLE = False


class RecognitionEngine(Enum):
    """Поддерживаемые движки распознавания речи."""
    WHISPER = "whisper"
    GOOGLE_CLOUD = "google_cloud"
    GOOGLE_WEB = "google_web"
    OPENAI = "openai"
    YANDEX = "yandex"
    VOSK = "vosk"


class RecognitionStatus(Enum):
    """Статусы процесса распознавания."""
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class RecognitionResult:
    """Результат распознавания речи."""
    text: str
    confidence: float
    language: str
    duration: float
    engine: RecognitionEngine
    alternatives: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.alternatives is None:
            self.alternatives = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class RecognitionConfig:
    """Конфигурация распознавания речи."""
    engine: RecognitionEngine = RecognitionEngine.WHISPER
    language: str = "ru"
    model: str = "base"
    timeout: float = 30.0
    phrase_timeout: float = 5.0
    energy_threshold: int = 300
    dynamic_energy_threshold: bool = True
    pause_threshold: float = 0.8
    non_speaking_duration: float = 0.5
    api_key: Optional[str] = None
    region: Optional[str] = None
    sample_rate: int = 16000
    chunk_size: int = 1024
    channels: int = 1
    enable_vad: bool = True  # Voice Activity Detection
    noise_reduction: bool = True
    auto_gain_control: bool = True
    echo_cancellation: bool = True
    model_path: Optional[str] = None  # Путь к модели для Vosk


class BaseRecognizer(ABC):
    """Базовый класс для всех распознавателей речи."""
    
    def __init__(self, config: RecognitionConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self._is_initialized = False
        self._status = RecognitionStatus.IDLE
        self._callbacks: Dict[str, List[Callable]] = {
            'on_start': [],
            'on_result': [],
            'on_error': [],
            'on_timeout': [],
            'on_partial': []
        }
    
    @abstractmethod
    def initialize(self) -> bool:
        """Инициализация распознавателя."""
        pass
    
    @abstractmethod
    def recognize_speech(self, audio_data: Union[np.ndarray, bytes]) -> RecognitionResult:
        """Распознавание речи из аудиоданных."""
        pass
    
    @abstractmethod
    def recognize_from_file(self, file_path: Union[str, Path]) -> RecognitionResult:
        """Распознавание речи из файла."""
        pass
    
    def add_callback(self, event: str, callback: Callable):
        """Добавление callback функции для события."""
        if event in self._callbacks:
            self._callbacks[event].append(callback)
    
    def remove_callback(self, event: str, callback: Callable):
        """Удаление callback функции."""
        if event in self._callbacks and callback in self._callbacks[event]:
            self._callbacks[event].remove(callback)
    
    def _trigger_callback(self, event: str, *args, **kwargs):
        """Вызов callback функций для события."""
        for callback in self._callbacks.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception as e:
                self.logger.error(f"Error in callback {callback.__name__}: {e}")
    
    @property
    def status(self) -> RecognitionStatus:
        """Текущий статус распознавателя."""
        return self._status
    
    @property
    def is_initialized(self) -> bool:
        """Проверка инициализации."""
        return self._is_initialized
    
    def cleanup(self):
        """Очистка ресурсов."""
        self._status = RecognitionStatus.IDLE
        self._is_initialized = False


class WhisperRecognizer(BaseRecognizer):
    """Распознаватель на основе OpenAI Whisper."""
    
    def __init__(self, config: RecognitionConfig):
        super().__init__(config)
        self._model = None
    
    def initialize(self) -> bool:
        """Инициализация Whisper модели."""
        if whisper is None:
            self.logger.error("Whisper не установлен")
            return False
        
        try:
            self.logger.info(f"Загрузка Whisper модели: {self.config.model}")
            self._model = whisper.load_model(self.config.model)
            self._is_initialized = True
            self.logger.info("Whisper инициализирован успешно")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка инициализации Whisper: {e}")
            return False
    
    def recognize_speech(self, audio_data: Union[np.ndarray, bytes]) -> RecognitionResult:
        """Распознавание речи через Whisper."""
        if not self._is_initialized:
            raise RuntimeError("Распознаватель не инициализирован")
        
        self._status = RecognitionStatus.PROCESSING
        self._trigger_callback('on_start')
        
        try:
            # Конвертация аудиоданных в формат для Whisper
            if isinstance(audio_data, bytes):
                audio_array = np.frombuffer(audio_data, dtype=np.float32)
            else:
                audio_array = audio_data.astype(np.float32)
            
            # Нормализация аудио
            if audio_array.max() > 1.0:
                audio_array = audio_array / 32768.0
            
            # Распознавание
            result = self._model.transcribe(
                audio_array,
                language=self.config.language if self.config.language != 'auto' else None,
                task='transcribe'
            )
            
            recognition_result = RecognitionResult(
                text=result['text'].strip(),
                confidence=1.0,  # Whisper не предоставляет confidence
                language=result.get('language', self.config.language),
                duration=len(audio_array) / self.config.sample_rate,
                engine=RecognitionEngine.WHISPER,
                metadata={
                    'segments': result.get('segments', []),
                    'model': self.config.model
                }
            )
            
            self._status = RecognitionStatus.COMPLETED
            self._trigger_callback('on_result', recognition_result)
            return recognition_result
            
        except Exception as e:
            self._status = RecognitionStatus.ERROR
            self.logger.error(f"Ошибка распознавания Whisper: {e}")
            self._trigger_callback('on_error', e)
            raise
    
    def recognize_from_file(self, file_path: Union[str, Path]) -> RecognitionResult:
        """Распознавание речи из файла."""
        if not self._is_initialized:
            raise RuntimeError("Распознаватель не инициализирован")
        
        try:
            result = self._model.transcribe(str(file_path))
            
            return RecognitionResult(
                text=result['text'].strip(),
                confidence=1.0,
                language=result.get('language', self.config.language),
                duration=result.get('duration', 0),
                engine=RecognitionEngine.WHISPER,
                metadata={
                    'segments': result.get('segments', []),
                    'file_path': str(file_path)
                }
            )
        except Exception as e:
            self.logger.error(f"Ошибка распознавания файла: {e}")
            raise


class GoogleCloudRecognizer(BaseRecognizer):
    """Распознаватель на основе Google Cloud Speech-to-Text."""
    
    def __init__(self, config: RecognitionConfig):
        super().__init__(config)
        self._client = None
    
    def initialize(self) -> bool:
        """Инициализация Google Cloud клиента."""
        if speech is None:
            self.logger.error("Google Cloud Speech не установлен")
            return False
        
        try:
            self._client = speech.SpeechClient()
            self._is_initialized = True
            self.logger.info("Google Cloud Speech инициализирован")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка инициализации Google Cloud: {e}")
            return False
    
    def recognize_speech(self, audio_data: Union[np.ndarray, bytes]) -> RecognitionResult:
        """Распознавание речи через Google Cloud."""
        if not self._is_initialized:
            raise RuntimeError("Распознаватель не инициализирован")
        
        try:
            # Конвертация в bytes если нужно
            if isinstance(audio_data, np.ndarray):
                audio_bytes = (audio_data * 32767).astype(np.int16).tobytes()
            else:
                audio_bytes = audio_data
            
            audio = speech.RecognitionAudio(content=audio_bytes)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=self.config.sample_rate,
                language_code=self.config.language,
                enable_automatic_punctuation=True,
                enable_word_confidence=True
            )
            
            response = self._client.recognize(config=config, audio=audio)
            
            if response.results:
                result = response.results[0]
                alternative = result.alternatives[0]
                
                return RecognitionResult(
                    text=alternative.transcript,
                    confidence=alternative.confidence,
                    language=self.config.language,
                    duration=len(audio_data) / self.config.sample_rate,
                    engine=RecognitionEngine.GOOGLE_CLOUD,
                    alternatives=[alt.transcript for alt in result.alternatives[1:]],
                    metadata={'response': response}
                )
            else:
                return RecognitionResult(
                    text="",
                    confidence=0.0,
                    language=self.config.language,
                    duration=0,
                    engine=RecognitionEngine.GOOGLE_CLOUD
                )
                
        except Exception as e:
            self.logger.error(f"Ошибка Google Cloud распознавания: {e}")
            raise
    
    def recognize_from_file(self, file_path: Union[str, Path]) -> RecognitionResult:
        """Распознавание речи из файла."""
        with open(file_path, 'rb') as audio_file:
            content = audio_file.read()
        
        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=self.config.sample_rate,
            language_code=self.config.language
        )
        
        response = self._client.recognize(config=config, audio=audio)
        
        if response.results:
            result = response.results[0]
            alternative = result.alternatives[0]
            
            return RecognitionResult(
                text=alternative.transcript,
                confidence=alternative.confidence,
                language=self.config.language,
                duration=0,  # Не доступно для файлов
                engine=RecognitionEngine.GOOGLE_CLOUD,
                alternatives=[alt.transcript for alt in result.alternatives[1:]]
            )
        else:
            return RecognitionResult(
                text="",
                confidence=0.0,
                language=self.config.language,
                duration=0,
                engine=RecognitionEngine.GOOGLE_CLOUD
            )


class VoiceRecognizer:
    """Главный класс для управления распознаванием речи."""
    
    def __init__(self, config: RecognitionConfig = None):
        self.config = config or RecognitionConfig()
        self.logger = logging.getLogger(self.__class__.__name__)
        self._recognizer: Optional[BaseRecognizer] = None
        self._recognizer_cache: Dict[RecognitionEngine, BaseRecognizer] = {}
        
        # Маппинг движков к классам
        self._recognizer_classes = {
            RecognitionEngine.WHISPER: WhisperRecognizer,
            RecognitionEngine.GOOGLE_CLOUD: GoogleCloudRecognizer,
            RecognitionEngine.VOSK: VoskRecognizer,
        }
    
    def initialize(self, engine: RecognitionEngine = None) -> bool:
        """Инициализация распознавателя."""
        engine = engine or self.config.engine
        
        if engine in self._recognizer_cache:
            self._recognizer = self._recognizer_cache[engine]
            return self._recognizer.is_initialized
        
        recognizer_class = self._recognizer_classes.get(engine)
        if not recognizer_class:
            self.logger.error(f"Неподдерживаемый движок: {engine}")
            return False
        
        # Создание конфигурации для конкретного движка
        engine_config = RecognitionConfig(
            engine=engine,
            language=self.config.language,
            model=self.config.model,
            timeout=self.config.timeout,
            api_key=self.config.api_key,
            sample_rate=self.config.sample_rate,
            model_path=self.config.model_path
        )
        
        self._recognizer = recognizer_class(engine_config)
        
        if self._recognizer.initialize():
            self._recognizer_cache[engine] = self._recognizer
            self.logger.info(f"Распознаватель {engine.value} инициализирован")
            return True
        else:
            self.logger.error(f"Не удалось инициализировать {engine.value}")
            return False
    
    def recognize_speech(self, audio_data: Union[np.ndarray, bytes]) -> RecognitionResult:
        """Распознавание речи."""
        if not self._recognizer or not self._recognizer.is_initialized:
            raise RuntimeError("Распознаватель не инициализирован")
        
        return self._recognizer.recognize_speech(audio_data)
    
    def recognize_from_file(self, file_path: Union[str, Path]) -> RecognitionResult:
        """Распознавание речи из файла."""
        if not self._recognizer or not self._recognizer.is_initialized:
            raise RuntimeError("Распознаватель не инициализирован")
        
        return self._recognizer.recognize_from_file(file_path)
    
    def switch_engine(self, engine: RecognitionEngine) -> bool:
        """Переключение движка распознавания."""
        return self.initialize(engine)
    
    def add_callback(self, event: str, callback: Callable):
        """Добавление callback функции."""
        if self._recognizer:
            self._recognizer.add_callback(event, callback)
    
    def get_available_engines(self) -> List[RecognitionEngine]:
        """Получение списка доступных движков."""
        available = []
        
        if whisper is not None:
            available.append(RecognitionEngine.WHISPER)
        if speech is not None:
            available.append(RecognitionEngine.GOOGLE_CLOUD)
        if sr is not None:
            available.append(RecognitionEngine.GOOGLE_WEB)
        if VOSK_AVAILABLE:
            available.append(RecognitionEngine.VOSK)
        
        return available
    
    def cleanup(self):
        """Очистка ресурсов."""
        for recognizer in self._recognizer_cache.values():
            recognizer.cleanup()
        self._recognizer_cache.clear()
        self._recognizer = None
    
    @property
    def current_engine(self) -> Optional[RecognitionEngine]:
        """Текущий движок распознавания."""
        return self._recognizer.config.engine if self._recognizer else None
    
    @property
    def status(self) -> RecognitionStatus:
        """Текущий статус."""
        return self._recognizer.status if self._recognizer else RecognitionStatus.IDLE


# Функция для создания распознавателя с настройками по умолчанию
def create_voice_recognizer(
    engine: RecognitionEngine = RecognitionEngine.WHISPER,
    language: str = "ru",
    model: str = "base"
) -> VoiceRecognizer:
    """Создание распознавателя с базовыми настройками."""
    config = RecognitionConfig(
        engine=engine,
        language=language,
        model=model
    )
    
    recognizer = VoiceRecognizer(config)
    recognizer.initialize()
    
    return recognizer