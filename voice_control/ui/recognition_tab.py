"""
Вкладка распознавания для графического интерфейса распознавания речи.
"""

import os
import sys
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QComboBox, QLineEdit, QTextEdit, QGroupBox, 
                            QFormLayout, QRadioButton, QButtonGroup, QMessageBox,
                            QFileDialog, QTabWidget, QApplication)
from PySide6.QtCore import Qt, Signal, Slot



# Настраиваем логирование через глобальную конфигурацию
try:
    from logging_config import configure_logging
    configure_logging()
except ImportError:
    # Fallback на базовую настройку, если глобальная конфигурация недоступна
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

from voice_control.microphone.qt_mic_gui import MicrophoneControlWidget
from voice_control.recognizers.yandex_recognizer import YandexSpeechRecognizer
from voice_control.recognizers.vosk_recognizer import VoskSpeechRecognizer
from voice_control.ui.gui_components import create_button, create_label, create_text_edit, create_progress_bar, create_status_indicator, create_scroll_area
from voice_control.voice_annotation_widget import VoiceAnnotationWidget

# Определяем корневую директорию проекта
current_dir = os.path.dirname(os.path.abspath(__file__))
speech_recognition_dir = os.path.dirname(current_dir)
voice_control_dir = os.path.dirname(speech_recognition_dir)
project_root = os.path.dirname(voice_control_dir)

# Настройка логирования
logger = logging.getLogger(__name__)


