"""Модуль унифицированной обработки ошибок."""

import logging
import traceback
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Union, Type
from datetime import datetime
import json
import sys
from pathlib import Path


class ErrorSeverity(Enum):
    """Уровни серьезности ошибок."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Категории ошибок."""
    SYSTEM = "system"
    NETWORK = "network"
    AUDIO = "audio"
    RECOGNITION = "recognition"
    COMMAND = "command"
    SECURITY = "security"
    VALIDATION = "validation"
    CONFIGURATION = "configuration"
    USER_INPUT = "user_input"
    EXTERNAL_API = "external_api"


class ErrorAction(Enum):
    """Действия при ошибках."""
    IGNORE = "ignore"
    LOG = "log"
    RETRY = "retry"
    FALLBACK = "fallback"
    NOTIFY_USER = "notify_user"
    ESCALATE = "escalate"
    SHUTDOWN = "shutdown"


@dataclass
class ErrorContext:
    """Контекст ошибки."""
    component: str
    operation: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorInfo:
    """Информация об ошибке."""
    id: str
    timestamp: datetime
    exception: Exception
    severity: ErrorSeverity
    category: ErrorCategory
    context: ErrorContext
    message: str
    stack_trace: str
    handled: bool = False
    retry_count: int = 0
    resolution: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseErrorHandler(ABC):
    """Базовый класс обработчика ошибок."""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"{self.__class__.__name__}.{name}")
    
    @abstractmethod
    def can_handle(self, error_info: ErrorInfo) -> bool:
        """Проверка возможности обработки ошибки."""
        pass
    
    @abstractmethod
    def handle(self, error_info: ErrorInfo) -> bool:
        """Обработка ошибки. Возвращает True если ошибка обработана."""
        pass
    
    def get_priority(self) -> int:
        """Приоритет обработчика (чем меньше, тем выше приоритет)."""
        return 100


class LoggingErrorHandler(BaseErrorHandler):
    """Обработчик для логирования ошибок."""
    
    def __init__(self, log_file: Optional[str] = None):
        super().__init__("logging")
        self.log_file = log_file
        
        if log_file:
            # Настройка отдельного логгера для ошибок
            self.error_logger = logging.getLogger("error_handler")
            handler = logging.FileHandler(log_file, encoding='utf-8')
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.error_logger.addHandler(handler)
            self.error_logger.setLevel(logging.ERROR)
        else:
            self.error_logger = self.logger
    
    def can_handle(self, error_info: ErrorInfo) -> bool:
        """Может обработать любую ошибку."""
        return True
    
    def handle(self, error_info: ErrorInfo) -> bool:
        """Логирование ошибки."""
        try:
            log_message = self._format_error_message(error_info)
            
            if error_info.severity == ErrorSeverity.CRITICAL:
                self.error_logger.critical(log_message)
            elif error_info.severity == ErrorSeverity.HIGH:
                self.error_logger.error(log_message)
            elif error_info.severity == ErrorSeverity.MEDIUM:
                self.error_logger.warning(log_message)
            else:
                self.error_logger.info(log_message)
            
            return True
        except Exception as e:
            self.logger.error(f"Ошибка при логировании: {e}")
            return False
    
    def _format_error_message(self, error_info: ErrorInfo) -> str:
        """Форматирование сообщения об ошибке."""
        parts = [
            f"ID: {error_info.id}",
            f"Category: {error_info.category.value}",
            f"Severity: {error_info.severity.value}",
            f"Component: {error_info.context.component}",
            f"Operation: {error_info.context.operation}",
            f"Message: {error_info.message}"
        ]
        
        if error_info.context.user_id:
            parts.append(f"User: {error_info.context.user_id}")
        
        if error_info.context.session_id:
            parts.append(f"Session: {error_info.context.session_id}")
        
        if error_info.retry_count > 0:
            parts.append(f"Retry: {error_info.retry_count}")
        
        if error_info.context.additional_data:
            parts.append(f"Data: {json.dumps(error_info.context.additional_data, ensure_ascii=False)}")
        
        parts.append(f"Stack: {error_info.stack_trace}")
        
        return " | ".join(parts)
    
    def get_priority(self) -> int:
        return 1000  # Низкий приоритет, выполняется последним


