"""Утилиты для перечисления окон"""

import os
import logging
import psutil
from typing import List, Dict, Any, Optional
import pygetwindow as gw

try:
    import win32gui
    import win32process
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    logging.warning("win32gui not available, some window enumeration features will be limited")

class WindowEnumerator:
    """Сервис для перечисления окон с детальной информацией"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_all_windows_with_details(self, detection_mode: int = 0) -> List[Dict[str, Any]]:
        """Получить список всех окон с детальной информацией
        
        Args:
            detection_mode: Режим обнаружения окон
                0 - Фильтрованный (только пользовательские окна)
                1 - Все окна (включая системные)
                2 - Базовый расширенный (+ скрытые окна)
                3 - Полный расширенный (все процессы)
        """
        windows_details = []
        
        try:
            if detection_mode >= 2:
                # Расширенные режимы - используем win32gui для получения всех окон
                if WIN32_AVAILABLE:
                    windows_details = self._get_windows_extended(detection_mode)
                else:
                    # Fallback к обычному режиму если win32 недоступен
                    windows_details = self._get_windows_basic(detection_mode >= 1)
            else:
                # Базовые режимы - используем pygetwindow
                windows_details = self._get_windows_basic(detection_mode >= 1)
        
        except Exception as e:
            self.logger.error(f"Error getting windows with details: {e}")
        
        return windows_details
    
    def _get_windows_basic(self, show_all: bool = False) -> List[Dict[str, Any]]:
        """Получить окна базовым способом через pygetwindow"""
        windows_details = []
        
        windows = gw.getAllWindows()
        for window in windows:
            if not window.title or not window.title.strip():
                continue
            
            if not show_all:
                # Фильтруем системные окна
                if (window.width < 50 or window.height < 50 or 
                    not window.visible or
                    window.title in ['Program Manager', 'Desktop', 'Taskbar']):
                    continue
            
            details = self._get_window_details(window)
            if details:
                windows_details.append(details)
        
        return windows_details
    
    def _get_windows_extended(self, detection_mode: int) -> List[Dict[str, Any]]:
        """Получить окна расширенным способом через win32gui с улучшенной обработкой."""
        windows_details = []
        process_cache = {}

        def enum_windows_callback(hwnd, windows_list):
            try:
                title = win32gui.GetWindowText(hwnd)
                if not title.strip():
                    self.logger.debug(f"Skipped window with empty title (hwnd: {hwnd})")
                    return True
                
                is_visible = win32gui.IsWindowVisible(hwnd)
                class_name = win32gui.GetClassName(hwnd)
                
                # Определяем, включать ли окно на основе режима
                should_include = False
                if detection_mode == 2:
                    if is_visible or (not is_visible and class_name not in ['Shell_TrayWnd', 'Progman', 'WorkerW']):
                        should_include = True
                elif detection_mode == 3:
                    should_include = True
                else:
                    should_include = is_visible
                
                if not should_include:
                    self.logger.debug(f"Filtered out window: {title} (visible: {is_visible}, class: {class_name})")
                    return True
                
                # Получаем размеры окна
                try:
                    rect = win32gui.GetWindowRect(hwnd)
                    left, top, right, bottom = rect
                    width = right - left
                    height = bottom - top
                except Exception as e:
                    self.logger.warning(f"Failed to get rect for {title}: {e}")
                    return True
                
                # Базовые детали
                details = {
                    'title': title,
                    'left': left,
                    'top': top,
                    'width': width,
                    'height': height,
                    'visible': is_visible,
                    'minimized': win32gui.IsIconic(hwnd) if hasattr(win32gui, 'IsIconic') else False,
                    'maximized': win32gui.IsZoomed(hwnd) if hasattr(win32gui, 'IsZoomed') else False,
                    'window_class': class_name
                }
                
                # Добавляем информацию о процессе
                try:
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    details['process_id'] = pid
                    if pid in process_cache:
                        process = process_cache[pid]
                    else:
                        process = psutil.Process(pid)
                        process_cache[pid] = process
                    exe_path = process.exe()
                    details['executable_path'] = exe_path
                    details['executable_name'] = os.path.basename(exe_path)
                except Exception as e:
                    self.logger.debug(f"Process info unavailable for {title}: {e}")
                    details['process_id'] = None
                    details['executable_path'] = ''
                    details['executable_name'] = ''
                
                windows_list.append(details)
                self.logger.debug(f"Added window: {title} (mode: {detection_mode})")
                
            except Exception as e:
                self.logger.warning(f"Error processing window {hwnd}: {e}")
            
            return True
        
        win32gui.EnumWindows(enum_windows_callback, windows_details)
        self.logger.info(f"Found {len(windows_details)} windows in mode {detection_mode}")
        return windows_details
    
    def get_window_details(self, window_title: str) -> Optional[Dict[str, Any]]:
        """Получить детальную информацию об окне по заголовку"""
        windows = gw.getWindowsWithTitle(window_title)
        if not windows:
            return None
        return self._get_window_details(windows[0])
    
    def _get_window_details(self, window: gw.Win32Window) -> Dict[str, Any]:
        """Получить детальную информацию об окне"""
        details = {
            'title': window.title,
            'left': window.left,
            'top': window.top,
            'width': window.width,
            'height': window.height,
            'visible': window.visible,
            'minimized': window.isMinimized,
            'maximized': window.isMaximized
        }
        
        # Добавляем информацию о процессе, если доступно
        if WIN32_AVAILABLE:
            try:
                hwnd = window._hWnd
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                process = psutil.Process(pid)
                
                details.update({
                    'process_id': pid,
                    'executable_path': process.exe(),
                    'executable_name': os.path.basename(process.exe()),
                    'window_class': win32gui.GetClassName(hwnd)
                })
            except Exception as e:
                self.logger.warning(f"Could not get process details for window: {e}")
        
        return details

# Глобальный экземпляр
window_enumerator = WindowEnumerator()