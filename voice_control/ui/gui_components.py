"""
Базовые компоненты графического интерфейса для распознавания речи.
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Union

from voice_control.utils.logger import setup_logging

from PySide6.QtWidgets import (QWidget, QPushButton, QLabel, QTextEdit, 
                            QVBoxLayout, QHBoxLayout, QComboBox, QLineEdit, 
                            QGroupBox, QFormLayout, QRadioButton, QButtonGroup,
                            QStatusBar, QProgressBar, QScrollArea)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

# Настройка логирования
logger = setup_logging(
    logger_name=__name__,
    level=logging.DEBUG,
    log_file=os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", f"gui_components_{datetime.now().strftime('%Y%m%d')}.log"),
    console=True,
    encoding='utf-8'
)


class VolumeIndicator(QWidget):
    """Индикатор громкости для отображения уровня звука."""
    
    def __init__(self, parent=None):
        """
        Инициализация индикатора громкости.
        
        Args:
            parent: Родительский виджет
        """
        super().__init__(parent)
        
        # Настройка размеров
        self.setMinimumHeight(20)
        self.setMaximumHeight(20)
        
        # Текущий уровень громкости (0.0 - 1.0)
        self.volume_level = 0.0
        
        # Цвета для разных уровней громкости
        self.low_color = Qt.GlobalColor.green
        self.medium_color = Qt.GlobalColor.yellow
        self.high_color = Qt.GlobalColor.red
        
        self.retranslate_ui()
    
    def retranslate_ui(self):
        """Обновляет переводы интерфейса."""
        # В данном виджете нет текстовых элементов для перевода,
        # но метод нужен для соответствия паттерну
        pass
    
    def set_volume(self, level: float):
        """
        Установка уровня громкости.
        
        Args:
            level: Уровень громкости (0.0 - 1.0)
        """
        self.volume_level = max(0.0, min(1.0, level))
        self.update()
    
    def paintEvent(self, event):
        """Отрисовка индикатора громкости."""
        painter = QPainter(self)
        
        # Размеры виджета
        width = self.width()
        height = self.height()
        
        # Определяем цвет в зависимости от уровня громкости
        if self.volume_level < 0.3:
            color = self.low_color
        elif self.volume_level < 0.7:
            color = self.medium_color
        else:
            color = self.high_color
        
        # Рисуем фон
        painter.fillRect(0, 0, width, height, Qt.GlobalColor.black)
        
        # Рисуем индикатор громкости
        bar_width = int(width * self.volume_level)
        painter.fillRect(0, 0, bar_width, height, color)


class StatusBar(QWidget):
    """Статусная строка для отображения информации о состоянии."""
    
    def __init__(self, parent=None):
        """
        Инициализация статусной строки.
        
        Args:
            parent: Родительский виджет
        """
        super().__init__(parent)
        
        # Настройка размеров
        self.setMinimumHeight(30)
        self.setMaximumHeight(30)
        
        # Создаем макет
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 0, 5, 0)
        
        # Метка для отображения статуса
        self.status_label = QLabel()
        self.status_label.setFont(QFont("Arial", 10))
        layout.addWidget(self.status_label)
        
        # Растягивающийся элемент
        layout.addStretch()
        
        # Метка для отображения информации
        self.info_label = QLabel("")
        self.info_label.setFont(QFont("Arial", 10))
        layout.addWidget(self.info_label)
        
        self.retranslate_ui()
    
    def retranslate_ui(self):
        """Обновляет переводы интерфейса."""
        self.status_label.setText(self.tr("Готов"))
    
    def set_status(self, text: str):
        """
        Установка текста статуса.
        
        Args:
            text: Текст статуса
        """
        self.status_label.setText(text)
    
    def set_info(self, text: str):
        """
        Установка информационного текста.
        
        Args:
            text: Информационный текст
        """
        self.info_label.setText(text)


# Импортируем QPainter здесь, чтобы избежать ошибок циклического импорта
from PySide6.QtGui import QPainter

def create_button(text: str, parent: QWidget = None, on_click: callable = None, icon_path: str = None) -> QPushButton:
    """Создает и возвращает QPushButton."""
    button = QPushButton(text, parent)
    if on_click:
        button.clicked.connect(on_click)
    if icon_path:
        from PySide6.QtGui import QIcon
        button.setIcon(QIcon(icon_path))
    return button

def create_label(text: str, parent: QWidget = None) -> QLabel:
    """Создает и возвращает QLabel."""
    return QLabel(text, parent)

def create_text_edit(parent: QWidget = None, read_only: bool = False) -> QTextEdit:
    """Создает и возвращает QTextEdit."""
    text_edit = QTextEdit(parent)
    text_edit.setReadOnly(read_only)
    return text_edit

def create_progress_bar(parent: QWidget = None) -> 'QProgressBar':
    """Создает и возвращает QProgressBar."""
    return QProgressBar(parent)

def create_status_indicator(parent: QWidget = None) -> QLabel:
    """Создает и возвращает QLabel для индикации статуса."""
    label = QLabel(parent)
    label.setFixedSize(16, 16)
    label.setStyleSheet("border-radius: 8px; background-color: gray;")
    return label

def create_scroll_area(widget: QWidget) -> 'QScrollArea':
    """Создает и возвращает QScrollArea с виджетом внутри."""
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setWidget(widget)
    return scroll_area
