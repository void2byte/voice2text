"""Factory for creating speech recognition instances.

Фабрика для создания экземпляров различных сервисов распознавания речи
с поддержкой кэширования и ленивой инициализации.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Type, List
from enum import Enum

from ..security.credentials_manager import SecureCredentialsManager
from ..utils.logger import PerformanceLogger


class RecognitionService(Enum):
    """Поддерживаемые сервисы распознавания речи."""
    WHISPER = "whisper"
    GOOGLE = "google"
    AZURE = "azure"
    YANDEX = "yandex"
    VOSK = "vosk"


class BaseRecognizer(ABC):
    """Базовый класс для распознавателей речи."""
    
    def __init__(self, credentials_manager: SecureCredentialsManager):
        """Инициализация распознавателя.
        
        Args:
            credentials_manager: Менеджер учетных данных
        """
        self._credentials_manager = credentials_manager
        self._logger = PerformanceLogger(f"{self.__class__.__name__}")
        self._initialized = False
    
    @abstractmethod
    async def initialize(self) -> None:
        """Инициализация распознавателя."""
        pass
    
    @abstractmethod
    async def recognize(self, audio_data: bytes, language: str = "ru", **kwargs) -> Dict[str, Any]:
        """Распознавание речи из аудио данных.
        
        Args:
            audio_data: Аудио данные в формате bytes
            language: Язык распознавания
            **kwargs: Дополнительные параметры
            
        Returns:
            Результат распознавания
        """
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Очистка ресурсов распознавателя."""
        pass
    
    async def ensure_initialized(self) -> None:
        """Обеспечение инициализации распознавателя."""
        if not self._initialized:
            await self.initialize()
            self._initialized = True


class WhisperRecognizer(BaseRecognizer):
    """Распознаватель на основе OpenAI Whisper."""
    
    def __init__(self, credentials_manager: SecureCredentialsManager):
        super().__init__(credentials_manager)
        self._model = None
        self._device = "cpu"
    
    async def initialize(self) -> None:
        """Инициализация Whisper модели."""
        try:
            import whisper
            
            # Определение устройства
            try:
                import torch
                self._device = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                self._device = "cpu"
            
            # Загрузка модели
            model_name = "base"  # Можно сделать конфигурируемым
            self._model = whisper.load_model(model_name, device=self._device)
            
            self._logger.info(f"Whisper model '{model_name}' loaded on {self._device}")
            
        except ImportError as e:
            self._logger.error(f"Whisper not available: {e}")
            raise RuntimeError("Whisper library not installed")
        except Exception as e:
            self._logger.error(f"Failed to initialize Whisper: {e}")
            raise
    
    async def recognize(self, audio_data: bytes, language: str = "ru", **kwargs) -> Dict[str, Any]:
        """Распознавание речи с помощью Whisper.
        
        Args:
            audio_data: Аудио данные
            language: Язык распознавания
            **kwargs: Дополнительные параметры
            
        Returns:
            Результат распознавания
        """
        await self.ensure_initialized()
        
        try:
            import numpy as np
            import io
            import soundfile as sf
            
            # Конвертация bytes в numpy array
            audio_io = io.BytesIO(audio_data)
            audio_array, sample_rate = sf.read(audio_io)
            
            # Whisper ожидает float32 с sample rate 16000
            if sample_rate != 16000:
                import librosa
                audio_array = librosa.resample(audio_array, orig_sr=sample_rate, target_sr=16000)
            
            audio_array = audio_array.astype(np.float32)
            
            # Распознавание
            result = self._model.transcribe(
                audio_array,
                language=language if language != "ru" else "russian",
                **kwargs
            )
            
            return {
                "text": result["text"].strip(),
                "language": result.get("language", language),
                "confidence": 1.0,  # Whisper не предоставляет confidence
                "segments": result.get("segments", []),
                "service": "whisper"
            }
            
        except Exception as e:
            self._logger.error(f"Whisper recognition failed: {e}")
            raise
    
    async def cleanup(self) -> None:
        """Очистка ресурсов Whisper."""
        if self._model is not None:
            del self._model
            self._model = None
            
            # Очистка GPU памяти если используется CUDA
            if self._device == "cuda":
                try:
                    import torch
                    torch.cuda.empty_cache()
                except ImportError:
                    pass
            
            self._logger.info("Whisper resources cleaned up")


class GoogleRecognizer(BaseRecognizer):
    """Распознаватель на основе Google Speech-to-Text."""
    
    def __init__(self, credentials_manager: SecureCredentialsManager):
        super().__init__(credentials_manager)
        self._client = None
    
    async def initialize(self) -> None:
        """Инициализация Google Speech client."""
        try:
            from google.cloud import speech
            
            # Получение учетных данных
            credentials = await self._credentials_manager.get_credentials("google_speech")
            
            # Создание клиента
            self._client = speech.SpeechClient(credentials=credentials)
            
            self._logger.info("Google Speech client initialized")
            
        except ImportError as e:
            self._logger.error(f"Google Cloud Speech library not available: {e}")
            raise RuntimeError("Google Cloud Speech library not installed")
        except Exception as e:
            self._logger.error(f"Failed to initialize Google Speech: {e}")
            raise
    
    async def recognize(self, audio_data: bytes, language: str = "ru", **kwargs) -> Dict[str, Any]:
        """Распознавание речи с помощью Google Speech.
        
        Args:
            audio_data: Аудио данные
            language: Язык распознавания
            **kwargs: Дополнительные параметры
            
        Returns:
            Результат распознавания
        """
        await self.ensure_initialized()
        
        try:
            from google.cloud import speech
            
            # Конфигурация распознавания
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code=language if language != "ru" else "ru-RU",
                **kwargs
            )
            
            audio = speech.RecognitionAudio(content=audio_data)
            
            # Выполнение распознавания
            response = self._client.recognize(config=config, audio=audio)
            
            if response.results:
                result = response.results[0]
                alternative = result.alternatives[0]
                
                return {
                    "text": alternative.transcript.strip(),
                    "language": language,
                    "confidence": alternative.confidence,
                    "alternatives": [
                        {
                            "text": alt.transcript,
                            "confidence": alt.confidence
                        }
                        for alt in result.alternatives
                    ],
                    "service": "google"
                }
            else:
                return {
                    "text": "",
                    "language": language,
                    "confidence": 0.0,
                    "alternatives": [],
                    "service": "google"
                }
                
        except Exception as e:
            self._logger.error(f"Google Speech recognition failed: {e}")
            raise
    
    async def cleanup(self) -> None:
        """Очистка ресурсов Google Speech."""
        if self._client is not None:
            self._client = None
            self._logger.info("Google Speech client cleaned up")


