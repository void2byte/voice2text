"""Модуль Dependency Injection контейнера."""

import logging
import threading
from abc import ABC, abstractmethod
from typing import Dict, Any, Type, TypeVar, Optional, Callable, List, Union
from dataclasses import dataclass
from enum import Enum
import inspect
from functools import wraps


T = TypeVar('T')


class LifetimeScope(Enum):
    """Области жизни зависимостей."""
    SINGLETON = "singleton"  # Один экземпляр на весь контейнер
    TRANSIENT = "transient"  # Новый экземпляр при каждом запросе
    SCOPED = "scoped"        # Один экземпляр в рамках области


@dataclass
class DependencyInfo:
    """Информация о зависимости."""
    interface: Type
    implementation: Type
    lifetime: LifetimeScope
    factory: Optional[Callable] = None
    instance: Optional[Any] = None
    dependencies: List[Type] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class DIException(Exception):
    """Исключения контейнера зависимостей."""
    pass


class CircularDependencyException(DIException):
    """Исключение циклической зависимости."""
    pass


class DependencyNotRegisteredException(DIException):
    """Исключение незарегистрированной зависимости."""
    pass


class DIScope:
    """Область жизни зависимостей."""
    
    def __init__(self, name: str):
        self.name = name
        self._instances: Dict[Type, Any] = {}
        self._lock = threading.RLock()
    
    def get_instance(self, dependency_type: Type) -> Optional[Any]:
        """Получение экземпляра из области."""
        with self._lock:
            return self._instances.get(dependency_type)
    
    def set_instance(self, dependency_type: Type, instance: Any):
        """Установка экземпляра в область."""
        with self._lock:
            self._instances[dependency_type] = instance
    
    def clear(self):
        """Очистка области."""
        with self._lock:
            self._instances.clear()
    
    def dispose(self):
        """Освобождение ресурсов области."""
        with self._lock:
            for instance in self._instances.values():
                if hasattr(instance, 'dispose'):
                    try:
                        instance.dispose()
                    except Exception as e:
                        logging.getLogger(self.__class__.__name__).error(
                            f"Ошибка при освобождении ресурсов {type(instance)}: {e}"
                        )
            self._instances.clear()


