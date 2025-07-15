"""Главный контроллер голосового управления."""

import logging
import threading
import asyncio
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json
from pathlib import Path

from .audio_manager import AudioManager
from .voice_recognizer import VoiceRecognizer, RecognitionResult, RecognitionConfig
from .command_processor import CommandProcessor, Command, CommandResult
from .response_generator import ResponseGenerator, ResponseContext, Response
from .di_container import DIContainer
from .error_handler import ErrorHandler, ErrorContext, ErrorCategory, ErrorSeverity
from .progress_manager import ProgressManager


class VoiceControllerState(Enum):
    """Состояния контроллера."""
    STOPPED = "stopped"
    STARTING = "starting"
    LISTENING = "listening"
    PROCESSING = "processing"
    RESPONDING = "responding"
    PAUSED = "paused"
    ERROR = "error"


class VoiceControllerMode(Enum):
    """Режимы работы контроллера."""
    CONTINUOUS = "continuous"  # Непрерывное прослушивание
    PUSH_TO_TALK = "push_to_talk"  # По нажатию кнопки
    VOICE_ACTIVATION = "voice_activation"  # По ключевому слову
    MANUAL = "manual"  # Ручной режим


@dataclass
class VoiceControllerConfig:
    """Конфигурация контроллера."""
    mode: VoiceControllerMode = VoiceControllerMode.CONTINUOUS
    auto_start: bool = False
    language: str = "ru"
    activation_phrase: str = "привет бот"
    response_enabled: bool = True
    audio_feedback: bool = True
    log_level: str = "INFO"
    max_session_duration: int = 3600  # секунды
    recognition_timeout: float = 5.0
    silence_timeout: float = 2.0
    confidence_threshold: float = 0.7
    enable_metrics: bool = True
    save_audio_history: bool = False
    audio_history_limit: int = 100


@dataclass
class VoiceSession:
    """Сессия голосового управления."""
    id: str
    user_id: Optional[str]
    start_time: datetime
    end_time: Optional[datetime] = None
    commands_count: int = 0
    successful_commands: int = 0
    failed_commands: int = 0
    total_audio_duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class VoiceControllerEventType(Enum):
    """Типы событий контроллера."""
    STATE_CHANGED = "state_changed"
    AUDIO_DETECTED = "audio_detected"
    RECOGNITION_STARTED = "recognition_started"
    RECOGNITION_COMPLETED = "recognition_completed"
    COMMAND_RECEIVED = "command_received"
    COMMAND_EXECUTED = "command_executed"
    RESPONSE_GENERATED = "response_generated"
    ERROR_OCCURRED = "error_occurred"
    SESSION_STARTED = "session_started"
    SESSION_ENDED = "session_ended"


@dataclass
class VoiceControllerEvent:
    """Событие контроллера."""
    type: VoiceControllerEventType
    timestamp: datetime
    data: Dict[str, Any] = field(default_factory=dict)
    session_id: Optional[str] = None


