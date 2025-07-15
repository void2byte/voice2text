"""Performance Logger for voice control system.

Логгер производительности для системы голосового управления
с поддержкой метрик, профилирования и мониторинга.
"""

import os
import time
import threading
import logging
import json
import psutil
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime, timezone
from contextlib import contextmanager
from functools import wraps
import traceback
import sys


@dataclass
class PerformanceMetric:
    """Метрика производительности."""
    name: str
    value: float
    unit: str
    timestamp: float
    component: str
    operation: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class OperationProfile:
    """Профиль операции."""
    operation_id: str
    component: str
    operation_name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    success: Optional[bool] = None
    error_message: Optional[str] = None
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None
    custom_metrics: Optional[Dict[str, float]] = None


class PerformanceLogger:
    """Логгер производительности для мониторинга системы.
    
    Обеспечивает сбор метрик производительности, профилирование
    операций и мониторинг ресурсов системы.
    """
    
    _instances: Dict[str, 'PerformanceLogger'] = {}
    _lock = threading.RLock()
    
    def __new__(cls, component_name: str, *args, **kwargs):
        """Singleton pattern для каждого компонента."""
        with cls._lock:
            if component_name not in cls._instances:
                instance = super().__new__(cls)
                cls._instances[component_name] = instance
            return cls._instances[component_name]
    
    def __init__(self, 
                 component_name: str,
                 log_level: int = logging.INFO,
                 log_dir: Optional[str] = None,
                 enable_file_logging: bool = True,
                 enable_console_logging: bool = True,
                 max_log_size: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 5):
        """Инициализация логгера производительности.
        
        Args:
            component_name: Название компонента
            log_level: Уровень логирования
            log_dir: Директория для логов
            enable_file_logging: Включить логирование в файл
            enable_console_logging: Включить логирование в консоль
            max_log_size: Максимальный размер лог-файла
            backup_count: Количество резервных копий
        """
        # Проверка инициализации
        if hasattr(self, '_initialized'):
            return
        
        self._component_name = component_name
        self._initialized = True
        
        # Настройка директории логов
        if log_dir:
            self._log_dir = Path(log_dir)
        else:
            self._log_dir = Path.home() / ".voice_control" / "logs"
        
        self._log_dir.mkdir(parents=True, exist_ok=True)
        
        # Настройка стандартного логгера
        self._logger = logging.getLogger(f"voice_control.{component_name}")
        self._logger.setLevel(log_level)
        
        # Очистка существующих обработчиков
        self._logger.handlers.clear()
        
        # Настройка форматтера
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Файловый обработчик
        if enable_file_logging:
            from logging.handlers import RotatingFileHandler
            log_file = self._log_dir / f"{component_name}.log"
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_log_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            self._logger.addHandler(file_handler)
        
        # Консольный обработчик
        if enable_console_logging:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self._logger.addHandler(console_handler)
        
        # Метрики производительности
        self._metrics: List[PerformanceMetric] = []
        self._operation_profiles: Dict[str, OperationProfile] = {}
        self._metrics_lock = threading.RLock()
        
        # Настройки мониторинга
        self._max_metrics_count = 10000
        self._enable_system_monitoring = True
        self._monitoring_interval = 60  # секунд
        
        # Счетчики
        self._operation_counters: Dict[str, int] = {}
        self._error_counters: Dict[str, int] = {}
        
        # Запуск мониторинга системы
        if self._enable_system_monitoring:
            self._start_system_monitoring()
        
        self.info(f"PerformanceLogger initialized for component: {component_name}")
    
    def _start_system_monitoring(self) -> None:
        """Запуск мониторинга системных ресурсов."""
        def monitor_system():
            while True:
                try:
                    # Мониторинг CPU
                    cpu_percent = psutil.cpu_percent(interval=1)
                    self.record_metric("system_cpu_usage", cpu_percent, "percent")
                    
                    # Мониторинг памяти
                    memory = psutil.virtual_memory()
                    self.record_metric("system_memory_usage", memory.percent, "percent")
                    self.record_metric("system_memory_available", memory.available / (1024**3), "GB")
                    
                    # Мониторинг диска
                    disk = psutil.disk_usage('/')
                    self.record_metric("system_disk_usage", disk.percent, "percent")
                    
                    # Мониторинг процесса
                    process = psutil.Process()
                    process_memory = process.memory_info().rss / (1024**2)  # MB
                    process_cpu = process.cpu_percent()
                    
                    self.record_metric("process_memory_usage", process_memory, "MB")
                    self.record_metric("process_cpu_usage", process_cpu, "percent")
                    
                    time.sleep(self._monitoring_interval)
                    
                except Exception as e:
                    self.error(f"System monitoring error: {e}")
                    time.sleep(self._monitoring_interval)
        
        monitor_thread = threading.Thread(target=monitor_system, daemon=True)
        monitor_thread.start()
    
    def debug(self, message: str, **kwargs) -> None:
        """Логирование отладочного сообщения."""
        self._logger.debug(self._format_message(message, **kwargs))
    
    def info(self, message: str, **kwargs) -> None:
        """Логирование информационного сообщения."""
        self._logger.info(self._format_message(message, **kwargs))
    
    def warning(self, message: str, **kwargs) -> None:
        """Логирование предупреждения."""
        self._logger.warning(self._format_message(message, **kwargs))

