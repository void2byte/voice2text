"""Unified Audio Manager for voice control operations.

Центральный компонент для управления всеми аудио операциями,
включая захват, обработку и распознавание речи.
"""

import asyncio
import threading
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass
from enum import Enum

from ..security.credentials_manager import SecureCredentialsManager
from ..utils.logger import PerformanceLogger
from ..utils.validator import InputValidator
from .recognition_factory import RecognitionFactory
from .audio_capture_pool import AudioCapturePool
from .progress_manager import ProgressManager


class AudioState(Enum):
    """Состояния аудио менеджера."""
    IDLE = "idle"
    RECORDING = "recording"
    PROCESSING = "processing"
    ERROR = "error"


@dataclass
class AudioConfig:
    """Конфигурация аудио менеджера."""
    sample_rate: int = 16000
    channels: int = 1
    chunk_size: int = 1024
    format: str = "int16"
    max_recording_time: int = 300  # 5 минут
    silence_threshold: float = 0.01
    silence_duration: float = 2.0


class AudioManager:
    """Unified Audio Manager для голосового управления.
    
    Обеспечивает централизованное управление всеми аудио операциями
    с поддержкой асинхронности, пулинга ресурсов и мониторинга производительности.
    """
    
    def __init__(self, config: Optional[AudioConfig] = None):
        """Инициализация AudioManager.
        
        Args:
            config: Конфигурация аудио менеджера
        """
        self._config = config or AudioConfig()
        self._state = AudioState.IDLE
        self._lock = threading.RLock()
        
        # Инициализация компонентов
        self._credentials_manager = SecureCredentialsManager()
        self._logger = PerformanceLogger("AudioManager")
        self._validator = InputValidator()
        self._recognition_factory = RecognitionFactory(self._credentials_manager)
        self._capture_pool = AudioCapturePool(self._config)
        self._progress_manager = ProgressManager()
        
        # Callbacks
        self._callbacks: Dict[str, List[Callable]] = {
            "state_changed": [],
            "audio_captured": [],
            "recognition_result": [],
            "error_occurred": []
        }
        
        self._logger.info("AudioManager initialized successfully")
    
    @property
    def state(self) -> AudioState:
        """Текущее состояние менеджера."""
        return self._state
    
    @property
    def config(self) -> AudioConfig:
        """Конфигурация менеджера."""
        return self._config
    
    def register_callback(self, event: str, callback: Callable) -> None:
        """Регистрация callback функции для события.
        
        Args:
            event: Тип события (state_changed, audio_captured, recognition_result, error_occurred)
            callback: Функция обратного вызова
        """
        if event not in self._callbacks:
            raise ValueError(f"Unknown event type: {event}")
        
        self._callbacks[event].append(callback)
        self._logger.debug(f"Callback registered for event: {event}")
    
    def unregister_callback(self, event: str, callback: Callable) -> None:
        """Отмена регистрации callback функции.
        
        Args:
            event: Тип события
            callback: Функция обратного вызова
        """
        if event in self._callbacks and callback in self._callbacks[event]:
            self._callbacks[event].remove(callback)
            self._logger.debug(f"Callback unregistered for event: {event}")
    
    def _emit_event(self, event: str, data: Any = None) -> None:
        """Вызов всех callback функций для события.
        
        Args:
            event: Тип события
            data: Данные события
        """
        for callback in self._callbacks.get(event, []):
            try:
                callback(data)
            except Exception as e:
                self._logger.error(f"Error in callback for {event}: {e}")
    
    def _set_state(self, new_state: AudioState) -> None:
        """Изменение состояния менеджера.
        
        Args:
            new_state: Новое состояние
        """
        with self._lock:
            if self._state != new_state:
                old_state = self._state
                self._state = new_state
                self._logger.info(f"State changed: {old_state.value} -> {new_state.value}")
                self._emit_event("state_changed", {
                    "old_state": old_state,
                    "new_state": new_state
                })
    
    async def start_recording(self, 
                            recognition_service: str = "whisper",
                            language: str = "ru",
                            **kwargs) -> str:
        """Начало записи и распознавания речи.
        
        Args:
            recognition_service: Сервис распознавания речи
            language: Язык распознавания
            **kwargs: Дополнительные параметры
            
        Returns:
            ID сессии записи
            
        Raises:
            ValueError: При некорректных параметрах
            RuntimeError: При ошибке инициализации
        """
        # Валидация параметров
        self._validator.validate_recognition_service(recognition_service)
        self._validator.validate_language(language)
        
        if self._state != AudioState.IDLE:
            raise RuntimeError(f"Cannot start recording in state: {self._state.value}")
        
        try:
            self._set_state(AudioState.RECORDING)
            
            # Создание сессии записи
            session_id = await self._capture_pool.create_session(
                recognition_service=recognition_service,
                language=language,
                **kwargs
            )
            
            # Запуск мониторинга прогресса
            self._progress_manager.start_session(session_id)
            
            self._logger.info(f"Recording started with session ID: {session_id}")
            return session_id
            
        except Exception as e:
            self._set_state(AudioState.ERROR)
            self._emit_event("error_occurred", {
                "error": str(e),
                "operation": "start_recording"
            })
            raise
    
    async def stop_recording(self, session_id: str) -> Dict[str, Any]:
        """Остановка записи и получение результата.
        
        Args:
            session_id: ID сессии записи
            
        Returns:
            Результат распознавания речи
            
        Raises:
            ValueError: При некорректном session_id
            RuntimeError: При ошибке обработки
        """
        if not session_id:
            raise ValueError("Session ID is required")
        
        try:
            self._set_state(AudioState.PROCESSING)
            
            # Остановка записи и получение аудио данных
            audio_data = await self._capture_pool.stop_session(session_id)
            self._emit_event("audio_captured", {
                "session_id": session_id,
                "audio_data": audio_data
            })
            
            # Распознавание речи
            recognizer = self._recognition_factory.get_recognizer(
                self._capture_pool.get_session_config(session_id)["recognition_service"]
            )
            
            result = await recognizer.recognize(audio_data)
            
            # Завершение сессии
            self._progress_manager.complete_session(session_id, result)
            
            self._emit_event("recognition_result", {
                "session_id": session_id,
                "result": result
            })
            
            self._set_state(AudioState.IDLE)
            self._logger.info(f"Recording completed for session: {session_id}")
            
            return result
            
        except Exception as e:
            self._set_state(AudioState.ERROR)
            self._progress_manager.fail_session(session_id, str(e))
            self._emit_event("error_occurred", {
                "error": str(e),
                "operation": "stop_recording",
                "session_id": session_id
            })
            raise
    
    async def cancel_recording(self, session_id: str) -> None:
        """Отмена записи.
        
        Args:
            session_id: ID сессии записи
        """
        try:
            await self._capture_pool.cancel_session(session_id)
            self._progress_manager.cancel_session(session_id)
            self._set_state(AudioState.IDLE)
            self._logger.info(f"Recording cancelled for session: {session_id}")
            
        except Exception as e:
            self._logger.error(f"Error cancelling recording: {e}")
            raise
    
    def get_active_sessions(self) -> List[str]:
        """Получение списка активных сессий.
        
        Returns:
            Список ID активных сессий
        """
        return self._capture_pool.get_active_sessions()
    
    def get_session_progress(self, session_id: str) -> Dict[str, Any]:
        """Получение прогресса сессии.
        
        Args:
            session_id: ID сессии
            
        Returns:
            Информация о прогрессе сессии
        """
        return self._progress_manager.get_progress(session_id)
    
    async def cleanup(self) -> None:
        """Очистка ресурсов менеджера."""
        try:
            # Остановка всех активных сессий
            active_sessions = self.get_active_sessions()
            for session_id in active_sessions:
                await self.cancel_recording(session_id)
            
            # Очистка компонентов
            await self._capture_pool.cleanup()
            self._progress_manager.cleanup()
            
            self._set_state(AudioState.IDLE)
            self._logger.info("AudioManager cleanup completed")
            
        except Exception as e:
            self._logger.error(f"Error during cleanup: {e}")
            raise
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        asyncio.create_task(self.cleanup())