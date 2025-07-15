#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Вкладка настроек приложения WindowCommander.
Позволяет настраивать параметры взаимодействия с окнами.
"""

import os
import sys
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QGroupBox, QCheckBox, QSpinBox,
    QComboBox, QFormLayout
)
from PySide6.QtCore import Qt, Signal, Slot

class SettingsTab(QWidget):
    """
    Вкладка настроек приложения
    """
    
    # Сигнал об изменении настроек
    settings_changed = Signal(dict)
    
    def __init__(self, logger):
        """
        Инициализация вкладки настроек
        
        Args:
            logger: Объект логгера
        """
        super().__init__()
        
        self.logger = logger
        
        # Путь к файлу настроек
        self.settings_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
            "settings.json"
        )
        
        # Загружаем настройки или устанавливаем по умолчанию
        self.settings = self.load_settings()
        
        # Настройка интерфейса
        self.setup_ui()
    
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        # Основной макет
        layout = QVBoxLayout(self)
        
        # Группа текстовых настроек
        self.text_group = QGroupBox(self.tr("Настройки отправки текста"))
        self.text_layout = QFormLayout(self.text_group)
        
        # Задержка между символами
        self.char_delay_spin = QSpinBox()
        self.char_delay_spin.setRange(0, 100)
        self.char_delay_spin.setValue(self.settings.get('char_delay', 10))
        self.char_delay_spin.setSuffix(self.tr(" мс"))
        self.text_layout.addRow(self.tr("Задержка между символами:"), self.char_delay_spin)
        
        # Метод отправки текста
        self.text_method_combo = QComboBox()
        self.text_method_combo.addItems([
            self.tr("Посимвольный ввод (WM_CHAR)"),
            self.tr("Буфер обмена (Ctrl+V)"),
            self.tr("SendMessage API"),
            self.tr("PostMessage API")
        ])
        self.text_method_combo.setCurrentIndex(self.settings.get('text_method', 0))
        self.text_layout.addRow(self.tr("Метод отправки текста:"), self.text_method_combo)
        
        # Восстанавливать буфер обмена
        self.restore_clipboard = QCheckBox(self.tr("Восстанавливать содержимое буфера обмена"))
        self.restore_clipboard.setChecked(self.settings.get('restore_clipboard', True))
        self.text_layout.addRow("", self.restore_clipboard)
        
        # Группа настроек интерфейса
        self.ui_group = QGroupBox(self.tr("Настройки интерфейса"))
        self.ui_layout = QFormLayout(self.ui_group)
        
        # Задержка по умолчанию
        self.default_delay_spin = QSpinBox()
        self.default_delay_spin.setRange(1, 10)
        self.default_delay_spin.setValue(self.settings.get('default_delay', 3))
        self.default_delay_spin.setSuffix(self.tr(" сек"))
        self.ui_layout.addRow(self.tr("Задержка перед отправкой по умолчанию:"), self.default_delay_spin)
        
        # Очищать после отправки
        self.clear_after_send = QCheckBox(self.tr("Очищать поле ввода после отправки"))
        self.clear_after_send.setChecked(self.settings.get('clear_after_send', True))
        self.ui_layout.addRow("", self.clear_after_send)
        
        # Предупреждения
        self.show_warnings = QCheckBox(self.tr("Показывать предупреждения"))
        self.show_warnings.setChecked(self.settings.get('show_warnings', True))
        self.ui_layout.addRow("", self.show_warnings)
        
        # Группа настроек мыши
        self.mouse_group = QGroupBox(self.tr("Настройки мыши"))
        self.mouse_layout = QFormLayout(self.mouse_group)
        
        # Задержка между нажатием и отпусканием
        self.click_duration_spin = QSpinBox()
        self.click_duration_spin.setRange(0, 500)
        self.click_duration_spin.setValue(self.settings.get('click_duration', 100))
        self.click_duration_spin.setSuffix(self.tr(" мс"))
        self.mouse_layout.addRow(self.tr("Длительность клика:"), self.click_duration_spin)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        self.save_button = QPushButton(self.tr("Сохранить настройки"))
        self.save_button.clicked.connect(self.save_settings_clicked)
        buttons_layout.addWidget(self.save_button)
        
        self.reset_button = QPushButton(self.tr("Сбросить к значениям по умолчанию"))
        self.reset_button.clicked.connect(self.reset_settings_clicked)
        buttons_layout.addWidget(self.reset_button)
        
        # Добавление групп в основной макет
        layout.addWidget(self.text_group)
        layout.addWidget(self.ui_group)
        layout.addWidget(self.mouse_group)
        layout.addLayout(buttons_layout)
        layout.addStretch(1)
        
        # Инициализация переводов
        self.retranslate_ui()
    
    def load_settings(self):
        """
        Загрузка настроек из файла
        
        Returns:
            dict: Словарь с настройками
        """
        default_settings = {
            'char_delay': 10,  # мс
            'text_method': 0,  # 0 - WM_CHAR, 1 - Ctrl+V, 2 - SendMessage, 3 - PostMessage
            'restore_clipboard': True,
            'default_delay': 3,  # сек
            'clear_after_send': True,
            'show_warnings': True,
            'click_duration': 100  # мс
        }
        
        if not os.path.exists(self.settings_file):
            self.logger.info(f"Файл настроек не найден, используем значения по умолчанию")
            return default_settings
        
        try:
            with open(self.settings_file, 'r') as f:
                settings = json.load(f)
            
            self.logger.info(f"Настройки загружены из {self.settings_file}")
            
            # Обновляем значения по умолчанию загруженными
            for key, value in settings.items():
                default_settings[key] = value
                
            return default_settings
            
        except Exception as e:
            self.logger.error(f"Ошибка при загрузке настроек: {str(e)}")
            return default_settings
    
    def save_settings_to_file(self, settings):
        """
        Сохранение настроек в файл
        
        Args:
            settings: Словарь с настройками
            
        Returns:
            bool: True если успешно, иначе False
        """
        try:
            # Создаем директорию если нужно
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=4)
                
            self.logger.info(f"Настройки сохранены в {self.settings_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении настроек: {str(e)}")
            return False
    
    def get_current_settings(self):
        """
        Получение текущих настроек из UI
        
        Returns:
            dict: Словарь с настройками
        """
        return {
            'char_delay': self.char_delay_spin.value(),
            'text_method': self.text_method_combo.currentIndex(),
            'restore_clipboard': self.restore_clipboard.isChecked(),
            'default_delay': self.default_delay_spin.value(),
            'clear_after_send': self.clear_after_send.isChecked(),
            'show_warnings': self.show_warnings.isChecked(),
            'click_duration': self.click_duration_spin.value()
        }
    
    def retranslate_ui(self):
        """Обновляет переводы интерфейса."""
        # Обновляем заголовки групп
        self.text_group.setTitle(self.tr("Настройки отправки текста"))
        self.ui_group.setTitle(self.tr("Настройки интерфейса"))
        self.mouse_group.setTitle(self.tr("Настройки мыши"))
        
        # Обновляем суффиксы спинбоксов
        self.char_delay_spin.setSuffix(self.tr(" мс"))
        self.default_delay_spin.setSuffix(self.tr(" сек"))
        self.click_duration_spin.setSuffix(self.tr(" мс"))
        
        # Обновляем элементы комбобокса
        current_method = self.text_method_combo.currentIndex()
        self.text_method_combo.clear()
        self.text_method_combo.addItems([
            self.tr("Посимвольный ввод (WM_CHAR)"),
            self.tr("Буфер обмена (Ctrl+V)"),
            self.tr("SendMessage API"),
            self.tr("PostMessage API")
        ])
        self.text_method_combo.setCurrentIndex(current_method)
        
        # Обновляем чекбоксы
        self.restore_clipboard.setText(self.tr("Восстанавливать содержимое буфера обмена"))
        self.clear_after_send.setText(self.tr("Очищать поле ввода после отправки"))
        self.show_warnings.setText(self.tr("Показывать предупреждения"))
        
        # Обновляем кнопки
        self.save_button.setText(self.tr("Сохранить настройки"))
        self.reset_button.setText(self.tr("Сбросить к значениям по умолчанию"))
        
        # Обновляем метки в формах (требует пересоздания строк)
        self._update_form_labels()
    
    @Slot()
    def save_settings_clicked(self):
        """Обработчик нажатия на кнопку сохранения настроек"""
        self.logger.info("Сохранение настроек")
        
        # Получаем текущие настройки из UI
        settings = self.get_current_settings()
        
        # Сохраняем в файл
        if self.save_settings_to_file(settings):
            # Сохраняем локально
            self.settings = settings
            
            # Отправляем сигнал об изменении настроек
            self.settings_changed.emit(settings)
    
    @Slot()
    def reset_settings_clicked(self):
        """Обработчик нажатия на кнопку сброса настроек"""
        self.logger.info("Сброс настроек к значениям по умолчанию")
        
        # Значения по умолчанию
        default_settings = {
            'char_delay': 10,
            'text_method': 0,
            'restore_clipboard': True,
            'default_delay': 3,
            'clear_after_send': True,
            'show_warnings': True,
            'click_duration': 100
        }
        
        # Обновляем UI
        self.char_delay_spin.setValue(default_settings['char_delay'])
        self.text_method_combo.setCurrentIndex(default_settings['text_method'])
        self.restore_clipboard.setChecked(default_settings['restore_clipboard'])
        self.default_delay_spin.setValue(default_settings['default_delay'])
        self.clear_after_send.setChecked(default_settings['clear_after_send'])
        self.show_warnings.setChecked(default_settings['show_warnings'])
        self.click_duration_spin.setValue(default_settings['click_duration'])
        
        # Не сохраняем автоматически, пользователь должен нажать "Сохранить настройки"
    
    def _update_form_labels(self):
        """Обновляет метки в формах"""
        # Очищаем и пересоздаем строки форм с обновленными переводами
        
        # Сохраняем текущие значения
        char_delay_value = self.char_delay_spin.value()
        text_method_index = self.text_method_combo.currentIndex()
        restore_clipboard_checked = self.restore_clipboard.isChecked()
        default_delay_value = self.default_delay_spin.value()
        clear_after_send_checked = self.clear_after_send.isChecked()
        show_warnings_checked = self.show_warnings.isChecked()
        click_duration_value = self.click_duration_spin.value()
        
        # Очищаем формы
        while self.text_layout.count():
            child = self.text_layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)
        
        while self.ui_layout.count():
            child = self.ui_layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)
        
        while self.mouse_layout.count():
            child = self.mouse_layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)
        
        # Пересоздаем виджеты с новыми переводами
        self.char_delay_spin = QSpinBox()
        self.char_delay_spin.setRange(0, 100)
        self.char_delay_spin.setValue(char_delay_value)
        self.char_delay_spin.setSuffix(self.tr(" мс"))
        self.text_layout.addRow(self.tr("Задержка между символами:"), self.char_delay_spin)
        
        self.text_method_combo = QComboBox()
        self.text_method_combo.addItems([
            self.tr("Посимвольный ввод (WM_CHAR)"),
            self.tr("Буфер обмена (Ctrl+V)"),
            self.tr("SendMessage API"),
            self.tr("PostMessage API")
        ])
        self.text_method_combo.setCurrentIndex(text_method_index)
        self.text_layout.addRow(self.tr("Метод отправки текста:"), self.text_method_combo)
        
        self.restore_clipboard = QCheckBox(self.tr("Восстанавливать содержимое буфера обмена"))
        self.restore_clipboard.setChecked(restore_clipboard_checked)
        self.text_layout.addRow("", self.restore_clipboard)
        
        self.default_delay_spin = QSpinBox()
        self.default_delay_spin.setRange(1, 10)
        self.default_delay_spin.setValue(default_delay_value)
        self.default_delay_spin.setSuffix(self.tr(" сек"))
        self.ui_layout.addRow(self.tr("Задержка перед отправкой по умолчанию:"), self.default_delay_spin)
        
        self.clear_after_send = QCheckBox(self.tr("Очищать поле ввода после отправки"))
        self.clear_after_send.setChecked(clear_after_send_checked)
        self.ui_layout.addRow("", self.clear_after_send)
        
        self.show_warnings = QCheckBox(self.tr("Показывать предупреждения"))
        self.show_warnings.setChecked(show_warnings_checked)
        self.ui_layout.addRow("", self.show_warnings)
        
        self.click_duration_spin = QSpinBox()
        self.click_duration_spin.setRange(0, 500)
        self.click_duration_spin.setValue(click_duration_value)
        self.click_duration_spin.setSuffix(self.tr(" мс"))
        self.mouse_layout.addRow(self.tr("Длительность клика:"), self.click_duration_spin)