class RetryErrorHandler(BaseErrorHandler):
    """Обработчик для повторных попыток."""
    
    def __init__(self, max_retries: int = 3, retry_categories: List[ErrorCategory] = None):
        super().__init__("retry")
        self.max_retries = max_retries
        self.retry_categories = retry_categories or [
            ErrorCategory.NETWORK,
            ErrorCategory.EXTERNAL_API
        ]
    
    def can_handle(self, error_info: ErrorInfo) -> bool:
        """Проверка возможности повтора."""
        return (
            error_info.category in self.retry_categories and
            error_info.retry_count < self.max_retries and
            error_info.severity != ErrorSeverity.CRITICAL
        )
    
    def handle(self, error_info: ErrorInfo) -> bool:
        """Обработка повтора."""
        try:
            error_info.retry_count += 1
            self.logger.info(
                f"Повторная попытка {error_info.retry_count}/{self.max_retries} "
                f"для ошибки {error_info.id}"
            )
            return True
        except Exception as e:
            self.logger.error(f"Ошибка при обработке повтора: {e}")
            return False
    
    def get_priority(self) -> int:
        return 10  # Высокий приоритет


class FallbackErrorHandler(BaseErrorHandler):
    """Обработчик для fallback действий."""
    
    def __init__(self, fallback_actions: Dict[ErrorCategory, Callable] = None):
        super().__init__("fallback")
        self.fallback_actions = fallback_actions or {}
    
    def can_handle(self, error_info: ErrorInfo) -> bool:
        """Проверка наличия fallback действия."""
        return error_info.category in self.fallback_actions
    
    def handle(self, error_info: ErrorInfo) -> bool:
        """Выполнение fallback действия."""
        try:
            action = self.fallback_actions[error_info.category]
            result = action(error_info)
            
            error_info.resolution = f"Fallback action executed: {action.__name__}"
            self.logger.info(f"Выполнено fallback действие для ошибки {error_info.id}")
            
            return bool(result)
        except Exception as e:
            self.logger.error(f"Ошибка при выполнении fallback: {e}")
            return False
    
    def get_priority(self) -> int:
        return 50  # Средний приоритет


class NotificationErrorHandler(BaseErrorHandler):
    """Обработчик для уведомлений пользователя."""
    
    def __init__(self, notification_callback: Optional[Callable[[ErrorInfo], None]] = None):
        super().__init__("notification")
        self.notification_callback = notification_callback
        self.user_messages = {
            ErrorCategory.AUDIO: "Проблема с аудио устройством",
            ErrorCategory.RECOGNITION: "Не удалось распознать речь",
            ErrorCategory.NETWORK: "Проблема с сетевым соединением",
            ErrorCategory.VALIDATION: "Некорректные данные",
            ErrorCategory.USER_INPUT: "Неверный ввод",
            ErrorCategory.EXTERNAL_API: "Сервис временно недоступен"
        }
    
    def can_handle(self, error_info: ErrorInfo) -> bool:
        """Проверка необходимости уведомления."""
        return (
            error_info.severity in [ErrorSeverity.MEDIUM, ErrorSeverity.HIGH] and
            error_info.category in self.user_messages
        )
    
    def handle(self, error_info: ErrorInfo) -> bool:
        """Отправка уведомления пользователю."""
        try:
            message = self.user_messages.get(
                error_info.category,
                "Произошла ошибка в системе"
            )
            
            if self.notification_callback:
                self.notification_callback(error_info)
            else:
                # Простое уведомление через лог
                self.logger.info(f"Уведомление пользователю: {message}")
            
            error_info.resolution = f"User notified: {message}"
            return True
        except Exception as e:
            self.logger.error(f"Ошибка при отправке уведомления: {e}")
            return False
    
    def get_priority(self) -> int:
        return 20  # Высокий приоритет


