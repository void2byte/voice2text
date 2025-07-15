"""Модуль обработки и интерпретации голосовых команд."""

import re
import logging
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Callable, Any, Union, Pattern
from datetime import datetime
import json
from pathlib import Path


class CommandType(Enum):
    """Типы команд."""
    SYSTEM = "system"  # Системные команды
    NAVIGATION = "navigation"  # Навигация
    CONTROL = "control"  # Управление
    QUERY = "query"  # Запросы
    CUSTOM = "custom"  # Пользовательские команды


class CommandPriority(Enum):
    """Приоритеты команд."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class CommandStatus(Enum):
    """Статусы выполнения команд."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class CommandContext:
    """Контекст выполнения команды."""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    language: str = "ru"
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CommandResult:
    """Результат выполнения команды."""
    success: bool
    message: str
    data: Any = None
    execution_time: float = 0.0
    error: Optional[Exception] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Command:
    """Представление команды."""
    id: str
    text: str
    command_type: CommandType
    priority: CommandPriority = CommandPriority.NORMAL
    parameters: Dict[str, Any] = field(default_factory=dict)
    context: CommandContext = field(default_factory=CommandContext)
    status: CommandStatus = CommandStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    executed_at: Optional[datetime] = None
    result: Optional[CommandResult] = None


class CommandPattern:
    """Паттерн для распознавания команд."""
    
    def __init__(
        self,
        pattern: Union[str, Pattern],
        command_type: CommandType,
        handler: Callable,
        priority: CommandPriority = CommandPriority.NORMAL,
        description: str = "",
        examples: List[str] = None,
        parameters: Dict[str, str] = None
    ):
        self.pattern = re.compile(pattern) if isinstance(pattern, str) else pattern
        self.command_type = command_type
        self.handler = handler
        self.priority = priority
        self.description = description
        self.examples = examples or []
        self.parameters = parameters or {}  # Описание параметров
    
    def match(self, text: str) -> Optional[Dict[str, Any]]:
        """Проверка соответствия текста паттерну."""
        match = self.pattern.search(text.lower())
        if match:
            return match.groupdict()
        return None
    
    def extract_parameters(self, text: str) -> Dict[str, Any]:
        """Извлечение параметров из текста."""
        match_result = self.match(text)
        if match_result:
            # Обработка извлеченных параметров
            processed_params = {}
            for key, value in match_result.items():
                if value is not None:
                    # Попытка конвертации типов
                    if key in self.parameters:
                        param_type = self.parameters[key]
                        if param_type == 'int':
                            try:
                                processed_params[key] = int(value)
                            except ValueError:
                                processed_params[key] = value
                        elif param_type == 'float':
                            try:
                                processed_params[key] = float(value)
                            except ValueError:
                                processed_params[key] = value
                        else:
                            processed_params[key] = value
                    else:
                        processed_params[key] = value
            return processed_params
        return {}


class BaseCommandHandler(ABC):
    """Базовый класс для обработчиков команд."""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"{self.__class__.__name__}.{name}")
    
    @abstractmethod
    def execute(self, command: Command) -> CommandResult:
        """Выполнение команды."""
        pass
    
    def validate(self, command: Command) -> bool:
        """Валидация команды перед выполнением."""
        return True
    
    def can_handle(self, command: Command) -> bool:
        """Проверка возможности обработки команды."""
        return True


class SystemCommandHandler(BaseCommandHandler):
    """Обработчик системных команд."""
    
    def __init__(self):
        super().__init__("system")
    
    def execute(self, command: Command) -> CommandResult:
        """Выполнение системной команды."""
        start_time = datetime.now()
        
        try:
            text = command.text.lower()
            
            if "помощь" in text or "справка" in text:
                return CommandResult(
                    success=True,
                    message="Доступные команды: помощь, статус, выход",
                    execution_time=(datetime.now() - start_time).total_seconds()
                )
            elif "статус" in text:
                return CommandResult(
                    success=True,
                    message="Система работает нормально",
                    data={"status": "ok", "timestamp": datetime.now().isoformat()},
                    execution_time=(datetime.now() - start_time).total_seconds()
                )
            elif "выход" in text or "стоп" in text:
                return CommandResult(
                    success=True,
                    message="Завершение работы",
                    data={"action": "shutdown"},
                    execution_time=(datetime.now() - start_time).total_seconds()
                )
            else:
                return CommandResult(
                    success=False,
                    message="Неизвестная системная команда",
                    execution_time=(datetime.now() - start_time).total_seconds()
                )
                
        except Exception as e:
            self.logger.error(f"Ошибка выполнения системной команды: {e}")
            return CommandResult(
                success=False,
                message=f"Ошибка: {str(e)}",
                error=e,
                execution_time=(datetime.now() - start_time).total_seconds()
            )