def setup_logging(logger_name, level=logging.INFO, log_file=None, console=True, encoding='utf-8'):
    """
    Настраивает и возвращает логгер.

    Args:
        logger_name (str): Имя логгера.
        level (int): Уровень логирования.
        log_file (str, optional): Путь к файлу лога. Defaults to None.
        console (bool, optional): Выводить ли логи в консоль. Defaults to True.
        encoding (str, optional): Кодировка файла лога. Defaults to 'utf-8'.

    Returns:
        logging.Logger: Настроенный экземпляр логгера.
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    logger.propagate = False  # Предотвращаем двойное логирование

    # Удаляем существующие обработчики, чтобы избежать дублирования
    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    if log_file:
        # Убедимся, что директория для логов существует
        log_dir = os.path.dirname(log_file)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        file_handler = logging.FileHandler(log_file, encoding=encoding)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    if console:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    return logger

    
    def error(self, message: str, **kwargs) -> None:
        """Логирование ошибки."""
        error_type = kwargs.get('error_type', 'general')
        with self._metrics_lock:
            self._error_counters[error_type] = self._error_counters.get(error_type, 0) + 1
        
        self._logger.error(self._format_message(message, **kwargs))
    
    def critical(self, message: str, **kwargs) -> None:
        """Логирование критической ошибки."""
        self._logger.critical(self._format_message(message, **kwargs))
    
    def _format_message(self, message: str, **kwargs) -> str:
        """Форматирование сообщения с дополнительными данными.
        
        Args:
            message: Основное сообщение
            **kwargs: Дополнительные данные
            
        Returns:
            Отформатированное сообщение
        """
        if kwargs:
            extra_info = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
            return f"{message} | {extra_info}"
        return message
    
    def record_metric(self, 
                     name: str, 
                     value: float, 
                     unit: str,
                     operation: Optional[str] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> None:
        """Запись метрики производительности.
        
        Args:
            name: Название метрики
            value: Значение метрики
            unit: Единица измерения
            operation: Название операции
            metadata: Дополнительные метаданные
        """
        with self._metrics_lock:
            metric = PerformanceMetric(
                name=name,
                value=value,
                unit=unit,
                timestamp=time.time(),
                component=self._component_name,
                operation=operation,
                metadata=metadata or {}
            )
            
            self._metrics.append(metric)
            
            # Ограничение количества метрик
            if len(self._metrics) > self._max_metrics_count:
                self._metrics = self._metrics[-self._max_metrics_count:]
            
            self.debug(f"Metric recorded: {name}={value} {unit}", 
                      operation=operation, metadata=metadata)
    
    @contextmanager
    def profile_operation(self, operation_name: str, **metadata):
        """Контекстный менеджер для профилирования операций.
        
        Args:
            operation_name: Название операции
            **metadata: Дополнительные метаданные
            
        Yields:
            ID операции
        """
        operation_id = f"{self._component_name}_{operation_name}_{int(time.time() * 1000)}"
        
        # Начало профилирования
        start_time = time.time()
        start_memory = self._get_memory_usage()
        start_cpu = self._get_cpu_usage()
        
        profile = OperationProfile(
            operation_id=operation_id,
            component=self._component_name,
            operation_name=operation_name,
            start_time=start_time,
            custom_metrics=metadata
        )
        
        with self._metrics_lock:
            self._operation_profiles[operation_id] = profile
            self._operation_counters[operation_name] = self._operation_counters.get(operation_name, 0) + 1
        
        try:
            self.debug(f"Operation started: {operation_name}", operation_id=operation_id)
            yield operation_id
            
            # Успешное завершение
            profile.success = True
            
        except Exception as e:
            # Ошибка в операции
            profile.success = False
            profile.error_message = str(e)
            self.error(f"Operation failed: {operation_name}", 
                      operation_id=operation_id, error=str(e))
            raise
            
        finally:
            # Завершение профилирования
            end_time = time.time()
            profile.end_time = end_time
            profile.duration = end_time - start_time
            profile.memory_usage = self._get_memory_usage() - start_memory
            profile.cpu_usage = self._get_cpu_usage() - start_cpu
            
            # Запись метрик
            self.record_metric(f"{operation_name}_duration", profile.duration, "seconds", operation_name)
            if profile.memory_usage:
                self.record_metric(f"{operation_name}_memory_delta", profile.memory_usage, "MB", operation_name)
            
            self.debug(f"Operation completed: {operation_name}", 
                      operation_id=operation_id, 
                      duration=profile.duration,
                      success=profile.success)
    
    def _get_memory_usage(self) -> float:
        """Получение текущего использования памяти в MB.
        
        Returns:
            Использование памяти в MB
        """
        try:
            process = psutil.Process()
            return process.memory_info().rss / (1024 * 1024)
        except Exception:
            return 0.0
    
    def _get_cpu_usage(self) -> float:
        """Получение текущего использования CPU.
        
        Returns:
            Использование CPU в процентах
        """
        try:
            process = psutil.Process()
            return process.cpu_percent()
        except Exception:
            return 0.0
    
    def performance_decorator(self, operation_name: Optional[str] = None):
        """Декоратор для автоматического профилирования функций.
        
        Args:
            operation_name: Название операции (по умолчанию имя функции)
            
        Returns:
            Декорированная функция
        """
        def decorator(func: Callable) -> Callable:
            op_name = operation_name or func.__name__
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                with self.profile_operation(op_name):
                    return func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def get_metrics(self, 
                   metric_name: Optional[str] = None,
                   operation: Optional[str] = None,
                   time_range: Optional[int] = None,
                   limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Получение метрик производительности.
        
        Args:
            metric_name: Фильтр по названию метрики
            operation: Фильтр по операции
            time_range: Временной диапазон в секундах
            limit: Ограничение количества результатов
            
        Returns:
            Список метрик
        """
        with self._metrics_lock:
            metrics = self._metrics.copy()
        
        # Применение фильтров
        if metric_name:
            metrics = [m for m in metrics if m.name == metric_name]
        
        if operation:
            metrics = [m for m in metrics if m.operation == operation]
        
        if time_range:
            current_time = time.time()
            metrics = [m for m in metrics if (current_time - m.timestamp) <= time_range]
        
        # Сортировка по времени (новые первыми)
        metrics.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Ограничение количества
        if limit:
            metrics = metrics[:limit]
        
        return [asdict(metric) for metric in metrics]
    
    def get_operation_profiles(self, 
                              operation_name: Optional[str] = None,
                              success_only: Optional[bool] = None,
                              limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Получение профилей операций.
        
        Args:
            operation_name: Фильтр по названию операции
            success_only: Фильтр по успешности операций
            limit: Ограничение количества результатов
            
        Returns:
            Список профилей операций
        """
        with self._metrics_lock:
            profiles = list(self._operation_profiles.values())
        
        # Применение фильтров
        if operation_name:
            profiles = [p for p in profiles if p.operation_name == operation_name]
        
        if success_only is not None:
            profiles = [p for p in profiles if p.success == success_only]
        
        # Сортировка по времени начала (новые первыми)
        profiles.sort(key=lambda x: x.start_time, reverse=True)
        
        # Ограничение количества
        if limit:
            profiles = profiles[:limit]
        
        return [asdict(profile) for profile in profiles]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики производительности.
        
        Returns:
            Статистика производительности
        """
        with self._metrics_lock:
            current_time = time.time()
            
            # Общая статистика
            total_operations = sum(self._operation_counters.values())
            total_errors = sum(self._error_counters.values())
            
            # Статистика за последний час
            recent_metrics = [m for m in self._metrics if (current_time - m.timestamp) <= 3600]
            recent_profiles = [p for p in self._operation_profiles.values() 
                             if p.start_time and (current_time - p.start_time) <= 3600]
            
            # Средняя длительность операций
            completed_profiles = [p for p in self._operation_profiles.values() if p.duration is not None]
            avg_duration = sum(p.duration for p in completed_profiles) / len(completed_profiles) if completed_profiles else 0
            
            # Успешность операций
            success_rate = 0
            if completed_profiles:
                successful = len([p for p in completed_profiles if p.success])
                success_rate = (successful / len(completed_profiles)) * 100
            
            return {
                "component": self._component_name,
                "total_metrics": len(self._metrics),
                "total_operations": total_operations,
                "total_errors": total_errors,
                "recent_metrics_count": len(recent_metrics),
                "recent_operations_count": len(recent_profiles),
                "average_operation_duration": avg_duration,
                "success_rate": success_rate,
                "operation_counters": self._operation_counters.copy(),
                "error_counters": self._error_counters.copy(),
                "memory_usage_mb": self._get_memory_usage(),
                "cpu_usage_percent": self._get_cpu_usage()
            }
    
    def export_metrics(self, output_file: str, format_type: str = "json") -> None:
        """Экспорт метрик в файл.
        
        Args:
            output_file: Путь к выходному файлу
            format_type: Формат экспорта (json, csv)
        """
        try:
            metrics_data = {
                "component": self._component_name,
                "export_timestamp": time.time(),
                "metrics": self.get_metrics(),
                "operation_profiles": self.get_operation_profiles(),
                "statistics": self.get_statistics()
            }
            
            if format_type == "json":
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(metrics_data, f, indent=2, ensure_ascii=False)
            elif format_type == "csv":
                import csv
                with open(output_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    
                    # Заголовки для метрик
                    writer.writerow(["Type", "Name", "Value", "Unit", "Timestamp", "Operation"])
                    
                    # Метрики
                    for metric in metrics_data["metrics"]:
                        writer.writerow([
                            "metric",
                            metric["name"],
                            metric["value"],
                            metric["unit"],
                            metric["timestamp"],
                            metric.get("operation", "")
                        ])
            else:
                raise ValueError(f"Unsupported format: {format_type}")
            
            self.info(f"Metrics exported to: {output_file}")
            
        except Exception as e:
            self.error(f"Metrics export failed: {e}")
            raise RuntimeError(f"Metrics export failed: {e}")
    
    def clear_metrics(self) -> None:
        """Очистка всех метрик и профилей."""
        with self._metrics_lock:
            self._metrics.clear()
            self._operation_profiles.clear()
            self._operation_counters.clear()
            self._error_counters.clear()
        
        self.info("All metrics and profiles cleared")
    
    def set_max_metrics_count(self, count: int) -> None:
        """Установка максимального количества метрик.
        
        Args:
            count: Максимальное количество метрик
        """
        self._max_metrics_count = count
        self.info(f"Max metrics count set to: {count}")
    
    @classmethod
    def get_logger(cls, component_name: str) -> 'PerformanceLogger':
        """Получение экземпляра логгера для компонента.
        
        Args:
            component_name: Название компонента
            
        Returns:
            Экземпляр логгера
        """
        return cls(component_name)