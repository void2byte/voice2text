"""
Вкладка настроек для Yandex SpeechKit.
"""
import logging
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLineEdit, QGroupBox, 
                               QFormLayout, QComboBox, QPushButton, QMessageBox, QLabel, QHBoxLayout)
from PySide6.QtCore import Signal, QSettings, QThread, QObject
from PySide6.QtGui import QMovie, QPixmap

# from ..base_recognizer import BaseRecognizer # Если нужно
from voice_control.recognizers.yandex_recognizer import YandexSpeechRecognizer

logger = logging.getLogger(__name__)

class YandexSettingsTab(QWidget):
    # settings_changed = Signal(dict) # Пример
    # yandex_api_key_valid = Signal(bool) # Пример, если нужна валидация ключа извне

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._populate_yandex_options()
        self.load_specific_settings(QSettings("Screph", "SpeechRecognition"))

    def retranslate_ui(self):
        self.yandex_settings_group.setTitle(self.tr("Настройки Yandex SpeechKit"))
        self.yandex_api_key_edit.setPlaceholderText(self.tr("Введите API-ключ Yandex"))
        # Получаем текущие данные, чтобы восстановить их после перевода
        current_lang_data = self.yandex_language_combo.currentData()
        current_model_data = self.yandex_model_combo.currentData()
        current_sample_rate_data = self.yandex_sample_rate_combo.currentData()

        # Обновляем тексты элементов QFormLayout
        form_layout = self.yandex_settings_group.layout()
        if form_layout and isinstance(form_layout, QFormLayout):
            api_key_label = form_layout.labelForField(self.yandex_api_key_edit)
            if api_key_label:
                api_key_label.setText(self.tr("API-ключ:"))
            
            language_label = form_layout.labelForField(self.yandex_language_combo)
            if language_label:
                language_label.setText(self.tr("Язык:"))
            
            model_label = form_layout.labelForField(self.yandex_model_combo)
            if model_label:
                model_label.setText(self.tr("Модель:"))
            
            audio_format_label = form_layout.labelForField(self.yandex_audio_format_combo)
            if audio_format_label:
                audio_format_label.setText(self.tr("Формат аудио:"))
            
            sample_rate_label = form_layout.labelForField(self.yandex_sample_rate_combo)
            if sample_rate_label:
                sample_rate_label.setText(self.tr("Частота дискретизации (Гц):"))

        # Обновляем тексты в ComboBox
        self.yandex_language_combo.setItemText(self.yandex_language_combo.findData("ru-RU"), self.tr("Русский"))
        self.yandex_language_combo.setItemText(self.yandex_language_combo.findData("en-US"), self.tr("Английский"))
        self.yandex_language_combo.setItemText(self.yandex_language_combo.findData("tr-TR"), self.tr("Турецкий"))

        self.yandex_model_combo.setItemText(self.yandex_model_combo.findData("general"), self.tr("По умолчанию (general)"))
        self.yandex_model_combo.setItemText(self.yandex_model_combo.findData("general:rc"), self.tr("Распознавание коротких фраз (general:rc)"))

        self.yandex_sample_rate_combo.setItemText(self.yandex_sample_rate_combo.findData("0"), self.tr("Авто (рекомендуется для OggOpus)"))

        self.check_yandex_key_button.setText(self.tr("Проверить ключ"))
        self.key_status_label.setText(self.tr("Не проверен"))

        # Восстанавливаем выбор
        self.yandex_language_combo.setCurrentIndex(self.yandex_language_combo.findData(current_lang_data))
        self.yandex_model_combo.setCurrentIndex(self.yandex_model_combo.findData(current_model_data))
        self.yandex_sample_rate_combo.setCurrentIndex(self.yandex_sample_rate_combo.findData(current_sample_rate_data))

    def _init_ui(self):
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        self.yandex_settings_group = QGroupBox()
        yandex_form_layout = QFormLayout(self.yandex_settings_group)

        self.yandex_api_key_edit = QLineEdit()
        yandex_form_layout.addRow("", self.yandex_api_key_edit)  # Текст будет установлен в retranslate_ui

        self.yandex_language_combo = QComboBox()
        yandex_form_layout.addRow("", self.yandex_language_combo)  # Текст будет установлен в retranslate_ui

        self.yandex_model_combo = QComboBox()
        yandex_form_layout.addRow("", self.yandex_model_combo)  # Текст будет установлен в retranslate_ui

        self.yandex_audio_format_combo = QComboBox()
        yandex_form_layout.addRow("", self.yandex_audio_format_combo)  # Текст будет установлен в retranslate_ui

        self.yandex_sample_rate_combo = QComboBox()
        yandex_form_layout.addRow("", self.yandex_sample_rate_combo)  # Текст будет установлен в retranslate_ui
        
        api_key_layout = QHBoxLayout()
        api_key_layout.addWidget(self.yandex_api_key_edit)
        self.check_yandex_key_button = QPushButton()
        api_key_layout.addWidget(self.check_yandex_key_button)
        yandex_form_layout.addRow(self.tr("API-ключ:"), api_key_layout)

        self.key_status_label = QLabel()
        yandex_form_layout.addRow(self.tr("Статус ключа:"), self.key_status_label)

        self.check_yandex_key_button.clicked.connect(self.check_yandex_api_key)

        layout.addWidget(self.yandex_settings_group)
        layout.addStretch()

        self.retranslate_ui()

    def _populate_yandex_options(self):
        logger.debug("Заполнение опций для Yandex...")
        # Языки (пример, реальные значения могут отличаться)
        self.yandex_language_combo.addItem("", "ru-RU")
        self.yandex_language_combo.addItem("", "en-US")
        self.yandex_language_combo.addItem("", "tr-TR")
        # TODO: Добавить больше языков, если поддерживаются Yandex

        # Модели (пример)
        self.yandex_model_combo.addItem("", "general")
        self.yandex_model_combo.addItem("", "general:rc") # Пример
        # TODO: Заполнить актуальными моделями Yandex

        # Форматы аудио
        self.yandex_audio_format_combo.addItem("LPCM", "lpcm")
        self.yandex_audio_format_combo.addItem("OggOpus", "oggopus")
        # TODO: Заполнить актуальными форматами

        # Частоты дискретизации
        self.yandex_sample_rate_combo.addItem("", "0") # 0 может означать авто
        self.yandex_sample_rate_combo.addItem("8000", "8000")
        self.yandex_sample_rate_combo.addItem("16000", "16000")
        self.yandex_sample_rate_combo.addItem("48000", "48000")
        # TODO: Заполнить актуальными частотами

    def get_settings(self) -> dict:
        api_key = self.yandex_api_key_edit.text().strip()
        if not api_key:
            logger.warning("API-ключ Yandex не введен.")
            # QMessageBox.warning(self, "Ошибка Yandex", "Введите API-ключ для Yandex SpeechKit")
            # return {} # или raise ValueError("API-ключ Yandex не введен.")

        config = {
            "api_key": api_key,
            "language_code": self.yandex_language_combo.currentData(),
            "model": self.yandex_model_combo.currentData(),
            "audio_format": self.yandex_audio_format_combo.currentData(),
            "sample_rate_hertz": int(self.yandex_sample_rate_combo.currentData()) 
                                 if self.yandex_sample_rate_combo.currentData() != "0" else None,
            # "folder_id": "YOUR_FOLDER_ID" # Если используется folder_id, его тоже нужно будет где-то хранить/вводить
        }
        # Удаляем None значения, если Yandex API их не ожидает
        config = {k: v for k, v in config.items() if v is not None}
        return config

    def set_settings(self, config: dict):
        self.yandex_api_key_edit.setText(config.get("api_key", ""))
        
        lang_code = config.get("language_code", "ru-RU")
        index = self.yandex_language_combo.findData(lang_code)
        if index != -1: self.yandex_language_combo.setCurrentIndex(index)

        model = config.get("model", "general")
        index = self.yandex_model_combo.findData(model)
        if index != -1: self.yandex_model_combo.setCurrentIndex(index)

        audio_format = config.get("audio_format", "lpcm")
        index = self.yandex_audio_format_combo.findData(audio_format)
        if index != -1: self.yandex_audio_format_combo.setCurrentIndex(index)

        sample_rate = str(config.get("sample_rate_hertz", "0")) # 0 для авто
        index = self.yandex_sample_rate_combo.findData(sample_rate)
        if index != -1: self.yandex_sample_rate_combo.setCurrentIndex(index)
        
        logger.debug(f"Настройки Yandex загружены: {config}")

    def is_valid(self) -> bool:
        api_key = self.yandex_api_key_edit.text().strip()
        if not api_key:
            QMessageBox.warning(self, self.tr("Ошибка Yandex"), self.tr("Введите API-ключ для Yandex SpeechKit."))
            return False
        # TODO: Добавить другие проверки, если необходимо (например, проверка формата ключа)
        # Можно добавить вызов self.check_yandex_api_key() если он будет реализован
        return True

    def load_specific_settings(self, settings: QSettings):
        """Загружает специфичные для Yandex настройки."""
        self.yandex_api_key_edit.setText(settings.value("yandex/api_key", ""))
        lang_code = settings.value("yandex/language_code", "ru-RU")
        index = self.yandex_language_combo.findData(lang_code)
        if index != -1: self.yandex_language_combo.setCurrentIndex(index)

        model = settings.value("yandex/model", "general")
        index = self.yandex_model_combo.findData(model)
        if index != -1: self.yandex_model_combo.setCurrentIndex(index)

        audio_format = settings.value("yandex/audio_format", "lpcm")
        index = self.yandex_audio_format_combo.findData(audio_format)
        if index != -1: self.yandex_audio_format_combo.setCurrentIndex(index)

        sample_rate = settings.value("yandex/sample_rate_hertz", "0") # 0 для авто
        index = self.yandex_sample_rate_combo.findData(sample_rate)
        if index != -1: self.yandex_sample_rate_combo.setCurrentIndex(index)

    def save_specific_settings(self, settings: QSettings):
        """Сохраняет специфичные для Yandex настройки."""
        settings.setValue("yandex/api_key", self.yandex_api_key_edit.text())
        settings.setValue("yandex/language_code", self.yandex_language_combo.currentData())
        settings.setValue("yandex/model", self.yandex_model_combo.currentData())
        settings.setValue("yandex/audio_format", self.yandex_audio_format_combo.currentData())
        settings.setValue("yandex/sample_rate_hertz", self.yandex_sample_rate_combo.currentData())

    def check_yandex_api_key(self):
        """Проверяет валидность API-ключа Yandex (примерная реализация)."""
        api_key = self.yandex_api_key_edit.text().strip()
        if not api_key:
            QMessageBox.warning(self, self.tr("Проверка ключа Yandex"), self.tr("API-ключ не введен."))
            return

        self.key_status_label.setText(self.tr("Проверка..."))
        self.check_yandex_key_button.setEnabled(False)

        # Создаем воркер и поток для проверки ключа
        self.check_thread = QThread()
        self.key_validator = YandexKeyValidator(api_key)
        self.key_validator.moveToThread(self.check_thread)

        self.check_thread.started.connect(self.key_validator.run)
        self.key_validator.finished.connect(self.on_key_check_finished)
        
        self.check_thread.start()

    def on_key_check_finished(self, is_valid, message):
        """Обработчик завершения проверки ключа."""
        if is_valid:
            self.key_status_label.setText(f"<font color='green'>{self.tr('Ключ валиден')}</font>")
        else:
            self.key_status_label.setText(f"<font color='red'>{self.tr('Ключ невалиден:')} {message}</font>")
        
        self.check_yandex_key_button.setEnabled(True)
        self.check_thread.quit()
        self.check_thread.wait()

    def save_specific_settings(self, settings: QSettings):
        """Сохраняет специфичные для Yandex настройки в QSettings."""
        settings.setValue("yandex/api_key", self.yandex_api_key_edit.text().strip())
        settings.setValue("yandex/language_index", self.yandex_language_combo.currentIndex())
        settings.setValue("yandex/model_index", self.yandex_model_combo.currentIndex())
        settings.setValue("yandex/audio_format_index", self.yandex_audio_format_combo.currentIndex())
        settings.setValue("yandex/sample_rate_index", self.yandex_sample_rate_combo.currentIndex())
        logger.info("Специфичные настройки Yandex сохранены.")

    def load_specific_settings(self, settings: QSettings):
        """Загружает специфичные для Yandex настройки из QSettings."""
        api_key = settings.value("yandex/api_key", "")
        self.yandex_api_key_edit.setText(api_key)
        
        lang_idx = settings.value("yandex/language_index", 0, type=int)
        if lang_idx < self.yandex_language_combo.count(): self.yandex_language_combo.setCurrentIndex(lang_idx)
        
        model_idx = settings.value("yandex/model_index", 0, type=int)
        if model_idx < self.yandex_model_combo.count(): self.yandex_model_combo.setCurrentIndex(model_idx)
        
        format_idx = settings.value("yandex/audio_format_index", 0, type=int)
        if format_idx < self.yandex_audio_format_combo.count(): self.yandex_audio_format_combo.setCurrentIndex(format_idx)
        
        rate_idx = settings.value("yandex/sample_rate_index", 0, type=int)
        if rate_idx < self.yandex_sample_rate_combo.count(): self.yandex_sample_rate_combo.setCurrentIndex(rate_idx)
        logger.info("Специфичные настройки Yandex загружены.")

    # def check_yandex_api_key(self):
    #     """Проверяет валидность API-ключа Yandex (примерная реализация)."""
    #     api_key = self.yandex_api_key_edit.text().strip()
    #     if not api_key:
    #         QMessageBox.warning(self, "Проверка ключа Yandex", "API-ключ не введен.")
    #         # self.yandex_api_key_valid.emit(False)
    #         return False
        
    #     # Здесь должна быть логика проверки ключа через Yandex API
    #     # Например, с использованием YandexSpeechKit клиента
    #     # try:
    #     #     client = YandexSpeechKit(api_key=api_key, folder_id='your_folder_id_if_needed')
    #     #     # Попробовать выполнить какой-то простой запрос, например, список языков
    #     #     # if client.validate_key(): # Псевдо-метод
    #     #     QMessageBox.information(self, "Проверка ключа Yandex", "API-ключ Yandex (предположительно) валиден.")
    #     #     # self.yandex_api_key_valid.emit(True)
    #     #     return True
    #     # except Exception as e:
    #     #     logger.error(f"Ошибка проверки API-ключа Yandex: {e}")
    #     #     QMessageBox.critical(self, "Проверка ключа Yandex", f"Ошибка при проверке ключа: {e}")
    #     #     # self.yandex_api_key_valid.emit(False)
    #     #     return False
    #     QMessageBox.information(self, "Проверка ключа Yandex", "Функция проверки ключа Yandex еще не реализована.")
    #     return True # Заглушка

