#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Менеджер переводов для приложения Screph.
Обеспечивает централизованное управление переводами для всех GUI компонентов.
"""

import os
import logging
from typing import List, Optional
from PySide6.QtCore import QObject, QTranslator, QLocale, QCoreApplication, Signal, QEvent
from PySide6.QtWidgets import QApplication, QComboBox, QMenu
from PySide6.QtGui import QAction, QActionGroup
from settings_modules.settings_manager import SettingsManager

logger = logging.getLogger(__name__)


class TranslationManager(QObject):
    """Менеджер переводов для приложения"""
    
    language_changed = Signal(str)  # Сигнал, который будет испускаться при смене языка

    def __init__(self, settings_manager: SettingsManager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.translators: List[QTranslator] = []
        self.registered_widgets = []

        # Загружаем язык из настроек
        self.default_language = self.settings_manager.get_setting('language')
        self.current_language = None  # Изначально язык не установлен

        self.translations_dir = self._get_translations_dir()
        logger.info(f"Translation manager initialized with translations dir: {self.translations_dir}")
        logger.info(f"Default language set to: {self.default_language}")
    
    def _get_translations_dir(self) -> str:
        """Получает путь к директории с переводами"""
        # Получаем путь относительно корня проекта
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(current_dir, "i18n")
    

    
    def get_available_languages(self) -> List[tuple]:
        """Получает список доступных языков, сканируя директорию с переводами.

        Returns:
            Список кортежей (название_языка, код_языка).
        """
        available_languages = [("English (US)", "en_US")]  # Английский всегда доступен
        lang_codes = set()

        if os.path.exists(self.translations_dir):
            for file in os.listdir(self.translations_dir):
                if file.endswith('.qm'):
                    # Извлекаем код языка из имени файла
                    lang_code = file.split('_')[0]
                    if file.startswith('qt_'):
                        lang_code = file.split('_')[1].split('.')[0]
                    else:
                        lang_code = file.split('.')[0]

                    # Убираем суффиксы, если они есть
                    if lang_code.endswith('_auto'):
                        lang_code = lang_code[:-5]

                    if lang_code != 'en_US' and lang_code:
                        lang_codes.add(lang_code)

        language_names = {
            'ru_RU': 'Русский (Россия)',
            'de_DE': 'Deutsch (Deutschland)',
            'fr_FR': 'Français (France)',
            'es_ES': 'Español (España)',
            'it_IT': 'Italiano (Italia)',
            'pt_BR': 'Português (Brasil)',
            'zh_CN': '中文 (简体)',
            'ja_JP': '日本語 (日本)',
            'ko_KR': '한국어 (대한민국)'
        }

        for lang_code in sorted(list(lang_codes)):
            name = language_names.get(lang_code, f"Language ({lang_code})")
            available_languages.append((name, lang_code))

        return available_languages
    
    def change_language(self, language_code: str) -> bool:
        """Изменяет язык интерфейса
        
        Args:
            language_code: Код языка (например, 'ru_RU')
            
        Returns:
            True если язык успешно изменен, False иначе
        """
        if language_code == self.current_language:
            logger.debug(f"Language {language_code} is already active")
            return True

        try:
            app = QApplication.instance()
            if not app:
                logger.error("No QApplication instance found")
                return False

            new_translators = self._create_translators(language_code)
            if not new_translators and language_code != 'en_US':
                logger.warning(f"No translations found for {language_code}, falling back to en_US")
                # Попытка переключиться на английский, если для выбранного языка нет перевода
                new_translators = self._create_translators('en_US')
                language_code = 'en_US'

            for translator in self.translators:
                app.removeTranslator(translator)

            for translator in new_translators:
                app.installTranslator(translator)

            self.translators = new_translators
            self.current_language = language_code
            self.settings_manager.set_setting('language', language_code)
            logger.info(f"Language setting updated to: {language_code}")

            self.language_changed.emit(language_code)
            self.update_registered_widgets()

            logger.info(f"Language changed to: {language_code}")
            return True

        except Exception as e:
            logger.error(f"Error changing language to {language_code}: {e}")
            return False
    
    def _create_translators(self, language_code: str) -> List[QTranslator]:
        """Создает переводчики для указанного языка
        
        Args:
            language_code: Код языка
            
        Returns:
            Список созданных переводчиков
        """
        translators = []
        
        # Приоритет: сначала пробуем автоматически сгенерированные файлы
        auto_file = os.path.join(self.translations_dir, f"{language_code}_auto.qm")
        main_file = os.path.join(self.translations_dir, f"{language_code}.qm")
        
        # Загружаем автоматически сгенерированный файл, если он существует
        if os.path.exists(auto_file):
            translator = QTranslator()
            if translator.load(auto_file):
                translators.append(translator)
                logger.debug(f"Auto translation loaded: {auto_file}")
            else:
                logger.warning(f"Failed to load auto translation: {auto_file}")
        # Иначе загружаем основной файл
        elif os.path.exists(main_file):
            translator = QTranslator()
            if translator.load(main_file):
                translators.append(translator)
                logger.debug(f"Main translation loaded: {main_file}")
            else:
                logger.warning(f"Failed to load main translation: {main_file}")
        
        # Переводы Qt (если доступны)
        qt_file = os.path.join(self.translations_dir, f"qt_{language_code}.qm")
        if os.path.exists(qt_file):
            translator = QTranslator()
            if translator.load(qt_file):
                translators.append(translator)
                logger.debug(f"Qt translation loaded: {qt_file}")
        
        return translators

    def _remove_translators(self):
        """Удаляет все активные переводчики"""
        app = QApplication.instance()
        if app:
            for translator in self.translators:
                app.removeTranslator(translator)
        
        self.translators.clear()
        logger.debug("All translators removed")

    
    def create_language_selection_widget(self, parent=None, widget_type='combobox', title=None):
        """Создает и настраивает виджет для выбора языка."""
        if widget_type == 'combobox':
            combo = QComboBox(parent)
            combo.setToolTip(QCoreApplication.translate("TranslationManager", "Select interface language"))
            self._populate_language_widget(combo)
            combo.currentTextChanged.connect(lambda text: self.change_language(combo.itemData(combo.currentIndex())))
            return combo
        elif widget_type == 'menu':
            if title is None:
                title = QCoreApplication.translate("TranslationManager", "Language")
            menu = QMenu(parent)
            menu.setTitle(title)
            action_group = QActionGroup(parent)
            action_group.setExclusive(True)
            self._populate_language_widget(menu, action_group)
            action_group.triggered.connect(lambda action: self.change_language(action.data()))
            return menu
        return None

    def _populate_language_widget(self, widget, action_group=None):
        """Заполняет виджет доступными языками."""
        available_languages = self.get_available_languages()
        current_language = self.get_current_language()

        if isinstance(widget, QComboBox):
            widget.clear()
            for lang_name, lang_code in available_languages:
                widget.addItem(lang_name, lang_code)
            current_index = widget.findData(current_language)
            if current_index >= 0:
                widget.setCurrentIndex(current_index)
        elif isinstance(widget, QMenu) and action_group:
            widget.clear()
            for lang_name, lang_code in available_languages:
                action = QAction(lang_name, widget)
                action.setData(lang_code)
                action.setCheckable(True)
                if lang_code == current_language:
                    action.setChecked(True)
                widget.addAction(action)
                action_group.addAction(action)


    def get_current_language(self) -> str:
        """Возвращает текущий язык"""
        return self.current_language
    
    def get_default_language(self) -> str:
        """Возвращает язык по умолчанию"""
        return self.default_language
    
    def register_widget(self, widget):
        """Регистрирует виджет для динамического обновления переводов."""
        if widget not in self.registered_widgets:
            self.registered_widgets.append(widget)
            # Привязываем обработчик события уничтожения виджета
            widget.destroyed.connect(lambda: self.unregister_widget(widget))
            logger.debug(f"Widget {widget.__class__.__name__} registered for translation updates.")

    def unregister_widget(self, widget):
        """Отменяет регистрацию виджета."""
        if widget in self.registered_widgets:
            self.registered_widgets.remove(widget)
            logger.debug(f"Widget {widget.__class__.__name__} unregistered.")

    def update_registered_widgets(self):
        """Обновляет переводы для всех зарегистрированных виджетов."""
        for widget in self.registered_widgets:
            try:
                if hasattr(widget, 'retranslate_ui'):
                    try:
                        widget.retranslate_ui()
                        logger.debug(f"Retranslating widget: {widget.__class__.__name__}")
                    except Exception as e:
                        logger.error(f"Error retranslating widget {widget.__class__.__name__}: {e}")
            except Exception as e:
                logger.error(f"Error retranslating widget {widget.__class__.__name__}: {e}")

    def cleanup(self):
        """Очистка ресурсов"""
        self._remove_translators()
        self.registered_widgets.clear()
        logger.info("Translation manager cleaned up")


# Глобальный экземпляр менеджера переводов
_translation_manager: Optional[TranslationManager] = None


def get_translation_manager(settings_manager: Optional[SettingsManager] = None) -> TranslationManager:
    """Получает глобальный экземпляр менеджера переводов"""
    global _translation_manager
    if _translation_manager is None:
        if settings_manager is None:
            raise ValueError("SettingsManager must be provided for the first call to get_translation_manager")
        _translation_manager = TranslationManager(settings_manager)
    return _translation_manager


def cleanup_translation_manager():
    """Очищает глобальный экземпляр менеджера переводов"""
    global _translation_manager
    if _translation_manager is not None:
        _translation_manager.cleanup()
        _translation_manager = None