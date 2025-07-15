#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Реализация класса QRunnable для работы с голосовыми аннотациями.
Использует пул потоков QThreadPool для повышения производительности.
"""

import logging
from PySide6.QtCore import QRunnable, QObject, Signal, QPoint, QThreadPool

# Настройка логгера
logger = logging.getLogger(__name__)


class VoiceAnnotationSignals(QObject):
    """
    Сигналы для использования с VoiceAnnotationRunnable.
    QRunnable не может иметь сигналы, поэтому мы используем отдельный класс.
    """
    finished = Signal()  # Сигнал о завершении работы
    position_widget = Signal(QPoint)  # Сигнал для позиционирования виджета
    show_widget = Signal()  # Сигнал для показа виджета
    start_recording = Signal()  # Сигнал для начала записи
    error = Signal(str)  # Сигнал об ошибке


class VoiceAnnotationRunnable(QRunnable):
    """
    Реализация голосовой аннотации как QRunnable для использования в QThreadPool.
    
    Преимущества перед QThread:
    - Меньше накладных расходов на создание/удаление отдельных потоков
    - Автоматическое распределение задач по доступным потокам
    - Улучшенная масштабируемость и производительность
    """
    
    def __init__(self, pos=None):
        """
        Инициализация задачи голосовой аннотации.
        
        Args:
            pos (QPoint, optional): Позиция виджета. По умолчанию None.
        """
        super().__init__()
        
        # Сигналы
        self.signals = VoiceAnnotationSignals()
        
        # Сохраняем позицию
        self.pos = pos
        
    def run(self):
        """
        Основной метод, выполняемый в потоке.
        Отправляет сигналы для обновления UI.
        """
        try:
            logger.debug("[ГОЛОСОВАЯ АННОТАЦИЯ] Начало выполнения задачи")
            
            # Если передана позиция, отправляем сигнал для позиционирования виджета
            if self.pos:
                logger.debug(f"[ГОЛОСОВАЯ АННОТАЦИЯ] Устанавливаем позицию виджета: {self.pos.x()}, {self.pos.y()}")
                self.signals.position_widget.emit(self.pos)
            
            # Отправляем сигнал для показа виджета
            logger.debug("[ГОЛОСОВАЯ АННОТАЦИЯ] Показываем виджет")
            self.signals.show_widget.emit()
            
            # Отправляем сигнал для начала записи
            logger.debug("[ГОЛОСОВАЯ АННОТАЦИЯ] Запускаем запись")
            self.signals.start_recording.emit()
            
            # Отправляем сигнал о завершении задачи
            logger.debug("[ГОЛОСОВАЯ АННОТАЦИЯ] Задача завершена")
            self.signals.finished.emit()
            
        except Exception as e:
            logger.error(f"[ГОЛОСОВАЯ АННОТАЦИЯ] Ошибка: {e}", exc_info=True)
            self.signals.error.emit(str(e))
