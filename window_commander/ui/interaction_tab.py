#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Вкладка отправки команд для приложения WindowCommander.
Позволяет отправлять текст и команды в выбранное окно.
"""

import os
import sys
import time
import pyperclip
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTextEdit, QLabel, QGroupBox, QSpinBox, QCheckBox,
    QMessageBox, QComboBox, QLineEdit
)
from PySide6.QtCore import Qt, Signal, Slot, QTimer

class InteractionTab(QWidget):
    """
    Вкладка отправки команд в окно
    """
    
    def __init__(self, logger, window_manager):
        """
        Инициализация вкладки отправки команд
        
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
        
        # Группа отправки текста
        text_group = QGroupBox(self.tr("Отправка текста"))
        text_layout = QVBoxLayout(text_group)
        
        # Поле ввода текста
        text_layout.addWidget(QLabel(self.tr("Текст для отправки:")))
        
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText(self.tr("Введите текст для отправки в выбранное окно"))
        self.text_input.setMinimumHeight(100)
        text_layout.addWidget(self.text_input)
        
        # Настройки отправки
        settings_layout = QHBoxLayout()
        
        # Задержка
        delay_layout = QHBoxLayout()
        delay_layout.addWidget(QLabel(self.tr("Задержка перед отправкой (сек):")))
        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(1, 10)
        self.delay_spin.setValue(3)
        delay_layout.addWidget(self.delay_spin)
        delay_layout.addStretch(1)
        
        settings_layout.addLayout(delay_layout)
        
        # Активация окна
        self.focus_checkbox = QCheckBox(self.tr("Активировать окно перед отправкой"))
        self.focus_checkbox.setChecked(False)
        settings_layout.addWidget(self.focus_checkbox)
        
        text_layout.addLayout(settings_layout)
        
        # Кнопки отправки
        buttons_layout = QHBoxLayout()
        
        self.send_button = QPushButton(self.tr("Отправить текст"))
        self.send_button.setMinimumHeight(30)
        self.send_button.clicked.connect(self.on_send_text_clicked)
        buttons_layout.addWidget(self.send_button)
        
        self.clipboard_button = QPushButton(self.tr("Отправить из буфера обмена"))
        self.clipboard_button.clicked.connect(self.on_send_clipboard_clicked)
        buttons_layout.addWidget(self.clipboard_button)
        
        text_layout.addLayout(buttons_layout)
        
        # Группа для специальных команд
        commands_group = QGroupBox(self.tr("Специальные команды"))
        commands_layout = QVBoxLayout(commands_group)
        
        # Выпадающий список команд
        command_layout = QHBoxLayout()
        command_layout.addWidget(QLabel(self.tr("Команда:")))
        
        self.command_combo = QComboBox()
        self.command_combo.addItems([
            "Enter", "Tab", "Escape", "Space",
            "Backspace", "Delete", "Ctrl+C", "Ctrl+V",
            "Ctrl+Z", "Ctrl+Y", "Ctrl+S", "Ctrl+A",
            "F1", "F2", "F3", "F4", "F5"
        ])
        command_layout.addWidget(self.command_combo)
        
        self.send_command_button = QPushButton(self.tr("Отправить команду"))
        self.send_command_button.clicked.connect(self.on_send_command_clicked)
        command_layout.addWidget(self.send_command_button)
        
        commands_layout.addLayout(command_layout)
        
        # Клик мышью
        click_layout = QHBoxLayout()
        click_layout.addWidget(QLabel(self.tr("Клик по координатам (X, Y):")))
        
        self.x_coord = QLineEdit()
        self.x_coord.setPlaceholderText("X")
        self.x_coord.setFixedWidth(60)
        click_layout.addWidget(self.x_coord)
        
        self.y_coord = QLineEdit()
        self.y_coord.setPlaceholderText("Y")
        self.y_coord.setFixedWidth(60)
        click_layout.addWidget(self.y_coord)
        
        self.click_button = QPushButton(self.tr("Отправить клик"))
        self.click_button.clicked.connect(self.on_click_button_clicked)
        click_layout.addWidget(self.click_button)
        
        commands_layout.addLayout(click_layout)
        
        # Статус отправки
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel(self.tr("Статус:")))
        
        self.status_label = QLabel(self.tr("Готов к отправке"))
        status_layout.addWidget(self.status_label)
        status_layout.addStretch(1)
        
        # Очистка поля после отправки
        self.clear_after_send = QCheckBox(self.tr("Очищать поле после отправки"))
        self.clear_after_send.setChecked(True)
        status_layout.addWidget(self.clear_after_send)
        
        commands_layout.addLayout(status_layout)
        
        # Добавление групп в основной макет
        layout.addWidget(text_group)
        layout.addWidget(commands_group)
        layout.addStretch(1)
        
        # Отключаем элементы управления, пока окно не выбрано
        self.set_controls_enabled(False)
        
        self.retranslate_ui()
    
    def update_window_info(self):
        """Обновление интерфейса после получения информации о окне"""
        if self.window_manager.get_window_info():
            self.status_label.setText(self.tr("Готов к отправке в выбранное окно"))
            self.set_controls_enabled(True)
        else:
            self.status_label.setText(self.tr("Окно не выбрано"))
            self.set_controls_enabled(False)
    
    def set_controls_enabled(self, enabled):
        """
        Включение/отключение элементов управления
        
        Args:
            enabled: True для включения, False для отключения
        """
        self.text_input.setEnabled(enabled)
        self.send_button.setEnabled(enabled)
        self.clipboard_button.setEnabled(enabled)
        self.command_combo.setEnabled(enabled)
        self.send_command_button.setEnabled(enabled)
        self.x_coord.setEnabled(enabled)
        self.y_coord.setEnabled(enabled)
        self.click_button.setEnabled(enabled)
    
    def retranslate_ui(self):
        """Обновляет переводы интерфейса."""
        # Обновление переводов будет выполнено при следующем обновлении UI
        pass
        
    def on_send_text_clicked(self):
        """Обработчик нажатия на кнопку отправки текста"""
        self.logger.info("Нажата кнопка отправки текста")
        
        text = self.text_input.toPlainText().strip()
        if not text:
            self.status_label.setText(self.tr("Ошибка: Введите текст для отправки"))
            return
        
        # Получаем настройки
        delay = self.delay_spin.value()
        with_focus = self.focus_checkbox.isChecked()
        
        # Запускаем отправку текста с обратным отсчетом
        self.status_label.setText(self.tr("Подготовка к отправке. Отправка через {} секунд...").format(delay))
        self.set_controls_enabled(False)
        
        # Создаем таймер для отсчета
        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self.update_countdown)
        self.countdown_value = delay
        
        # Сохраняем параметры для передачи в обработчик
        self.send_params = {
            'text': text,
            'with_focus': with_focus,
            'clear_after': self.clear_after_send.isChecked()
        }
        
        # Запускаем таймер
        self.countdown_timer.start(1000)  # Срабатывает каждую секунду
        self.update_countdown()
    
    def update_countdown(self):
        """Обновление обратного отсчета"""
        if self.countdown_value <= 0:
            # Останавливаем таймер
            self.countdown_timer.stop()
            
            # Отправляем текст
            self.send_text_now()
            
            return
        
        # Обновляем отображение отсчета
        self.status_label.setText(f"Отправка через {self.countdown_value} сек...")
        self.countdown_value -= 1
    
    def send_text_now(self):
        """Отправка текста после завершения отсчета"""
        try:
            # Извлекаем параметры
            text = self.send_params['text']
            with_focus = self.send_params['with_focus']
            clear_after = self.send_params['clear_after']
            
            # Отправляем текст через менеджер окон
            if self.window_manager.send_text(text, with_focus):
                self.status_label.setText("Текст успешно отправлен")
                
                # Очищаем поле ввода, если нужно
                if clear_after:
                    self.text_input.clear()
            else:
                self.status_label.setText("Ошибка при отправке текста")
                
        except Exception as e:
            self.logger.error(f"Ошибка при отправке текста: {str(e)}")
            self.status_label.setText(f"Ошибка: {str(e)}")
            
        finally:
            # Восстанавливаем элементы управления
            self.set_controls_enabled(True)
    
    def on_send_clipboard_clicked(self):
        """Обработчик нажатия на кнопку отправки из буфера обмена"""
        self.logger.info("Нажата кнопка отправки из буфера обмена")
        
        try:
            # Получаем текст из буфера обмена
            clipboard_text = pyperclip.paste()
            
            if not clipboard_text:
                self.status_label.setText("Буфер обмена пуст")
                return
            
            # Вставляем текст в поле ввода
            self.text_input.setPlainText(clipboard_text)
            
            # Запускаем отправку
            self.on_send_text_clicked()
            
        except Exception as e:
            self.logger.error(f"Ошибка при работе с буфером обмена: {str(e)}")
            self.status_label.setText(f"Ошибка буфера обмена: {str(e)}")
    
    def on_send_command_clicked(self):
        """Обработчик нажатия на кнопку отправки команды"""
        self.logger.info("Нажата кнопка отправки команды")
        
        command = self.command_combo.currentText()
        with_focus = self.focus_checkbox.isChecked()
        
        try:
            if self.window_manager.send_command(command, with_focus):
                self.status_label.setText(f"Команда {command} успешно отправлена")
            else:
                self.status_label.setText(f"Ошибка при отправке команды {command}")
                
        except Exception as e:
            self.logger.error(f"Ошибка при отправке команды: {str(e)}")
            self.status_label.setText(f"Ошибка: {str(e)}")
    
    def on_click_button_clicked(self):
        """Обработчик нажатия на кнопку отправки клика"""
        self.logger.info("Нажата кнопка отправки клика")
        
        try:
            # Получаем координаты
            x_text = self.x_coord.text().strip()
            y_text = self.y_coord.text().strip()
            
            if not x_text or not y_text:
                self.status_label.setText("Введите координаты X и Y")
                return
            
            # Преобразуем в числа
            try:
                x = int(x_text)
                y = int(y_text)
            except ValueError:
                self.status_label.setText("Координаты должны быть целыми числами")
                return
            
            # Отправляем клик через менеджер окон
            with_focus = self.focus_checkbox.isChecked()
            
            if self.window_manager.click_at_position(x, y, with_focus):
                self.status_label.setText(f"Клик по координатам ({x}, {y}) успешно отправлен")
            else:
                self.status_label.setText(f"Ошибка при отправке клика по координатам ({x}, {y})")
                
        except Exception as e:
            self.logger.error(f"Ошибка при отправке клика: {str(e)}")
            self.status_label.setText(f"Ошибка: {str(e)}")
