"""
Вкладка настроек для Vosk.
"""
import logging
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLineEdit, QGroupBox, 
                               QFormLayout, QComboBox, QPushButton, QFileDialog, QMessageBox, QProgressBar)
from PySide6.QtCore import Signal, QStandardPaths, QThread, Slot
import requests
import zipfile
import shutil
import json # Для парсинга списка моделей, если он будет в JSON

# Импортируем новые модули
from voice_control.utils.vosk_model_loader import VoskModelTester, ModelLoadingDialog
from .vosk_model_downloader import VoskModelDownloader, VoskModelRegistry

# from voice_control.recognizers.base_recognizer import BaseRecognizer # Если нужно

logger = logging.getLogger(__name__)

class VoskSettingsTab(QWidget):
    # settings_changed = Signal(dict) # Пример

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._populate_vosk_options()
        self._load_available_vosk_models() # Загружаем список моделей при инициализации

    def retranslate_ui(self):
        self.vosk_settings_group.setTitle(self.tr("Настройки Vosk"))
        self.vosk_model_path_edit.setPlaceholderText(self.tr("Укажите путь к модели Vosk"))
        self.vosk_browse_model_button.setText(self.tr("Обзор..."))

        # Обновляем тексты элементов QFormLayout
        form_layout = self.vosk_settings_group.layout()
        if form_layout and isinstance(form_layout, QFormLayout):
            form_layout.labelForField(self.vosk_model_path_edit.parent()).setText(self.tr("Путь к модели:"))
            form_layout.labelForField(self.vosk_model_selection_combo).setText(self.tr("Выберите модель для скачивания:"))
            form_layout.labelForField(self.vosk_download_progress_bar).setText(self.tr("Прогресс скачивания:"))
            form_layout.labelForField(self.vosk_language_combo).setText(self.tr("Язык (если модель указана вручную):"))
            form_layout.labelForField(self.vosk_sample_rate_combo).setText(self.tr("Частота дискретизации (Гц):"))

        self.vosk_model_selection_combo.setToolTip(self.tr("Выберите модель из списка доступных для скачивания."))
        self.vosk_download_model_button.setText(self.tr("Скачать выбранную модель"))
        self.vosk_language_combo.setToolTip(self.tr("Язык обычно определяется выбранной моделью. "
                                           "Это поле может быть информационным или для выбора специфичных вариантов, если модель мультиязычная."))
        self.vosk_sample_rate_combo.setToolTip(self.tr("Убедитесь, что выбранная частота дискретизации соответствует модели Vosk."))
        self.vosk_test_model_button.setText(self.tr("Тестировать загрузку модели"))
        self.vosk_test_model_button.setToolTip(self.tr("Проверить, может ли модель быть загружена в память. Полезно для больших моделей."))

        # Обновляем тексты в ComboBox
        current_lang_data = self.vosk_language_combo.currentData()
        self.vosk_language_combo.setItemText(self.vosk_language_combo.findData("auto"), self.tr("Определяется моделью"))
        self.vosk_language_combo.setItemText(self.vosk_language_combo.findData("ru"), self.tr("Русский (если модель русская)"))
        self.vosk_language_combo.setItemText(self.vosk_language_combo.findData("en"), self.tr("Английский (если модель английская)"))
        self.vosk_language_combo.setCurrentIndex(self.vosk_language_combo.findData(current_lang_data))

    def _init_ui(self):
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        self.vosk_settings_group = QGroupBox()
        vosk_form_layout = QFormLayout(self.vosk_settings_group)

        self.vosk_model_path_edit = QLineEdit()
        self.vosk_browse_model_button = QPushButton()
        self.vosk_browse_model_button.clicked.connect(self._browse_vosk_model)
        model_path_layout = QVBoxLayout() # Используем QVBoxLayout для строки с полем и кнопкой
        model_path_layout.addWidget(self.vosk_model_path_edit)
        model_path_layout.addWidget(self.vosk_browse_model_button)
        vosk_form_layout.addRow(self.tr("Путь к модели:"), model_path_layout)

        self.vosk_model_selection_combo = QComboBox()
        vosk_form_layout.addRow(self.tr("Выберите модель для скачивания:"), self.vosk_model_selection_combo)
        self.vosk_model_selection_combo.currentIndexChanged.connect(self._update_model_path_from_selection)

        self.vosk_download_model_button = QPushButton()
        self.vosk_download_model_button.clicked.connect(self._download_selected_vosk_model)
        vosk_form_layout.addRow(self.vosk_download_model_button)

        self.vosk_download_progress_bar = QProgressBar()
        self.vosk_download_progress_bar.setVisible(False) # Скрыть по умолчанию
        vosk_form_layout.addRow(self.tr("Прогресс скачивания:"), self.vosk_download_progress_bar)

        self.vosk_language_combo = QComboBox() # Оставляем для совместимости или если пользователь вручную укажет путь
        vosk_form_layout.addRow(self.tr("Язык (если модель указана вручную):"), self.vosk_language_combo)

        self.vosk_sample_rate_combo = QComboBox()
        vosk_form_layout.addRow(self.tr("Частота дискретизации (Гц):"), self.vosk_sample_rate_combo)

        # Кнопка тестирования загрузки модели
        self.vosk_test_model_button = QPushButton()
        self.vosk_test_model_button.clicked.connect(self._test_model_loading)
        vosk_form_layout.addRow(self.vosk_test_model_button)

        layout.addWidget(self.vosk_settings_group)
        layout.addStretch()

    def retranslate_ui(self):
        """Обновляет переводы интерфейса."""

    def _populate_vosk_options(self):
        logger.debug("Заполнение опций для Vosk...")
        # Языки (это больше информационно, т.к. язык определяется моделью)
        # Можно оставить пустым или добавить популярные, но с оговоркой
        self.vosk_language_combo.addItem("", "auto")
        self.vosk_language_combo.addItem("", "ru")
        self.vosk_language_combo.addItem("", "en")
        # TODO: Возможно, стоит убрать или сделать нередактируемым, если язык жестко привязан к модели
        # Этот комбобокс теперь больше для информации, если модель указана вручную

        # Частоты дискретизации (типичные для Vosk моделей)
        self.vosk_sample_rate_combo.addItem("16000", "16000")
        self.vosk_sample_rate_combo.addItem("8000", "8000")
        self.vosk_sample_rate_combo.addItem("48000", "48000") # Некоторые модели могут поддерживать
        # TODO: Заполнить актуальными частотами, которые обычно используются с Vosk

    def _browse_vosk_model(self):
        # Определяем начальную директорию для диалога
        initial_dir = QStandardPaths.writableLocation(QStandardPaths.HomeLocation)
        current_path = self.vosk_model_path_edit.text()
        if current_path and os.path.exists(current_path):
            if os.path.isdir(current_path):
                initial_dir = current_path
            else:
                initial_dir = os.path.dirname(current_path)
        
        # Vosk модели обычно это директории
        dir_path = QFileDialog.getExistingDirectory(
            self,
            self.tr("Выберите папку с моделью Vosk"),
            initial_dir
        )
        if dir_path:
            self.vosk_model_path_edit.setText(dir_path)
            logger.info(f"Выбрана папка с моделью Vosk: {dir_path}")
            # Можно попытаться автоматически определить язык и частоту по файлам модели,
            # но это может быть сложно и зависит от структуры модели.
            # Например, проверить наличие файла 'mfcc.conf' и его содержимое.

    def get_settings(self) -> dict:
        model_path = self.vosk_model_path_edit.text().strip()
        if not model_path:
            logger.warning("Путь к модели Vosk не указан.")
            # QMessageBox.warning(self, "Ошибка Vosk", "Укажите путь к модели Vosk.")
            # return {} # или raise ValueError("Путь к модели Vosk не указан.")

        config = {
            "model_path": model_path,
            "language": self.vosk_language_combo.currentData(), # Может быть 'auto' или конкретный язык
            "sample_rate": int(self.vosk_sample_rate_combo.currentData()),
        }
        return config

    def set_settings(self, config: dict):
        self.vosk_model_path_edit.setText(config.get("model_path", ""))
        
        lang = config.get("language", "auto")
        index = self.vosk_language_combo.findData(lang)
        if index != -1: self.vosk_language_combo.setCurrentIndex(index)

        sample_rate = str(config.get("sample_rate", "16000"))
        index = self.vosk_sample_rate_combo.findData(sample_rate)
        if index != -1: self.vosk_sample_rate_combo.setCurrentIndex(index)

        logger.debug(f"Настройки Vosk загружены: {config}")

    def is_valid(self) -> bool:
        model_path = self.vosk_model_path_edit.text().strip()
        if not model_path:
            QMessageBox.warning(self, self.tr("Ошибка Vosk"), self.tr("Укажите путь к модели Vosk."))
            return False
        if not os.path.exists(model_path) or not os.path.isdir(model_path):
            QMessageBox.warning(self, self.tr("Ошибка Vosk"), self.tr("Указанный путь к модели Vosk не существует или не является папкой: {}").format(model_path))
            return False
        
        # Проверка наличия ключевых файлов модели (пример)
        # conf_path = os.path.join(model_path, "conf", "model.conf") # или mfcc.conf
        # am_path = os.path.join(model_path, "am", "final.mdl")
        # if not os.path.exists(conf_path) or not os.path.exists(am_path):
        #     QMessageBox.warning(self, "Ошибка Vosk", f"Папка {model_path} не содержит ожидаемых файлов модели Vosk.")
        #     return False
            
        logger.info(f"Проверка пути к модели Vosk: {model_path} - OK")
        return True

    def save_specific_settings(self, settings):
        """Сохраняет специфичные для Vosk настройки в QSettings."""
        settings.setValue("vosk/model_path", self.vosk_model_path_edit.text().strip())
        settings.setValue("vosk/language_index", self.vosk_language_combo.currentIndex())
        settings.setValue("vosk/sample_rate_index", self.vosk_sample_rate_combo.currentIndex())
        logger.info("Специфичные настройки Vosk сохранены.")

    def load_specific_settings(self, settings):
        """Загружает специфичные для Vosk настройки из QSettings."""
        model_path = settings.value("vosk/model_path", "")
        self.vosk_model_path_edit.setText(model_path)
        
        lang_idx = settings.value("vosk/language_index", 0, type=int)
        if lang_idx < self.vosk_language_combo.count(): self.vosk_language_combo.setCurrentIndex(lang_idx)
        
        rate_idx = settings.value("vosk/sample_rate_index", 0, type=int)
        if rate_idx < self.vosk_sample_rate_combo.count(): self.vosk_sample_rate_combo.setCurrentIndex(rate_idx)
        logger.info("Специфичные настройки Vosk загружены.")

    MODELS_URL = "https://alphacephei.com/vosk/models/model-list.json" # Предполагаемый URL списка моделей
    # Реальные ссылки на модели могут отличаться, это для примера
    # Пример структуры model-list.json:
    # [
    #   {"name": "vosk-model-small-ru-0.22", "url": "https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip", "lang": "ru", "size_mb": 45},
    #   {"name": "vosk-model-small-en-us-0.15", "url": "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip", "lang": "en-us", "size_mb": 40}
    # ]
    # На сайте https://alphacephei.com/vosk/models нет прямого JSON, придется парсить HTML или найти другой источник
    # Пока что используем заглушку, если не удастся получить реальный список
