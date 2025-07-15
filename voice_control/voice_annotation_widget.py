#!/usr/bin/env python3
"""
Виджет для голосовой аннотации выделенных областей экрана.
Позволяет записать звук, распознать его и отредактировать полученный текст.
"""

import os
import sys
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QSizePolicy, QMessageBox
from PySide6.QtGui import QColor, QPalette, QIcon, QFont, QFocusEvent, QShowEvent
from PySide6.QtCore import Qt, QTimer, QSize, Signal, QSettings, QPropertyAnimation, QThread, QObject, Slot, QPoint, QRect

# Импортируем RecognitionWorker из нового файла
from voice_control.recognition_worker import RecognitionWorker
from voice_control.voice_annotation_view import VoiceAnnotationView
from voice_control.voice_annotation_model import VoiceAnnotationModel

# Импортируем наши модули
from voice_control.recognizers.yandex_recognizer import YandexSpeechRecognizer
from voice_control.recognizers.vosk_recognizer import VoskSpeechRecognizer
# from voice_control.recognizers.google_recognizer import GoogleSpeechRecognizer
from voice_control.microphone.qt_audio_capture import QtAudioCapture

# Настройка логирования
logger = logging.getLogger(__name__)


# НЕОБХОДИМО ИСПРАВИТЬ ИНИЦИАЛИЗАЦИЮ SpeechRecognizer
class  VoiceAnnotationWidget(QWidget):
    """
    Виджет для голосовой аннотации выделенных областей.
    По сути, теперь это Контроллер (или ViewModel), который управляет VoiceAnnotationView и VoiceAnnotationModel.
    """
    
    # Сигнал для отправки готового текста аннотации
    annotation_ready = Signal(str)
    recognition_finished = Signal(str)
    
    def __init__(self, settings_manager=None, parent=None):
        logger.info("VoiceAnnotationWidget.__init__: Initializing...")
        """
        Инициализация виджета голосовой аннотации.
        
        Args:
            settings_manager: Менеджер настроек приложения
            parent: Родительский виджет
        """
        super().__init__(parent)
        
        self.settings_manager = settings_manager
        self.settings_dialog = None  # Инициализируем диалог настроек
        self.settings_window = None

        # Позволяем виджету изменять размер по вертикали
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.MinimumExpanding)

        # Создаем Модель (Model)
        self.model = VoiceAnnotationModel(self.settings_manager, self)

        # Создаем Представление (View)
        self.view = VoiceAnnotationView(self)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.addWidget(self.view)
        self.setLayout(main_layout)

        # Подключаем сигналы от View к методам этого контроллера
        self.view.record_button_pressed.connect(self._toggle_recording)
        self.view.settings_button_clicked.connect(self.open_settings_dialog)

        self.view.text_set.connect(self.recognition_finished.emit)
        self.view.done_button_clicked.connect(self._finalize_annotation)
        self.view.close_button_clicked.connect(self.close) # Подключаем кнопку закрытия
        self.view.text_changed_signal.connect(self._on_view_text_changed)

        # Подключаем сигналы от Модели к методам обновления View
        self.model.text_changed.connect(self.view.set_current_text)
        self.model.is_recording_changed.connect(self._on_model_is_recording_changed)
        self.model.is_recognizing_changed.connect(self._on_model_is_recognizing_changed)
        self.model.error_message_changed.connect(self._on_model_error_message_changed)

        # Создаем объект для захвата звука
        self.audio_capture = QtAudioCapture()
        
        # Подключаем сигнал изменения громкости от микрофона
        self.audio_capture.volume_changed.connect(self._on_volume_changed)
        
        # Создаем распознаватель речи
        self.recognizer = None
        self.recognition_thread = None
        self.recognition_worker = None
        
        # Флаг записи
        self.is_recording = False
        
        # Флаг для отложенного закрытия виджета
        self._finalize_after_recognition = False
        
        # Для плавного отображения уровня звука
        self.current_level = 0
        self.target_level = 0
        
        # Таймер для плавного обновления индикатора уровня звука
        self.level_timer = QTimer()
        self.level_timer.timeout.connect(self._update_sound_level_smooth)
        self.level_timer.start(50)  # Обновляем 20 раз в секунду для плавности
        
        # Таймер для автоматической остановки записи по достижении максимальной длительности
        self.recording_timer = QTimer()
        self.recording_timer.setSingleShot(True)
        self.recording_timer.timeout.connect(self.stop_recording)
        
        # Файл для записи
        self.temp_wav_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_recording.wav")
        
        # Загружаем настройки распознавателя
        self.load_recognizer()
        
        # Подключаем сигнал окончания записи
        self.audio_capture.recording_stopped.connect(self._on_recording_stopped)
        
        # Вызываем retranslate_ui в конце инициализации
        self.retranslate_ui()
    
    def start_recording_and_show(self):
        """Показывает виджет и начинает запись, если она еще не идет."""
        self.show()
        if not self.model.is_recording:
            self._toggle_recording()

    def retranslate_ui(self):
        """Обновляет переводы интерфейса."""
        # Обновляем переводы в представлении
        if hasattr(self.view, 'retranslate_ui'):
            self.view.retranslate_ui()
        
        # Обновляем переводы в модели, если необходимо
        if hasattr(self.model, 'retranslate_ui'):
            self.model.retranslate_ui()
    
    def _on_view_text_changed(self, text: str):
        """Обработка изменения текста в представлении. Обновляет модель."""
        logger.debug(self.tr("Текст в View изменен: '{}...'. Обновляем модель.").format(text[:50]))
        self.model.current_text = text

    # НОВЫЕ СЛОТЫ ДЛЯ СИГНАЛОВ МОДЕЛИ
    def _on_model_is_recording_changed(self, is_recording: bool):
        logger.debug(self.tr("Модель: is_recording изменился на {}").format(is_recording))
        self.view._update_record_button_style(is_recording)
        if not is_recording:
            self.target_level = 0 # Сброс целевого уровня для индикатора звука
            if self.recording_timer.isActive():
                 self.recording_timer.stop()
        else:
            self.recording_timer.start(self.model.max_duration_sec * 1000)
        QTimer.singleShot(0, self.adjustSize) # Корректируем размер после изменения состояния записи

    def _on_model_is_recognizing_changed(self, is_recognizing: bool):
        logger.debug(self.tr("Модель: is_recognizing изменился на {}").format(is_recognizing))
        if is_recognizing:
            self.view.show_text_edit(True)
            self.view.setMinimumHeight(150)
            self.view.resize(self.view.width(), 150)
            self.view.set_placeholder_text(self.tr("Распознавание..."))
        # Обновление UI может быть более сложным, например, блокировка кнопки записи

    def _on_model_error_message_changed(self, error_message: str):
        logger.debug(self.tr("Модель: error_message изменился на '{}'").format(error_message))
        if error_message: # Если есть сообщение об ошибке
            self.model.current_text = error_message # Показываем ошибку в текстовом поле
            self.view.show_text_edit(True)
        # Иначе, если error_message пуст, текст не меняем, это может быть просто сброс

    def _load_voice_settings(self):
        """Загрузка настроек голосовой аннотации в Модель."""
        if self.settings_manager:
            self.model.load_settings(self.settings_manager)
        else:
            logger.warning("VoiceAnnotationWidget: Менеджер настроек не предоставлен. Модель использует значения по умолчанию.")
            self.model.load_settings(None) # Позволяем модели использовать значения по умолчанию

    def reload_recognizer(self):
        """Перезагружает распознаватель речи с новыми настройками."""
        logger.info(self.tr("Перезагрузка распознавателя речи..."))
        self.load_recognizer()

    def load_recognizer(self):
        """Загрузка распознавателя речи из настроек.
        
        Создает экземпляр распознавателя в зависимости от выбранного типа.
        """
        logger.debug(self.tr("Начинаем загрузку распознавателя речи..."))
        settings = QSettings("Screph", "SpeechRecognition")
        
        # Получаем тип распознавателя из настроек
        recognizer_type = settings.value("recognizer_type", "yandex")
        logger.info(self.tr("Выбранный тип распознавателя: {}").format(recognizer_type))
        
        try:
            if recognizer_type == "yandex":
                self._load_yandex_recognizer(settings)
            elif recognizer_type == "vosk":
                self._load_vosk_recognizer(settings)
            # elif recognizer_type == "google":
            #     self._load_google_recognizer(settings)
            else:
                logger.error(self.tr("Неизвестный тип распознавателя: {}").format(recognizer_type))
                self.recognizer = None
        except Exception as e:
            logger.error(self.tr("Ошибка при загрузке распознавателя {}: {}").format(recognizer_type, e))
            self.recognizer = None
    
    def _load_yandex_recognizer(self, settings):
        """Загрузка Yandex распознавателя."""
        # Используем ключи с префиксом 'yandex/' для группировки настроек
        api_key = settings.value("yandex/api_key", "")
        logger.info(f"VoiceAnnotationWidget: Загрузка Yandex распознавателя. API-ключ из настроек: {'*' * (len(api_key) - 4) + api_key[-4:] if api_key else 'None'}")
        
        if not api_key:
            logger.warning("API ключ Yandex SpeechKit не установлен в настройках")
            logger.info(self.tr("Для настройки API ключа откройте диалог настроек через кнопку 'Настройки'"))
            self.recognizer = None
            return
        
        # Загружаем настройки напрямую, без использования индексов
        language = settings.value("yandex/language", "ru-RU")
        model = settings.value("yandex/model", "general")
        
        # Настройки качества звука по умолчанию берутся из GUI
        audio_format = settings.value("yandex/audio_format", "lpcm")
        sample_rate = settings.value("yandex/sample_rate_hertz", 16000, type=int)
        
        # Глобальная настройка качества звука может переопределить значения
        if self.model.audio_quality == "low":
            audio_format = "lpcm"
            sample_rate = 8000
        elif self.model.audio_quality == "high":
            audio_format = "oggopus"
            sample_rate = 48000
        # Для "medium" используются значения из настроек (GUI) или значения по умолчанию
        
        config = {
            'api_key': api_key,
            'language_code': language,
            'model': model,
            'audio_format_hint': audio_format,
            'sample_rate_hertz': sample_rate
        }
        
        logger.debug(f"VoiceAnnotationWidget: Конфигурация для YandexSpeechRecognizer: {config}")
        self.recognizer = YandexSpeechRecognizer(config)
        logger.info(self.tr("Yandex распознаватель создан (язык: {}, модель: {})").format(language, model))
    
    def _load_vosk_recognizer(self, settings):
        """Загрузка Vosk распознавателя."""
        model_path = settings.value("vosk/model_path", "")
        language_index = settings.value("vosk/language_index", 0, type=int)
        sample_rate_index = settings.value("vosk/sample_rate_index", 0, type=int)
        
        # Списки значений точно как в vosk_settings_tab.py
        languages = ["auto", "ru", "en"]  # соответствует комбобоксу в настройках
        sample_rates = [16000, 8000, 48000]  # соответствует комбобоксу в настройках
        
        language = languages[min(language_index, len(languages)-1)]
        sample_rate = sample_rates[min(sample_rate_index, len(sample_rates)-1)]
        
        config = {
            'model_path': model_path,
            'language': language,
            'sample_rate': sample_rate
        }
        
        self.recognizer = VoskSpeechRecognizer(config)
        logger.info(self.tr("Vosk распознаватель создан (модель: {}, язык: {}, частота: {})").format(model_path, language, sample_rate))
    
    def _load_google_recognizer(self, settings):
        """Загрузка Google распознавателя."""
        credentials_path = settings.value("google_credentials_path", "")
        language_code = settings.value("google_language_code", "ru-RU")
        
        config = {
            'credentials_path': credentials_path,
            'language_code': language_code
        }
        
        self.recognizer = GoogleSpeechRecognizer(config)
        logger.info(self.tr("Google распознаватель создан (язык: {})").format(language_code))
    
    def open_settings_dialog(self):
        """Открывает окно настроек распознавания речи."""
        from voice_control.ui.speech_recognition_gui import run_speech_recognition_app
        logger.debug(self.tr("Открытие окна настроек распознавания речи..."))
        if self.settings_window is None or not self.settings_window.isVisible():
            self.settings_window = run_speech_recognition_app(self.settings_manager)
            self.settings_window.show()
        else:
            self.settings_window.activateWindow()
            self.settings_window.raise_()
        return self.settings_window

    def _on_settings_closed(self):
        """Обработчик закрытия окна настроек."""
        logger.info(self.tr("Окно настроек закрыто, перезагружаем распознаватель..."))
        self.load_recognizer()
        self.settings_window = None # Сбрасываем ссылку

    def _toggle_recording(self):
        """Переключение записи звука."""
        if not self.model.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        """Начало записи звука."""
        logger.info("VoiceAnnotationWidget.start_recording: Attempting to start recording.")
        logger.debug(self.tr("Вызван метод start_recording()"))
        
        if self.model.is_recording: # ДОБАВЛЕНА ПРОВЕРКА
            logger.warning(self.tr("VoiceAnnotationWidget.start_recording: Попытка начать запись, когда она уже идет. Игнорируется."))
            return

        if self.recognizer is None:
            logger.error(self.tr("Не настроен распознаватель речи"))
            logger.error(self.tr("Возможные причины:"))
            logger.error(self.tr("1. API ключ Yandex SpeechKit не установлен"))
            logger.error(self.tr("2. Ошибка при инициализации распознавателя"))
            logger.error(self.tr("3. Проблемы с сетевым подключением к Yandex"))
            logger.error(self.tr("Решение: откройте настройки и проверьте API ключ Yandex SpeechKit"))
            
            # Попытаемся перезагрузить распознаватель
            logger.info(self.tr("Попытка повторной загрузки распознавателя..."))
            self.load_recognizer()
            
            if self.recognizer is None:
                logger.error(self.tr("Повторная загрузка распознавателя не удалась"))
                return
            else:
                logger.info(self.tr("Распознаватель успешно загружен при повторной попытке"))
        
        try:
            self.model.annotation_emitted_once = False
            
            self.view.clear_text_edit()
            self.view.show_text_edit(False)
            
            self.view.setMinimumHeight(40)
            self.view.resize(self.view.width(), 40)
            
            devices = self.audio_capture.get_available_devices()
            if not devices:
                logger.error(self.tr("Не найдены микрофоны"))
                return
            
            if self.audio_capture.start_recording():
                self.model.is_recording = True
                
                logger.info(self.tr("Начата запись звука (макс. длительность: {} сек)").format(self.model.max_duration_sec))
            else:
                logger.error(self.tr("Не удалось начать запись"))
        except Exception as e:
            logger.error(self.tr("Ошибка при запуске записи: {}").format(e))

    def stop_recording(self):
        """Остановка записи звука."""
        logger.info("VoiceAnnotationWidget.stop_recording: Attempting to stop recording.")
        logger.debug(self.tr("Попытка остановить запись..."))
        try:
            if self.recording_timer.isActive():
                self.recording_timer.stop()
            
            if self.model.is_recording: 
                if not self.audio_capture.stop_recording(): 
                    logger.error(self.tr("audio_capture.stop_recording() не удалось."))
                    self.model.is_recording = False
            else:
                logger.debug(self.tr("Запись не была активна, вызов stop_recording проигнорирован для audio_capture."))
                if not self.view.record_button.isChecked(): 
                    self.model.is_recording = False

        except Exception as e:
            logger.error(self.tr("Ошибка при вызове audio_capture.stop_recording: {}").format(e), exc_info=True)
            self.model.is_recording = False
        
        if self.view.record_button.isChecked():
            self.view.record_button.setChecked(False)
            self.model.is_recording = False

    def _update_button_and_animation_on_stop(self):
        """Вспомогательный метод для обновления UI кнопки и анимации при остановке."""
        self.view._update_record_button_style(False)
        self.target_level = 0
        logger.debug(self.tr("UI кнопки и анимация обновлены после остановки записи."))

    def _on_recording_stopped(self):
        """Обработчик сигнала о завершении записи."""
        logger.info(self.tr("Получен сигнал о завершении записи от audio_capture"))
        self.model.is_recording = False 

        try:
            audio_data = self.audio_capture.get_recorded_data()
            if audio_data and len(audio_data) > 0:
                logger.info(self.tr("Аудиоданные успешно получены из буфера: {} байт.").format(len(audio_data[0]) if isinstance(audio_data, tuple) and audio_data else len(audio_data)))
                
                if self.model.auto_recognition_enabled:
                    logger.debug(self.tr("Автоматическое распознавание включено, запускаем _recognize_recorded_audio."))
                    self._recognize_recorded_audio(audio_data)
                else:
                    logger.info(self.tr("Автоматическое распознавание выключено."))
                    self.view.show_text_edit(True)
                    self.view.setMinimumHeight(150)
                    self.view.resize(self.view.width(), 150)
                    self.model.current_text = self.tr("Запись завершена. Отредактируйте текст или нажмите 'Готово'.")
                    QApplication.processEvents()
            else:
                logger.warning(self.tr("Не удалось получить аудиоданные из буфера (пустые данные или null)."))
                self.model.current_text = self.tr("<нет записи>") 

        except Exception as e:
            logger.error(self.tr("Ошибка при обработке аудиоданных в _on_recording_stopped: {}").format(e), exc_info=True)
            self.model.error_message = self.tr("Ошибка обработки аудио: {}").format(e)

    def _on_volume_changed(self, volume):
        """Обработчик сигнала изменения громкости."""
        if self.model.is_recording:
            self.target_level = int(volume * 100)
    
    def _update_sound_level_smooth(self):
        """Плавное обновление индикатора уровня звука."""
        if not self.model.is_recording and self.current_level < 1:
            if self.view.sound_level.value() != 0:
                self.view.set_sound_level(0)
            return
            
        if self.current_level < self.target_level:
            self.current_level = min(self.target_level, self.current_level + 5)
        elif self.current_level > self.target_level:
            self.current_level = max(self.target_level, self.current_level - 3)
        else: 
            if not self.model.is_recording and self.target_level == 0:
                self.current_level = 0

        self.view.set_sound_level(self.current_level)
        
        if not self.model.is_recording and self.target_level > 0:
            self.target_level = max(0, self.target_level - 2)

    def _recognize_recorded_audio(self, audio_data=None):
        """Распознавание записанного аудио.
        
        Args:
            audio_data: Кортеж (raw_data, sample_rate, channels, sample_width) или None
                      Если None, будет использован файл self.temp_wav_file
        """
        try:
            self.view.show_text_edit(True)
            self.view.setMinimumHeight(150)
            self.view.resize(self.view.width(), 150)
            
            self.view.set_placeholder_text(self.tr("Распознавание..."))
            QApplication.processEvents()
            
            if audio_data and hasattr(self.recognizer, 'recognize_audio_data'):
                if isinstance(audio_data, (bytes, bytearray)):
                    prepared_data = (audio_data, self.audio_capture.sample_rate, 
                              self.audio_capture.channels, self.audio_capture.sample_size // 8)
                    logger.info(self.tr("Преобразовано в формат кортежа: {} байт, {} Гц, {} канал(ов), {} байт/сэмпл").format(
                        len(audio_data), self.audio_capture.sample_rate, 
                        self.audio_capture.channels, self.audio_capture.sample_size // 8))
                    worker_audio_data = prepared_data
                    worker_file_path = None
                elif isinstance(audio_data, tuple) and len(audio_data) == 4:
                    worker_audio_data = audio_data
                    worker_file_path = None
                else:
                    logger.error(self.tr("Неподдерживаемый формат аудиоданных: {}").format(type(audio_data)))
                    self.model.error_message = self.tr("Ошибка: неверный формат аудио.")
                    return
                
                self.recognition_thread = QThread()
                self.recognition_worker = RecognitionWorker(self.recognizer, 
                                                  audio_file_path=worker_file_path, 
                                                  audio_data_tuple=worker_audio_data)
                self.recognition_worker.moveToThread(self.recognition_thread)

                self.recognition_worker.recognition_finished.connect(self._on_recognition_result)
                self.recognition_worker.recognition_error.connect(self._on_recognition_error)
                self.recognition_thread.started.connect(self.recognition_worker.run)
                self.recognition_thread.finished.connect(self.recognition_thread.deleteLater)
                self.recognition_thread.finished.connect(self.recognition_worker.deleteLater) 
                self.recognition_thread.finished.connect(self._clear_recognition_refs)

                self.model.is_recognizing = True
                self.recognition_thread.start()
            
        except Exception as e:
            logger.error(self.tr("Ошибка при настройке или запуске потока распознавания: {}").format(e), exc_info=True)
            self.model.error_message = self.tr("Внутренняя ошибка: {}").format(e)
            self.model.is_recognizing = False
            if self.recognition_thread:
                if self.recognition_thread.isRunning():
                    self.recognition_thread.quit()
                    self.recognition_thread.wait(1000) 
                self.recognition_thread.deleteLater()
                self.recognition_thread = None
            if self.recognition_worker:
                self.recognition_worker.deleteLater()
                self.recognition_worker = None

    def _clear_recognition_refs(self):
        logger.debug(self.tr("Очистка ссылок на поток и воркер распознавания."))
        self.recognition_thread = None
        self.recognition_worker = None

    def _on_recognition_result(self, result: dict):
        """Обработка успешного результата распознавания из потока."""
        logger.debug(self.tr("Получен результат распознавания из потока: {}").format(result))
        self.model.is_recognizing = False
        QApplication.processEvents()

        if self.recognition_thread and self.recognition_thread.isRunning():
            self.recognition_thread.quit()

        if result.get('success'):
            full_text = ""
            if 'normalized_text' in result and result['normalized_text'] and result['normalized_text'].strip():
                full_text = result['normalized_text']
            elif 'text' in result and result['text'] and result['text'].strip():
                full_text = result['text']

            # Если основной текст НЕ найден, тогда пытаемся собрать из 'results'
            if not full_text.strip() and 'results' in result and result['results']:
                logger.debug(self.tr("Основной текст не найден, пытаемся собрать из 'results'..."))
                try:
                    texts = []
                    for res_item in result['results']:
                        if 'alternatives' in res_item and res_item['alternatives']:
                            texts.append(res_item['alternatives'][0].get('text', ''))
                        elif 'text' in res_item:
                            texts.append(res_item.get('text', ''))
                    full_text = " ".join(filter(None, texts))
                    logger.debug(self.tr("Собранный текст из results: {}").format(full_text))
                except Exception as e:
                    logger.error(self.tr("Ошибка при сборке текста из results: {}").format(e))
                    # full_text останется пустым или тем, что было до этого

            if full_text.strip():
                self.model.current_text = full_text.strip()
                self.view.show_text_edit(True)
                self.view.get_text_edit_widget().setFocus()
                logger.info(self.tr("Распознанный текст: '{}...' ({} символов)").format(full_text[:50], len(full_text)))
            else:
                self.model.error_message = self.tr("Ошибка: не удалось распознать текст.")
                self.view.show_text_edit(True)
                logger.error(self.tr("Ошибка распознавания: не удалось распознать текст."))
        else:
            error_msg = result.get('error', self.tr('Неизвестная ошибка распознавания'))
            self.model.error_message = self.tr("Ошибка: {}").format(error_msg)
            self.view.show_text_edit(True)
            logger.error(self.tr("Ошибка распознавания: {}").format(error_msg))

        if self._finalize_after_recognition:
            self._finalize_after_recognition = False
            logger.debug(self.tr("Распознавание завершено, скрываем виджет."))
            self._emit_and_hide()

    def _on_recognition_error(self, error_message: str):
        """Обработка ошибки распознавания из потока."""
        logger.error(self.tr("Ошибка в потоке распознавания: {}").format(error_message))
        self.model.is_recognizing = False
        if self.recognition_thread and self.recognition_thread.isRunning():
            self.recognition_thread.quit()

        self.model.error_message = self.tr("Ошибка распознавания: {}").format(error_message)
        self.view.show_text_edit(True)

        if self._finalize_after_recognition:
            self._finalize_after_recognition = False
            logger.debug(self.tr("Ошибка распознавания, скрываем виджет."))
            self._emit_and_hide() 

    def get_annotation_text(self) -> str:
        """
        Получение текста аннотации.
        
        Returns:
            Текст аннотации
        """
        return self.model.current_text

    def _set_annotation_text(self, text: str):
        """
        Установка текста аннотации.
        
        Args:
            text: Текст аннотации
        """
        self.model.current_text = text

    def showEvent(self, event: QShowEvent):
        super().showEvent(event) # Вызов super() в начале
        self.model.reset_state() 
        
        self.view.text_edit.setPlaceholderText(self.tr("Говорите..."))

        if not self.model.is_recognizing:
            self.view.show_text_edit(False)
            # self.view.setMinimumHeight(40) # управляется из view.show_text_edit
            # self.view.resize(self.view.width(), 40) # управляется из view.show_text_edit
        else:
            self.view.show_text_edit(True)
        
        # Сбрасываем флаг отправки аннотации при каждом показе виджета,
        # чтобы можно было отправить новую аннотацию, если виджет был скрыт и показан снова.
        self.model.annotation_emitted_once = False
        self.setFocus() # Устанавливаем фокус на виджет при показе
        QTimer.singleShot(0, self.adjustSize) # Корректируем размер после отображения





    def _on_settings_applied(self, recognizer_instance):
        """Слот для обработки сигнала settings_applied из SettingsTab."""
        logger.info(self.tr("Настройки распознавания применены из диалога."))
        if self.model:
            self.model.set_recognizer(recognizer_instance)
        # Возможно, здесь нужно обновить какие-то элементы UI в VoiceAnnotationWidget
        # на основе новых настроек, если это применимо.

    def set_voice_input_mode_enabled(self, enabled: bool):
        # Включает/выключает возможность голосового ввода (например, для блокировки во время рисования)
        pass

    def _finalize_annotation(self):
        logger.debug(self.tr("Завершение аннотации..."))
        if self.model.is_recording:
            logger.debug(self.tr("Запись активна. Устанавливаем флаг для завершения после распознавания."))
            self._finalize_after_recognition = True
            self.stop_recording()
        elif self.model.is_recognizing:
            logger.debug(self.tr("Распознавание активно. Устанавливаем флаг для завершения."))
            self._finalize_after_recognition = True
        else:
            logger.debug(self.tr("Запись и распознавание неактивны. Немедленное завершение."))
            self._emit_and_hide()

    def _emit_and_hide(self):
        if self.model.annotation_emitted_once:
            logger.debug(self.tr("Аннотация уже была отправлена один раз, повторная отправка отменена."))
            if not self.isHidden():
                self.hide()
                self.clearFocus()
                self.releaseKeyboard()
            return

        text = self.model.current_text.strip()
        mode = self.settings_manager.get_setting("main/recognition_mode", 0)

        logger.info(self.tr("Аннотация готова: '{}...' ({} символов), режим: {}").format(text[:50], len(text), mode))

        if mode == 1:  # Копировать и скрыть
            QApplication.clipboard().setText(text)
            self.hide()
            self.clearFocus()
            self.releaseKeyboard()
            return
        elif mode == 2:  # Копировать, очистить и скрыть
            QApplication.clipboard().setText(text)
            if self.model.current_text:
                self.model.current_text = ""
            self.hide()
            self.clearFocus()
            self.releaseKeyboard()
            return


        self.annotation_ready.emit(text)
        self.model.annotation_emitted_once = True

        if not self.isHidden():
            self.hide()
            self.clearFocus()
            self.releaseKeyboard()
            self.clearFocus()

        top_level_window = self.window()
        if top_level_window and top_level_window != self:
            logger.debug(self.tr("Attempting to set focus to top level window: {}").format(top_level_window))
            top_level_window.setFocus(Qt.FocusReason.OtherFocusReason)
        else:
            parent_to_focus = self.parentWidget()
            if parent_to_focus:
                logger.debug(self.tr("Fallback: Attempting to set focus to parent: {}").format(parent_to_focus))
                parent_to_focus.setFocus(Qt.FocusReason.OtherFocusReason)

        logger.debug(self.tr("VoiceAnnotationWidget reset, hidden, and keyboard released."))

    def keyPressEvent(self, event):
        if not self.isVisible(): # Если виджет не видим, не обрабатываем нажатия
            super().keyPressEvent(event) # Передаем событие дальше, если необходимо
            return

        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            logger.debug(self.tr("Нажата клавиша Enter/Return, завершаем аннотацию."))
            self._finalize_annotation()
        elif event.key() == Qt.Key.Key_Escape:
            logger.debug(self.tr("Нажата клавиша Escape, скрываем виджет без отправки аннотации."))
            self.model.annotation_emitted_once = True # Считаем, что "действие" выполнено
            self.hide()
            self.clearFocus()
            self.releaseKeyboard() # <--- Добавлено
            # event.accept() # Опционально, если мы точно не хотим, чтобы кто-то еще обработал Escape
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        logger.debug(self.tr("VoiceAnnotationWidget closeEvent"))
        # Принудительно останавливаем запись и потоки, если они активны
        if self.model.is_recording: 
            self.stop_recording()
        
        if self.recognition_thread and self.recognition_thread.isRunning():
            logger.info(self.tr("Остановка потока распознавания при закрытии виджета..."))
            self.recognition_thread.quit()
            if not self.recognition_thread.wait(1000): # Ждем до 1 секунды
                logger.warning(self.tr("Поток распознавания не завершился штатно, прерываем..."))
                self.recognition_thread.terminate()
                self.recognition_thread.wait() # Ждем завершения после terminate
        super().closeEvent(event)

    def focusOutEvent(self, event: QFocusEvent):
        """Обрабатывает потерю фокуса виджетом."""
        # logger.debug(f"VoiceAnnotationWidget потерял фокус (reason: {event.reason()}), новый фокус: {QApplication.focusWidget()}, скрываем.")
        # self.reset_and_hide()
        pass # Отключаем скрытие при потере фокуса

    def _is_in_settings_context(self) -> bool:
        """Проверяет, находится ли виджет в контексте настроек или других специальных контейнеров."""
        parent = self.parentWidget()
        while parent:
            # Проверяем имя класса родительского виджета
            parent_class_name = parent.__class__.__name__
            
            # Список классов, в контексте которых виджет не должен автоматически скрываться
            settings_context_classes = [
                'SettingsTab',
                'QStackedWidget',  # Может быть частью настроек
                'QTabWidget',      # Вкладки настроек
                'QDialog',         # Диалоговые окна настроек
                'QGroupBox'        # Группы настроек
            ]
            
            if parent_class_name in settings_context_classes:
                logger.debug(self.tr("VoiceAnnotationWidget находится в контексте настроек: {}").format(parent_class_name))
                return True
                
            # Также проверяем по имени объекта, если оно содержит 'settings'
            if hasattr(parent, 'objectName') and 'settings' in parent.objectName().lower():
                logger.debug(self.tr("VoiceAnnotationWidget находится в контексте настроек по имени объекта: {}").format(parent.objectName()))
                return True
                
            parent = parent.parentWidget()
            
        return False

    def _reset_and_hide(self):
        logger.debug(self.tr("Сброс и скрытие виджета."))
        self.model.reset_state()
        self.view.reset_ui() # Сброс UI в View
        self.hide()
        self.releaseKeyboard() # Освобождаем клавиатуру
        self.clearFocus()      # Снимаем фокус с себя

        # Попытка вернуть фокус родительскому окну верхнего уровня
        top_level_window = self.window()
        if top_level_window and top_level_window != self:
            logger.debug(self.tr("Attempting to set focus to top level window: {}").format(top_level_window))
            top_level_window.setFocus(Qt.FocusReason.OtherFocusReason)
        else:
            # Fallback, если self.window() не подходит (например, это и есть главное окно, что маловероятно для такого виджета)
            parent_to_focus = self.parentWidget()
            if parent_to_focus:
                logger.debug(self.tr("Fallback: Attempting to set focus to parent: {}").format(parent_to_focus))
                parent_to_focus.setFocus(Qt.FocusReason.OtherFocusReason)

        logger.debug(self.tr("VoiceAnnotationWidget reset, hidden, and keyboard released."))

    def cleanup(self):
        """Принудительно останавливает все активные потоки и очищает ресурсы."""
        logger.info(self.tr("Starting cleanup for VoiceAnnotationWidget..."))
        if self.audio_capture:
            # Проверяем, что audio_capture еще существует
            if self.audio_capture.is_recording: # было is_recording()
                self.audio_capture.stop_recording()
            # self.audio_capture.cleanup() # Удаляем эту строку
            # logger.debug("QtAudioCapture cleanup called.") # И эту
            self.audio_capture = None # Явно удаляем ссылку
        if self.recognition_thread and self.recognition_thread.isRunning():
            logger.info(self.tr("Остановка потока распознавания..."))
            self.recognition_thread.quit()
            if not self.recognition_thread.wait(1000): # Ждем до 1 секунды
                logger.warning(self.tr("Поток распознавания не завершился штатно, прерываем..."))
                self.recognition_thread.terminate()
                self.recognition_thread.wait() # Ждем завершения после terminate
        logger.info(self.tr("Cleanup for VoiceAnnotationWidget complete."))

# Самостоятельный запуск для тестирования
if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = VoiceAnnotationWidget()
    widget.show()
    sys.exit(app.exec())