class VoskRecognizer(BaseRecognizer):
    """Распознаватель на основе Vosk (оффлайн)."""
    
    def __init__(self, credentials_manager: SecureCredentialsManager):
        super().__init__(credentials_manager)
        self._model = None
        self._recognizer = None
    
    async def initialize(self) -> None:
        """Инициализация Vosk модели."""
        try:
            import vosk
            import json
            
            # Путь к модели (должен быть конфигурируемым)
            model_path = "models/vosk-model-ru-0.42"  # Пример пути
            
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Vosk model not found at: {model_path}")
            
            self._model = vosk.Model(model_path)
            self._recognizer = vosk.KaldiRecognizer(self._model, 16000)
            
            self._logger.info(f"Vosk model loaded from {model_path}")
            
        except ImportError as e:
            self._logger.error(f"Vosk library not available: {e}")
            raise RuntimeError("Vosk library not installed")
        except Exception as e:
            self._logger.error(f"Failed to initialize Vosk: {e}")
            raise
    
    async def recognize(self, audio_data: bytes, language: str = "ru", **kwargs) -> Dict[str, Any]:
        """Распознавание речи с помощью Vosk.
        
        Args:
            audio_data: Аудио данные
            language: Язык распознавания (игнорируется для Vosk)
            **kwargs: Дополнительные параметры
            
        Returns:
            Результат распознавания
        """
        await self.ensure_initialized()
        
        try:
            import json
            
            # Обработка аудио данных
            self._recognizer.AcceptWaveform(audio_data)
            result_json = self._recognizer.FinalResult()
            result = json.loads(result_json)
            
            return {
                "text": result.get("text", "").strip(),
                "language": language,
                "confidence": result.get("confidence", 1.0),
                "service": "vosk"
            }
            
        except Exception as e:
            self._logger.error(f"Vosk recognition failed: {e}")
            raise
    
    async def cleanup(self) -> None:
        """Очистка ресурсов Vosk."""
        if self._recognizer is not None:
            self._recognizer = None
        if self._model is not None:
            self._model = None
        
        self._logger.info("Vosk resources cleaned up")


class RecognitionFactory:
    """Фабрика для создания распознавателей речи.
    
    Обеспечивает создание и кэширование экземпляров распознавателей
    с поддержкой ленивой инициализации.
    """
    
    def __init__(self, credentials_manager: SecureCredentialsManager):
        """Инициализация фабрики.
        
        Args:
            credentials_manager: Менеджер учетных данных
        """
        self._credentials_manager = credentials_manager
        self._logger = PerformanceLogger("RecognitionFactory")
        self._recognizers: Dict[str, BaseRecognizer] = {}
        
        # Регистрация доступных распознавателей
        self._recognizer_classes: Dict[str, Type[BaseRecognizer]] = {
            RecognitionService.WHISPER.value: WhisperRecognizer,
            RecognitionService.GOOGLE.value: GoogleRecognizer,
            RecognitionService.VOSK.value: VoskRecognizer,
            # Добавить другие распознаватели по мере необходимости
        }
    
    def get_recognizer(self, service: str) -> BaseRecognizer:
        """Получение экземпляра распознавателя.
        
        Args:
            service: Название сервиса распознавания
            
        Returns:
            Экземпляр распознавателя
            
        Raises:
            ValueError: При неподдерживаемом сервисе
        """
        if service not in self._recognizer_classes:
            available_services = list(self._recognizer_classes.keys())
            raise ValueError(f"Unsupported recognition service: {service}. "
                           f"Available services: {available_services}")
        
        # Ленивое создание экземпляра
        if service not in self._recognizers:
            recognizer_class = self._recognizer_classes[service]
            self._recognizers[service] = recognizer_class(self._credentials_manager)
            self._logger.info(f"Created recognizer instance for service: {service}")
        
        return self._recognizers[service]
    
    def get_available_services(self) -> List[str]:
        """Получение списка доступных сервисов.
        
        Returns:
            Список названий доступных сервисов
        """
        return list(self._recognizer_classes.keys())
    
    async def cleanup(self) -> None:
        """Очистка всех созданных распознавателей."""
        for service, recognizer in self._recognizers.items():
            try:
                await recognizer.cleanup()
                self._logger.info(f"Cleaned up recognizer for service: {service}")
            except Exception as e:
                self._logger.error(f"Error cleaning up {service} recognizer: {e}")
        
        self._recognizers.clear()
        self._logger.info("All recognizers cleaned up")