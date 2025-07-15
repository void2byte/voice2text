#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Главное окно приложения WindowCommander.
Содержит вкладки для выбора окна, отправки команд и настроек.
"""

import os
import sys
import json
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QMessageBox, 
    QStatusBar, QVBoxLayout, QWidget
)
from PySide6.QtCore import Qt, QSize, Slot

# Импорт вкладок
from .window_tab import WindowTab
from .interaction_tab import InteractionTab
from .settings_tab import SettingsTab

# Импорт ядра приложения
from ..core.window_manager import WindowManager


class MainWindow(QMainWindow):
    """
    Главное окно приложения WindowCommander
    """
    
    def __init__(self, logger):
        """
        Инициализация главного окна
        
        Args:
            logger: Объект логгера
        """
        super().__init__()
        
        self.logger = logger
        self.logger.info("Инициализация главного окна")
        
        # Путь к файлу конфигурации
        self.config_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
            "window_config.json"
        )
        
        # Установка базовых свойств окна
        self.setWindowTitle(self.tr("Window Commander - Взаимодействие с окнами"))
        self.setMinimumSize(700, 500)
        
        # Создание объекта для работы с окнами
        self.window_manager = WindowManager(logger)
        
        # Настройка интерфейса
        self.logger.info("Настройка интерфейса")
        self.setup_ui()
        
        # Загрузка сохраненной конфигурации
        self.logger.info("Загрузка конфигурации")
        self.load_config()
        
        self.logger.info("Инициализация главного окна завершена")
        
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной макет
        main_layout = QVBoxLayout(central_widget)
        
        # Создание вкладок
        self.tab_widget = QTabWidget()
        
        # Настройка вкладок
        self.window_tab = WindowTab(self.logger, self.window_manager)
        self.interaction_tab = InteractionTab(self.logger, self.window_manager)
        self.settings_tab = SettingsTab(self.logger)
        
        # Добавление вкладок
        self.tab_widget.addTab(self.window_tab, self.tr("Выбор окна"))
        self.tab_widget.addTab(self.interaction_tab, self.tr("Отправка команд"))
        self.tab_widget.addTab(self.settings_tab, self.tr("Настройки"))
        
        # Добавление вкладок в основной макет
        main_layout.addWidget(self.tab_widget)
        
        # Создание строки состояния
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(self.tr("Готов к работе"))
        
        # Соединение сигналов
        self.window_tab.window_selected.connect(self.on_window_selected)
        self.settings_tab.settings_changed.connect(self.on_settings_changed)
        
        self.retranslate_ui()
    
    def load_config(self):
        """Загрузка конфигурации из файла"""
        if not os.path.exists(self.config_file):
            self.logger.warning(f"Файл конфигурации не найден: {self.config_file}")
            self.status_bar.showMessage(self.tr("Конфигурация не найдена. Выберите окно."))
            return
            
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                
            self.logger.debug(f"Загружена конфигурация: {config}")
            
            # Проверяем существование окна и загружаем конфигурацию
            if self.window_manager.load_window_info(config):
                self.status_bar.showMessage(self.tr("Конфигурация успешно загружена"))
                self.window_tab.update_window_info()
                self.interaction_tab.update_window_info()
            else:
                self.status_bar.showMessage(self.tr("Окно из конфигурации не существует. Выберите новое окно."))
        
        except Exception as e:
            self.logger.error(f"Ошибка при загрузке конфигурации: {str(e)}")
            self.status_bar.showMessage(self.tr("Ошибка при загрузке конфигурации"))
    
    def save_config(self, config):
        """
        Сохранение конфигурации в файл
        
        Args:
            config: Словарь с конфигурацией
        """
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
                
            self.logger.info(f"Конфигурация сохранена в: {self.config_file}")
            self.status_bar.showMessage(self.tr("Конфигурация сохранена"))
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении конфигурации: {str(e)}")
            self.status_bar.showMessage(self.tr("Ошибка при сохранении конфигурации"))
            return False
    
    @Slot(dict)
    def on_window_selected(self, window_info):
        """
        Обработчик выбора окна
        
        Args:
            window_info: Информация о выбранном окне
        """
        self.logger.info(f"Выбрано окно: {window_info}")
        
        # Обновляем информацию о окне в менеджере окон
        self.window_manager.set_window_info(window_info)
        
        # Сохраняем конфигурацию
        self.save_config(window_info)
        
        # Обновляем вкладки
        self.interaction_tab.update_window_info()
        
        # Переключаемся на вкладку взаимодействия
        self.tab_widget.setCurrentIndex(1)
    
    @Slot(dict)
    def on_settings_changed(self, settings):
        """
        Обработчик изменения настроек
        
        Args:
            settings: Новые настройки
        """
        self.logger.info(f"Настройки изменены: {settings}")
        self.window_manager.apply_settings(settings)
        self.status_bar.showMessage(self.tr("Настройки сохранены"))
    
    def retranslate_ui(self):
        """Обновляет переводы интерфейса."""
        self.setWindowTitle(self.tr("Window Commander - Взаимодействие с окнами"))
        self.tab_widget.setTabText(0, self.tr("Выбор окна"))
        self.tab_widget.setTabText(1, self.tr("Отправка команд"))
        self.tab_widget.setTabText(2, self.tr("Настройки"))
        
    def closeEvent(self, event):
        """
        Обработчик закрытия окна
        
        Args:
            event: Событие закрытия
        """
        self.logger.info("Закрытие приложения")
        # Здесь можно добавить сохранение несохраненных данных и т.д.
        event.accept()