class NavigationCommandHandler(BaseCommandHandler):
    """Обработчик команд навигации."""
    
    def __init__(self):
        super().__init__("navigation")
    
    def execute(self, command: Command) -> CommandResult:
        """Выполнение команды навигации."""
        start_time = datetime.now()
        
        try:
            text = command.text.lower()
            parameters = command.parameters
            
            if "открой" in text or "перейди" in text:
                target = parameters.get('target', 'главная страница')
                return CommandResult(
                    success=True,
                    message=f"Переход к: {target}",
                    data={"action": "navigate", "target": target},
                    execution_time=(datetime.now() - start_time).total_seconds()
                )
            elif "назад" in text:
                return CommandResult(
                    success=True,
                    message="Возврат назад",
                    data={"action": "back"},
                    execution_time=(datetime.now() - start_time).total_seconds()
                )
            elif "вперед" in text:
                return CommandResult(
                    success=True,
                    message="Переход вперед",
                    data={"action": "forward"},
                    execution_time=(datetime.now() - start_time).total_seconds()
                )
            else:
                return CommandResult(
                    success=False,
                    message="Неизвестная команда навигации",
                    execution_time=(datetime.now() - start_time).total_seconds()
                )
                
        except Exception as e:
            self.logger.error(f"Ошибка выполнения команды навигации: {e}")
            return CommandResult(
                success=False,
                message=f"Ошибка: {str(e)}",
                error=e,
                execution_time=(datetime.now() - start_time).total_seconds()
            )


