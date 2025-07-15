import logging
import pygetwindow as gw
from typing import Dict, Optional, Callable
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QMessageBox
from window_binder.binder_widget import BinderWidget
from window_binder.error_handlers import ErrorHandler, WindowOperationError, with_error_handling
from window_binder.utils.window_identifier import window_identification_service
from window_binder.models.binding_model import IdentificationMethod, WindowIdentifier


class WidgetManager(QObject):
    """Класс для управления виджетами привязок"""
    stop_recognition_signal = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.binders: Dict[str, BinderWidget] = {}
        self.logger = logging.getLogger(__name__)
        self.error_handler = ErrorHandler()
        self._start_recognition_callback: Optional[Callable] = None
        self._stop_recognition_callback: Optional[Callable] = None
        self._binder_moved_callback: Optional[Callable] = None
        self._delete_requested_callback: Optional[Callable] = None
    
    def set_callbacks(self, start_recognition_callback: Callable, stop_recognition_callback: Callable, binder_moved_callback: Callable, delete_requested_callback: Optional[Callable] = None):
        """Установить callback функции"""
        self._start_recognition_callback = start_recognition_callback
        self._stop_recognition_callback = stop_recognition_callback
        self._binder_moved_callback = binder_moved_callback
        self._delete_requested_callback = delete_requested_callback
    
    def get_widget(self, binding_id: str) -> Optional[BinderWidget]:
        """Получить виджет по ID привязки"""
        return self.binders.get(binding_id)
    
    def get_all_widgets(self) -> Dict[str, BinderWidget]:
        """Получить все виджеты"""
        return self.binders.copy()
    
    def widget_exists(self, binding_id: str) -> bool:
        """Проверить существование виджета"""
        return binding_id in self.binders
    
    def get_widget_count(self) -> int:
        """Получить количество виджетов"""
        return len(self.binders)
    
    @with_error_handling(context="WidgetManager.create_binder")
    def create_binder(self, binding_id: str, app_name: str, x: int, y: int, pos_x: int, pos_y: int) -> Optional[BinderWidget]:
        """Создать виджет привязки"""
        self.logger.info(f"WidgetManager: [BINDING_DATA] Creating binder - ID: {binding_id}, App: '{app_name}', Window coords: ({x}, {y}), Relative pos: ({pos_x}, {pos_y})")
        
        try:
            # Используем улучшенную логику поиска окон с поддержкой частичного совпадения
            self.logger.debug(f"WidgetManager: [WINDOW_SEARCH] Searching for window with title: '{app_name}'")
            win = window_identification_service.find_window(WindowIdentifier(title=app_name, identification_methods=[IdentificationMethod.TITLE_PARTIAL]))
            if not win:
                self.logger.warning(f"WidgetManager: [WINDOW_SEARCH] Window not found for title: '{app_name}'")
                self.error_handler.handle_window_not_found(app_name)
                raise WindowOperationError(f"Window '{app_name}' not found")
            
            win.activate()
            self.logger.info(f"WidgetManager: [WINDOW_FOUND] Found and activated window - Title: '{win.title}' (searched: '{app_name}'), Position: ({win.left}, {win.top}), Size: ({win.width}, {win.height})")
            
        except WindowOperationError:
            # Ошибка уже обработана в error_handler
            return None
        except Exception as e:
            self.logger.error(f"WidgetManager: [WINDOW_ERROR] Unexpected error during window search: {e}")
            self.error_handler.handle_widget_creation_error(binding_id, e)
            return None
        
        # Создаем виджет
        self.logger.debug(f"WidgetManager: [WIDGET_CREATE] Creating BinderWidget instance for binding {binding_id}")
        widget = BinderWidget(binding_id)
        
        # Устанавливаем значения по умолчанию для позиции, если они равны 0
        # Это гарантирует, что кнопка будет видна
        default_pos_x = 50 if pos_x == 0 else pos_x
        default_pos_y = 50 if pos_y == 0 else pos_y
        
        # Логируем если использовались значения по умолчанию
        if pos_x == 0 or pos_y == 0:
            self.logger.warning(f"WidgetManager: [POSITION_DEFAULT] Using default position values - Original: ({pos_x}, {pos_y}) -> Default: ({default_pos_x}, {default_pos_y})")
        
        # Вычисляем абсолютные координаты
        absolute_x = win.left + default_pos_x
        absolute_y = win.top + default_pos_y
        
        self.logger.info(f"WidgetManager: [POSITION_CALC] Position calculation - Window: ({win.left}, {win.top}), Relative: ({default_pos_x}, {default_pos_y}), Absolute: ({absolute_x}, {absolute_y})")
        
        widget.move(absolute_x, absolute_y)
        widget.show()
        
        self.logger.info(f"WidgetManager: [WIDGET_DISPLAY] Binder widget created and displayed at ({absolute_x}, {absolute_y}) for binding {binding_id}")
        
        # Подключаем сигналы
        if self._start_recognition_callback:
            widget.start_recognition.connect(self._start_recognition_callback)
        if self._stop_recognition_callback:
            widget.stop_recognition.connect(self._stop_recognition_callback)
        if self._binder_moved_callback:
            widget.moved.connect(self._binder_moved_callback)
        if self._delete_requested_callback:
            widget.delete_requested.connect(self._delete_requested_callback)

        widget.stop_recognition.connect(self.stop_recognition_signal.emit)
        
        # Сохраняем виджет
        self.binders[binding_id] = widget
        
        return widget
    
    def remove_binder(self, binding_id: str) -> bool:
        """Удалить виджет привязки"""
        if binding_id not in self.binders:
            self.logger.warning(f"WidgetManager: [REMOVE_ERROR] Binder {binding_id} not found")
            return False
        
        widget = self.binders[binding_id]
        
        # Получаем информацию о виджете перед удалением
        widget_pos = widget.pos()
        widget_size = widget.size()
        
        self.logger.info(f"WidgetManager: [REMOVE_WIDGET] Removing widget - ID: {binding_id}, Position: ({widget_pos.x()}, {widget_pos.y()}), Size: ({widget_size.width()}, {widget_size.height()})")
        
        self.binders.pop(binding_id)
        widget.hide()
        widget.deleteLater()
        
        self.logger.info(f"WidgetManager: [REMOVE_SUCCESS] Successfully removed binder {binding_id}")
        return True
    
    def get_binder(self, binding_id: str) -> Optional[BinderWidget]:
        """Получить виджет привязки по ID"""
        return self.binders.get(binding_id)
    
    def hide_all_binders(self):
        """Скрыть все виджеты привязок"""
        widget_count = len(self.binders)
        self.logger.info(f"WidgetManager: [HIDE_ALL] Hiding {widget_count} binders")
        
        for binding_id, widget in self.binders.items():
            try:
                widget.hide()
                self.logger.debug(f"WidgetManager: [HIDE_WIDGET] Hidden widget {binding_id}")
            except Exception as e:
                self.logger.error(f"WidgetManager: [HIDE_ERROR] Error hiding widget {binding_id}: {e}")
        
        self.logger.info(f"WidgetManager: [HIDE_ALL_SUCCESS] All {widget_count} binders hidden")
    
    def show_all_binders(self):
        """Показать все виджеты привязок"""
        widget_count = len(self.binders)
        self.logger.info(f"WidgetManager: [SHOW_ALL] Showing {widget_count} binders")
        
        for binding_id, widget in self.binders.items():
            try:
                widget.show()
                self.logger.debug(f"WidgetManager: [SHOW_WIDGET] Shown widget {binding_id}")
            except Exception as e:
                self.logger.error(f"WidgetManager: [SHOW_ERROR] Error showing widget {binding_id}: {e}")
        
        self.logger.info(f"WidgetManager: [SHOW_ALL_SUCCESS] All {widget_count} binders shown")
    
    def update_binder_position(self, binding_id: str, app_name: str) -> bool:
        """Обновить позицию виджета относительно окна приложения"""
        if binding_id not in self.binders:
            self.logger.warning(f"WidgetManager: Binder {binding_id} not found")
            return False
        
        try:
            # Используем улучшенную логику поиска окон
            win = window_identification_service.find_window(WindowIdentifier(title=app_name, identification_methods=[IdentificationMethod.TITLE_PARTIAL]))
            if not win:
                self.logger.warning(f"WidgetManager: Window '{app_name}' not found for position update")
                return False
            widget = self.binders[binding_id]
            
            # Получаем текущую относительную позицию из данных привязки
            # Это должно быть передано извне, но пока используем текущую позицию
            current_pos = widget.pos()
            new_x = win.left + (current_pos.x() - win.left)
            new_y = win.top + (current_pos.y() - win.top)
            
            widget.move(new_x, new_y)
            self.logger.info(f"WidgetManager: Updated binder {binding_id} position to ({new_x}, {new_y})")
            return True
            
        except Exception as e:
            self.logger.error(f"WidgetManager: Error updating binder position: {e}")
            return False
    
    def get_binders_count(self) -> int:
        """Получить количество активных виджетов"""
        return len(self.binders)
    
    def remove_widget(self, binding_id: str) -> bool:
        """Удалить конкретный виджет"""
        if binding_id not in self.binders:
            self.logger.warning(f"WidgetManager: [REMOVE_WIDGET_ERROR] Widget {binding_id} not found for removal")
            return False
        
        widget = self.binders[binding_id]
        
        # Получаем информацию о виджете перед удалением
        try:
            widget_pos = widget.pos()
            widget_size = widget.size()
            self.logger.info(f"WidgetManager: [REMOVE_WIDGET_INFO] Removing widget - ID: {binding_id}, Position: ({widget_pos.x()}, {widget_pos.y()}), Size: ({widget_size.width()}, {widget_size.height()})")
        except Exception as e:
            self.logger.warning(f"WidgetManager: [REMOVE_WIDGET_WARNING] Could not get widget info for {binding_id}: {e}")
        
        self.binders.pop(binding_id)
        try:
            widget.close()
            widget.deleteLater()
            self.logger.info(f"WidgetManager: [REMOVE_WIDGET_SUCCESS] Successfully removed widget {binding_id}")
            return True
        except Exception as e:
            self.logger.error(f"WidgetManager: [REMOVE_WIDGET_ERROR] Error removing widget {binding_id}: {e}")
            return False
    
    def clear_all_widgets(self):
        """Удалить все виджеты"""
        widget_count = len(self.binders)
        self.logger.info(f"WidgetManager: [CLEAR_ALL] Starting to clear {widget_count} widgets")
        
        for binding_id in list(self.binders.keys()):
            self.logger.debug(f"WidgetManager: [CLEAR_WIDGET] Clearing widget {binding_id}")
            self.remove_widget(binding_id)
        
        self.logger.info(f"WidgetManager: [CLEAR_ALL_SUCCESS] All {widget_count} widgets cleared")
    
    def cleanup(self):
        """Очистить все виджеты"""
        widget_count = len(self.binders)
        self.logger.info(f"WidgetManager: [CLEANUP] Starting cleanup of {widget_count} widgets")
        
        for binding_id in list(self.binders.keys()):
            self.logger.debug(f"WidgetManager: [CLEANUP_WIDGET] Cleaning up widget {binding_id}")
            self.remove_binder(binding_id)
        
        self.logger.info(f"WidgetManager: [CLEANUP_SUCCESS] Cleanup completed for {widget_count} widgets")