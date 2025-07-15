"""
Модуль с виджетом для редактирования горячих клавиш.
"""

import logging
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PySide6.QtGui import QKeySequence, QKeyEvent

# Настройка логгера
logger = logging.getLogger(__name__)


class HotkeyEditor(QWidget):
    """Виджет для редактирования горячих клавиш"""
    
    # Сигнал об изменении горячей клавиши
    key_changed = Signal(str)
    
    def __init__(self, label_text: str, key_sequence: str = "", parent=None):
        """
        Инициализация виджета
        
        Args:
            label_text: Текст метки
            key_sequence: Текущее значение горячей клавиши
            parent: Родительский виджет
        """
        super().__init__(parent)
        
        self.recording = False
        self.current_sequence = key_sequence
        
        self._init_ui(label_text)
    
    def _init_ui(self, label_text: str):
        """
        Инициализация пользовательского интерфейса
        
        Args:
            label_text: Текст метки
        """
        layout = QHBoxLayout()
        self.setLayout(layout)
        
        # Минимальные отступы для компактности
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Метка
        self.label = QLabel(label_text)
        layout.addWidget(self.label)
        
        # Кнопка для отображения и записи горячей клавиши
        self.key_button = QPushButton(self.current_sequence or "Нажмите для записи")
        self.key_button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.key_button.clicked.connect(self._start_recording)
        layout.addWidget(self.key_button)
        
        # Кнопка для очистки
        self.clear_button = QPushButton("Очистить")
        self.clear_button.clicked.connect(self._clear_hotkey)
        layout.addWidget(self.clear_button)
    
    def _start_recording(self):
        """Запуск записи горячей клавиши"""
        self.recording = True
        self.key_button.setText("Нажмите клавишу...")
        self.key_button.setFocus()
    
    def _stop_recording(self):
        """Остановка записи горячей клавиши"""
        self.recording = False
        self.key_button.setText(self.current_sequence or "Нажмите для записи")
    
    def _clear_hotkey(self):
        """Очистка горячей клавиши"""
        self.current_sequence = ""
        self.key_button.setText("Нажмите для записи")
        self.key_changed.emit("")
    
    def keyPressEvent(self, event: QKeyEvent):
        """
        Обработка нажатия клавиш
        
        Args:
            event: Объект события нажатия клавиши
        """
        if not self.recording:
            return super().keyPressEvent(event)
        
        # Игнорируем модификаторы клавиш, так как они будут обработаны вместе с основной клавишей
        if event.key() in (Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt, Qt.Key.Key_Meta):
            return
        
        # Получаем модификаторы
        modifiers = event.modifiers()
        
        # Формируем последовательность клавиш
        key_combo = QKeySequence(int(modifiers) | event.key())
        self.current_sequence = key_combo.toString()
        
        logger.debug(f"Записана горячая клавиша: {self.current_sequence}")
        
        # Останавливаем запись
        self._stop_recording()
        
        # Отправляем сигнал об изменении
        self.key_changed.emit(self.current_sequence)
    
    def focusOutEvent(self, event):
        """
        Обработка потери фокуса
        
        Args:
            event: Объект события потери фокуса
        """
        if self.recording:
            self._stop_recording()
        
        super().focusOutEvent(event)
    
    def get_key_sequence(self) -> str:
        """
        Получает текущую последовательность клавиш
        
        Returns:
            str: Строковое представление последовательности клавиш
        """
        return self.current_sequence