# Список доступных моделей перенесен в VoskModelRegistry

    def _load_available_vosk_models(self):
        """Загружает список доступных моделей из реестра."""
        try:
            self.available_models = VoskModelRegistry.get_available_models()
            logger.info(f"Загружен список из {len(self.available_models)} моделей Vosk.")
        except Exception as e:
            logger.error(f"Ошибка при загрузке списка моделей Vosk: {e}")
            self.available_models = VoskModelRegistry.AVAILABLE_MODELS_FALLBACK
            QMessageBox.warning(self, "Ошибка загрузки моделей", 
                                f"Произошла ошибка при загрузке списка моделей. Будет использован встроенный список.\n{e}")

        self.vosk_model_selection_combo.clear()
        self.vosk_model_selection_combo.addItem("Выберите модель...", None)
        for model_info in self.available_models:
            self.vosk_model_selection_combo.addItem(model_info["name"], model_info)

    def _update_model_path_from_selection(self, index):
        model_data = self.vosk_model_selection_combo.itemData(index)
        if model_data:
            # Используем метод из реестра для получения пути
            models_dir = VoskModelRegistry.get_project_models_dir()
            target_model_path = os.path.join(models_dir, model_data["model_dir_name"])
            self.vosk_model_path_edit.setText(target_model_path)
            # Также можно обновить язык и частоту, если они есть в model_data
            lang_index = self.vosk_language_combo.findData(model_data.get("lang", "auto"))
            if lang_index != -1: self.vosk_language_combo.setCurrentIndex(lang_index)
            # Частота дискретизации обычно 16000 для большинства моделей, можно добавить в model_data если нужно

    def _download_selected_vosk_model(self):
        current_index = self.vosk_model_selection_combo.currentIndex()
        if current_index <= 0: # Пропускаем "Выберите модель..."
            QMessageBox.information(self, self.tr("Скачивание модели"), self.tr("Пожалуйста, выберите модель для скачивания."))
            return

        model_data = self.vosk_model_selection_combo.itemData(current_index)
        model_url = model_data["url"]
        model_name = model_data["name"]
        model_dir_name = model_data["model_dir_name"]

        # Используем метод из реестра для получения директории моделей
        download_dir = VoskModelRegistry.get_project_models_dir()
        os.makedirs(download_dir, exist_ok=True)

        target_model_path = os.path.join(download_dir, model_dir_name)

        if os.path.exists(target_model_path):
            reply = QMessageBox.question(self, self.tr("Модель существует"), 
                                         self.tr("Папка с моделью '{}' уже существует. Перекачать?").format(model_dir_name),
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                self.vosk_model_path_edit.setText(target_model_path) # Установить путь к существующей
                return
            else:
                try:
                    shutil.rmtree(target_model_path)
                    logger.info(f"Удалена существующая папка модели: {target_model_path}")
                except Exception as e:
                    QMessageBox.critical(self, self.tr("Ошибка удаления"), self.tr("Не удалось удалить существующую папку модели: {}").format(e))
                    return

        self.vosk_download_model_button.setEnabled(False)
        self.vosk_download_progress_bar.setVisible(True)
        self.vosk_download_progress_bar.setValue(0)

        self.download_thread = VoskModelDownloader(model_url, download_dir, model_name, model_dir_name)
        self.download_thread.progress.connect(self.vosk_download_progress_bar.setValue)
        self.download_thread.finished_signal.connect(self._on_download_finished)
        self.download_thread.error_signal.connect(self._on_download_error)
        self.download_thread.start()

    def _on_download_finished(self, final_model_path):
        self.vosk_download_model_button.setEnabled(True)
        self.vosk_download_progress_bar.setVisible(False)
        QMessageBox.information(self, self.tr("Скачивание завершено"), self.tr("Модель '{}' успешно скачана и распакована в:\n{}").format(os.path.basename(final_model_path), final_model_path))
        self.vosk_model_path_edit.setText(final_model_path)
        # Обновляем язык, если он есть в данных модели
        current_index = self.vosk_model_selection_combo.currentIndex()
        if current_index > 0:
            model_data = self.vosk_model_selection_combo.itemData(current_index)
            lang_code = model_data.get("lang", "auto")
            lang_idx = self.vosk_language_combo.findData(lang_code)
            if lang_idx != -1: self.vosk_language_combo.setCurrentIndex(lang_idx)

    def _on_download_error(self, error_message):
        self.vosk_download_model_button.setEnabled(True)
        self.vosk_download_progress_bar.setVisible(False)
        QMessageBox.critical(self, self.tr("Ошибка скачивания"), self.tr("Не удалось скачать модель:\n{}").format(error_message))
    
    def _test_model_loading(self):
        """Тестирует загрузку модели с отображением диалога прогресса."""
        model_path = self.vosk_model_path_edit.text().strip()
        if not model_path:
            QMessageBox.warning(self, self.tr("Ошибка"), self.tr("Укажите путь к модели для тестирования."))
            return
        
        # Проверяем валидность пути перед тестированием
        is_valid, error_msg = VoskModelTester.validate_model_path(model_path)
        if not is_valid:
            QMessageBox.warning(self, self.tr("Ошибка модели"), error_msg)
            return
        
        # Запускаем тестирование с диалогом прогресса
        success, model, recognizer = VoskModelTester.test_model_loading(model_path, self)
        
        if success:
            QMessageBox.information(self, self.tr("Тест успешен"), 
                                   self.tr("Модель '{}' успешно загружена в память!\n\nМодель готова к использованию для распознавания речи.").format(os.path.basename(model_path)))
        else:
            QMessageBox.warning(self, self.tr("Тест не пройден"), 
                               self.tr("Загрузка модели была отменена или произошла ошибка."))


# Класс ModelDownloadThread перенесен в vosk_model_downloader.py




if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication
    import sys

    logging.basicConfig(level=logging.DEBUG)

    app = QApplication(sys.argv)
    window = VoskSettingsTab()
    window.setWindowTitle("Тест вкладки настроек Vosk")
    window.show()
    sys.exit(app.exec())