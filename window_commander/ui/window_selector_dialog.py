#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Модуль с диалогом для выбора окна через перетаскивание метки.
Предоставляет визуальный интерфейс для выбора окон Windows.
"""

import os
import sys
import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QApplication, QMessageBox, QFrame, QGroupBox, QStyle,
    QSizePolicy, QSpacerItem
)
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QCursor, QPixmap

# Импортируем наш модуль для поиска окон
from ..core.window_finder import WindowFinder

class WindowSelectorDialog(QDialog):
    """
    Диалог выбора окна с помощью перетаскивания метки
    """
    
    def __init__(self, logger=None):
        """
        Инициализация диалога выбора окна
        
        Args:
            logger: Объект логгера
        """
        super().__init__()
        
        self.logger = logger or logging.getLogger(__name__)
        self.selected_window_info = None
        self.tracking = False
        self.window_finder = WindowFinder(logger)
        self.target_pressed = False
        
        # Настройка интерфейса
        self.setup_ui()
        
        # Таймер для отслеживания позиции мыши
        self.track_timer = QTimer(self)
        self.track_timer.timeout.connect(self.track_mouse)
        
        # Запоминаем позицию окна, чтобы восстановить её при закрытии
        self.original_position = self.pos()
    
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        self.setWindowTitle("Выбор окна")
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        self.setMinimumSize(400, 300)
        
        # Основной макет
        layout = QVBoxLayout(self)
        
        # Инструкции
        instructions = QLabel(
            "<b>Перетащите метку на нужное окно для его выбора</b><br>"
            "Нажмите и удерживайте левую кнопку мыши на метке, затем<br>"
            "перетащите её на целевое окно и отпустите кнопку мыши."
        )
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instructions.setStyleSheet("font-size: 14px; margin: 10px;")
        layout.addWidget(instructions)
        
        # Создаем метку для перетаскивания
        target_layout = QHBoxLayout()
        layout.addLayout(target_layout)
        
        target_layout.addStretch()
        
        self.target_frame = QFrame()
        self.target_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.target_frame.setFrameShadow(QFrame.Shadow.Raised)
        self.target_frame.setMinimumSize(120, 120)
        self.target_frame.setMaximumSize(120, 120)
        self.target_frame.setStyleSheet(
            "background-color: #F0F0F0; "
            "border: 2px solid #3498db; "
            "border-radius: 10px;"
        )
        target_layout.addWidget(self.target_frame)
        
        target_label_layout = QVBoxLayout(self.target_frame)
        
        # Создаем контейнер для наложения изображения и текста
        target_container = QFrame()
        target_container.setFixedSize(100, 100)
        target_container_layout = QVBoxLayout(target_container)
        target_container_layout.setContentsMargins(0, 0, 0, 0)  # Убираем отступы
        
        # Изображение
        image_label = QLabel()
        pixmap = QPixmap("\\resources\\target.jpg")
        scaled_pixmap = pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        image_label.setPixmap(scaled_pixmap)
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Добавляем оба элемента в контейнер
        target_container_layout.addWidget(image_label)
 
        # Добавляем контейнер в основной макет
        target_label_layout.addWidget(target_container)
        
        # Установка курсора перетаскивания для метки
        self.target_frame.setCursor(Qt.CursorShape.DragMoveCursor)
        
        # Обработка событий мыши для метки
        self.target_frame.mousePressEvent = self.target_mouse_press
        self.target_frame.mouseReleaseEvent = self.target_mouse_release
        self.target_frame.mouseMoveEvent = self.target_mouse_move
        
        target_layout.addStretch()
        
        # Информация о текущем окне под курсором
        info_group = QGroupBox("Информация о выбранном окне")
        info_layout = QVBoxLayout(info_group)
        
        self.info_label = QLabel("Выберите окно, перетащив на него метку...")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setStyleSheet("font-size: 12px; margin: 5px;")
        self.info_label.setWordWrap(True)
        self.info_label.setMinimumHeight(80)
        info_layout.addWidget(self.info_label)
        
        layout.addWidget(info_group)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        layout.addLayout(buttons_layout)
        
        select_button = QPushButton("Выбрать текущее окно")
        select_button.clicked.connect(self.accept_current_window)
        select_button.setEnabled(False)
        select_button.setMinimumHeight(40)
        self.select_button = select_button
        buttons_layout.addWidget(select_button)
        
        cancel_button = QPushButton("Отмена")
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_button)
    
    def target_mouse_press(self, event):
        """
        Обработка нажатия кнопки мыши на метке
        
        Args:
            event: Событие нажатия кнопки мыши
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.logger.info("Начало перетаскивания метки")
            self.target_pressed = True
            
            # Запускаем таймер отслеживания
            self.tracking = True
            self.track_timer.start(50)  # Обновление каждые 50 мс для более плавного отслеживания
            
            # Сохраняем позицию курсора относительно метки
            self.drag_start_pos = event.pos()
            
            # Изменяем стиль метки при нажатии
            self.target_frame.setStyleSheet(
                "background-color: #E1F0FA; "
                "border: 2px solid #2980b9; "
                "border-radius: 10px;"
            )
            
            event.accept()
    
    def target_mouse_release(self, event):
        """
        Обработка отпускания кнопки мыши на метке
        
        Args:
            event: Событие отпускания кнопки мыши
        """
        if event.button() == Qt.MouseButton.LeftButton and self.target_pressed:
            self.logger.info("Завершение перетаскивания метки")
            self.target_pressed = False
            
            # Останавливаем таймер отслеживания
            if self.tracking:
                self.tracking = False
                self.track_timer.stop()
                self.logger.info("Таймер отслеживания остановлен")
            
            # Возвращаем стиль метки
            self.target_frame.setStyleSheet(
                "background-color: #F0F0F0; "
                "border: 2px solid #3498db; "
                "border-radius: 10px;"
            )
            
            # Если окно было выбрано, активируем кнопку выбора
            if self.selected_window_info:
                self.select_button.setEnabled(True)
                self.logger.info(f"Выбрано окно: {self.selected_window_info.get('title', 'Неизвестно')}")
            
            event.accept()
    
    def target_mouse_move(self, event):
        """
        Обработка перемещения мыши при перетаскивании метки
        
        Args:
            event: Событие перемещения мыши
        """
        if not self.target_pressed:
            return
            
        event.accept()
    
    def accept_current_window(self):
        """Принятие текущего выбранного окна"""
        if self.selected_window_info:
            self.logger.info(f"Принято выбранное окно: {self.selected_window_info}")
            self.accept()
        else:
            self.logger.warning("Попытка принять окно, когда ничего не выбрано")
    
    def track_mouse(self):
        """Отслеживание позиции мыши и обновление информации о окне"""
        if not self.tracking:
            return
            
        try:
            # Получаем позицию курсора напрямую через QCursor
            cursor_pos = QCursor.pos()
            x, y = cursor_pos.x(), cursor_pos.y()
            
            # Получаем окно по координатам
            hwnd = self.window_finder.get_window_at_point(x, y)
            
            if hwnd:
                # Получаем информацию о окне
                window_info = self.window_finder.get_window_info(hwnd)
                
                if window_info:
                    # Обновляем временную информацию о выбранном окне
                    self.selected_window_info = window_info
                    
                    # Обновляем метку с информацией
                    info_text = f"Заголовок: {window_info.get('title', 'Неизвестно')}\n"
                    info_text += f"Класс: {window_info.get('class_name', 'Неизвестно')}\n"
                    info_text += f"HWND: {hwnd}"
                    
                    # Обновляем информацию в диалоге
                    self.info_label.setText(info_text)
                    
        except Exception as e:
            self.logger.error(f"Ошибка при отслеживании мыши: {str(e)}")
    
    def keyPressEvent(self, event):
        """
        Обработка нажатий клавиш
        
        Args:
            event: Событие нажатия клавиши
        """
        # Нажатие Enter - принять текущее выбранное окно
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            if self.selected_window_info:
                self.logger.info(f"Выбрано окно: {self.selected_window_info}")
                # Останавливаем таймер, если он работает
                if self.tracking:
                    self.tracking = False
                    self.track_timer.stop()
                self.accept()
            else:
                self.logger.warning("Окно не выбрано")
                QMessageBox.warning(self, "Предупреждение", "Окно не выбрано!")
        
        # Нажатие Escape - отмена
        elif event.key() == Qt.Key.Key_Escape:
            self.logger.info("Отмена выбора окна")
            self.selected_window_info = None
            
            # Останавливаем таймер, если он работает
            if self.tracking:
                self.tracking = False
                self.track_timer.stop()
                
            self.reject()
        else:
            # Стандартная обработка клавиш
            super().keyPressEvent(event)
    
    def closeEvent(self, event):
        """
        Обработка закрытия диалога
        
        Args:
            event: Событие закрытия
        """
        # Останавливаем таймер при закрытии
        if self.tracking:
            self.tracking = False
            self.track_timer.stop()
            
        event.accept()