class VoiceController:
    """Главный контроллер голосового управления."""
    
    def __init__(self, config: VoiceControllerConfig = None, container: DIContainer = None):
        self.config = config or VoiceControllerConfig()
        self.container = container or DIContainer("voice_controller")
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Состояние
        self._state = VoiceControllerState.STOPPED
        self._mode = self.config.mode
        self._current_session: Optional[VoiceSession] = None
        self._is_running = False
        self._is_paused = False
        
        # Компоненты
        self._audio_manager: Optional[AudioManager] = None
        self._voice_recognizer: Optional[VoiceRecognizer] = None
        self._command_processor: Optional[CommandProcessor] = None
        self._response_generator: Optional[ResponseGenerator] = None
        self._error_handler: Optional[ErrorHandler] = None
        self._progress_manager: Optional[ProgressManager] = None
        
        # События и колбэки
        self._event_handlers: Dict[VoiceControllerEventType, List[Callable]] = {}
        self._state_change_callbacks: List[Callable[[VoiceControllerState], None]] = []
        
        # Синхронизация
        self._lock = threading.RLock()
        self._processing_lock = threading.Lock()
        
        # Метрики и история
        self._sessions_history: List[VoiceSession] = []
        self._events_history: List[VoiceControllerEvent] = []
        self._metrics: Dict[str, Any] = {}
        
        # Инициализация компонентов
        self._initialize_components()
        
        self.logger.info("VoiceController инициализирован")
    
    def _initialize_components(self):
        """Инициализация компонентов через DI контейнер."""
        try:
            # Регистрация зависимостей если не зарегистрированы
            if not self.container.is_registered(AudioManager):
                self.container.register_singleton(AudioManager)
            
            if not self.container.is_registered(VoiceRecognizer):
                self.container.register_singleton(VoiceRecognizer)
            
            if not self.container.is_registered(CommandProcessor):
                self.container.register_singleton(CommandProcessor)
            
            if not self.container.is_registered(ResponseGenerator):
                self.container.register_singleton(ResponseGenerator)
            
            if not self.container.is_registered(ErrorHandler):
                self.container.register_singleton(ErrorHandler)
            
            if not self.container.is_registered(ProgressManager):
                self.container.register_singleton(ProgressManager)
            
            # Разрешение зависимостей
            self._audio_manager = self.container.resolve(AudioManager)
            self._voice_recognizer = self.container.resolve(VoiceRecognizer)
            self._command_processor = self.container.resolve(CommandProcessor)
            self._response_generator = self.container.resolve(ResponseGenerator)
            self._error_handler = self.container.resolve(ErrorHandler)
            self._progress_manager = self.container.resolve(ProgressManager)
            
            # Настройка колбэков
            self._setup_component_callbacks()
            
            self.logger.info("Компоненты инициализированы")
            
        except Exception as e:
            self.logger.error(f"Ошибка инициализации компонентов: {e}")
            self._handle_error(e, "component_initialization")
    
    def _setup_component_callbacks(self):
        """Настройка колбэков компонентов."""
        if self._audio_manager:
            self._audio_manager.add_audio_callback(self._on_audio_data)
        
        if self._voice_recognizer:
            self._voice_recognizer.add_recognition_callback(self._on_recognition_result)
    
    def start(self, user_id: Optional[str] = None) -> bool:
        """Запуск контроллера."""
        with self._lock:
            if self._state != VoiceControllerState.STOPPED:
                self.logger.warning("Контроллер уже запущен")
                return False
            
            try:
                self._set_state(VoiceControllerState.STARTING)
                
                # Создание новой сессии
                session_id = f"session_{datetime.now().timestamp()}_{hash(user_id or 'anonymous') % 10000}"
                self._current_session = VoiceSession(
                    id=session_id,
                    user_id=user_id,
                    start_time=datetime.now()
                )
                
                # Запуск компонентов
                if not self._start_components():
                    self._set_state(VoiceControllerState.ERROR)
                    return False
                
                self._is_running = True
                self._set_state(VoiceControllerState.LISTENING)
                
                # Событие начала сессии
                self._emit_event(VoiceControllerEventType.SESSION_STARTED, {
                    "session_id": session_id,
                    "user_id": user_id
                })
                
                self.logger.info(f"Контроллер запущен, сессия: {session_id}")
                return True
                
            except Exception as e:
                self.logger.error(f"Ошибка запуска контроллера: {e}")
                self._handle_error(e, "controller_start")
                self._set_state(VoiceControllerState.ERROR)
                return False
    
    def stop(self) -> bool:
        """Остановка контроллера."""
        with self._lock:
            if self._state == VoiceControllerState.STOPPED:
                return True
            
            try:
                self._is_running = False
                
                # Остановка компонентов
                self._stop_components()
                
                # Завершение сессии
                if self._current_session:
                    self._current_session.end_time = datetime.now()
                    self._sessions_history.append(self._current_session)
                    
                    # Событие завершения сессии
                    self._emit_event(VoiceControllerEventType.SESSION_ENDED, {
                        "session_id": self._current_session.id,
                        "duration": (self._current_session.end_time - self._current_session.start_time).total_seconds(),
                        "commands_count": self._current_session.commands_count
                    })
                    
                    self._current_session = None
                
                self._set_state(VoiceControllerState.STOPPED)
                self.logger.info("Контроллер остановлен")
                return True
                
            except Exception as e:
                self.logger.error(f"Ошибка остановки контроллера: {e}")
                self._handle_error(e, "controller_stop")
                return False
    
    def pause(self) -> bool:
        """Приостановка контроллера."""
        with self._lock:
            if self._state not in [VoiceControllerState.LISTENING, VoiceControllerState.PROCESSING]:
                return False
            
            self._is_paused = True
            self._set_state(VoiceControllerState.PAUSED)
            
            if self._audio_manager:
                self._audio_manager.pause_capture()
            
            self.logger.info("Контроллер приостановлен")
            return True
    
    def resume(self) -> bool:
        """Возобновление работы контроллера."""
        with self._lock:
            if self._state != VoiceControllerState.PAUSED:
                return False
            
            self._is_paused = False
            self._set_state(VoiceControllerState.LISTENING)
            
            if self._audio_manager:
                self._audio_manager.resume_capture()
            
            self.logger.info("Контроллер возобновлен")
            return True
    
    def process_text_command(self, text: str, context: Dict[str, Any] = None) -> Optional[Response]:
        """Обработка текстовой команды."""
        if not self._is_running:
            self.logger.warning("Контроллер не запущен")
            return None
        
        try:
            with self._processing_lock:
                self._set_state(VoiceControllerState.PROCESSING)
                
                # Создание команды
                command = Command(
                    text=text,
                    confidence=1.0,
                    timestamp=datetime.now(),
                    context=context or {},
                    session_id=self._current_session.id if self._current_session else None
                )
                
                # Обработка команды
                response = self._process_command(command)
                
                self._set_state(VoiceControllerState.LISTENING)
                return response
                
        except Exception as e:
            self.logger.error(f"Ошибка обработки текстовой команды: {e}")
            self._handle_error(e, "text_command_processing")
            self._set_state(VoiceControllerState.LISTENING)
            return None
    
    def _start_components(self) -> bool:
        """Запуск компонентов."""
        try:
            # Запуск аудио менеджера
            if self._audio_manager and not self._audio_manager.start_capture():
                self.logger.error("Не удалось запустить аудио менеджер")
                return False
            
            # Настройка распознавания речи
            if self._voice_recognizer:
                config = RecognitionConfig(
                    language=self.config.language,
                    timeout=self.config.recognition_timeout,
                    confidence_threshold=self.config.confidence_threshold
                )
                self._voice_recognizer.configure(config)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка запуска компонентов: {e}")
            return False
    
    def _stop_components(self):
        """Остановка компонентов."""
        try:
            if self._audio_manager:
                self._audio_manager.stop_capture()
        except Exception as e:
            self.logger.error(f"Ошибка остановки компонентов: {e}")
    
    def _on_audio_data(self, audio_data: bytes, sample_rate: int):
        """Обработка аудио данных."""
        if not self._is_running or self._is_paused:
            return
        
        try:
            # Событие обнаружения аудио
            self._emit_event(VoiceControllerEventType.AUDIO_DETECTED, {
                "data_size": len(audio_data),
                "sample_rate": sample_rate
            })
            
            # Распознавание речи
            if self._voice_recognizer:
                self._voice_recognizer.recognize_audio_async(audio_data, sample_rate)
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки аудио: {e}")
            self._handle_error(e, "audio_processing")
    
    def _on_recognition_result(self, result: RecognitionResult):
        """Обработка результата распознавания."""
        if not self._is_running or self._is_paused:
            return
        
        try:
            # Событие завершения распознавания
            self._emit_event(VoiceControllerEventType.RECOGNITION_COMPLETED, {
                "text": result.text,
                "confidence": result.confidence,
                "success": result.success
            })
            
            if result.success and result.confidence >= self.config.confidence_threshold:
                # Создание команды
                command = Command(
                    text=result.text,
                    confidence=result.confidence,
                    timestamp=datetime.now(),
                    context=result.metadata,
                    session_id=self._current_session.id if self._current_session else None
                )
                
                # Обработка команды
                self._process_command_async(command)
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки результата распознавания: {e}")
            self._handle_error(e, "recognition_result_processing")
    
    def _process_command_async(self, command: Command):
        """Асинхронная обработка команды."""
        def process():
            try:
                with self._processing_lock:
                    self._set_state(VoiceControllerState.PROCESSING)
                    self._process_command(command)
                    self._set_state(VoiceControllerState.LISTENING)
            except Exception as e:
                self.logger.error(f"Ошибка асинхронной обработки команды: {e}")
                self._handle_error(e, "async_command_processing")
                self._set_state(VoiceControllerState.LISTENING)
        
        thread = threading.Thread(target=process, daemon=True)
        thread.start()
    
    def _process_command(self, command: Command) -> Optional[Response]:
        """Обработка команды."""
        try:
            # Событие получения команды
            self._emit_event(VoiceControllerEventType.COMMAND_RECEIVED, {
                "command_id": command.id,
                "text": command.text,
                "confidence": command.confidence
            })
            
            # Обработка через процессор команд
            if self._command_processor:
                result = self._command_processor.process_command(command)
                command.result = result
                
                # Событие выполнения команды
                self._emit_event(VoiceControllerEventType.COMMAND_EXECUTED, {
                    "command_id": command.id,
                    "success": result.success if result else False,
                    "message": result.message if result else None
                })
            
            # Генерация ответа
            response = None
            if self.config.response_enabled and self._response_generator:
                context = ResponseContext(
                    user_id=self._current_session.user_id if self._current_session else None,
                    session_id=self._current_session.id if self._current_session else None,
                    language=self.config.language
                )
                
                response = self._response_generator.generate_response(command, context)
                
                # Событие генерации ответа
                self._emit_event(VoiceControllerEventType.RESPONSE_GENERATED, {
                    "response_id": response.id,
                    "text": response.text,
                    "command_id": command.id
                })
            
            # Обновление статистики сессии
            if self._current_session:
                self._current_session.commands_count += 1
                if command.result and command.result.success:
                    self._current_session.successful_commands += 1
                else:
                    self._current_session.failed_commands += 1
            
            return response
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки команды: {e}")
            self._handle_error(e, "command_processing")
            return None
    
    def _set_state(self, new_state: VoiceControllerState):
        """Установка нового состояния."""
        if self._state != new_state:
            old_state = self._state
            self._state = new_state
            
            # Событие изменения состояния
            self._emit_event(VoiceControllerEventType.STATE_CHANGED, {
                "old_state": old_state.value,
                "new_state": new_state.value
            })
            
            # Вызов колбэков
            for callback in self._state_change_callbacks:
                try:
                    callback(new_state)
                except Exception as e:
                    self.logger.error(f"Ошибка в колбэке изменения состояния: {e}")
            
            self.logger.debug(f"Состояние изменено: {old_state.value} -> {new_state.value}")
    
    def _emit_event(self, event_type: VoiceControllerEventType, data: Dict[str, Any]):
        """Генерация события."""
        event = VoiceControllerEvent(
            type=event_type,
            timestamp=datetime.now(),
            data=data,
            session_id=self._current_session.id if self._current_session else None
        )
        
        # Добавление в историю
        self._events_history.append(event)
        if len(self._events_history) > 1000:  # Ограничение размера истории
            self._events_history = self._events_history[-500:]
        
        # Вызов обработчиков событий
        handlers = self._event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                self.logger.error(f"Ошибка в обработчике события {event_type.value}: {e}")
    
    def _handle_error(self, exception: Exception, operation: str):
        """Обработка ошибки."""
        if self._error_handler:
            context = ErrorContext(
                component="VoiceController",
                operation=operation,
                session_id=self._current_session.id if self._current_session else None
            )
            self._error_handler.handle_exception(exception, context)
        
        # Событие ошибки
        self._emit_event(VoiceControllerEventType.ERROR_OCCURRED, {
            "error": str(exception),
            "operation": operation
        })
    
    # Публичные методы для управления
    
    def get_state(self) -> VoiceControllerState:
        """Получение текущего состояния."""
        return self._state
    
    def get_current_session(self) -> Optional[VoiceSession]:
        """Получение текущей сессии."""
        return self._current_session
    
    def add_state_change_callback(self, callback: Callable[[VoiceControllerState], None]):
        """Добавление колбэка изменения состояния."""
        self._state_change_callbacks.append(callback)
    
    def add_event_handler(self, event_type: VoiceControllerEventType, handler: Callable[[VoiceControllerEvent], None]):
        """Добавление обработчика событий."""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
    
    def get_sessions_history(self, limit: int = 100) -> List[VoiceSession]:
        """Получение истории сессий."""
        return self._sessions_history[-limit:]
    
    def get_events_history(self, limit: int = 100) -> List[VoiceControllerEvent]:
        """Получение истории событий."""
        return self._events_history[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики."""
        with self._lock:
            total_sessions = len(self._sessions_history)
            total_commands = sum(session.commands_count for session in self._sessions_history)
            successful_commands = sum(session.successful_commands for session in self._sessions_history)
            
            return {
                "state": self._state.value,
                "mode": self._mode.value,
                "is_running": self._is_running,
                "is_paused": self._is_paused,
                "current_session": self._current_session.id if self._current_session else None,
                "total_sessions": total_sessions,
                "total_commands": total_commands,
                "successful_commands": successful_commands,
                "success_rate": (successful_commands / total_commands * 100) if total_commands > 0 else 0,
                "total_events": len(self._events_history)
            }
    
    def export_data(self, file_path: Union[str, Path], include_events: bool = True):
        """Экспорт данных в файл."""
        data = {
            "config": {
                "mode": self.config.mode.value,
                "language": self.config.language,
                "confidence_threshold": self.config.confidence_threshold
            },
            "statistics": self.get_statistics(),
            "sessions": []
        }
        
        # Экспорт сессий
        for session in self._sessions_history:
            session_data = {
                "id": session.id,
                "user_id": session.user_id,
                "start_time": session.start_time.isoformat(),
                "end_time": session.end_time.isoformat() if session.end_time else None,
                "commands_count": session.commands_count,
                "successful_commands": session.successful_commands,
                "failed_commands": session.failed_commands,
                "total_audio_duration": session.total_audio_duration
            }
            data["sessions"].append(session_data)
        
        # Экспорт событий
        if include_events:
            data["events"] = []
            for event in self._events_history:
                event_data = {
                    "type": event.type.value,
                    "timestamp": event.timestamp.isoformat(),
                    "session_id": event.session_id,
                    "data": event.data
                }
                data["events"].append(event_data)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def dispose(self):
        """Освобождение ресурсов."""
        try:
            self.stop()
            
            # Очистка истории
            self._sessions_history.clear()
            self._events_history.clear()
            self._event_handlers.clear()
            self._state_change_callbacks.clear()
            
            # Освобождение контейнера
            if self.container:
                self.container.clear()
            
            self.logger.info("VoiceController освобожден")
            
        except Exception as e:
            self.logger.error(f"Ошибка освобождения ресурсов: {e}")


# Функция для создания контроллера с настройками по умолчанию
def create_voice_controller(
    mode: VoiceControllerMode = VoiceControllerMode.CONTINUOUS,
    language: str = "ru",
    auto_start: bool = False
) -> VoiceController:
    """Создание контроллера голосового управления с настройками по умолчанию."""
    config = VoiceControllerConfig(
        mode=mode,
        language=language,
        auto_start=auto_start
    )
    
    return VoiceController(config)