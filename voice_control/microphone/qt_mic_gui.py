"""
Графический интерфейс для управления микрофоном с использованием PySide6.
"""

import os
import sys
import time
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QComboBox, 
                            QProgressBar, QFileDialog, QMessageBox, QGroupBox)
from PySide6.QtCore import Qt, QTimer, Signal, Slot

# Добавляем корневую директорию проекта в sys.path, если она еще не добавлена
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Импортируем наш модуль для захвата аудио
from voice_control.microphone.qt_audio_capture import QtAudioCapture

# Настройка логирования
logger = logging.getLogger(__name__)


class MicrophoneControlWidget(QWidget):
    """
    Виджет для управления микрофоном.
    Включает в себя выбор устройства, кнопки управления и индикатор громкости.
    """
    
    # Сигналы
    recording_started = Signal()  # Сигнал о начале записи
    recording_stopped = Signal(str)  # Сигнал о завершении записи (с путем к файлу)
    
    def __init__(self, parent=None):
        """
        Инициализация виджета управления микрофоном.
        
        Args:
            parent: Родительский виджет (по умолчанию None)
        """
        super().__init__(parent)
        
        # Инициализация компонентов
        self.init_ui()
        
        # Инициализация захвата аудио
        self.audio_capture = QtAudioCapture(self)
        
        # Подключаем сигналы
        self.audio_capture.recording_started.connect(self.on_recording_started)
        self.audio_capture.recording_stopped.connect(self.on_recording_stopped)
        self.audio_capture.volume_changed.connect(self.on_volume_changed)
        
        # Заполняем список устройств
        self.refresh_devices()
        
        # Таймер для обновления времени записи
        self.timer = QTimer(self)
        self.timer.setInterval(100)  # 100 мс
        self.timer.timeout.connect(self.update_recording_time)
        
        # Путь к последнему записанному файлу
        self.last_recording_path = None
        
        # Директория для сохранения записей
        self.recordings_dir = os.path.join(project_root, "recordings")
        os.makedirs(self.recordings_dir, exist_ok=True)
    
    def init_ui(self):
        """Инициализация пользовательского интерфейса."""
        # Главный макет
        main_layout = QVBoxLayout(self)
        
        # Группа для выбора устройства
        device_group = QGroupBox(self.tr("Устройство ввода"))
        device_layout = QHBoxLayout(device_group)
        
        # Выпадающий список устройств
        self.device_combo = QComboBox()
        device_layout.addWidget(QLabel(self.tr("Микрофон:")))
        device_layout.addWidget(self.device_combo, 1)
        
        # Кнопка обновления списка устройств
        self.refresh_button = QPushButton(self.tr("Обновить"))
        self.refresh_button.clicked.connect(self.refresh_devices)
        device_layout.addWidget(self.refresh_button)
        
        main_layout.addWidget(device_group)
        
        # Группа для управления записью
        control_group = QGroupBox(self.tr("Управление записью"))
        control_layout = QVBoxLayout(control_group)
        
        # Индикатор громкости
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel(self.tr("Громкость:")))
        
        self.volume_bar = QProgressBar()
        self.volume_bar.setMinimum(0)
        self.volume_bar.setMaximum(100)
        self.volume_bar.setValue(0)
        volume_layout.addWidget(self.volume_bar)
        
        control_layout.addLayout(volume_layout)
        
        # Время записи
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel(self.tr("Время записи:")))
        
        self.time_label = QLabel(self.tr("00:00.0"))
        time_layout.addWidget(self.time_label)
        time_layout.addStretch()
        
        control_layout.addLayout(time_layout)
        
        # Кнопки управления
        button_layout = QHBoxLayout()
        
        self.record_button = QPushButton(self.tr("Начать запись"))
        self.record_button.clicked.connect(self.toggle_recording)
        button_layout.addWidget(self.record_button)
        
        self.save_button = QPushButton(self.tr("Сохранить запись"))
        self.save_button.clicked.connect(self.save_recording)
        self.save_button.setEnabled(False)
        button_layout.addWidget(self.save_button)
        
        control_layout.addLayout(button_layout)
        
        main_layout.addWidget(control_group)
        
        self.retranslate_ui()
        
    def retranslate_ui(self):
        """Обновляет переводы интерфейса."""
        # Обновление переводов будет выполнено при следующем обновлении UI
        pass
    
    def refresh_devices(self):
        """Обновить список доступных устройств ввода."""
        # Сохраняем текущий выбор
        current_index = self.device_combo.currentIndex()
        
        # Очищаем список
        self.device_combo.clear()
        
        # Получаем список устройств
        devices = self.audio_capture.get_available_devices()
        
        # Заполняем выпадающий список
        for device in devices:
            self.device_combo.addItem(device['name'], device['index'])
        
        # Восстанавливаем выбор, если возможно
        if current_index >= 0 and current_index < self.device_combo.count():
            self.device_combo.setCurrentIndex(current_index)
        elif self.device_combo.count() > 0:
            self.device_combo.setCurrentIndex(0)
            # Устанавливаем устройство
            self.on_device_changed(0)
        
        # Подключаем сигнал изменения выбора
        self.device_combo.currentIndexChanged.connect(self.on_device_changed)
    
    @Slot(int)
    def on_device_changed(self, index: int):
        """
        Обработчик изменения выбранного устройства.
        
        Args:
            index: Индекс выбранного элемента в выпадающем списке
        """
        if index < 0:
            return
        
        # Получаем индекс устройства
        device_index = self.device_combo.currentData()
        
        # Устанавливаем устройство
        if device_index is not None:
            self.audio_capture.set_device(device_index)
    
    def toggle_recording(self):
        """Переключение состояния записи (начать/остановить)."""
        if self.audio_capture.is_recording:
            # Останавливаем запись
            self.audio_capture.stop_recording()
        else:
            # Начинаем запись
            self.audio_capture.start_recording()
    
    @Slot()
    def on_recording_started(self):
        """Обработчик начала записи."""
        # Меняем текст кнопки
        self.record_button.setText(self.tr("Остановить запись"))
        
        # Запускаем таймер
        self.timer.start()
        
        # Отключаем кнопку сохранения
        self.save_button.setEnabled(False)
        
        # Отключаем выбор устройства
        self.device_combo.setEnabled(False)
        self.refresh_button.setEnabled(False)
        
        # Излучаем сигнал
        self.recording_started.emit()
    
    @Slot()
    def on_recording_stopped(self):
        """Обработчик завершения записи."""
        # Меняем текст кнопки
        self.record_button.setText(self.tr("Начать запись"))
        
        # Останавливаем таймер
        self.timer.stop()
        
        # Включаем кнопку сохранения
        self.save_button.setEnabled(True)
        
        # Включаем выбор устройства
        self.device_combo.setEnabled(True)
        self.refresh_button.setEnabled(True)
        
        # Генерируем имя файла для записи
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(self.recordings_dir, f"recording_{timestamp}.wav")
        
        try:
            # Получаем аудиоданные в виде кортежа (raw_data, sample_rate, channels, sample_width)
            logger.info(f"Получение аудиоданных для сохранения в {file_path}")
            audio_data = self.audio_capture.get_recorded_data()
            
            # Распаковываем кортеж с данными и параметрами аудио
            raw_data, sample_rate, channels, sample_width = audio_data
            
            # Проверяем, есть ли данные для записи
            if raw_data and len(raw_data) > 0:
                # Сохраняем WAV-файл с корректными параметрами
                import wave
                
                with wave.open(file_path, 'wb') as wav_file:
                    wav_file.setnchannels(channels)
                    wav_file.setsampwidth(sample_width)
                    wav_file.setframerate(sample_rate)
                    wav_file.writeframes(raw_data)
                
                logger.info(f"Сохранен WAV-файл: {len(raw_data)} байт, {sample_rate} Гц, {channels} канал(ов), {sample_width*8} бит")
            else:
                # Создаем пустой WAV-файл с указанными параметрами
                import wave
                
                with wave.open(file_path, 'wb') as wav_file:
                    wav_file.setnchannels(channels)
                    wav_file.setsampwidth(sample_width)
                    wav_file.setframerate(sample_rate)
                    wav_file.writeframes(b'')
                
                logger.warning(f"Создан пустой WAV-файл - нет аудиоданных")
                
                # Сохраняем путь к последней записи
                self.last_recording_path = file_path
                
                # Излучаем сигнал с путем к записи
                self.recording_stopped.emit(file_path)
                logger.info(f"Излучен сигнал recording_stopped с файлом {file_path}")
        except Exception as e:
            logger.error(f"Ошибка при сохранении записи: {e}")

    
    @Slot(float)
    def on_volume_changed(self, volume: float):
        """
        Обработчик изменения громкости.
        
        Args:
            volume: Уровень громкости (0.0 - 1.0)
        """
        # Обновляем индикатор громкости
        self.volume_bar.setValue(int(volume * 100))
    
    @Slot()
    def update_recording_time(self):
        """Обновление отображаемого времени записи."""
        if not self.audio_capture.is_recording:
            return
        
        # Получаем длительность записи
        duration = self.audio_capture.get_recording_duration()
        
        # Форматируем время (MM:SS.d)
        minutes = int(duration) // 60
        seconds = int(duration) % 60
        deciseconds = int((duration - int(duration)) * 10)
        
        time_str = f"{minutes:02d}:{seconds:02d}.{deciseconds:1d}"
        
        # Обновляем метку времени
        self.time_label.setText(time_str)
    
    def save_recording(self):
        """Сохранить запись в выбранный пользователем файл."""
        if not self.last_recording_path or not os.path.exists(self.last_recording_path):
            QMessageBox.warning(self, "Ошибка", "Нет доступной записи для сохранения")
            return
        
        # Открываем диалог сохранения файла
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить запись", "", "Аудио файлы (*.wav)"
        )
        
        if file_path:
            # Копируем файл
            try:
                import shutil
                shutil.copy2(self.last_recording_path, file_path)
                logger.info(f"Запись сохранена в: {file_path}")
                QMessageBox.information(self, "Успех", f"Запись сохранена в:\n{file_path}")
            except Exception as e:
                logger.error(f"Ошибка при сохранении записи: {e}")
                QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить запись: {e}")


class MicrophoneControlWindow(QMainWindow):
    """Главное окно для управления микрофоном."""
    
    def __init__(self):
        """Инициализация главного окна."""
        super().__init__()
        
        # Настройка окна
        self.setWindowTitle("Управление микрофоном")
        self.setMinimumSize(500, 300)
        
        # Создаем виджет управления микрофоном
        self.mic_widget = MicrophoneControlWidget()
        
        # Устанавливаем центральный виджет
        self.setCentralWidget(self.mic_widget)


# Запуск приложения
def main():
    """Основная функция для запуска приложения."""
    # Настройка логирования через глобальную конфигурацию
    try:
        from logging_config import configure_logging
        configure_logging()
    except ImportError:
        # Fallback на базовую настройку, если глобальная конфигурация недоступна
        logging.basicConfig(level=logging.INFO)
    
    # Создаем приложение Qt
    app = QApplication(sys.argv)
    
    # Устанавливаем стиль
    app.setStyle("Fusion")
    
    # Создаем и показываем окно
    window = MicrophoneControlWindow()
    window.show()
    
    # Запускаем цикл обработки событий
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
