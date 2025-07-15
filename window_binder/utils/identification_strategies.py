"""Стратегии для идентификации окон"""

import os
import re
import logging
import psutil
from typing import Optional
import pygetwindow as gw
from window_binder.models.binding_model import WindowIdentifier, IdentificationMethod

try:
    import win32gui
    import win32process
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    logging.warning("win32gui not available, some window identification features will be limited")

class IdentificationStrategy:
    """Базовый класс для стратегий идентификации"""
    def find(self, identifier: WindowIdentifier) -> Optional[gw.Win32Window]:
        raise NotImplementedError

class TitleExactStrategy(IdentificationStrategy):
    def find(self, identifier: WindowIdentifier) -> Optional[gw.Win32Window]:
        if not identifier.title:
            return None
        windows = gw.getWindowsWithTitle(identifier.title)
        return windows[0] if windows else None

class TitlePartialStrategy(IdentificationStrategy):
    def find(self, identifier: WindowIdentifier) -> Optional[gw.Win32Window]:
        if not identifier.title:
            return None
        base_title = self._extract_base_title(identifier.title)
        all_windows = gw.getAllWindows()
        for window in all_windows:
            if not window.title.strip():
                continue
            window_base_title = self._extract_base_title(window.title)
            if (base_title.lower() in window_base_title.lower() or 
                window_base_title.lower() in base_title.lower()):
                return window
        return None

    def _extract_base_title(self, title: str) -> str:
        base_title = re.sub(r'\s*\(\d+\)\s*$', '', title)
        return base_title.strip()

class ExecutablePathStrategy(IdentificationStrategy):
    def find(self, identifier: WindowIdentifier) -> Optional[gw.Win32Window]:
        if not identifier.executable_path or not WIN32_AVAILABLE:
            return None
        matching_titles = []
        def enum_callback(hwnd, lparam):
            if win32gui.IsWindowVisible(hwnd):
                try:
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    process = psutil.Process(pid)
                    if process.exe().lower() == identifier.executable_path.lower():
                        title = win32gui.GetWindowText(hwnd)
                        if title.strip():
                            matching_titles.append(title)
                except:
                    pass
            return True
        win32gui.EnumWindows(enum_callback, None)
        if matching_titles:
            return gw.getWindowsWithTitle(matching_titles[0])[0] if gw.getWindowsWithTitle(matching_titles[0]) else None
        return None

class ExecutableNameStrategy(IdentificationStrategy):
    def find(self, identifier: WindowIdentifier) -> Optional[gw.Win32Window]:
        if not identifier.executable_name or not WIN32_AVAILABLE:
            return None
        matching_titles = []
        def enum_callback(hwnd, lparam):
            if win32gui.IsWindowVisible(hwnd):
                try:
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    process = psutil.Process(pid)
                    process_name = os.path.basename(process.exe()).lower()
                    if process_name == identifier.executable_name.lower():
                        title = win32gui.GetWindowText(hwnd)
                        if title.strip():
                            matching_titles.append(title)
                except:
                    pass
            return True
        win32gui.EnumWindows(enum_callback, None)
        if matching_titles:
            return gw.getWindowsWithTitle(matching_titles[0])[0] if gw.getWindowsWithTitle(matching_titles[0]) else None
        return None

class WindowClassStrategy(IdentificationStrategy):
    def find(self, identifier: WindowIdentifier) -> Optional[gw.Win32Window]:
        if not identifier.window_class or not WIN32_AVAILABLE:
            return None
        matching_titles = []
        def enum_callback(hwnd, lparam):
            if win32gui.IsWindowVisible(hwnd):
                class_name = win32gui.GetClassName(hwnd)
                if class_name == identifier.window_class:
                    title = win32gui.GetWindowText(hwnd)
                    if title.strip():
                        matching_titles.append(title)
            return True
        win32gui.EnumWindows(enum_callback, None)
        if matching_titles:
            return gw.getWindowsWithTitle(matching_titles[0])[0] if gw.getWindowsWithTitle(matching_titles[0]) else None
        return None