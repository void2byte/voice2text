"""
Модуль управления голосом (Voice Control).
Предоставляет функциональность для работы с микрофоном, записи аудио.
"""

import os
import sys

# Добавляем корневую директорию проекта в путь поиска модулей
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from .core.voice_controller import VoiceController

__version__ = '1.0.0'
__author__ = 'Screph Team'
