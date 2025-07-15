#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Менеджер окон для приложения WindowCommander.
Обеспечивает взаимодействие с окнами Windows через Windows API.
"""

import os
import sys
import time
import json
import ctypes
import pyperclip
from ctypes import wintypes
from PySide6.QtWidgets import QApplication

# Константы Windows API
WM_CHAR = 0x0102
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_PASTE = 0x0302
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_MOUSEMOVE = 0x0200
VK_CONTROL = 0x11
VK_V = 0x56
VK_RETURN = 0x0D

# Загружаем Windows API функции
user32 = ctypes.WinDLL('user32')

class WindowManager:
    """
    Менеджер окон для взаимодействия с окнами Windows
    """
    
    def __init__(self, logger):
        """
        Инициализация менеджера окон
        
        Args:
            logger: Объект логгера
        """
        self.logger = logger
        self.window_info = None
        self.settings = {
            'char_delay': 10,  # мс
            'text_method': 0,  # 0 - WM_CHAR, 1 - Ctrl+V, 2 - SendMessage, 3 - PostMessage
            'restore_clipboard': True,
            'default_delay': 3,  # сек
            'clear_after_send': True,
            'show_warnings': True,
            'click_duration': 100  # мс
        }
        
        # Проверяем, есть ли возможность использовать win32gui
        try:
            import win32gui
            self.win32gui_available = True
        except ImportError:
            self.logger.warning("Модуль win32gui не доступен, некоторые функции будут ограничены")
            self.win32gui_available = False
    
    def select_window(self):
        """
        Запуск выбора окна
        
        Returns:
            dict: Информация о выбранном окне или None при ошибке
        """
        self.logger.info("Запуск выбора окна")
        
        try:
            # Импортируем модуль для выбора окна
            from core.window_selector import WindowSelector
            
            # Создаем и запускаем селектор окон
            selector = WindowSelector(self.logger)
            window_info = selector.select_window()
            
            if window_info:
                self.window_info = window_info
                self.logger.info(f"Выбрано окно: {window_info}")
                return window_info
            else:
                self.logger.warning("Окно не выбрано")
                return None
                
        except Exception as e:
            self.logger.error(f"Ошибка при выборе окна: {str(e)}")
            return None
    
    def load_window_info(self, window_info):
        """
        Загрузка информации о окне
        
        Args:
            window_info: Словарь с информацией о окне
            
        Returns:
            bool: True если окно существует, иначе False
        """
        self.logger.info(f"Загрузка информации о окне: {window_info}")
        
        # Проверяем, существует ли окно
        if self.win32gui_available:
            try:
                import win32gui
                if 'hwnd' in window_info and not win32gui.IsWindow(window_info['hwnd']):
                    self.logger.warning(f"Окно с HWND {window_info['hwnd']} не существует")
                    return False
            except Exception as e:
                self.logger.error(f"Ошибка при проверке окна: {str(e)}")
                # Продолжаем без проверки
        
        # Сохраняем информацию о окне
        self.window_info = window_info
        return True
    
    def get_window_info(self):
        """
        Получение информации о текущем окне
        
        Returns:
            dict: Информация о окне или None
        """
        return self.window_info
    
    def set_window_info(self, window_info):
        """
        Установка информации о окне
        
        Args:
            window_info: Словарь с информацией о окне
        """
        self.window_info = window_info
    
    def clear_window_info(self):
        """Очистка информации о окне"""
        self.window_info = None
    
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
            
        if self.win32gui_available:
            try:
                import win32gui
                return win32gui.IsWindow(hwnd)
            except Exception as e:
                self.logger.error(f"Ошибка при проверке окна: {str(e)}")
                return False
        else:
            # Если win32gui недоступен, используем ctypes
            try:
                return user32.IsWindow(hwnd)
            except Exception as e:
                self.logger.error(f"Ошибка при проверке окна через ctypes: {str(e)}")
                return False
    
    def activate_window(self, hwnd):
        """
        Активация окна
        
        Args:
            hwnd: Хендл окна
            
        Returns:
            bool: True если успешно, иначе False
        """
        if not self.window_exists(hwnd):
            return False
            
        try:
            # Активируем окно
            if not user32.SetForegroundWindow(hwnd):
                self.logger.warning(f"Не удалось активировать окно с HWND {hwnd}")
                return False
                
            # Ждем, пока окно станет активным
            time.sleep(0.1)
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка при активации окна: {str(e)}")
            return False
    
    def send_text(self, text, with_focus=False):
        """
        Отправка текста в окно
        
        Args:
            text: Текст для отправки
            with_focus: Если True, активировать окно перед отправкой
            
        Returns:
            bool: True если успешно, иначе False
        """
        self.logger.info(f"Отправка текста в окно: '{text}'")
        
        if not self.window_info or 'hwnd' not in self.window_info:
            self.logger.error("Информация о окне не установлена")
            return False
            
        hwnd = self.window_info['hwnd']
        
        if not self.window_exists(hwnd):
            self.logger.error(f"Окно с HWND {hwnd} не существует")
            return False
        
        # Если нужна активация окна
        if with_focus and not self.activate_window(hwnd):
            return False
        
        # Выбираем метод отправки текста
        method = self.settings.get('text_method', 0)
        
        if method == 0:
            # WM_CHAR
            return self._send_text_by_char(hwnd, text)
        elif method == 1:
            # Ctrl+V
            return self._send_text_by_clipboard(hwnd, text)
        elif method == 2:
            # SendMessage
            return self._send_text_by_send_message(hwnd, text)
        elif method == 3:
            # PostMessage
            return self._send_text_by_post_message(hwnd, text)
        else:
            self.logger.error(f"Неизвестный метод отправки текста: {method}")
            return False
    
    def _send_text_by_char(self, hwnd, text):
        """
        Отправка текста посимвольно через WM_CHAR
        
        Args:
            hwnd: Хендл окна
            text: Текст для отправки
            
        Returns:
            bool: True если успешно, иначе False
        """
        self.logger.info("Используется метод отправки посимвольно (WM_CHAR)")
        
        try:
            for char in text:
                char_code = ord(char)
                user32.SendMessageW(hwnd, WM_CHAR, char_code, 0)
                time.sleep(self.settings.get('char_delay', 10) / 1000.0)
                
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка при отправке текста посимвольно: {str(e)}")
            return False
    
    def _send_text_by_clipboard(self, hwnd, text):
        """
        Отправка текста через буфер обмена (Ctrl+V)
        
        Args:
            hwnd: Хендл окна
            text: Текст для отправки
            
        Returns:
            bool: True если успешно, иначе False
        """
        self.logger.info("Используется метод отправки через буфер обмена (Ctrl+V)")
        
        # Сохраняем текущее содержимое буфера обмена
        old_clipboard = ""
        if self.settings.get('restore_clipboard', True):
            try:
                old_clipboard = pyperclip.paste()
            except Exception as e:
                self.logger.error(f"Ошибка при сохранении буфера обмена: {str(e)}")
        
        try:
            # Копируем текст в буфер обмена
            pyperclip.copy(text)
            
            # Отправляем Ctrl+V
            # Отправляем Ctrl+V через SendMessage
            # Получаем скан-коды клавиш
            scan_ctrl = user32.MapVirtualKeyW(VK_CONTROL, 0) << 16
            lParam_ctrl = 0x00000001 | scan_ctrl  # 0x1 - бит repeat count
            
            scan_v = user32.MapVirtualKeyW(VK_V, 0) << 16
            lParam_v = 0x00000001 | scan_v | 0x20000000  # Добавляем бит 29 (Ctrl нажат)
            
            # Отправляем нажатие Ctrl
            user32.SendMessageW(hwnd, WM_KEYDOWN, VK_CONTROL, lParam_ctrl)
            time.sleep(0.05)
            
            # Отправляем нажатие V
            user32.SendMessageW(hwnd, WM_KEYDOWN, VK_V, lParam_v)
            time.sleep(0.1)
            
            # Отпускаем V
            user32.SendMessageW(hwnd, WM_KEYUP, VK_V, lParam_v)
            time.sleep(0.05)
            
            # Отпускаем Ctrl
            user32.SendMessageW(hwnd, WM_KEYUP, VK_CONTROL, lParam_ctrl)
            
            # Восстанавливаем буфер обмена, если нужно
            if self.settings.get('restore_clipboard', True) and old_clipboard:
                pyperclip.copy(old_clipboard)
                
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка при отправке текста через буфер обмена: {str(e)}")
            
            # Восстанавливаем буфер обмена в случае ошибки
            if self.settings.get('restore_clipboard', True) and old_clipboard:
                try:
                    pyperclip.copy(old_clipboard)
                except:
                    pass
                    
            return False
    
    def _send_text_by_send_message(self, hwnd, text):
        """
        Отправка текста через SendMessage
        
        Args:
            hwnd: Хендл окна
            text: Текст для отправки
            
        Returns:
            bool: True если успешно, иначе False
        """
        self.logger.info("Используется метод отправки через SendMessage API")
        
        try:
            # Попробуем отправить текст напрямую через WM_PASTE
            buffer = ctypes.create_unicode_buffer(text)
            result = user32.SendMessageW(hwnd, WM_PASTE, 0, 0)
            
            if result == 0:
                self.logger.warning("WM_PASTE не поддерживается окном, используем посимвольный ввод")
                return self._send_text_by_char(hwnd, text)
                
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка при отправке текста через SendMessage: {str(e)}")
            return False
    
    def _send_text_by_post_message(self, hwnd, text):
        """
        Отправка текста через PostMessage
        
        Args:
            hwnd: Хендл окна
            text: Текст для отправки
            
        Returns:
            bool: True если успешно, иначе False
        """
        self.logger.info("Используется метод отправки через PostMessage API")
        
        try:
            # Метод через буфер обмена, но с использованием PostMessage
            # Сохраняем текущее содержимое буфера обмена
            old_clipboard = ""
            if self.settings.get('restore_clipboard', True):
                try:
                    old_clipboard = pyperclip.paste()
                except Exception as e:
                    self.logger.error(f"Ошибка при сохранении буфера обмена: {str(e)}")
            
            # Копируем текст в буфер обмена
            pyperclip.copy(text)
            
            # Отправляем Ctrl+V через PostMessage
            # Отправляем нажатие Ctrl
            user32.PostMessageW(hwnd, WM_KEYDOWN, VK_CONTROL, 0)
            time.sleep(0.05)
            
            # Отправляем нажатие V
            user32.PostMessageW(hwnd, WM_KEYDOWN, VK_V, 0)
            time.sleep(0.1)
            
            # Отпускаем V
            user32.PostMessageW(hwnd, WM_KEYUP, VK_V, 0)
            time.sleep(0.05)
            
            # Отпускаем Ctrl
            user32.PostMessageW(hwnd, WM_KEYUP, VK_CONTROL, 0)
            
            # Восстанавливаем буфер обмена, если нужно
            if self.settings.get('restore_clipboard', True) and old_clipboard:
                pyperclip.copy(old_clipboard)
                
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка при отправке текста через PostMessage: {str(e)}")
            
            # Восстанавливаем буфер обмена в случае ошибки
            if self.settings.get('restore_clipboard', True) and old_clipboard:
                try:
                    pyperclip.copy(old_clipboard)
                except:
                    pass
                    
            return False
    
    def send_command(self, command, with_focus=False):
        """
        Отправка специальной команды в окно
        
        Args:
            command: Команда для отправки (Enter, Tab, Escape, и т.д.)
            with_focus: Если True, активировать окно перед отправкой
            
        Returns:
            bool: True если успешно, иначе False
        """
        self.logger.info(f"Отправка команды в окно: {command}")
        
        if not self.window_info or 'hwnd' not in self.window_info:
            self.logger.error("Информация о окне не установлена")
            return False
            
        hwnd = self.window_info['hwnd']
        
        if not self.window_exists(hwnd):
            self.logger.error(f"Окно с HWND {hwnd} не существует")
            return False
        
        # Если нужна активация окна
        if with_focus and not self.activate_window(hwnd):
            return False
        
        # Словарь для преобразования команд в виртуальные коды клавиш
        command_to_vk = {
            'Enter': 0x0D,
            'Tab': 0x09,
            'Escape': 0x1B,
            'Space': 0x20,
            'Backspace': 0x08,
            'Delete': 0x2E,
            'Ctrl+C': [VK_CONTROL, 0x43],  # C
            'Ctrl+V': [VK_CONTROL, 0x56],  # V
            'Ctrl+Z': [VK_CONTROL, 0x5A],  # Z
            'Ctrl+Y': [VK_CONTROL, 0x59],  # Y
            'Ctrl+S': [VK_CONTROL, 0x53],  # S
            'Ctrl+A': [VK_CONTROL, 0x41],  # A
            'F1': 0x70,
            'F2': 0x71,
            'F3': 0x72,
            'F4': 0x73,
            'F5': 0x74
        }
        
        try:
            # Проверяем, есть ли команда в словаре
            if command not in command_to_vk:
                self.logger.error(f"Неизвестная команда: {command}")
                return False
            
            # Получаем виртуальный код клавиши
            vk = command_to_vk[command]
            
            # Отправляем команду в зависимости от типа
            if isinstance(vk, list):
                # Комбинация клавиш (Ctrl+X)
                control_key = vk[0]
                main_key = vk[1]
                
                # Отправляем нажатие Ctrl
                user32.PostMessageW(hwnd, WM_KEYDOWN, control_key, 0)
                time.sleep(0.05)
                
                # Отправляем нажатие основной клавиши
                user32.PostMessageW(hwnd, WM_KEYDOWN, main_key, 0)
                time.sleep(0.1)
                
                # Отпускаем основную клавишу
                user32.PostMessageW(hwnd, WM_KEYUP, main_key, 0)
                time.sleep(0.05)
                
                # Отпускаем Ctrl
                user32.PostMessageW(hwnd, WM_KEYUP, control_key, 0)
            else:
                # Одиночная клавиша
                user32.PostMessageW(hwnd, WM_KEYDOWN, vk, 0)
                time.sleep(0.1)
                user32.PostMessageW(hwnd, WM_KEYUP, vk, 0)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка при отправке команды: {str(e)}")
            return False
    
    def click_at_position(self, x, y, with_focus=False):
        """
        Отправка клика в указанные координаты окна
        
        Args:
            x: Координата X относительно окна
            y: Координата Y относительно окна
            with_focus: Если True, активировать окно перед кликом
            
        Returns:
            bool: True если успешно, иначе False
        """
        self.logger.info(f"Отправка клика в координаты ({x}, {y})")
        
        if not self.window_info or 'hwnd' not in self.window_info:
            self.logger.error("Информация о окне не установлена")
            return False
            
        hwnd = self.window_info['hwnd']
        
        if not self.window_exists(hwnd):
            self.logger.error(f"Окно с HWND {hwnd} не существует")
            return False
        
        # Если нужна активация окна
        if with_focus and not self.activate_window(hwnd):
            return False
        
        try:
            # Преобразуем координаты в lParam формат (младшие 16 бит - x, старшие - y)
            lParam = (y << 16) | (x & 0xFFFF)
            
            # Отправляем сообщение о перемещении мыши
            user32.PostMessageW(hwnd, WM_MOUSEMOVE, 0, lParam)
            time.sleep(0.05)
            
            # Отправляем сообщение о нажатии кнопки мыши
            user32.PostMessageW(hwnd, WM_LBUTTONDOWN, 1, lParam)
            
            # Ждем указанное время (длительность клика)
            click_duration = self.settings.get('click_duration', 100) / 1000.0
            time.sleep(click_duration)
            
            # Отправляем сообщение об отпускании кнопки мыши
            user32.PostMessageW(hwnd, WM_LBUTTONUP, 0, lParam)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка при отправке клика: {str(e)}")
            return False
    
    def apply_settings(self, settings):
        """
        Применение новых настроек
        
        Args:
            settings: Словарь с настройками
        """
        self.logger.info(f"Применение новых настроек: {settings}")
        self.settings.update(settings)
