"""Утилиты для работы с экраном"""

from typing import Tuple
import pyautogui

def get_screen_size() -> Tuple[int, int]:
    """Получить размер экрана"""
    try:
        return pyautogui.size()
    except Exception:
        return (1920, 1080)  # Значение по умолчанию