"""Утилиты для расширенной идентификации окон"""

import os
import re
import logging
import psutil
from typing import List, Optional, Dict, Any
import pygetwindow as gw
from window_binder.models.binding_model import WindowIdentifier, IdentificationMethod
from window_binder.utils.identification_strategies import (IdentificationStrategy, TitleExactStrategy, TitlePartialStrategy, ExecutablePathStrategy, ExecutableNameStrategy, WindowClassStrategy)
from window_binder.utils.window_enumerator import window_enumerator

try:
    import win32gui
    import win32process
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    logging.warning("win32gui not available, some window identification features will be limited")


class WindowIdentificationService:
    """Сервис для расширенной идентификации окон"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.strategies = {
            IdentificationMethod.TITLE_EXACT: TitleExactStrategy(),
            IdentificationMethod.TITLE_PARTIAL: TitlePartialStrategy(),
            IdentificationMethod.EXECUTABLE_PATH: ExecutablePathStrategy(),
            IdentificationMethod.EXECUTABLE_NAME: ExecutableNameStrategy(),
            IdentificationMethod.WINDOW_CLASS: WindowClassStrategy(),
        }
    
    def find_window(self, identifier: WindowIdentifier) -> Optional[gw.Win32Window]:
        """Найти окно по идентификатору"""
        for method in identifier.identification_methods:
            window = self._find_by_method(identifier, method)
            if window:
                self.logger.info(f"Window found using method: {method.value}")
                return window
        
        return None
    
    def _find_by_method(self, identifier: WindowIdentifier, method: IdentificationMethod) -> Optional[gw.Win32Window]:
        """Найти окно по конкретному методу"""
        try:
            if method == IdentificationMethod.COMBINED:
                return self._find_by_combined(identifier)
            strategy = self.strategies.get(method)
            if strategy:
                return strategy.find(identifier)
        except Exception as e:
            self.logger.error(f"Error finding window by method {method.value}: {e}")
        
        return None
    
    def _find_by_combined(self, identifier: WindowIdentifier) -> Optional[gw.Win32Window]:
        """Найти окно используя комбинированный подход"""
        # Пробуем все доступные стратегии по очереди
        for method, strategy in self.strategies.items():
            # Пропускаем, если этот метод уже был в списке основных
            if method in identifier.identification_methods:
                continue
            
            try:
                window = strategy.find(identifier)
                if window:
                    self.logger.info(f"Window found using combined strategy: {method.value}")
                    return window
            except Exception as e:
                self.logger.error(f"Error in combined strategy with method {method.value}: {e}")
        
        return None
    
    def get_all_windows_with_details(self, detection_mode: int = 0) -> List[Dict[str, Any]]:
        """Получить список всех окон с деталями"""
        return window_enumerator.get_all_windows_with_details(detection_mode)

    def get_window_details(self, window_title: str) -> Optional[Dict[str, Any]]:
        """Получить детальную информацию об окне по заголовку"""
        return window_enumerator.get_window_details(window_title)

    def create_identifier_from_window(self, window_title: str, 
                                     identification_methods: List[IdentificationMethod] = None) -> Optional[WindowIdentifier]:
        """Создать идентификатор из существующего окна"""
        details = window_enumerator.get_window_details(window_title)
        if not details:
            return None
        
        if identification_methods is None:
            identification_methods = [IdentificationMethod.TITLE_EXACT, IdentificationMethod.TITLE_PARTIAL]

        return WindowIdentifier(
            title=details['title'],
            executable_path=details.get('executable_path'),
            executable_name=details.get('executable_name'),
            window_class=details.get('window_class'),
            identification_methods=identification_methods
        )

# Глобальный экземпляр сервиса
window_identification_service = WindowIdentificationService()