class ErrorHandler:
    """Главный обработчик ошибок."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._handlers: List[BaseErrorHandler] = []
        self._error_history: List[ErrorInfo] = []
        self._error_stats: Dict[str, int] = {}
        self._lock = threading.RLock()
        
        # Регистрация обработчиков по умолчанию
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Регистрация обработчиков по умолчанию."""
        self.register_handler(LoggingErrorHandler())
        self.register_handler(RetryErrorHandler())
        self.register_handler(NotificationErrorHandler())
    
    def register_handler(self, handler: BaseErrorHandler):
        """Регистрация обработчика ошибок."""
        with self._lock:
            self._handlers.append(handler)
            # Сортировка по приоритету
            self._handlers.sort(key=lambda h: h.get_priority())
            self.logger.info(f"Зарегистрирован обработчик: {handler.name}")
    
    def handle_exception(
        self,
        exception: Exception,
        context: ErrorContext,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.SYSTEM
    ) -> ErrorInfo:
        """Обработка исключения."""
        error_info = self._create_error_info(exception, context, severity, category)
        return self.handle_error(error_info)
    
    def handle_error(self, error_info: ErrorInfo) -> ErrorInfo:
        """Обработка ошибки."""
        with self._lock:
            # Добавление в историю
            self._error_history.append(error_info)
            if len(self._error_history) > 1000:  # Ограничение размера истории
                self._error_history = self._error_history[-500:]
            
            # Обновление статистики
            category_key = error_info.category.value
            self._error_stats[category_key] = self._error_stats.get(category_key, 0) + 1
        
        # Обработка через зарегистрированные обработчики
        for handler in self._handlers:
            try:
                if handler.can_handle(error_info):
                    if handler.handle(error_info):
                        error_info.handled = True
                        self.logger.debug(f"Ошибка {error_info.id} обработана через {handler.name}")
                        break
            except Exception as e:
                self.logger.error(f"Ошибка в обработчике {handler.name}: {e}")
        
        if not error_info.handled:
            self.logger.warning(f"Ошибка {error_info.id} не была обработана")
        
        return error_info
    
    def _create_error_info(self, exception: Exception, context: ErrorContext, severity: ErrorSeverity, category: ErrorCategory) -> ErrorInfo:
        """Создание информации об ошибке."""
        timestamp = datetime.now()
        error_id = f"err_{timestamp.timestamp()}_{hash(str(exception)) % 10000}"
        
        # Получение stack trace
        stack_trace = ""
        if hasattr(exception, '__traceback__') and exception.__traceback__:
            stack_trace = ''.join(traceback.format_tb(exception.__traceback__))
        else:
            stack_trace = traceback.format_exc()
        
        return ErrorInfo(
            id=error_id,
            timestamp=timestamp,
            exception=exception,
            severity=severity,
            category=category,
            context=context,
            message=str(exception),
            stack_trace=stack_trace
        )
    
    def get_error_history(self, limit: int = 100) -> List[ErrorInfo]:
        """Получение истории ошибок."""
        with self._lock:
            return self._error_history[-limit:]
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Получение статистики ошибок."""
        with self._lock:
            total_errors = len(self._error_history)
            
            severity_stats = {}
            recent_errors = self._error_history[-100:] if self._error_history else []
            
            for error in recent_errors:
                severity = error.severity.value
                severity_stats[severity] = severity_stats.get(severity, 0) + 1
            
            return {
                "total_errors": total_errors,
                "category_stats": self._error_stats.copy(),
                "severity_stats": severity_stats,
                "handlers_count": len(self._handlers),
                "recent_errors_count": len(recent_errors)
            }
    
    def clear_history(self):
        """Очистка истории ошибок."""
        with self._lock:
            self._error_history.clear()
            self._error_stats.clear()
    
    def export_errors(self, file_path: Union[str, Path], format: str = "json"):
        """Экспорт ошибок в файл."""
        with self._lock:
            errors_data = []
            for error in self._error_history:
                error_dict = {
                    "id": error.id,
                    "timestamp": error.timestamp.isoformat(),
                    "severity": error.severity.value,
                    "category": error.category.value,
                    "message": error.message,
                    "component": error.context.component,
                    "operation": error.context.operation,
                    "handled": error.handled,
                    "retry_count": error.retry_count,
                    "resolution": error.resolution
                }
                errors_data.append(error_dict)
        
        if format.lower() == "json":
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(errors_data, f, ensure_ascii=False, indent=2)
        else:
            raise ValueError(f"Неподдерживаемый формат: {format}")


# Декораторы для обработки ошибок
def handle_errors(
    category: ErrorCategory = ErrorCategory.SYSTEM,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    component: str = None,
    reraise: bool = False
):
    """Декоратор для автоматической обработки ошибок."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context = ErrorContext(
                    component=component or func.__module__,
                    operation=func.__name__
                )
                
                # Получение глобального обработчика ошибок
                error_handler = get_error_handler()
                error_handler.handle_exception(e, context, severity, category)
                
                if reraise:
                    raise
                return None
        return wrapper
    return decorator


# Глобальный обработчик ошибок
_global_error_handler = ErrorHandler()


def get_error_handler() -> ErrorHandler:
    """Получение глобального обработчика ошибок."""
    return _global_error_handler


def handle_exception(
    exception: Exception,
    component: str,
    operation: str,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    category: ErrorCategory = ErrorCategory.SYSTEM,
    **context_data
) -> ErrorInfo:
    """Обработка исключения через глобальный обработчик."""
    context = ErrorContext(
        component=component,
        operation=operation,
        additional_data=context_data
    )
    return _global_error_handler.handle_exception(exception, context, severity, category)


def register_error_handler(handler: BaseErrorHandler):
    """Регистрация обработчика в глобальном обработчике."""
    _global_error_handler.register_handler(handler)