class RecognitionTab(QWidget):
    """Вкладка распознавания речи."""
    
    def __init__(self, settings_manager, parent=None):
        """
        Инициализация вкладки распознавания.
        
        Args:
            parent: Родительский виджет
        """
        super().__init__(parent)
        self.settings_manager = settings_manager
        
        # Инициализация компонентов
        self.init_ui()
        
        # Распознаватель речи
        self.recognizer = None
        self.voice_widget = None  # Будет инициализировано в init_ui()
        
        # Директория для сохранения результатов
        self.results_dir = os.path.join(project_root, "recognition_results")
        os.makedirs(self.results_dir, exist_ok=True)

    def retranslate_ui(self):
        self.voice_input_group.setTitle(self.tr("Голосовой ввод"))
        self.results_group.setTitle(self.tr("Результаты распознавания"))
        self.results_text.setPlaceholderText(self.tr("Здесь будут отображаться результаты распознавания..."))
        self.clear_results_button.setText(self.tr("Очистить"))
        self.save_results_button.setText(self.tr("Сохранить"))

        if hasattr(self.voice_widget, 'retranslate_ui'):
            self.voice_widget.retranslate_ui()

    def init_ui(self):
        """Инициализация пользовательского интерфейса."""
        # Макет вкладки
        layout = QVBoxLayout(self)
        
        # Создание группы для голосового ввода
        self.voice_input_group = QGroupBox()
        voice_input_layout = QVBoxLayout(self.voice_input_group)
        
        # Создаем виджет голосовой аннотации
        try:
            # Пытаемся использовать виджет голосовой аннотации
            self.voice_widget = VoiceAnnotationWidget(self.settings_manager)
            self.voice_widget.annotation_ready.connect(self.on_speech_recognized)
            voice_input_layout.addWidget(self.voice_widget)
            logger.info("Успешно добавлен виджет голосовой аннотации")
        except Exception as e:
            # Если не удалось, используем резервный вариант
            logger.error(f"Не удалось создать виджет голосовой аннотации: {e}")
            
            # Создаем стандартный виджет микрофона
            self.voice_widget = MicrophoneControlWidget()
            self.voice_widget.recording_stopped.connect(self.on_recording_stopped)
            voice_input_layout.addWidget(self.voice_widget)
            logger.info("Используется стандартный виджет микрофона")
        
        # Добавляем группу голосового ввода в макет
        layout.addWidget(self.voice_input_group)
        
        # Группа результатов
        self.results_group = QGroupBox()
        results_layout = QVBoxLayout(self.results_group)
        
        # Поле для отображения результатов
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        results_layout.addWidget(self.results_text)
        
        # Кнопки управления результатами
        buttons_layout = QHBoxLayout()
        
        self.clear_results_button = QPushButton()
        self.clear_results_button.clicked.connect(self.clear_results)
        buttons_layout.addWidget(self.clear_results_button)
        
        self.save_results_button = QPushButton()
        self.save_results_button.clicked.connect(self.save_results)
        buttons_layout.addWidget(self.save_results_button)
        
        results_layout.addLayout(buttons_layout)
        
        layout.addWidget(self.results_group)

        self.retranslate_ui()
    
    def set_recognizer(self, recognizer: YandexSpeechRecognizer):
        """
        Установка распознавателя речи.
        
        Args:
            recognizer: Распознаватель речи
        """
        self.recognizer = recognizer
        
        # Если используем виджет голосовой аннотации, передадим ему распознаватель
        if hasattr(self, 'voice_widget') and self.voice_widget and isinstance(self.voice_widget, VoiceAnnotationWidget):
            try:
                # Пытаемся установить распознаватель в виджет голосовой аннотации
                if hasattr(self.voice_widget, 'recognizer'):
                    self.voice_widget.recognizer = recognizer
                    logger.info("Распознаватель установлен в виджет голосовой аннотации")
            except Exception as e:
                logger.error(f"Ошибка при установке распознавателя в виджет голосовой аннотации: {e}")
    
    def on_speech_recognized(self, text: str):
        """
        Обработчик события распознавания речи из виджета голосовой аннотации.
        
        Args:
            text: Распознанный текст
        """
        if not text.strip():
            return
        
        # Добавляем текст в поле результатов
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.results_text.append(f"<b>{self.tr('Распознано в')} {timestamp}:</b>")
        self.results_text.append(f"<pre>{text}</pre>")
        self.results_text.append("<hr>")
        
        # Прокручиваем поле результатов вниз
        self.results_text.verticalScrollBar().setValue(self.results_text.verticalScrollBar().maximum())
    
    def on_recording_stopped(self, file_path: str):
        """
        Обработчик завершения записи с микрофона (для стандартного виджета MicrophoneControlWidget).
        
        Args:
            file_path: Путь к записанному файлу
        """
        if self.recognizer is None:
            QMessageBox.warning(self, self.tr("Ошибка"), self.tr("Сначала настройте API-ключ и параметры распознавания"))
            return
        
        # Распознаем записанный файл
        self.recognize_audio_file(file_path)
    
    def recognize_audio_file(self, file_path: str):
        """
        Распознавание аудиофайла.
        
        Args:
            file_path: Путь к аудиофайлу
        """
        try:
            # Показываем сообщение о начале распознавания
            self.results_text.append(f"<b>{self.tr('Распознавание файла')}: {os.path.basename(file_path)}</b>")
            self.results_text.append(f"<i>{self.tr('Начало')}: {datetime.now().strftime('%H:%M:%S')}</i>")
            QApplication.processEvents()
            
            # Распознаем файл
            self.results_text.append(f"<b>{self.tr('Используемые параметры')}:</b>")
            self.results_text.append(f"<b>{self.tr('Язык')}:</b> {self.recognizer.language}")
            self.results_text.append(f"<b>{self.tr('Модель')}:</b> {self.recognizer.model}")
            self.results_text.append(f"<b>{self.tr('Тип обработки')}:</b> {self.recognizer.processing_type}")
            self.results_text.append(f"<b>{self.tr('Формат аудио')}:</b> {self.recognizer.audio_format}")
            self.results_text.append(f"<b>{self.tr('Частота дискретизации')}:</b> {self.recognizer.sample_rate} {self.tr('Гц')}")
            self.results_text.append("<hr>")
            
            # Добавляем информацию о файле
            file_size = os.path.getsize(file_path)
            self.results_text.append(f"<b>{self.tr('Файл')}:</b> {os.path.basename(file_path)} ({file_size} {self.tr('байт')})")
            
            # Распознаем файл
            logger.info(f"Запуск распознавания файла: {file_path}")
            
            # Обновляем интерфейс во время длительной операции
            QApplication.processEvents()
            
            # Распознаем файл
            result = self.recognizer.recognize_file(file_path)
            
            # Выводим результаты
            if result['success']:
                # Проверяем наличие общего текста
                if 'text' in result and result['text'].strip():
                    self.results_text.append(f"<b>{self.tr('Общий текст')}:</b>")
                    self.results_text.append(f"<pre>{result['text']}</pre>")
                    
                if 'normalized_text' in result and result['normalized_text'].strip():
                    self.results_text.append(f"<b>{self.tr('Общий нормализованный текст')}:</b>")
                    self.results_text.append(f"<pre>{result['normalized_text']}</pre>")
                
                # Выводим результаты по каналам
                if 'results' in result and result['results']:
                    for channel_result in result['results']:
                        self.results_text.append(f"<hr><b>{self.tr('Канал')}: {channel_result['channel']}</b>")
                        
                        raw_text = channel_result.get('raw_text', '')
                        if raw_text and raw_text.strip():
                            self.results_text.append(f"<b>{self.tr('Исходный текст')}:</b>")
                            self.results_text.append(f"<pre>{raw_text}</pre>")
                        
                        normalized_text = channel_result.get('normalized_text', '')
                        if normalized_text and normalized_text.strip():
                            self.results_text.append(f"<b>{self.tr('Нормализованный текст')}:</b>")
                            self.results_text.append(f"<pre>{normalized_text}</pre>")
                        
                        utterances = channel_result.get('utterances', [])
                        if utterances:
                            self.results_text.append(f"<b>{self.tr('Фрагменты речи')}:</b>")
                            for utterance in utterances:
                                self.results_text.append(
                                    f"- {utterance.get('text', '')} "
                                    f"[{utterance.get('start', 0):.3f} - {utterance.get('end', 0):.3f}]"
                                )
                    
                    self.results_text.append(f"<b>{self.tr('Параметры распознавания')}:</b>")
                    self.results_text.append(f"<b>{self.tr('Язык')}:</b> {self.recognizer.language}")
                    self.results_text.append(f"<b>{self.tr('Модель')}:</b> {self.recognizer.model}")
                    self.results_text.append(f"<b>{self.tr('Тип обработки')}:</b> {self.recognizer.processing_type}")
                    self.results_text.append(f"<b>{self.tr('Формат аудио')}:</b> {self.recognizer.audio_format}")
                    self.results_text.append(f"<b>{self.tr('Частота дискретизации')}:</b> {self.recognizer.sample_rate} {self.tr('Гц')}")
            
            else:
                self.results_text.append(f"<span style='color:red'><b>{self.tr('Ошибка')}:</b> {result['error']}</span>")
            
            self.results_text.append(f"<i>{self.tr('Завершено')}: {datetime.now().strftime('%H:%M:%S')}</i><br>")
            
            # Прокручиваем к концу
            self.results_text.verticalScrollBar().setValue(
                self.results_text.verticalScrollBar().maximum()
            )
            
        except Exception as e:
            logger.error(f"Ошибка при распознавании файла: {e}")
            self.results_text.append(f"<span style='color:red'><b>{self.tr('Ошибка')}:</b> {e}</span>")
    
    def clear_results(self):
        """Очистка результатов распознавания."""
        self.results_text.clear()
    
    def save_results(self):
        """Сохранение результатов распознавания в файл."""
        if self.results_text.toPlainText().strip() == "":
            QMessageBox.warning(self, self.tr("Ошибка"), self.tr("Нет результатов для сохранения"))
            return
        
        # Генерируем имя файла
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_path = os.path.join(self.results_dir, f"recognition_results_{timestamp}.txt")
        
        # Открываем диалог сохранения
        file_path, _ = QFileDialog.getSaveFileName(
            self, self.tr("Сохранить результаты"), default_path, self.tr("Текстовые файлы (*.txt)")
        )
        
        if file_path:
            try:
                # Сохраняем результаты
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.results_text.toPlainText())
                
                QMessageBox.information(self, self.tr("Успех"), f"{self.tr('Результаты сохранены в')}:\n{file_path}")
                
            except Exception as e:
                logger.error(f"Ошибка при сохранении результатов: {e}")
                QMessageBox.critical(self, self.tr("Ошибка"), f"{self.tr('Ошибка при сохранении результатов')}: {e}")
