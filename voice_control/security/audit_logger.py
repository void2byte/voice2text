"""Audit Logger for security events tracking.

Логгер аудита для отслеживания событий безопасности
с поддержкой различных уровней логирования и форматов.
"""

import os
import json
import time
import threading
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime, timezone
from enum import Enum
import hashlib
import uuid

from ..utils.logger import PerformanceLogger


class SecurityEventType(Enum):
    """Типы событий безопасности."""
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    AUTHENTICATION_SUCCESS = "authentication_success"
    AUTHENTICATION_FAILURE = "authentication_failure"
    CREDENTIALS_STORED = "credentials_stored"
    CREDENTIALS_ACCESSED = "credentials_accessed"
    CREDENTIALS_DELETED = "credentials_deleted"
    ENCRYPTION_KEY_ROTATED = "encryption_key_rotated"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    SYSTEM_ERROR = "system_error"
    CONFIGURATION_CHANGED = "configuration_changed"
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    SECURITY_VIOLATION = "security_violation"


class SecurityLevel(Enum):
    """Уровни безопасности событий."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityEvent:
    """Событие безопасности."""
    event_id: str
    timestamp: float
    event_type: str
    security_level: str
    message: str
    details: Dict[str, Any]
    source_ip: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    component: Optional[str] = None
    action: Optional[str] = None
    resource: Optional[str] = None
    result: Optional[str] = None
    risk_score: Optional[int] = None
    tags: Optional[List[str]] = None


class AuditLogger:
    """Логгер аудита для отслеживания событий безопасности.
    
    Обеспечивает централизованное логирование событий безопасности
    с поддержкой различных форматов вывода и уровней детализации.
    """
    
    def __init__(self, 
                 component_name: str,
                 log_dir: Optional[str] = None,
                 max_log_size: int = 10 * 1024 * 1024,  # 10MB
                 max_log_files: int = 5,
                 enable_console_output: bool = False):
        """Инициализация логгера аудита.
        
        Args:
            component_name: Название компонента
            log_dir: Директория для логов
            max_log_size: Максимальный размер лог-файла
            max_log_files: Максимальное количество лог-файлов
            enable_console_output: Включить вывод в консоль
        """
        self._component_name = component_name
        self._logger = PerformanceLogger(f"AuditLogger-{component_name}")
        
        # Настройка директории логов
        if log_dir:
            self._log_dir = Path(log_dir)
        else:
            self._log_dir = Path.home() / ".voice_control" / "audit_logs"
        
        self._log_dir.mkdir(parents=True, exist_ok=True)
        
        # Настройки ротации логов
        self._max_log_size = max_log_size
        self._max_log_files = max_log_files
        self._enable_console_output = enable_console_output
        
        # Текущий лог-файл
        self._current_log_file = self._get_current_log_file()
        
        # Блокировка для потокобезопасности
        self._lock = threading.RLock()
        
        # Кэш событий для анализа
        self._events_cache: List[SecurityEvent] = []
        self._max_cache_size = 1000
        
        # Счетчики событий
        self._event_counters: Dict[str, int] = {}
        
        # Настройки фильтрации
        self._min_security_level = SecurityLevel.LOW
        self._enabled_event_types: set = set(SecurityEventType)
        
        self._logger.info(f"AuditLogger initialized for component: {component_name}")
        self._log_system_event("audit_logger_initialized", "Audit logger started", {})
    
    def _get_current_log_file(self) -> Path:
        """Получение пути к текущему лог-файлу.
        
        Returns:
            Путь к лог-файлу
        """
        timestamp = datetime.now().strftime("%Y%m%d")
        return self._log_dir / f"audit_{self._component_name}_{timestamp}.log"
    
    def _should_rotate_log(self) -> bool:
        """Проверка необходимости ротации лога.
        
        Returns:
            True если нужна ротация
        """
        if not self._current_log_file.exists():
            return False
        
        return self._current_log_file.stat().st_size >= self._max_log_size
    
    def _rotate_log(self) -> None:
        """Ротация лог-файлов."""
        try:
            # Получение списка существующих лог-файлов
            log_pattern = f"audit_{self._component_name}_*.log"
            existing_logs = sorted(
                self._log_dir.glob(log_pattern),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            # Удаление старых логов
            if len(existing_logs) >= self._max_log_files:
                for old_log in existing_logs[self._max_log_files-1:]:
                    try:
                        old_log.unlink()
                        self._logger.info(f"Deleted old audit log: {old_log}")
                    except Exception as e:
                        self._logger.error(f"Failed to delete old log {old_log}: {e}")
            
            # Создание нового лог-файла
            self._current_log_file = self._get_current_log_file()
            
            self._logger.info(f"Log rotated to: {self._current_log_file}")
            
        except Exception as e:
            self._logger.error(f"Log rotation failed: {e}")
    
    def _write_to_log(self, event: SecurityEvent) -> None:
        """Запись события в лог-файл.
        
        Args:
            event: Событие для записи
        """
        try:
            # Проверка ротации
            if self._should_rotate_log():
                self._rotate_log()
            
            # Формирование записи
            log_entry = {
                "timestamp": datetime.fromtimestamp(event.timestamp, tz=timezone.utc).isoformat(),
                "event_id": event.event_id,
                "component": self._component_name,
                "event_type": event.event_type,
                "security_level": event.security_level,
                "message": event.message,
                "details": event.details,
                "source_ip": event.source_ip,
                "user_agent": event.user_agent,
                "session_id": event.session_id,
                "user_id": event.user_id,
                "action": event.action,
                "resource": event.resource,
                "result": event.result,
                "risk_score": event.risk_score,
                "tags": event.tags or []
            }
            
            # Запись в файл
            with open(self._current_log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
            
            # Установка безопасных прав доступа
            os.chmod(self._current_log_file, 0o600)
            
            # Вывод в консоль если включен
            if self._enable_console_output:
                print(f"[AUDIT] {event.security_level.upper()}: {event.message}")
            
        except Exception as e:
            self._logger.error(f"Failed to write audit log: {e}")
    
    def _generate_event_id(self) -> str:
        """Генерация уникального ID события.
        
        Returns:
            Уникальный ID
        """
        return str(uuid.uuid4())
    
    def _calculate_risk_score(self, event_type: str, security_level: str, details: Dict[str, Any]) -> int:
        """Расчет оценки риска события.
        
        Args:
            event_type: Тип события
            security_level: Уровень безопасности
            details: Детали события
            
        Returns:
            Оценка риска (0-100)
        """
        base_scores = {
            SecurityLevel.LOW.value: 10,
            SecurityLevel.MEDIUM.value: 30,
            SecurityLevel.HIGH.value: 60,
            SecurityLevel.CRITICAL.value: 90
        }
        
        risk_score = base_scores.get(security_level, 10)
        
        # Дополнительные факторы риска
        if "failed_attempts" in details:
            attempts = details["failed_attempts"]
            if attempts > 3:
                risk_score += min(attempts * 5, 30)
        
        if "suspicious_patterns" in details:
            risk_score += 20
        
        if "privilege_escalation" in details:
            risk_score += 25
        
        return min(risk_score, 100)
    
    def log_security_event(self, 
                          event_type: Union[str, SecurityEventType],
                          message: str,
                          details: Dict[str, Any],
                          security_level: Union[str, SecurityLevel] = SecurityLevel.MEDIUM,
                          source_ip: Optional[str] = None,
                          user_agent: Optional[str] = None,
                          session_id: Optional[str] = None,
                          user_id: Optional[str] = None,
                          action: Optional[str] = None,
                          resource: Optional[str] = None,
                          result: Optional[str] = None,
                          tags: Optional[List[str]] = None) -> str:
        """Логирование события безопасности.
        
        Args:
            event_type: Тип события
            message: Сообщение о событии
            details: Детали события
            security_level: Уровень безопасности
            source_ip: IP-адрес источника
            user_agent: User Agent
            session_id: ID сессии
            user_id: ID пользователя
            action: Выполненное действие
            resource: Ресурс, к которому был доступ
            result: Результат операции
            tags: Теги для категоризации
            
        Returns:
            ID созданного события
        """
        with self._lock:
            # Преобразование enum в строку
            if isinstance(event_type, SecurityEventType):
                event_type = event_type.value
            if isinstance(security_level, SecurityLevel):
                security_level = security_level.value
            
            # Проверка фильтров
            if not self._should_log_event(event_type, security_level):
                return ""
            
            # Создание события
            event_id = self._generate_event_id()
            current_time = time.time()
            
            # Расчет оценки риска
            risk_score = self._calculate_risk_score(event_type, security_level, details)
            
            event = SecurityEvent(
                event_id=event_id,
                timestamp=current_time,
                event_type=event_type,
                security_level=security_level,
                message=message,
                details=details.copy(),
                source_ip=source_ip,
                user_agent=user_agent,
                session_id=session_id,
                user_id=user_id,
                component=self._component_name,
                action=action,
                resource=resource,
                result=result,
                risk_score=risk_score,
                tags=tags or []
            )
            
            # Запись в лог
            self._write_to_log(event)
            
            # Добавление в кэш
            self._add_to_cache(event)
            
            # Обновление счетчиков
            self._update_counters(event_type, security_level)
            
            # Проверка на подозрительную активность
            self._check_suspicious_activity(event)
            
            return event_id
    
    def _should_log_event(self, event_type: str, security_level: str) -> bool:
        """Проверка необходимости логирования события.
        
        Args:
            event_type: Тип события
            security_level: Уровень безопасности
            
        Returns:
            True если событие должно быть залогировано
        """
        # Проверка уровня безопасности
        level_priority = {
            SecurityLevel.LOW.value: 1,
            SecurityLevel.MEDIUM.value: 2,
            SecurityLevel.HIGH.value: 3,
            SecurityLevel.CRITICAL.value: 4
        }
        
        min_priority = level_priority.get(self._min_security_level.value, 1)
        event_priority = level_priority.get(security_level, 1)
        
        if event_priority < min_priority:
            return False
        
        # Проверка типа события
        try:
            event_enum = SecurityEventType(event_type)
            return event_enum in self._enabled_event_types
        except ValueError:
            # Неизвестный тип события - логируем
            return True
    
    def _add_to_cache(self, event: SecurityEvent) -> None:
        """Добавление события в кэш.
        
        Args:
            event: Событие для добавления
        """
        self._events_cache.append(event)
        
        # Ограничение размера кэша
        if len(self._events_cache) > self._max_cache_size:
            self._events_cache = self._events_cache[-self._max_cache_size:]
    
    def _update_counters(self, event_type: str, security_level: str) -> None:
        """Обновление счетчиков событий.
        
        Args:
            event_type: Тип события
            security_level: Уровень безопасности
        """
        self._event_counters[event_type] = self._event_counters.get(event_type, 0) + 1
        self._event_counters[f"level_{security_level}"] = self._event_counters.get(f"level_{security_level}", 0) + 1
        self._event_counters["total"] = self._event_counters.get("total", 0) + 1
    
    def _check_suspicious_activity(self, event: SecurityEvent) -> None:
        """Проверка на подозрительную активность.
        
        Args:
            event: Событие для анализа
        """
        # Анализ частоты событий
        recent_events = [
            e for e in self._events_cache
            if (event.timestamp - e.timestamp) < 300  # Последние 5 минут
            and e.event_type == event.event_type
        ]
        
        if len(recent_events) > 10:  # Более 10 событий за 5 минут
            self.log_security_event(
                SecurityEventType.SUSPICIOUS_ACTIVITY,
                f"High frequency of {event.event_type} events detected",
                {
                    "event_count": len(recent_events),
                    "time_window": 300,
                    "original_event_id": event.event_id
                },
                SecurityLevel.HIGH
            )
    
    def _log_system_event(self, event_type: str, message: str, details: Dict[str, Any]) -> None:
        """Логирование системного события.
        
        Args:
            event_type: Тип события
            message: Сообщение
            details: Детали
        """
        self.log_security_event(
            event_type,
            message,
            details,
            SecurityLevel.LOW,
            tags=["system"]
        )
    
    def set_security_level_filter(self, min_level: SecurityLevel) -> None:
        """Установка минимального уровня безопасности для логирования.
        
        Args:
            min_level: Минимальный уровень
        """
        self._min_security_level = min_level
        self._logger.info(f"Security level filter set to: {min_level.value}")
    
    def set_event_type_filter(self, enabled_types: List[SecurityEventType]) -> None:
        """Установка фильтра типов событий.
        
        Args:
            enabled_types: Список разрешенных типов событий
        """
        self._enabled_event_types = set(enabled_types)
        self._logger.info(f"Event type filter set to: {[t.value for t in enabled_types]}")
    
    def get_recent_events(self, 
                         count: int = 100,
                         event_type: Optional[str] = None,
                         security_level: Optional[str] = None,
                         time_range: Optional[int] = None) -> List[Dict[str, Any]]:
        """Получение последних событий.
        
        Args:
            count: Количество событий
            event_type: Фильтр по типу события
            security_level: Фильтр по уровню безопасности
            time_range: Временной диапазон в секундах
            
        Returns:
            Список событий
        """
        with self._lock:
            events = self._events_cache.copy()
            
            # Применение фильтров
            if time_range:
                current_time = time.time()
                events = [e for e in events if (current_time - e.timestamp) <= time_range]
            
            if event_type:
                events = [e for e in events if e.event_type == event_type]
            
            if security_level:
                events = [e for e in events if e.security_level == security_level]
            
            # Сортировка по времени (новые первыми)
            events.sort(key=lambda x: x.timestamp, reverse=True)
            
            # Ограничение количества
            events = events[:count]
            
            # Преобразование в словари
            return [asdict(event) for event in events]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики событий.
        
        Returns:
            Статистика событий
        """
        with self._lock:
            current_time = time.time()
            
            # Статистика по времени
            last_hour = [e for e in self._events_cache if (current_time - e.timestamp) <= 3600]
            last_day = [e for e in self._events_cache if (current_time - e.timestamp) <= 86400]
            
            # Статистика по уровням безопасности
            level_stats = {}
            for level in SecurityLevel:
                level_count = len([e for e in self._events_cache if e.security_level == level.value])
                level_stats[level.value] = level_count
            
            # Топ событий
            event_type_counts = {}
            for event in self._events_cache:
                event_type_counts[event.event_type] = event_type_counts.get(event.event_type, 0) + 1
            
            top_events = sorted(event_type_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            return {
                "total_events": len(self._events_cache),
                "events_last_hour": len(last_hour),
                "events_last_day": len(last_day),
                "security_level_distribution": level_stats,
                "top_event_types": dict(top_events),
                "counters": self._event_counters.copy(),
                "cache_size": len(self._events_cache),
                "log_file": str(self._current_log_file)
            }
    
    def export_logs(self, 
                   output_file: str,
                   start_time: Optional[float] = None,
                   end_time: Optional[float] = None,
                   format_type: str = "json") -> None:
        """Экспорт логов в файл.
        
        Args:
            output_file: Путь к выходному файлу
            start_time: Начальное время (timestamp)
            end_time: Конечное время (timestamp)
            format_type: Формат экспорта (json, csv)
        """
        try:
            # Получение событий
            events = self._events_cache.copy()
            
            # Фильтрация по времени
            if start_time:
                events = [e for e in events if e.timestamp >= start_time]
            if end_time:
                events = [e for e in events if e.timestamp <= end_time]
            
            # Экспорт
            if format_type == "json":
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump([asdict(event) for event in events], f, indent=2, ensure_ascii=False)
            elif format_type == "csv":
                import csv
                with open(output_file, 'w', newline='', encoding='utf-8') as f:
                    if events:
                        writer = csv.DictWriter(f, fieldnames=asdict(events[0]).keys())
                        writer.writeheader()
                        for event in events:
                            writer.writerow(asdict(event))
            else:
                raise ValueError(f"Unsupported format: {format_type}")
            
            # Логирование экспорта
            self.log_security_event(
                SecurityEventType.DATA_EXPORT,
                f"Audit logs exported to {output_file}",
                {
                    "output_file": output_file,
                    "format": format_type,
                    "events_count": len(events),
                    "start_time": start_time,
                    "end_time": end_time
                },
                SecurityLevel.MEDIUM
            )
            
            self._logger.info(f"Logs exported to: {output_file}")
            
        except Exception as e:
            self._logger.error(f"Log export failed: {e}")
            raise RuntimeError(f"Log export failed: {e}")
    
    def clear_cache(self) -> None:
        """Очистка кэша событий."""
        with self._lock:
            self._events_cache.clear()
            self._event_counters.clear()
        
        self._log_system_event("cache_cleared", "Event cache cleared", {})
        self._logger.info("Event cache cleared")