"""Модуль для обработки ошибок в системе привязок окон"""

import logging
import traceback
from typing import Callable, Any
from functools import wraps
from PySide6.QtWidgets import QMessageBox


class ErrorHandler:
    """Класс для централизованной обработки ошибок"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def handle_window_not_found(self, app_name: str, show_dialog: bool = True) -> None:
        """Обработка ошибки "окно не найдено"""
        error_msg = f"Окно '{app_name}' не найдено. Убедитесь, что приложение запущено."
        self.logger.warning(f"WindowNotFound: {error_msg}")
        
        if show_dialog:
            QMessageBox.warning(None, "Окно не найдено", error_msg)
    
    def handle_invalid_coordinates(self, coords: tuple, show_dialog: bool = True) -> None:
        """Обработка ошибки некорректных координат"""
        error_msg = f"Некорректные координаты: {coords}"
        self.logger.error(f"InvalidCoordinates: {error_msg}")
        
        if show_dialog:
            QMessageBox.critical(None, "Ошибка координат", error_msg)
    
    def handle_file_operation_error(self, operation: str, file_path: str, error: Exception, show_dialog: bool = True) -> None:
        """Обработка ошибок файловых операций"""
        error_msg = f"Ошибка {operation} файла '{file_path}': {str(error)}"
        self.logger.error(f"FileOperationError: {error_msg}")
        
        if show_dialog:
            QMessageBox.critical(None, "Ошибка файловой операции", error_msg)
    
    def handle_widget_creation_error(self, binding_id: str, error: Exception, show_dialog: bool = True) -> None:
        """Обработка ошибок создания виджетов"""
        error_msg = f"Ошибка создания виджета для привязки '{binding_id}': {str(error)}"
        self.logger.error(f"WidgetCreationError: {error_msg}")
        
        if show_dialog:
            QMessageBox.critical(None, "Ошибка создания виджета", error_msg)
    
    def handle_validation_error(self, field: str, value: Any, error_msg: str, show_dialog: bool = True) -> None:
        """Обработка ошибок валидации"""
        full_error_msg = f"Ошибка валидации поля '{field}' (значение: {value}): {error_msg}"
        self.logger.warning(f"ValidationError: {full_error_msg}")
        
        if show_dialog:
            QMessageBox.warning(None, "Ошибка валидации", error_msg)
    
    def handle_unexpected_error(self, context: str, error: Exception, show_dialog: bool = True) -> None:
        """Обработка неожиданных ошибок"""
        error_msg = f"Неожиданная ошибка в {context}: {str(error)}"
        self.logger.error(f"UnexpectedError: {error_msg}")
        self.logger.debug(f"Traceback: {traceback.format_exc()}")
        
        if show_dialog:
            QMessageBox.critical(None, "Неожиданная ошибка", 
                               f"Произошла неожиданная ошибка.\n\nКонтекст: {context}\nОшибка: {str(error)}")


def with_error_handling(error_handler: ErrorHandler = None, context: str = "", show_dialog: bool = True):
    """Декоратор для автоматической обработки ошибок"""
    if error_handler is None:
        error_handler = ErrorHandler()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                func_context = context or f"{func.__module__}.{func.__name__}"
                error_handler.handle_unexpected_error(func_context, e, show_dialog)
                return None
        return wrapper
    return decorator


class WindowOperationError(Exception):
    """Исключение для ошибок операций с окнами"""
    pass


class BindingOperationError(Exception):
    """Исключение для ошибок операций с привязками"""
    pass


class ValidationError(Exception):
    """Исключение для ошибок валидации"""
    pass


class FileOperationError(Exception):
    """Исключение для ошибок файловых операций"""
    pass