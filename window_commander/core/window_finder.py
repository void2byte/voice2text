#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Модуль для поиска и получения информации о окнах Windows.
Предоставляет базовые функции для работы с Windows API.
"""

import os
import sys
import ctypes
from ctypes import wintypes
import logging

# Загружаем Windows API функции
user32 = ctypes.WinDLL('user32')
kernel32 = ctypes.WinDLL('kernel32')

class WindowFinder:
    """
    Класс для поиска окон Windows и получения информации о них
    """
    
    def __init__(self, logger=None):
        """
        Инициализация поисковика окон
        
        Args:
            logger: Объект логгера
        """
        self.logger = logger or logging.getLogger(__name__)
        
        # Проверяем, есть ли возможность использовать win32gui
        try:
            import win32gui
            import win32process
            self.win32gui_available = True
            self.win32gui = win32gui
            self.win32process = win32process
        except ImportError:
            self.logger.warning("Модуль win32gui не доступен, будут использованы альтернативные методы")
            self.win32gui_available = False
    
    def get_window_info(self, hwnd):
        """
        Получение информации о окне по его хендлу
        
        Args:
            hwnd: Хендл окна
            
        Returns:
            dict: Информация о окне или None при ошибке
        """
        self.logger.info(f"Получение информации о окне с HWND {hwnd}")
        
        try:
            if not hwnd:
                self.logger.error("Некорректный HWND окна")
                return None
                
            # Если доступен win32gui
            if self.win32gui_available:
                # Получаем заголовок окна
                title = self.win32gui.GetWindowText(hwnd)
                
                # Получаем класс окна
                class_name = self.win32gui.GetClassName(hwnd)
                
                # Получаем размеры и позицию окна
                rect = self.win32gui.GetWindowRect(hwnd)
                
                # Получаем PID процесса
                _, pid = self.win32process.GetWindowThreadProcessId(hwnd)
                
                # Формируем информацию о окне
                window_info = {
                    'hwnd': hwnd,
                    'title': title,
                    'class_name': class_name,
                    'rect': rect,
                    'pid': pid
                }
                
                self.logger.info(f"Информация о окне получена: {window_info}")
                return window_info
                
            else:
                # Альтернативный способ через ctypes
                # Получаем заголовок окна
                buffer_size = 256
                title_buffer = ctypes.create_unicode_buffer(buffer_size)
                user32.GetWindowTextW(hwnd, title_buffer, buffer_size)
                title = title_buffer.value
                
                # Получаем класс окна
                class_buffer = ctypes.create_unicode_buffer(buffer_size)
                user32.GetClassNameW(hwnd, class_buffer, buffer_size)
                class_name = class_buffer.value
                
                # Получаем размеры и позицию окна
                rect = wintypes.RECT()
                user32.GetWindowRect(hwnd, ctypes.byref(rect))
                window_rect = (rect.left, rect.top, rect.right, rect.bottom)
                
                # Получаем PID процесса
                pid = wintypes.DWORD()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                
                # Формируем информацию о окне
                window_info = {
                    'hwnd': hwnd,
                    'title': title,
                    'class_name': class_name,
                    'rect': window_rect,
                    'pid': pid.value
                }
                
                self.logger.info(f"Информация о окне получена: {window_info}")
                return window_info
                
        except Exception as e:
            self.logger.error(f"Ошибка при получении информации о окне: {str(e)}")
            return None
    
    def get_window_at_point(self, x, y):
        """
        Получение окна по координатам экрана
        
        Args:
            x: Координата X
            y: Координата Y
            
        Returns:
            int: Хендл окна или 0 при ошибке
        """
        self.logger.info(f"Получение окна по координатам ({x}, {y})")
        
        try:
            # Конвертируем координаты в LPARAM для WindowFromPoint
            point = wintypes.POINT(x, y)
            hwnd = user32.WindowFromPoint(point)
            
            if hwnd:
                self.logger.info(f"Найдено окно с HWND {hwnd}")
                return hwnd
            else:
                self.logger.warning("Не найдено окно по указанным координатам")
                return 0
                
        except Exception as e:
            self.logger.error(f"Ошибка при получении окна по координатам: {str(e)}")
            return 0
            
    def window_exists(self, hwnd):
        """
        Проверка существования окна по HWND
        
        Args:
            hwnd: Хендл окна
            
        Returns:
            bool: True если окно существует, иначе False
        """
        if not hwnd:
            return False
            
        try:
            if self.win32gui_available:
                return self.win32gui.IsWindow(hwnd)
            else:
                return bool(user32.IsWindow(hwnd))
        except Exception as e:
            self.logger.error(f"Ошибка при проверке окна: {str(e)}")
            return False