class DIContainer:
    """Контейнер зависимостей."""
    
    def __init__(self, name: str = "default"):
        self.name = name
        self.logger = logging.getLogger(f"{self.__class__.__name__}.{name}")
        self._dependencies: Dict[Type, DependencyInfo] = {}
        self._singletons: Dict[Type, Any] = {}
        self._scopes: Dict[str, DIScope] = {}
        self._current_scope: Optional[str] = None
        self._resolution_stack: List[Type] = []
        self._lock = threading.RLock()
        
        # Регистрация самого контейнера
        self.register_instance(DIContainer, self)
    
    def register_singleton(self, interface: Type[T], implementation: Type[T] = None) -> 'DIContainer':
        """Регистрация singleton зависимости."""
        return self._register(interface, implementation, LifetimeScope.SINGLETON)
    
    def register_transient(self, interface: Type[T], implementation: Type[T] = None) -> 'DIContainer':
        """Регистрация transient зависимости."""
        return self._register(interface, implementation, LifetimeScope.TRANSIENT)
    
    def register_scoped(self, interface: Type[T], implementation: Type[T] = None) -> 'DIContainer':
        """Регистрация scoped зависимости."""
        return self._register(interface, implementation, LifetimeScope.SCOPED)
    
    def register_factory(self, interface: Type[T], factory: Callable[[], T], lifetime: LifetimeScope = LifetimeScope.TRANSIENT) -> 'DIContainer':
        """Регистрация фабрики."""
        with self._lock:
            dependency_info = DependencyInfo(
                interface=interface,
                implementation=interface,
                lifetime=lifetime,
                factory=factory
            )
            self._dependencies[interface] = dependency_info
            self.logger.debug(f"Зарегистрирована фабрика для {interface.__name__} с областью {lifetime.value}")
        return self
    
    def register_instance(self, interface: Type[T], instance: T) -> 'DIContainer':
        """Регистрация готового экземпляра."""
        with self._lock:
            dependency_info = DependencyInfo(
                interface=interface,
                implementation=type(instance),
                lifetime=LifetimeScope.SINGLETON,
                instance=instance
            )
            self._dependencies[interface] = dependency_info
            self._singletons[interface] = instance
            self.logger.debug(f"Зарегистрирован экземпляр для {interface.__name__}")
        return self
    
    def _register(self, interface: Type[T], implementation: Type[T], lifetime: LifetimeScope) -> 'DIContainer':
        """Внутренняя регистрация зависимости."""
        if implementation is None:
            implementation = interface
        
        with self._lock:
            # Анализ зависимостей конструктора
            dependencies = self._analyze_dependencies(implementation)
            
            dependency_info = DependencyInfo(
                interface=interface,
                implementation=implementation,
                lifetime=lifetime,
                dependencies=dependencies
            )
            
            self._dependencies[interface] = dependency_info
            self.logger.debug(f"Зарегистрирована зависимость {interface.__name__} -> {implementation.__name__} с областью {lifetime.value}")
        
        return self
    
    def _analyze_dependencies(self, implementation: Type) -> List[Type]:
        """Анализ зависимостей конструктора."""
        try:
            signature = inspect.signature(implementation.__init__)
            dependencies = []
            
            for param_name, param in signature.parameters.items():
                if param_name == 'self':
                    continue
                
                if param.annotation != inspect.Parameter.empty:
                    dependencies.append(param.annotation)
                else:
                    self.logger.warning(f"Параметр {param_name} в {implementation.__name__} не имеет аннотации типа")
            
            return dependencies
        except Exception as e:
            self.logger.error(f"Ошибка анализа зависимостей для {implementation.__name__}: {e}")
            return []
    
    def resolve(self, interface: Type[T]) -> T:
        """Разрешение зависимости."""
        with self._lock:
            try:
                self._resolution_stack.append(interface)
                return self._resolve_internal(interface)
            finally:
                if interface in self._resolution_stack:
                    self._resolution_stack.remove(interface)
    
    def _resolve_internal(self, interface: Type[T]) -> T:
        """Внутреннее разрешение зависимости."""
        # Проверка циклических зависимостей
        if self._resolution_stack.count(interface) > 1:
            cycle = " -> ".join([t.__name__ for t in self._resolution_stack])
            raise CircularDependencyException(f"Обнаружена циклическая зависимость: {cycle}")
        
        # Поиск зарегистрированной зависимости
        dependency_info = self._dependencies.get(interface)
        if not dependency_info:
            raise DependencyNotRegisteredException(f"Зависимость {interface.__name__} не зарегистрирована")
        
        # Возврат готового экземпляра
        if dependency_info.instance is not None:
            return dependency_info.instance
        
        # Singleton
        if dependency_info.lifetime == LifetimeScope.SINGLETON:
            if interface in self._singletons:
                return self._singletons[interface]
            
            instance = self._create_instance(dependency_info)
            self._singletons[interface] = instance
            return instance
        
        # Scoped
        elif dependency_info.lifetime == LifetimeScope.SCOPED:
            if self._current_scope:
                scope = self._scopes.get(self._current_scope)
                if scope:
                    instance = scope.get_instance(interface)
                    if instance is not None:
                        return instance
                    
                    instance = self._create_instance(dependency_info)
                    scope.set_instance(interface, instance)
                    return instance
            
            # Если нет активной области, создаем как transient
            return self._create_instance(dependency_info)
        
        # Transient
        else:
            return self._create_instance(dependency_info)
    
    def _create_instance(self, dependency_info: DependencyInfo) -> Any:
        """Создание экземпляра зависимости."""
        try:
            # Использование фабрики
            if dependency_info.factory:
                return dependency_info.factory()
            
            # Разрешение зависимостей конструктора
            constructor_args = []
            for dep_type in dependency_info.dependencies:
                arg = self._resolve_internal(dep_type)
                constructor_args.append(arg)
            
            # Создание экземпляра
            instance = dependency_info.implementation(*constructor_args)
            
            # Вызов метода инициализации если есть
            if hasattr(instance, 'initialize'):
                instance.initialize()
            
            self.logger.debug(f"Создан экземпляр {dependency_info.implementation.__name__}")
            return instance
            
        except Exception as e:
            self.logger.error(f"Ошибка создания экземпляра {dependency_info.implementation.__name__}: {e}")
            raise DIException(f"Не удалось создать экземпляр {dependency_info.implementation.__name__}: {e}")
    
    def try_resolve(self, interface: Type[T]) -> Optional[T]:
        """Попытка разрешения зависимости без исключений."""
        try:
            return self.resolve(interface)
        except Exception as e:
            self.logger.debug(f"Не удалось разрешить зависимость {interface.__name__}: {e}")
            return None
    
    def is_registered(self, interface: Type) -> bool:
        """Проверка регистрации зависимости."""
        return interface in self._dependencies
    
    def create_scope(self, name: str) -> 'ScopeContext':
        """Создание области жизни."""
        return ScopeContext(self, name)
    
    def _enter_scope(self, name: str):
        """Вход в область жизни."""
        with self._lock:
            if name not in self._scopes:
                self._scopes[name] = DIScope(name)
            self._current_scope = name
            self.logger.debug(f"Вход в область {name}")
    
    def _exit_scope(self, name: str):
        """Выход из области жизни."""
        with self._lock:
            if self._current_scope == name:
                self._current_scope = None
            
            scope = self._scopes.get(name)
            if scope:
                scope.dispose()
                del self._scopes[name]
            
            self.logger.debug(f"Выход из области {name}")
    
    def get_registered_types(self) -> List[Type]:
        """Получение списка зарегистрированных типов."""
        return list(self._dependencies.keys())
    
    def get_dependency_info(self, interface: Type) -> Optional[DependencyInfo]:
        """Получение информации о зависимости."""
        return self._dependencies.get(interface)
    
    def clear(self):
        """Очистка контейнера."""
        with self._lock:
            # Освобождение ресурсов singleton'ов
            for instance in self._singletons.values():
                if hasattr(instance, 'dispose'):
                    try:
                        instance.dispose()
                    except Exception as e:
                        self.logger.error(f"Ошибка при освобождении ресурсов {type(instance)}: {e}")
            
            # Освобождение областей
            for scope in self._scopes.values():
                scope.dispose()
            
            self._dependencies.clear()
            self._singletons.clear()
            self._scopes.clear()
            self._current_scope = None
            self._resolution_stack.clear()
            
            # Повторная регистрация самого контейнера
            self.register_instance(DIContainer, self)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики контейнера."""
        with self._lock:
            return {
                "registered_dependencies": len(self._dependencies),
                "singleton_instances": len(self._singletons),
                "active_scopes": len(self._scopes),
                "current_scope": self._current_scope,
                "resolution_stack_depth": len(self._resolution_stack)
            }


class ScopeContext:
    """Контекст области жизни зависимостей."""
    
    def __init__(self, container: DIContainer, name: str):
        self.container = container
        self.name = name
    
    def __enter__(self):
        self.container._enter_scope(self.name)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.container._exit_scope(self.name)


# Декораторы для автоматической регистрации
def injectable(lifetime: LifetimeScope = LifetimeScope.TRANSIENT):
    """Декоратор для автоматической регистрации класса."""
    def decorator(cls):
        cls._di_lifetime = lifetime
        cls._di_injectable = True
        return cls
    return decorator


def singleton(cls):
    """Декоратор для регистрации singleton."""
    return injectable(LifetimeScope.SINGLETON)(cls)


def transient(cls):
    """Декоратор для регистрации transient."""
    return injectable(LifetimeScope.TRANSIENT)(cls)


def scoped(cls):
    """Декоратор для регистрации scoped."""
    return injectable(LifetimeScope.SCOPED)(cls)


def auto_register(container: DIContainer, *modules):
    """Автоматическая регистрация классов с декораторами."""
    for module in modules:
        for name in dir(module):
            obj = getattr(module, name)
            if (inspect.isclass(obj) and 
                hasattr(obj, '_di_injectable') and 
                obj._di_injectable):
                
                lifetime = getattr(obj, '_di_lifetime', LifetimeScope.TRANSIENT)
                
                if lifetime == LifetimeScope.SINGLETON:
                    container.register_singleton(obj)
                elif lifetime == LifetimeScope.SCOPED:
                    container.register_scoped(obj)
                else:
                    container.register_transient(obj)


# Глобальный контейнер по умолчанию
_default_container = DIContainer("global")


def get_container() -> DIContainer:
    """Получение глобального контейнера."""
    return _default_container


def resolve(interface: Type[T]) -> T:
    """Разрешение зависимости через глобальный контейнер."""
    return _default_container.resolve(interface)


def register_singleton(interface: Type[T], implementation: Type[T] = None) -> DIContainer:
    """Регистрация singleton в глобальном контейнере."""
    return _default_container.register_singleton(interface, implementation)


def register_transient(interface: Type[T], implementation: Type[T] = None) -> DIContainer:
    """Регистрация transient в глобальном контейнере."""
    return _default_container.register_transient(interface, implementation)


def register_scoped(interface: Type[T], implementation: Type[T] = None) -> DIContainer:
    """Регистрация scoped в глобальном контейнере."""
    return _default_container.register_scoped(interface, implementation)


def register_instance(interface: Type[T], instance: T) -> DIContainer:
    """Регистрация экземпляра в глобальном контейнере."""
    return _default_container.register_instance(interface, instance)