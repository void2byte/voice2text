"""Audio Capture Pool for managing multiple audio recording sessions.

Пул для управления множественными сессиями записи аудио
с поддержкой асинхронности и оптимизации ресурсов.
"""

import asyncio
import threading
import uuid
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import io

from ..utils.logger import PerformanceLogger


class SessionState(Enum):
    """Состояния сессии записи."""
    CREATED = "created"
    RECORDING = "recording"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass
class AudioSession:
    """Информация о сессии записи аудио."""
    session_id: str
    state: SessionState
    config: Dict[str, Any]
    created_at: float
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    audio_data: Optional[bytes] = None
    error: Optional[str] = None
    thread: Optional[threading.Thread] = None
    stop_event: threading.Event = field(default_factory=threading.Event)
    audio_buffer: io.BytesIO = field(default_factory=io.BytesIO)


class AudioCapturePool:
    """Пул для управления сессиями записи аудио.
    
    Обеспечивает эффективное управление ресурсами при множественных
    одновременных записях с поддержкой асинхронности.
    """
    
    def __init__(self, config):
        """Инициализация пула.
        
        Args:
            config: Конфигурация аудио
        """
        self._config = config
        self._logger = PerformanceLogger("AudioCapturePool")
        self._sessions: Dict[str, AudioSession] = {}
        self._lock = threading.RLock()
        self._max_sessions = 5  # Максимальное количество одновременных сессий
        
        # Проверка доступности аудио библиотек
        self._audio_backend = self._detect_audio_backend()
        self._logger.info(f"Audio backend detected: {self._audio_backend}")
    
    def _detect_audio_backend(self) -> str:
        """Определение доступного аудио бэкенда.
        
        Returns:
            Название доступного бэкенда
        """
        backends = [
            ("pyaudio", self._check_pyaudio),
            ("sounddevice", self._check_sounddevice),
            ("wave", self._check_wave)  # Fallback для тестирования
        ]
        
        for backend_name, check_func in backends:
            if check_func():
                return backend_name
        
        raise RuntimeError("No suitable audio backend found")
    
    def _check_pyaudio(self) -> bool:
        """Проверка доступности PyAudio."""
        try:
            import pyaudio
            return True
        except ImportError:
            return False
    
    def _check_sounddevice(self) -> bool:
        """Проверка доступности sounddevice."""
        try:
            import sounddevice as sd
            return True
        except ImportError:
            return False
    
    def _check_wave(self) -> bool:
        """Проверка доступности wave (всегда доступен)."""
        try:
            import wave
            return True
        except ImportError:
            return False
    
    async def create_session(self, **kwargs) -> str:
        """Создание новой сессии записи.
        
        Args:
            **kwargs: Параметры сессии
            
        Returns:
            ID созданной сессии
            
        Raises:
            RuntimeError: При превышении лимита сессий
        """
        with self._lock:
            # Проверка лимита активных сессий
            active_sessions = [s for s in self._sessions.values() 
                             if s.state in [SessionState.CREATED, SessionState.RECORDING]]
            
            if len(active_sessions) >= self._max_sessions:
                raise RuntimeError(f"Maximum number of sessions ({self._max_sessions}) reached")
            
            # Создание новой сессии
            session_id = str(uuid.uuid4())
            session = AudioSession(
                session_id=session_id,
                state=SessionState.CREATED,
                config=kwargs,
                created_at=time.time()
            )
            
            self._sessions[session_id] = session
            
            # Запуск записи в отдельном потоке
            session.thread = threading.Thread(
                target=self._record_audio,
                args=(session,),
                daemon=True
            )
            session.thread.start()
            
            self._logger.info(f"Audio session created: {session_id}")
            return session_id
    
    def _record_audio(self, session: AudioSession) -> None:
        """Запись аудио в отдельном потоке.
        
        Args:
            session: Сессия записи
        """
        try:
            session.state = SessionState.RECORDING
            session.started_at = time.time()
            
            if self._audio_backend == "pyaudio":
                self._record_with_pyaudio(session)
            elif self._audio_backend == "sounddevice":
                self._record_with_sounddevice(session)
            else:
                self._record_with_wave(session)  # Fallback
            
            if not session.stop_event.is_set():
                session.state = SessionState.COMPLETED
                session.completed_at = time.time()
                
        except Exception as e:
            session.state = SessionState.FAILED
            session.error = str(e)
            session.completed_at = time.time()
            self._logger.error(f"Recording failed for session {session.session_id}: {e}")
    
    def _record_with_pyaudio(self, session: AudioSession) -> None:
        """Запись аудио с использованием PyAudio.
        
        Args:
            session: Сессия записи
        """
        import pyaudio
        
        audio = pyaudio.PyAudio()
        
        try:
            stream = audio.open(
                format=pyaudio.paInt16,
                channels=self._config.channels,
                rate=self._config.sample_rate,
                input=True,
                frames_per_buffer=self._config.chunk_size
            )
            
            self._logger.debug(f"PyAudio stream opened for session {session.session_id}")
            
            while not session.stop_event.is_set():
                try:
                    data = stream.read(self._config.chunk_size, exception_on_overflow=False)
                    session.audio_buffer.write(data)
                    
                    # Проверка максимального времени записи
                    if (time.time() - session.started_at) > self._config.max_recording_time:
                        self._logger.warning(f"Maximum recording time reached for session {session.session_id}")
                        break
                        
                except Exception as e:
                    if not session.stop_event.is_set():
                        self._logger.error(f"Error reading audio data: {e}")
                    break
            
            stream.stop_stream()
            stream.close()
            
        finally:
            audio.terminate()
    
    def _record_with_sounddevice(self, session: AudioSession) -> None:
        """Запись аудио с использованием sounddevice.
        
        Args:
            session: Сессия записи
        """
        import sounddevice as sd
        import numpy as np
        
        def audio_callback(indata, frames, time, status):
            if status:
                self._logger.warning(f"Audio callback status: {status}")
            
            if not session.stop_event.is_set():
                # Конвертация в int16 и запись в буфер
                audio_data = (indata * 32767).astype(np.int16)
                session.audio_buffer.write(audio_data.tobytes())
        
        try:
            with sd.InputStream(
                samplerate=self._config.sample_rate,
                channels=self._config.channels,
                dtype=np.float32,
                callback=audio_callback,
                blocksize=self._config.chunk_size
            ):
                self._logger.debug(f"Sounddevice stream opened for session {session.session_id}")
                
                while not session.stop_event.is_set():
                    # Проверка максимального времени записи
                    if (time.time() - session.started_at) > self._config.max_recording_time:
                        self._logger.warning(f"Maximum recording time reached for session {session.session_id}")
                        break
                    
                    time.sleep(0.1)  # Небольшая пауза
                    
        except Exception as e:
            if not session.stop_event.is_set():
                raise e
    
    def _record_with_wave(self, session: AudioSession) -> None:
        """Заглушка для записи аудио (для тестирования).
        
        Args:
            session: Сессия записи
        """
        import wave
        import struct
        import math
        
        # Генерация тестового аудио сигнала
        duration = min(5.0, self._config.max_recording_time)  # Максимум 5 секунд
        sample_rate = self._config.sample_rate
        frequency = 440  # Нота A4
        
        for i in range(int(duration * sample_rate)):
            if session.stop_event.is_set():
                break
            
            # Генерация синусоиды
            sample = int(32767 * math.sin(2 * math.pi * frequency * i / sample_rate))
            session.audio_buffer.write(struct.pack('<h', sample))
            
            # Небольшая пауза для имитации реального времени
            if i % 1000 == 0:
                time.sleep(0.001)
    
    async def stop_session(self, session_id: str) -> bytes:
        """Остановка сессии записи и получение аудио данных.
        
        Args:
            session_id: ID сессии
            
        Returns:
            Записанные аудио данные
            
        Raises:
            ValueError: При некорректном session_id
            RuntimeError: При ошибке сессии
        """
        with self._lock:
            if session_id not in self._sessions:
                raise ValueError(f"Session not found: {session_id}")
            
            session = self._sessions[session_id]
            
            # Остановка записи
            session.stop_event.set()
            
            # Ожидание завершения потока
            if session.thread and session.thread.is_alive():
                session.thread.join(timeout=5.0)
                
                if session.thread.is_alive():
                    self._logger.warning(f"Recording thread did not stop gracefully for session {session_id}")
            
            # Проверка состояния сессии
            if session.state == SessionState.FAILED:
                raise RuntimeError(f"Session failed: {session.error}")
            
            # Получение аудио данных
            session.audio_data = session.audio_buffer.getvalue()
            session.audio_buffer.close()
            
            if session.state != SessionState.CANCELLED:
                session.state = SessionState.COMPLETED
                session.completed_at = time.time()
            
            self._logger.info(f"Session stopped: {session_id}, data size: {len(session.audio_data)} bytes")
            return session.audio_data
    
    async def cancel_session(self, session_id: str) -> None:
        """Отмена сессии записи.
        
        Args:
            session_id: ID сессии
        """
        with self._lock:
            if session_id not in self._sessions:
                self._logger.warning(f"Attempt to cancel non-existent session: {session_id}")
                return
            
            session = self._sessions[session_id]
            session.state = SessionState.CANCELLED
            session.stop_event.set()
            
            # Ожидание завершения потока
            if session.thread and session.thread.is_alive():
                session.thread.join(timeout=3.0)
            
            # Очистка буфера
            session.audio_buffer.close()
            session.completed_at = time.time()
            
            self._logger.info(f"Session cancelled: {session_id}")
    
    def get_active_sessions(self) -> List[str]:
        """Получение списка активных сессий.
        
        Returns:
            Список ID активных сессий
        """
        with self._lock:
            return [
                session_id for session_id, session in self._sessions.items()
                if session.state in [SessionState.CREATED, SessionState.RECORDING]
            ]
    
    def get_session_config(self, session_id: str) -> Dict[str, Any]:
        """Получение конфигурации сессии.
        
        Args:
            session_id: ID сессии
            
        Returns:
            Конфигурация сессии
            
        Raises:
            ValueError: При некорректном session_id
        """
        with self._lock:
            if session_id not in self._sessions:
                raise ValueError(f"Session not found: {session_id}")
            
            return self._sessions[session_id].config.copy()
    
    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """Получение информации о сессии.
        
        Args:
            session_id: ID сессии
            
        Returns:
            Информация о сессии
        """
        with self._lock:
            if session_id not in self._sessions:
                raise ValueError(f"Session not found: {session_id}")
            
            session = self._sessions[session_id]
            
            return {
                "session_id": session.session_id,
                "state": session.state.value,
                "created_at": session.created_at,
                "started_at": session.started_at,
                "completed_at": session.completed_at,
                "duration": (
                    (session.completed_at or time.time()) - session.started_at
                    if session.started_at else None
                ),
                "audio_size": len(session.audio_data) if session.audio_data else 0,
                "error": session.error
            }
    
    async def cleanup(self) -> None:
        """Очистка всех сессий и ресурсов."""
        with self._lock:
            # Остановка всех активных сессий
            active_sessions = self.get_active_sessions()
            for session_id in active_sessions:
                try:
                    await self.cancel_session(session_id)
                except Exception as e:
                    self._logger.error(f"Error cancelling session {session_id}: {e}")
            
            # Очистка завершенных сессий
            completed_sessions = list(self._sessions.keys())
            for session_id in completed_sessions:
                try:
                    session = self._sessions[session_id]
                    if session.audio_buffer and not session.audio_buffer.closed:
                        session.audio_buffer.close()
                    del self._sessions[session_id]
                except Exception as e:
                    self._logger.error(f"Error cleaning up session {session_id}: {e}")
            
            self._logger.info("AudioCapturePool cleanup completed")