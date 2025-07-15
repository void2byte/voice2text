"""
Модуль с диалоговым окном настроек для селектора элементов.
"""

import logging
import os
from typing import Optional, Dict, Any

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QPushButton,
    QDialogButtonBox, QMessageBox
)
from PySide6.QtCore import Qt, Signal

from screen_selector.selector_modules.settings_modules.tabs.voice_settings_tab import VoiceSettingsTab
from screen_selector.selector_modules.settings_modules.tabs.notification_settings_tab import NotificationSettingsTab
from screen_selector.selector_modules.settings_modules.tabs.file_settings_tab import FileSettingsTab
from screen_selector.selector_modules.settings_modules.tabs.selection_settings_tab import SelectionSettingsTab
from screen_selector.selector_modules.settings_modules.tabs.magnifier_settings_tab import MagnifierSettingsTab
from screen_selector.selector_modules.settings_modules.tabs.ui_settings_tab import UISettingsTab
from screen_selector.selector_modules.settings_modules.settings_manager import SettingsManager

# Настройка логгера
logger = logging.getLogger(__name__)


class SelectorSettingsDialog(QDialog):
    """Диалоговое окно настроек для селектора элементов"""
    
    settings_changed = Signal(dict)
    
    def __init__(self, settings_manager: Optional[SettingsManager] = None, active_element_selector=None, parent=None):
        """
        Инициализация диалогового окна настроек
        
        Args:
            settings_manager: Менеджер настроек
            active_element_selector: Активный диалог выбора элементов
            parent: Родительский виджет
        """
        super().__init__(parent)
        
        self.settings_manager = settings_manager or SettingsManager()
        self.active_element_selector = active_element_selector
        self.settings_tabs = []
        
        # Настраиваем окно
        self.setWindowTitle(self.tr("Настройки выбора элементов"))
        self.setMinimumSize(600, 400)
        self.setModal(True)
        
        # Создаем интерфейс
        self._init_ui()
        
        # Загружаем настройки во все вкладки
        self._load_settings()
        
        # Инициализируем переводы
        self.retranslate_ui()
        
        logger.debug("Инициализирован диалог настроек селектора элементов")
    
    def _init_ui(self):
        """Инициализация пользовательского интерфейса"""
        # Основной макет
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # Создаем виджет с вкладками
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Создаем вкладки настроек
        self._create_selection_tab()        # Вкладка настроек выделения
        self._create_magnifier_tab()        # Вкладка настроек лупы
        self._create_ui_tab()               # Вкладка настроек интерфейса
        self._create_voice_annotation_tab() # Вкладка настроек голосовой аннотации
        self._create_notifications_tab()    # Вкладка настроек уведомлений
        self._create_files_tab()            # Вкладка настроек файлов
        
        # Кнопки "ОК", "Применить" и "Отмена"
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | 
                                QDialogButtonBox.StandardButton.Apply | 
                                QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        # Кнопка "Применить" - применяет настройки без закрытия диалога
        apply_button = button_box.button(QDialogButtonBox.StandardButton.Apply)
        apply_button.clicked.connect(self.apply_settings)
        
        main_layout.addWidget(button_box)
    
    def _create_selection_tab(self):
        """Создание вкладки настроек выделения"""
        selection_tab = SelectionSettingsTab(self.settings_manager)
        self.tab_widget.addTab(selection_tab, self.tr("Выделение"))
        self.settings_tabs.append(selection_tab)
        
        # Подключаем сигнал изменения настроек
        selection_tab.settings_changed.connect(self._on_tab_settings_changed)
    
    def _create_magnifier_tab(self):
        """Создание вкладки настроек лупы"""
        magnifier_tab = MagnifierSettingsTab(self.settings_manager)
        self.tab_widget.addTab(magnifier_tab, self.tr("Лупа"))
        self.settings_tabs.append(magnifier_tab)
        
        # Подключаем сигнал изменения настроек
        magnifier_tab.settings_changed.connect(self._on_tab_settings_changed)
    
    def _create_ui_tab(self):
        """Создание вкладки настроек интерфейса"""
        ui_tab = UISettingsTab(self.settings_manager)
        self.tab_widget.addTab(ui_tab, self.tr("Интерфейс"))
        self.settings_tabs.append(ui_tab)
        
        # Подключаем сигнал изменения настроек
        ui_tab.settings_changed.connect(self._on_tab_settings_changed)
    
    def _create_voice_annotation_tab(self):
        """Создание вкладки настроек голосовой аннотации"""
        voice_tab = VoiceSettingsTab(self.settings_manager)
        self.tab_widget.addTab(voice_tab, self.tr("Голосовая аннотация"))
        self.settings_tabs.append(voice_tab)
        
        # Подключаем сигнал изменения настроек
        voice_tab.settings_changed.connect(self._on_tab_settings_changed)
    
    def _create_notifications_tab(self):
        """Создание вкладки настроек уведомлений"""
        notifications_tab = NotificationSettingsTab(self.settings_manager)
        self.tab_widget.addTab(notifications_tab, self.tr("Уведомления"))
        self.settings_tabs.append(notifications_tab)
        
        # Подключаем сигнал изменения настроек
        notifications_tab.settings_changed.connect(self._on_tab_settings_changed)
    
    def _create_files_tab(self):
        """Создание вкладки настроек файлов"""
        files_tab = FileSettingsTab(self.settings_manager)
        self.tab_widget.addTab(files_tab, self.tr("Файлы и форматы"))
        self.settings_tabs.append(files_tab)
        
        # Подключаем сигнал изменения настроек
        files_tab.settings_changed.connect(self._on_tab_settings_changed)
    
    def _load_settings(self):
        """Загрузка настроек во все вкладки"""
        # Настройки загружаются автоматически в конструкторах вкладок
        logger.debug("Загружены настройки во все вкладки")
    
    def _on_tab_settings_changed(self, settings: Dict[str, Any]):
        """
        Обработчик изменения настроек на любой вкладке
        
        Args:
            settings: Словарь с настройками
        """
        # Если есть менеджер настроек, сохраняем изменения немедленно
        if self.settings_manager:
            self.settings_manager.update_settings(settings)
            logger.debug(f"Обновлены настройки: {settings.keys()}")
        
        # Если есть активный диалог выбора элементов, применяем к нему настройки
        if self.active_element_selector:
            self._apply_settings_to_active_dialog(settings)
    
    def _apply_settings_to_active_dialog(self, settings: Dict[str, Any]):
        """
        Применяет настройки к активному диалогу выбора элементов
        
        Args:
            settings: Словарь с настройками
        """
        try:
            # Применяем настройки лупы
            if "magnifier" in settings and hasattr(self.active_element_selector, 'magnifier'):
                magnifier_settings = settings["magnifier"]
                # Включение/выключение лупы
                if "enabled" in magnifier_settings:
                    if magnifier_settings["enabled"]:
                        self.active_element_selector.magnifier.show()
                    else:
                        self.active_element_selector.magnifier.hide()
                
                # Размер лупы
                if "size" in magnifier_settings:
                    self.active_element_selector.magnifier.set_size(magnifier_settings["size"])
                
                # Коэффициент увеличения
                if "zoom_factor" in magnifier_settings:
                    self.active_element_selector.magnifier.set_zoom_factor(magnifier_settings["zoom_factor"])
                
                # Сетка в лупе
                if "grid_enabled" in magnifier_settings:
                    self.active_element_selector.magnifier.set_grid_enabled(magnifier_settings["grid_enabled"])
            
            # В дальнейшем можно добавить применение других настроек
            # Например, настройки выделения, интерфейса и т.д.
            
            logger.debug("Настройки применены к активному диалогу выбора элементов в реальном времени")
        except Exception as e:
            logger.error(f"Ошибка при применении настроек к активному диалогу: {e}")
    
    def apply_settings(self):
        """Обработчик нажатия кнопки "Применить" - применяет настройки без закрытия диалога"""
        # Собираем все настройки со всех вкладок
        all_settings = {}
        for tab in self.settings_tabs:
            tab_settings = tab.get_settings()
            all_settings.update(tab_settings)
        
        # Сохраняем все настройки в файл
        if self.settings_manager:
            # Метод update_settings уже включает в себя сохранение настроек
            self.settings_manager.update_settings(all_settings)
            logger.info("Настройки применены")
        
        # Отправляем сигнал об изменении настроек
        self.settings_changed.emit(all_settings)
    
    def accept(self):
        """Обработчик нажатия кнопки "OK" """
        # Применяем настройки и закрываем диалог
        self.apply_settings()
        
        # Закрываем диалог
        super().accept()
    
    def reject(self):
        """Обработчик нажатия кнопки "Отмена" """
        # Если настройки были изменены, предлагаем сохранить их
        if self.settings_manager and self.settings_manager.is_dirty():
            reply = QMessageBox.question(
                self,
                self.tr("Сохранение настроек"),
                self.tr("Настройки были изменены. Сохранить изменения?"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Сохраняем настройки и закрываем диалог
                self.settings_manager.save_settings()
                logger.info("Настройки сохранены при отмене")
                super().reject()
            elif reply == QMessageBox.StandardButton.No:
                # Отменяем изменения и закрываем диалог
                self.settings_manager.load_settings()  # Перезагружаем настройки из файла
                logger.info("Изменения настроек отменены")
                super().reject()
            else:  # Cancel
                # Ничего не делаем, остаемся в диалоге
                return
        else:
            # Просто закрываем диалог
            super().reject()
    
    def get_settings(self) -> Dict[str, Any]:
        """
        Получение всех настроек диалога
        
        Returns:
            Dict[str, Any]: Словарь с настройками
        """
        all_settings = {}
        for tab in self.settings_tabs:
            tab_settings = tab.get_settings()
            all_settings.update(tab_settings)
        return all_settings
    
    def retranslate_ui(self):
        """Обновляет переводы интерфейса"""
        self.setWindowTitle(self.tr("Настройки выбора элементов"))
        
        # Обновляем названия вкладок
        if hasattr(self, 'tab_widget') and self.tab_widget.count() > 0:
            tab_titles = [
                self.tr("Выделение"),
                self.tr("Лупа"),
                self.tr("Интерфейс"),
                self.tr("Голосовая аннотация"),
                self.tr("Уведомления"),
                self.tr("Файлы и форматы")
            ]
            
            for i, title in enumerate(tab_titles):
                if i < self.tab_widget.count():
                    self.tab_widget.setTabText(i, title)
        
        # Обновляем переводы во всех вкладках
        for tab in self.settings_tabs:
            if hasattr(tab, 'retranslate_ui'):
                tab.retranslate_ui()
