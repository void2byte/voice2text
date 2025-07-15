#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Модуль для выбора окон Windows.
Объединяет функциональность поиска и выбора окон для использования в приложении.
"""

import os
import sys
import logging

# Импортируем разделенные модули
from .window_finder import WindowFinder
from ..ui.window_selector_dialog import WindowSelectorDialog

class WindowSelector:
    """
    Класс для выбора окон Windows
    """
    
    def __init__(self, logger=None):
        """
        Инициализация селектора окон
        
        Args:
            logger: Объект логгера
        """
        self.logger = logger or logging.getLogger(__name__)
        self.window_finder = WindowFinder(logger)
    
    def select_window(self):
        """
        Запуск диалога выбора окна
        
        Returns:
            dict: Информация о выбранном окне или None при отмене
        """
        self.logger.info("Запуск выбора окна")
        self.logger.info("Запуск диалога выбора окна")
        
        # Создаем и показываем диалог выбора окна
        dialog = WindowSelectorDialog(self.logger)
        if dialog.exec():
            return dialog.selected_window_info
        else:
            return None
    
    def get_window_info(self, hwnd):
        """
        Получение информации о окне по его хендлу
        
        Args:
            hwnd: Хендл окна
            
        Returns:
            dict: Информация о окне или None при ошибке
        """
        return self.window_finder.get_window_info(hwnd)
    
    def get_window_at_point(self, x, y):
        """
        Получение окна по координатам экрана
        
        Args:
            x: Координата X
            y: Координата Y
            
        Returns:
            int: Хендл окна или 0 при ошибке
        """
        return self.window_finder.get_window_at_point(x, y)
        
    def window_exists(self, hwnd):
        """
        Проверка существования окна по HWND
        
        Args:
            hwnd: Хендл окна
            
        Returns:
            bool: True если окно существует, иначе False
        """
        return self.window_finder.window_exists(hwnd)