#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Пакет core для приложения WindowCommander.
Содержит основные классы и функции для работы с окнами Windows.
"""

from .window_manager import WindowManager
from .window_selector import WindowSelector

__all__ = ['WindowManager', 'WindowSelector']
