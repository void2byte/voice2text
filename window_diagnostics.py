#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Диагностика окон - утилита для анализа проблем с обнаружением окон
"""

import sys
import os
import logging
import pygetwindow as gw
import win32gui
import win32con
from typing import List, Dict, Any

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from window_binder.utils import WindowUtils

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_all_windows_detailed() -> List[Dict[str, Any]]:
    """Получить подробную информацию о всех окнах"""
    windows_info = []
    
    def enum_windows_callback(hwnd, windows_list):
        if win32gui.IsWindowVisible(hwnd):
            window_text = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)
            
            # Получаем размеры окна
            try:
                rect = win32gui.GetWindowRect(hwnd)
                left, top, right, bottom = rect
                width = right - left
                height = bottom - top
            except:
                left = top = width = height = 0
            
            # Проверяем состояние окна
            try:
                is_minimized = win32gui.IsIconic(hwnd)
                # IsZoomed может отсутствовать в некоторых версиях
                is_maximized = False
                try:
                    is_maximized = win32gui.IsZoomed(hwnd)
                except AttributeError:
                    # Альтернативный способ проверки максимизации
                    window_placement = win32gui.GetWindowPlacement(hwnd)
                    is_maximized = window_placement[1] == win32con.SW_SHOWMAXIMIZED
            except:
                is_minimized = False
                is_maximized = False
            
            window_info = {
                'hwnd': hwnd,
                'title': window_text,
                'class_name': class_name,
                'left': left,
                'top': top,
                'width': width,
                'height': height,
                'is_minimized': is_minimized,
                'is_maximized': is_maximized,
                'is_visible': True
            }
            
            windows_list.append(window_info)
        
        return True
    
    windows_list = []
    win32gui.EnumWindows(enum_windows_callback, windows_list)
    
    return windows_list

def get_pygetwindow_windows() -> List[Dict[str, Any]]:
    """Получить окна через pygetwindow"""
    windows_info = []
    
    try:
        windows = gw.getAllWindows()
        for window in windows:
            if window.title.strip():  # Только окна с названием
                window_info = {
                    'title': window.title,
                    'left': window.left,
                    'top': window.top,
                    'width': window.width,
                    'height': window.height,
                    'is_minimized': window.isMinimized,
                    'is_maximized': window.isMaximized,
                    'is_visible': window.visible
                }
                windows_info.append(window_info)
    except Exception as e:
        logger.error(f"Ошибка при получении окон через pygetwindow: {e}")
    
    return windows_info

def search_window_by_partial_title(search_term: str) -> List[Dict[str, Any]]:
    """Поиск окон по частичному совпадению названия"""
    all_windows = get_all_windows_detailed()
    matching_windows = []
    
    search_term_lower = search_term.lower()
    
    for window in all_windows:
        title_lower = window['title'].lower()
        if search_term_lower in title_lower:
            matching_windows.append(window)
    
    return matching_windows

def test_window_detection(target_window_name: str):
    """Тестирование обнаружения конкретного окна"""
    logger.info(f"=== Диагностика окна: '{target_window_name}' ===")
    
    # Тест 1: Точное совпадение через pygetwindow
    logger.info("\n1. Тест точного совпадения через pygetwindow:")
    try:
        windows = gw.getWindowsWithTitle(target_window_name)
        if windows:
            logger.info(f"✅ Найдено {len(windows)} окон с точным названием")
            for i, window in enumerate(windows):
                logger.info(f"   Окно {i+1}: {window.title} at ({window.left}, {window.top})")
        else:
            logger.warning("❌ Окна с точным названием не найдены")
    except Exception as e:
        logger.error(f"❌ Ошибка при поиске: {e}")
    
    # Тест 2: Поиск по частичному совпадению
    logger.info("\n2. Поиск по частичному совпадению:")
    matching_windows = search_window_by_partial_title(target_window_name)
    if matching_windows:
        logger.info(f"✅ Найдено {len(matching_windows)} окон с частичным совпадением:")
        for window in matching_windows:
            logger.info(f"   - '{window['title']}' (класс: {window['class_name']})")
    else:
        logger.warning("❌ Окна с частичным совпадением не найдены")
    
    # Тест 3: Поиск через WindowUtils
    logger.info("\n3. Тест через WindowUtils:")
    window_info = WindowUtils.get_window_info(target_window_name)
    if window_info:
        logger.info(f"✅ WindowUtils нашел окно: {window_info}")
    else:
        logger.warning("❌ WindowUtils не нашел окно")
    
    # Тест 4: Показать все окна с похожими названиями
    logger.info("\n4. Все окна с похожими названиями:")
    words = target_window_name.split()
    for word in words:
        if len(word) > 3:  # Ищем только значимые слова
            similar_windows = search_window_by_partial_title(word)
            if similar_windows:
                logger.info(f"   Окна содержащие '{word}':")
                for window in similar_windows[:5]:  # Показываем только первые 5
                    logger.info(f"     - '{window['title']}'")

def show_all_windows():
    """Показать все доступные окна"""
    logger.info("=== Все доступные окна ===")
    
    # Через win32gui
    logger.info("\n1. Окна через win32gui:")
    win32_windows = get_all_windows_detailed()
    visible_windows = [w for w in win32_windows if w['title'].strip()]
    
    logger.info(f"Найдено {len(visible_windows)} видимых окон с названиями:")
    for window in visible_windows[:20]:  # Показываем первые 20
        logger.info(f"   - '{window['title']}' (класс: {window['class_name']})")
    
    if len(visible_windows) > 20:
        logger.info(f"   ... и еще {len(visible_windows) - 20} окон")
    
    # Через pygetwindow
    logger.info("\n2. Окна через pygetwindow:")
    pg_windows = get_pygetwindow_windows()
    logger.info(f"Найдено {len(pg_windows)} окон:")
    for window in pg_windows[:20]:  # Показываем первые 20
        logger.info(f"   - '{window['title']}'")
    
    if len(pg_windows) > 20:
        logger.info(f"   ... и еще {len(pg_windows) - 20} окон")

def main():
    """Главная функция диагностики"""
    logger.info("🔍 Запуск диагностики окон")
    
    # Показываем все окна
    show_all_windows()
    
    # Тестируем конкретные окна из привязок
    logger.info("\n" + "="*60)
    
    # Читаем привязки из файла
    try:
        import json
        bindings_file = os.path.join("settings", "bindings.json")
        if os.path.exists(bindings_file):
            with open(bindings_file, 'r', encoding='utf-8') as f:
                bindings = json.load(f)
            
            logger.info(f"\nТестирование окон из {len(bindings)} привязок:")
            
            tested_apps = set()
            for binding_data in bindings:
                app_name = binding_data.get('app_name', '')
                if app_name and app_name not in tested_apps:
                    tested_apps.add(app_name)
                    logger.info(f"\n{'='*60}")
                    test_window_detection(app_name)
        else:
            logger.warning("Файл привязок не найден")
    
    except Exception as e:
        logger.error(f"Ошибка при чтении привязок: {e}")
    
    # Дополнительно тестируем реально открытое окно
    logger.info(f"\n{'='*60}")
    logger.info("\nТестирование реально открытого окна:")
    test_window_detection("‎Мой Регломобайл @ ‎sergei (204331)")
    
    logger.info("\n✅ Диагностика завершена")

if __name__ == "__main__":
    main()