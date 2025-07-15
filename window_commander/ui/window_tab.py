#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Вкладка выбора окна приложения WindowCommander.
Позволяет выбирать окна Windows для взаимодействия.
"""

import os
import sys
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTextEdit, QLabel, QGroupBox, QMessageBox
)
from PySide6.QtCore import Qt, Signal, Slot

class WindowTab(QWidget):
    """
    Вкладка выбора окна
    """
    
    # Сигнал о выборе окна (передает словарь с информацией о окне)
    window_selected = Signal(dict)
    
    def __init__(self, logger, window_manager):
        """
        Инициализация вкладки выбора окна
        
        Args:
            logger: Объект логгера
            window_manager: Менеджер окон
        """
        super().__init__()
        
        self.logger = logger
        self.window_manager = window_manager
        
        # Настройка интерфейса
        self.setup_ui()
    
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        # Основной макет
        layout = QVBoxLayout(self)
        
        # Группа выбора окна
        select_group = QGroupBox("Выбор окна")
        select_layout = QVBoxLayout(select_group)
        
        # Кнопка выбора окна
        select_button = QPushButton("Выбрать окно")
        select_button.setMinimumHeight(40)
        select_button.clicked.connect(self.on_select_window_clicked)
        select_layout.addWidget(select_button)
        
        # Добавляем поле с информацией о текущем окне
        info_label = QLabel("Информация о выбранном окне:")
        select_layout.addWidget(info_label)
        
        self.window_info_text = QTextEdit()
        self.window_info_text.setReadOnly(True)
        self.window_info_text.setMinimumHeight(100)
        select_layout.addWidget(self.window_info_text)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        
        self.refresh_button = QPushButton("Обновить информацию")
        self.refresh_button.clicked.connect(self.update_window_info)
        self.refresh_button.setEnabled(False)
        buttons_layout.addWidget(self.refresh_button)
        
        self.clear_button = QPushButton("Очистить выбор")
        self.clear_button.clicked.connect(self.clear_window_selection)
        self.clear_button.setEnabled(False)
        buttons_layout.addWidget(self.clear_button)
        
        select_layout.addLayout(buttons_layout)
        
        # Инструкции
        instructions_group = QGroupBox("Инструкции")
        instructions_layout = QVBoxLayout(instructions_group)
        
        instructions_text = """
        <b>Как выбрать окно для взаимодействия:</b>
        <ol>
            <li>Нажмите кнопку "Выбрать окно"</li>
            <li>Откроется окно выбора</li>
            <li>Наведите курсор на нужное окно</li>
            <li>Нажмите клавишу Enter для выбора</li>
        </ol>
        <p>После выбора окна вы сможете взаимодействовать с ним через вкладку "Отправка команд".</p>
        """
        
        instructions_label = QLabel()
        instructions_label.setText(instructions_text)
        instructions_label.setTextFormat(Qt.TextFormat.RichText)
        instructions_label.setWordWrap(True)
        instructions_layout.addWidget(instructions_label)
        
        # Добавление групп в основной макет
        layout.addWidget(select_group)
        layout.addWidget(instructions_group)
        layout.addStretch(1)
    
    def on_select_window_clicked(self):
        """Обработчик нажатия на кнопку выбора окна"""
        self.logger.info("Запуск выбора окна")
        
        try:
            # Запускаем выбор окна через менеджер окон
            window_info = self.window_manager.select_window()
            
            if window_info:
                self.logger.info(f"Выбрано окно: {window_info}")
                
                # Обновляем UI
                self.refresh_button.setEnabled(True)
                self.clear_button.setEnabled(True)
                
                # Отправляем сигнал о выборе окна
                self.window_selected.emit(window_info)
                
                # Обновляем информацию
                self.update_window_info()
            else:
                self.logger.warning("Окно не выбрано")
                
        except Exception as e:
            self.logger.error(f"Ошибка при выборе окна: {str(e)}")
            QMessageBox.critical(
                self, 
                "Ошибка", 
                f"Произошла ошибка при выборе окна: {str(e)}"
            )
    
    def update_window_info(self):
        """Обновление информации о выбранном окне"""
        window_info = self.window_manager.get_window_info()
        
        if not window_info:
            self.window_info_text.setPlainText("Окно не выбрано")
            self.refresh_button.setEnabled(False)
            self.clear_button.setEnabled(False)
            return
        
        # Форматируем информацию о окне
        info_text = f"Заголовок: {window_info.get('title', 'Неизвестно')}\n"
        info_text += f"HWND: {window_info.get('hwnd', 'Неизвестно')}\n"
        info_text += f"Класс: {window_info.get('class_name', 'Неизвестно')}\n"
        
        if 'rect' in window_info:
            rect = window_info['rect']
            info_text += f"Позиция: X={rect[0]}, Y={rect[1]}, "
            info_text += f"Ширина={rect[2]-rect[0]}, Высота={rect[3]-rect[1]}\n"
        
        if 'pid' in window_info:
            info_text += f"PID: {window_info['pid']}\n"
        
        # Обновляем текстовое поле
        self.window_info_text.setPlainText(info_text)
        
        # Активируем кнопки
        self.refresh_button.setEnabled(True)
        self.clear_button.setEnabled(True)
    
    def clear_window_selection(self):
        """Очистка выбора окна"""
        self.logger.info("Очистка выбора окна")
        
        # Очищаем информацию о окне в менеджере
        self.window_manager.clear_window_info()
        
        # Обновляем UI
        self.window_info_text.setPlainText("Окно не выбрано")
        self.refresh_button.setEnabled(False)
        self.clear_button.setEnabled(False)