class YandexKeyValidator(QObject):
    finished = Signal(bool, str)

    def __init__(self, api_key):
        super().__init__()
        self.api_key = api_key

    def run(self):
        import requests
        headers = {
            'Authorization': f'Api-Key {self.api_key}',
        }
        # Делаем тестовый запрос на синтез речи для проверки ключа
        url = 'https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize'
        data = {
            'text': 'test',
            'lang': 'ru-RU',
            'voice': 'oksana',
            'format': 'lpcm',
            'sampleRateHertz': '8000'
        }
        try:
            response = requests.post(url, headers=headers, data=data, timeout=10)
            # Код 401 однозначно говорит о неверном ключе
            if response.status_code == 401:
                self.finished.emit(False, self.tr("Неверный API ключ (401)"))
            # Любой другой ответ, кроме 401, означает, что ключ, скорее всего, валиден,
            # даже если сам запрос завершился с другой ошибкой (например, нехватка средств или неверные параметры).
            # Успешный ответ (200) подтверждает валидность.
            elif response.status_code == 200:
                 self.finished.emit(True, "")
            else:
                # Если код ответа не 200 и не 401, мы считаем ключ валидным, но сообщаем о возможной проблеме.
                # Это может быть полезно для диагностики (например, не указан каталог).
                self.finished.emit(True, f"{self.tr('Ключ валиден, но есть ответ от сервера')}: {response.status_code}")

        except requests.exceptions.RequestException as e:
            self.finished.emit(False, str(e))

if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication
    import sys

    logging.basicConfig(level=logging.DEBUG)

    app = QApplication(sys.argv)
    window = YandexSettingsTab()
    window.setWindowTitle("Тест вкладки настроек Yandex")
    window.show()
    sys.exit(app.exec())