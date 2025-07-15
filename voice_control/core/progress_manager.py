"""Progress Manager for tracking voice control operations.

Менеджер для отслеживания прогресса операций голосового управления
с поддержкой уведомлений и метрик производительности.
"""

import time
import threading
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from enum import Enum

from ..utils.logger import PerformanceLogger


class OperationStatus(Enum):
    """Статусы операций."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ProgressInfo:
    """Информация о прогрессе операции."""
    operation_id: str
    operation_type: str
    status: OperationStatus
    progress_percent: float = 0.0
    current_step: str = ""
    total_steps: int = 0
    completed_steps: int = 0
    started_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ProgressManager:
    """Менеджер для отслеживания прогресса операций.
    
    Обеспечивает централизованное отслеживание прогресса различных операций
    с поддержкой уведомлений и метрик производительности.
    """
    
    def __init__(self):
        """Инициализация менеджера прогресса."""
        self._logger = PerformanceLogger("ProgressManager")
        self._operations: Dict[str, ProgressInfo] = {}
        self._lock = threading.RLock()
        self._callbacks: Dict[str, List[Callable]] = {
            "progress_updated": [],
            "operation_completed": [],
            "operation_failed": [],
            "operation_cancelled": []
        }
        
        # Метрики производительности
        self._metrics = {
            "total_operations": 0,
            "completed_operations": 0,
            "failed_operations": 0,
            "cancelled_operations": 0,
            "average_duration": 0.0
        }
        
        self._logger.info("ProgressManager initialized")
    
    def register_callback(self, event: str, callback: Callable) -> None:
        """Регистрация callback функции для события.
        
        Args:
            event: Тип события
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
    
    def _emit_event(self, event: str, progress_info: ProgressInfo) -> None:
        """Вызов всех callback функций для события.
        
        Args:
            event: Тип события
            progress_info: Информация о прогрессе
        """
        for callback in self._callbacks.get(event, []):
            try:
                callback(progress_info)
            except Exception as e:
                self._logger.error(f"Error in callback for {event}: {e}")
    
    def start_session(self, session_id: str, 
                     operation_type: str = "voice_recognition",
                     total_steps: int = 3,
                     metadata: Optional[Dict[str, Any]] = None) -> None:
        """Начало отслеживания сессии.
        
        Args:
            session_id: ID сессии
            operation_type: Тип операции
            total_steps: Общее количество шагов
            metadata: Дополнительные метаданные
        """
        with self._lock:
            progress_info = ProgressInfo(
                operation_id=session_id,
                operation_type=operation_type,
                status=OperationStatus.PENDING,
                total_steps=total_steps,
                metadata=metadata or {}
            )
            
            self._operations[session_id] = progress_info
            self._metrics["total_operations"] += 1
            
            self._logger.info(f"Session started: {session_id} ({operation_type})")
            self._emit_event("progress_updated", progress_info)
    
    def update_progress(self, session_id: str,
                       progress_percent: Optional[float] = None,
                       current_step: Optional[str] = None,
                       completed_steps: Optional[int] = None,
                       metadata_update: Optional[Dict[str, Any]] = None) -> None:
        """Обновление прогресса операции.
        
        Args:
            session_id: ID сессии
            progress_percent: Процент выполнения (0-100)
            current_step: Текущий шаг
            completed_steps: Количество завершенных шагов
            metadata_update: Обновления метаданных
        """
        with self._lock:
            if session_id not in self._operations:
                self._logger.warning(f"Attempt to update non-existent session: {session_id}")
                return
            
            progress_info = self._operations[session_id]
            
            # Обновление полей
            if progress_percent is not None:
                progress_info.progress_percent = max(0.0, min(100.0, progress_percent))
            
            if current_step is not None:
                progress_info.current_step = current_step
            
            if completed_steps is not None:
                progress_info.completed_steps = completed_steps
                # Автоматический расчет процента если не указан
                if progress_percent is None and progress_info.total_steps > 0:
                    progress_info.progress_percent = (
                        completed_steps / progress_info.total_steps * 100.0
                    )
            
            if metadata_update:
                progress_info.metadata.update(metadata_update)
            
            progress_info.updated_at = time.time()
            
            # Обновление статуса
            if progress_info.status == OperationStatus.PENDING:
                progress_info.status = OperationStatus.IN_PROGRESS
            
            self._logger.debug(f"Progress updated for {session_id}: {progress_info.progress_percent:.1f}%")
            self._emit_event("progress_updated", progress_info)
    
    def complete_session(self, session_id: str, result: Optional[Dict[str, Any]] = None) -> None:
        """Завершение сессии с успехом.
        
        Args:
            session_id: ID сессии
            result: Результат операции
        """
        with self._lock:
            if session_id not in self._operations:
                self._logger.warning(f"Attempt to complete non-existent session: {session_id}")
                return
            
            progress_info = self._operations[session_id]
            progress_info.status = OperationStatus.COMPLETED
            progress_info.progress_percent = 100.0
            progress_info.completed_steps = progress_info.total_steps
            progress_info.completed_at = time.time()
            progress_info.updated_at = progress_info.completed_at
            
            if result:
                progress_info.metadata["result"] = result
            
            # Обновление метрик
            self._metrics["completed_operations"] += 1
            self._update_average_duration(progress_info)
            
            self._logger.info(f"Session completed: {session_id}")
            self._emit_event("operation_completed", progress_info)
    
    def fail_session(self, session_id: str, error_message: str) -> None:
        """Завершение сессии с ошибкой.
        
        Args:
            session_id: ID сессии
            error_message: Сообщение об ошибке
        """
        with self._lock:
            if session_id not in self._operations:
                self._logger.warning(f"Attempt to fail non-existent session: {session_id}")
                return
            
            progress_info = self._operations[session_id]
            progress_info.status = OperationStatus.FAILED
            progress_info.error_message = error_message
            progress_info.completed_at = time.time()
            progress_info.updated_at = progress_info.completed_at
            
            # Обновление метрик
            self._metrics["failed_operations"] += 1
            self._update_average_duration(progress_info)
            
            self._logger.error(f"Session failed: {session_id} - {error_message}")
            self._emit_event("operation_failed", progress_info)
    
    def cancel_session(self, session_id: str) -> None:
        """Отмена сессии.
        
        Args:
            session_id: ID сессии
        """
        with self._lock:
            if session_id not in self._operations:
                self._logger.warning(f"Attempt to cancel non-existent session: {session_id}")
                return
            
            progress_info = self._operations[session_id]
            progress_info.status = OperationStatus.CANCELLED
            progress_info.completed_at = time.time()
            progress_info.updated_at = progress_info.completed_at
            
            # Обновление метрик
            self._metrics["cancelled_operations"] += 1
            self._update_average_duration(progress_info)
            
            self._logger.info(f"Session cancelled: {session_id}")
            self._emit_event("operation_cancelled", progress_info)
    
    def get_progress(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Получение информации о прогрессе сессии.
        
        Args:
            session_id: ID сессии
            
        Returns:
            Информация о прогрессе или None если сессия не найдена
        """
        with self._lock:
            if session_id not in self._operations:
                return None
            
            progress_info = self._operations[session_id]
            
            return {
                "operation_id": progress_info.operation_id,
                "operation_type": progress_info.operation_type,
                "status": progress_info.status.value,
                "progress_percent": progress_info.progress_percent,
                "current_step": progress_info.current_step,
                "total_steps": progress_info.total_steps,
                "completed_steps": progress_info.completed_steps,
                "started_at": progress_info.started_at,
                "updated_at": progress_info.updated_at,
                "completed_at": progress_info.completed_at,
                "duration": (
                    (progress_info.completed_at or time.time()) - progress_info.started_at
                ),
                "error_message": progress_info.error_message,
                "metadata": progress_info.metadata.copy()
            }
    
    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """Получение информации о всех сессиях.
        
        Returns:
            Список информации о всех сессиях
        """
        with self._lock:
            return [self.get_progress(session_id) for session_id in self._operations.keys()]
    
    def get_active_sessions(self) -> List[str]:
        """Получение списка активных сессий.
        
        Returns:
            Список ID активных сессий
        """
        with self._lock:
            return [
                session_id for session_id, progress_info in self._operations.items()
                if progress_info.status in [OperationStatus.PENDING, OperationStatus.IN_PROGRESS]
            ]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Получение метрик производительности.
        
        Returns:
            Словарь с метриками
        """
        with self._lock:
            return self._metrics.copy()
    
    def _update_average_duration(self, progress_info: ProgressInfo) -> None:
        """Обновление средней продолжительности операций.
        
        Args:
            progress_info: Информация о завершенной операции
        """
        if progress_info.completed_at:
            duration = progress_info.completed_at - progress_info.started_at
            completed_ops = (
                self._metrics["completed_operations"] + 
                self._metrics["failed_operations"] + 
                self._metrics["cancelled_operations"]
            )
            
            if completed_ops > 0:
                current_avg = self._metrics["average_duration"]
                self._metrics["average_duration"] = (
                    (current_avg * (completed_ops - 1) + duration) / completed_ops
                )
    
    def cleanup_completed_sessions(self, max_age_hours: float = 24.0) -> int:
        """Очистка завершенных сессий старше указанного времени.
        
        Args:
            max_age_hours: Максимальный возраст сессий в часах
            
        Returns:
            Количество удаленных сессий
        """
        with self._lock:
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            sessions_to_remove = []
            
            for session_id, progress_info in self._operations.items():
                if (progress_info.status in [OperationStatus.COMPLETED, 
                                            OperationStatus.FAILED, 
                                            OperationStatus.CANCELLED] and
                    progress_info.completed_at and
                    (current_time - progress_info.completed_at) > max_age_seconds):
                    
                    sessions_to_remove.append(session_id)
            
            for session_id in sessions_to_remove:
                del self._operations[session_id]
            
            if sessions_to_remove:
                self._logger.info(f"Cleaned up {len(sessions_to_remove)} old sessions")
            
            return len(sessions_to_remove)
    
    def cleanup(self) -> None:
        """Полная очистка менеджера прогресса."""
        with self._lock:
            # Отмена всех активных сессий
            active_sessions = self.get_active_sessions()
            for session_id in active_sessions:
                self.cancel_session(session_id)
            
            # Очистка всех данных
            self._operations.clear()
            
            # Сброс метрик
            self._metrics = {
                "total_operations": 0,
                "completed_operations": 0,
                "failed_operations": 0,
                "cancelled_operations": 0,
                "average_duration": 0.0
            }
            
            self._logger.info("ProgressManager cleanup completed")