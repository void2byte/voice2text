import win32gui
import win32process
import psutil
import os
import logging
from typing import Optional, Dict, Any
from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from window_binder.models.binding_model import IdentificationMethod, WindowIdentifier, SelectedWindowData
from window_binder.highlight_window import HighlightWindow

class PickerWidget(QLabel):
    window_selected = Signal(SelectedWindowData)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPixmap(QPixmap("assets/icons/picker_icon.svg"))
        self.setFixedSize(32, 32)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self._is_picking = False
        self._highlight_window = HighlightWindow()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_picking = True
            self.grabMouse()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._is_picking:
            screen_pos = self.mapToGlobal(event.pos())
            hwnd = win32gui.WindowFromPoint((screen_pos.x(), screen_pos.y()))
            if hwnd:
                rect = win32gui.GetWindowRect(hwnd)
                self._highlight_window.highlight(rect)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._is_picking:
            self._is_picking = False
            self.releaseMouse()
            self._highlight_window.hide_highlight()

            screen_pos = self.mapToGlobal(event.pos())
            hwnd = win32gui.WindowFromPoint((screen_pos.x(), screen_pos.y()))
            if hwnd:
                window_info = self._get_window_info(hwnd)
                identifier = self._create_window_identifier(window_info)
                if identifier:
                    logging.info(f"PickerWidget: Selected window with identifier '{identifier.get_display_name()}' at ({screen_pos.x()}, {screen_pos.y()})")
                    selected_data = SelectedWindowData(identifier=identifier, x=screen_pos.x(), y=screen_pos.y())
                    self.window_selected.emit(selected_data)
                else:
                    logging.warning(f"PickerWidget: Could not create window identifier for hwnd {hwnd}")
            event.accept()

    def _create_window_identifier(self, window_info: Dict[str, Any]) -> Optional[WindowIdentifier]:
        """Создать объект WindowIdentifier из информации об окне"""
        if not window_info:
            return None
        
        # По умолчанию используем частичное совпадение заголовка
        default_methods = [IdentificationMethod.TITLE_PARTIAL]

        return WindowIdentifier(
            title=window_info.get('title'),
            executable_path=window_info.get('executable_path'),
            executable_name=window_info.get('executable_name'),
            window_class=window_info.get('window_class'),
            identification_methods=default_methods
        )

    def _get_window_info(self, hwnd) -> Optional[Dict[str, Any]]:
        """Получить расширенную информацию об окне в зависимости от метода идентификации"""
        try:
            window_info = {
                'title': None,
                'executable_path': None,
                'executable_name': None,
                'window_class': None,
                'process_id': None
            }
            
            # Получаем заголовок окна
            window_title = self._get_window_title(hwnd)
            if not window_title:
                return None
            
            window_info['title'] = window_title
            
            # Всегда пытаемся получить дополнительную информацию, если это возможно
            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                process = psutil.Process(pid)
                
                window_info['process_id'] = pid
                window_info['executable_path'] = process.exe()
                window_info['executable_name'] = os.path.basename(process.exe())
                
            except (psutil.NoSuchProcess, psutil.AccessDenied, Exception) as e:
                logging.warning(f"Could not get process info for hwnd {hwnd}: {e}")

            try:
                window_info['window_class'] = win32gui.GetClassName(hwnd)
            except Exception as e:
                logging.warning(f"Could not get window class for hwnd {hwnd}: {e}")
            
            logging.info(f"PickerWidget: получен список информации об окне: {window_info}")
            return window_info
            
        except Exception as e:
            logging.error(f"PickerWidget: Error getting window info for hwnd {hwnd}: {e}")
            return None
    
    def _get_window_title(self, hwnd) -> Optional[str]:
        """Получить точное название окна"""
        try:
            # Сначала пробуем получить заголовок через win32gui
            window_title = win32gui.GetWindowText(hwnd)
            
            # Если заголовок пустой, пробуем получить через родительское окно
            if not window_title or not window_title.strip():
                parent_hwnd = win32gui.GetParent(hwnd)
                if parent_hwnd:
                    window_title = win32gui.GetWindowText(parent_hwnd)
            
            # Если все еще пустой, пробуем получить через владельца окна
            if not window_title or not window_title.strip():
                owner_hwnd = win32gui.GetWindow(hwnd, win32gui.GW_OWNER)
                if owner_hwnd:
                    window_title = win32gui.GetWindowText(owner_hwnd)
            
            # Очищаем и проверяем результат
            if window_title and window_title.strip():
                return window_title.strip()
            
            return None
            
        except Exception as e:
            logging.error(f"Error getting window title for hwnd {hwnd}: {e}")
            return None