class CommandProcessor:
    """Главный процессор команд."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._patterns: List[CommandPattern] = []
        self._handlers: Dict[CommandType, BaseCommandHandler] = {}
        self._command_history: List[Command] = []
        self._active_commands: Dict[str, Command] = {}
        self._lock = threading.RLock()
        
        # Регистрация базовых обработчиков
        self._register_default_handlers()
        self._register_default_patterns()
    
    def _register_default_handlers(self):
        """Регистрация обработчиков по умолчанию."""
        self.register_handler(CommandType.SYSTEM, SystemCommandHandler())
        self.register_handler(CommandType.NAVIGATION, NavigationCommandHandler())
    
    def _register_default_patterns(self):
        """Регистрация паттернов по умолчанию."""
        # Системные команды
        self.add_pattern(
            r"(помощь|справка|help)",
            CommandType.SYSTEM,
            lambda cmd: self._handlers[CommandType.SYSTEM].execute(cmd),
            description="Показать справку",
            examples=["помощь", "справка"]
        )
        
        self.add_pattern(
            r"(статус|состояние|status)",
            CommandType.SYSTEM,
            lambda cmd: self._handlers[CommandType.SYSTEM].execute(cmd),
            description="Показать статус системы",
            examples=["статус", "состояние"]
        )
        
        self.add_pattern(
            r"(выход|стоп|завершить|exit|stop)",
            CommandType.SYSTEM,
            lambda cmd: self._handlers[CommandType.SYSTEM].execute(cmd),
            description="Завершить работу",
            examples=["выход", "стоп", "завершить"]
        )
        
        # Команды навигации
        self.add_pattern(
            r"(открой|перейди|открыть)\s+(?P<target>.+)",
            CommandType.NAVIGATION,
            lambda cmd: self._handlers[CommandType.NAVIGATION].execute(cmd),
            description="Открыть или перейти к указанному объекту",
            examples=["открой файл", "перейди на главную"],
            parameters={"target": "str"}
        )
        
        self.add_pattern(
            r"(назад|back)",
            CommandType.NAVIGATION,
            lambda cmd: self._handlers[CommandType.NAVIGATION].execute(cmd),
            description="Вернуться назад",
            examples=["назад"]
        )
    
    def register_handler(self, command_type: CommandType, handler: BaseCommandHandler):
        """Регистрация обработчика команд."""
        with self._lock:
            self._handlers[command_type] = handler
            self.logger.info(f"Зарегистрирован обработчик для {command_type.value}")
    
    def add_pattern(
        self,
        pattern: Union[str, Pattern],
        command_type: CommandType,
        handler: Callable,
        priority: CommandPriority = CommandPriority.NORMAL,
        description: str = "",
        examples: List[str] = None,
        parameters: Dict[str, str] = None
    ):
        """Добавление паттерна команды."""
        command_pattern = CommandPattern(
            pattern=pattern,
            command_type=command_type,
            handler=handler,
            priority=priority,
            description=description,
            examples=examples,
            parameters=parameters
        )
        
        with self._lock:
            # Вставка с учетом приоритета
            inserted = False
            for i, existing_pattern in enumerate(self._patterns):
                if command_pattern.priority.value > existing_pattern.priority.value:
                    self._patterns.insert(i, command_pattern)
                    inserted = True
                    break
            
            if not inserted:
                self._patterns.append(command_pattern)
        
        self.logger.info(f"Добавлен паттерн: {pattern}")
    
    def add_command_handler(
        self,
        pattern: str,
        handler: Callable,
        command_type: CommandType = CommandType.CUSTOM,
        priority: CommandPriority = CommandPriority.NORMAL,
        description: str = ""
    ):
        """Упрощенное добавление обработчика команды."""
        def wrapper(command: Command) -> CommandResult:
            try:
                start_time = datetime.now()
                result = handler(command.parameters)
                execution_time = (datetime.now() - start_time).total_seconds()
                
                if isinstance(result, CommandResult):
                    result.execution_time = execution_time
                    return result
                else:
                    return CommandResult(
                        success=True,
                        message=str(result) if result is not None else "Команда выполнена",
                        data=result,
                        execution_time=execution_time
                    )
            except Exception as e:
                return CommandResult(
                    success=False,
                    message=f"Ошибка выполнения: {str(e)}",
                    error=e,
                    execution_time=(datetime.now() - start_time).total_seconds()
                )
        
        self.add_pattern(
            pattern=pattern,
            command_type=command_type,
            handler=wrapper,
            priority=priority,
            description=description
        )
    
    def process_command(self, text: str, context: CommandContext = None) -> Command:
        """Обработка текстовой команды."""
        if context is None:
            context = CommandContext()
        
        # Поиск подходящего паттерна
        matched_pattern = None
        parameters = {}
        
        with self._lock:
            for pattern in self._patterns:
                match_result = pattern.match(text)
                if match_result is not None:
                    matched_pattern = pattern
                    parameters = pattern.extract_parameters(text)
                    break
        
        # Создание команды
        command_id = f"cmd_{datetime.now().timestamp()}_{hash(text) % 10000}"
        
        if matched_pattern:
            command = Command(
                id=command_id,
                text=text,
                command_type=matched_pattern.command_type,
                priority=matched_pattern.priority,
                parameters=parameters,
                context=context
            )
        else:
            # Неизвестная команда
            command = Command(
                id=command_id,
                text=text,
                command_type=CommandType.CUSTOM,
                priority=CommandPriority.LOW,
                parameters={},
                context=context,
                status=CommandStatus.FAILED
            )
            command.result = CommandResult(
                success=False,
                message="Команда не распознана"
            )
        
        # Добавление в историю
        with self._lock:
            self._command_history.append(command)
            if len(self._command_history) > 1000:  # Ограничение размера истории
                self._command_history = self._command_history[-500:]
        
        return command
    
    def execute_command(self, command: Command) -> CommandResult:
        """Выполнение команды."""
        if command.status == CommandStatus.FAILED:
            return command.result
        
        command.status = CommandStatus.PROCESSING
        command.executed_at = datetime.now()
        
        with self._lock:
            self._active_commands[command.id] = command
        
        try:
            # Поиск подходящего паттерна для выполнения
            for pattern in self._patterns:
                if pattern.match(command.text):
                    result = pattern.handler(command)
                    command.result = result
                    command.status = CommandStatus.COMPLETED if result.success else CommandStatus.FAILED
                    break
            else:
                # Команда не найдена
                command.result = CommandResult(
                    success=False,
                    message="Обработчик команды не найден"
                )
                command.status = CommandStatus.FAILED
        
        except Exception as e:
            self.logger.error(f"Ошибка выполнения команды {command.id}: {e}")
            command.result = CommandResult(
                success=False,
                message=f"Ошибка выполнения: {str(e)}",
                error=e
            )
            command.status = CommandStatus.FAILED
        
        finally:
            with self._lock:
                if command.id in self._active_commands:
                    del self._active_commands[command.id]
        
        return command.result
    
    def process_and_execute(self, text: str, context: CommandContext = None) -> CommandResult:
        """Обработка и выполнение команды в одном вызове."""
        command = self.process_command(text, context)
        return self.execute_command(command)
    
    def get_command_history(self, limit: int = 100) -> List[Command]:
        """Получение истории команд."""
        with self._lock:
            return self._command_history[-limit:]
    
    def get_active_commands(self) -> List[Command]:
        """Получение активных команд."""
        with self._lock:
            return list(self._active_commands.values())
    
    def cancel_command(self, command_id: str) -> bool:
        """Отмена выполнения команды."""
        with self._lock:
            if command_id in self._active_commands:
                command = self._active_commands[command_id]
                command.status = CommandStatus.CANCELLED
                del self._active_commands[command_id]
                return True
        return False
    
    def get_available_commands(self) -> List[Dict[str, Any]]:
        """Получение списка доступных команд."""
        commands = []
        for pattern in self._patterns:
            commands.append({
                'pattern': pattern.pattern.pattern,
                'type': pattern.command_type.value,
                'priority': pattern.priority.value,
                'description': pattern.description,
                'examples': pattern.examples,
                'parameters': pattern.parameters
            })
        return commands
    
    def export_commands_config(self, file_path: Union[str, Path]):
        """Экспорт конфигурации команд в файл."""
        config = {
            'commands': self.get_available_commands(),
            'exported_at': datetime.now().isoformat()
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    def import_commands_config(self, file_path: Union[str, Path]):
        """Импорт конфигурации команд из файла."""
        with open(file_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Очистка текущих паттернов (кроме системных)
        with self._lock:
            self._patterns = [p for p in self._patterns if p.command_type == CommandType.SYSTEM]
        
        # Добавление команд из конфигурации
        for cmd_config in config.get('commands', []):
            if cmd_config['type'] != 'system':  # Не перезаписываем системные команды
                self.add_pattern(
                    pattern=cmd_config['pattern'],
                    command_type=CommandType(cmd_config['type']),
                    handler=lambda c: CommandResult(True, "Команда из конфигурации"),
                    priority=CommandPriority(cmd_config['priority']),
                    description=cmd_config.get('description', ''),
                    examples=cmd_config.get('examples', []),
                    parameters=cmd_config.get('parameters', {})
                )
    
    def clear_history(self):
        """Очистка истории команд."""
        with self._lock:
            self._command_history.clear()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики использования команд."""
        with self._lock:
            total_commands = len(self._command_history)
            successful_commands = sum(1 for cmd in self._command_history 
                                    if cmd.result and cmd.result.success)
            
            command_types = {}
            for cmd in self._command_history:
                cmd_type = cmd.command_type.value
                command_types[cmd_type] = command_types.get(cmd_type, 0) + 1
            
            return {
                'total_commands': total_commands,
                'successful_commands': successful_commands,
                'success_rate': successful_commands / total_commands if total_commands > 0 else 0,
                'active_commands': len(self._active_commands),
                'command_types': command_types,
                'available_patterns': len(self._patterns)
            }


# Функция для создания процессора с базовыми настройками
def create_command_processor() -> CommandProcessor:
    """Создание процессора команд с настройками по умолчанию."""
    processor = CommandProcessor()
    
    # Можно добавить дополнительные настройки
    
    return processor