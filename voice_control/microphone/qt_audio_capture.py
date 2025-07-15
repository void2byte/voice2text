"""
Модуль для захвата аудио с микрофона с использованием PySide6.
Реализация класса для записи аудио с использованием PyAudio в Qt-приложении

Оптимизированная версия, использующая QThreadPool вместо создания
QThread для каждой записи, что снижает накладные расходы и увеличивает производительность.
"""

import os
import sys
import time
import wave
import logging
import numpy as np
import pyaudio
from typing import Optional, List, Dict, Any, Tuple, BinaryIO

from PySide6.QtCore import QObject, Signal, Slot, QTimer, QThreadPool

# Импортируем новые оптимизированные компоненты
from voice_control.microphone.qt_audio_runnable import AudioCaptureRunnable

# Настройка логирования
logger = logging.getLogger(__name__)


class QtAudioCapture(QObject):
    """
    Класс для захвата аудио с микрофона с использованием QThreadPool.
    
    Оптимизированная версия, использующая AudioCaptureRunnable вместо
    прямого обращения к QAudioSource для снижения нагрузки на основной поток GUI.
    
    Позволяет:
    - Получать список доступных устройств ввода аудио
    - Выбирать устройство ввода
    - Записывать аудио с микрофона
    - Получать уровень громкости звука
    - Сохранять записанное аудио в WAV-файл
    """
    
    # Сигналы
    recording_started = Signal()  # Сигнал о начале записи
    recording_stopped = Signal()  # Сигнал о завершении записи
    volume_changed = Signal(float)  # Сигнал об изменении громкости (0.0 - 1.0)
    
    def __init__(self, parent=None):
        """
        Инициализация объекта захвата аудио.
        
        Args:
            parent: Родительский объект Qt (по умолчанию None)
        """
        super().__init__(parent)
        
        # Инициализация параметров
        self.current_device_index = 0
        self.available_devices = []
        self.is_recording = False
        self.start_time = 0
        
        # Настройки формата аудио
        self.sample_rate = 16000  # Частота дискретизации (Гц) - снижена для лучшей работы с распознаванием речи
        self.sample_size = 16     # Размер сэмпла (бит)
        self.channels = 1         # Количество каналов (1 - моно)
        self.chunk_size = 1024    # Размер чанка для чтения
        
        # Объект для записи аудио и пул потоков
        self.audio_capture_runnable = None
        self.thread_pool = QThreadPool.globalInstance()
        
        # Кэшированные данные последней записи
        self._cached_audio_data = b''
        self._cached_metadata = (16000, 1, 2)  # rate, channels, sample_width
        
        # Получаем максимальное количество потоков и резервируем доп. поток для UI
        max_threads = max(2, self.thread_pool.maxThreadCount())
        logger.debug(f"Доступно потоков в пуле: {max_threads}")
        
        # Инициализация устройств ввода
        self._init_audio_devices()
    
    def _init_audio_devices(self):
        """Инициализация устройств ввода аудио."""
        try:
            # Используем PyAudio для получения списка устройств
            p = pyaudio.PyAudio()
            
            # Получаем список устройств
            self.available_devices = []
            device_count = p.get_device_count()
            
            for i in range(device_count):
                try:
                    device_info = p.get_device_info_by_index(i)
                    # Фильтруем только устройства ввода
                    if device_info.get('maxInputChannels', 0) > 0:
                        self.available_devices.append({
                            'index': i,
                            'name': device_info.get('name', f'Устройство {i}'),
                            'channels': device_info.get('maxInputChannels', 1),
                            'sample_rate': int(device_info.get('defaultSampleRate', 44100))
                        })
                        #logger.info(f"Найдено устройство ввода: {device_info.get('name')}")
                except Exception as e:
                    logger.warning(f"Ошибка при получении информации об устройстве {i}: {e}")
            
            # Если есть доступные устройства, выбираем первое
            if self.available_devices:
                self.set_device(self.available_devices[0]['index'])
            else:
                logger.warning("Нет доступных устройств ввода аудио")
                
            # Освобождаем ресурсы
            p.terminate()
            
        except Exception as e:
            logger.error(f"Ошибка при инициализации аудио: {e}")
    
    def get_available_devices(self) -> List[Dict[str, Any]]:
        """
        Получить список доступных устройств ввода аудио.
        
        Returns:
            Список словарей с информацией об устройствах:
            [{'index': int, 'name': str, 'channels': int, 'sample_rate': int}, ...]
        """
        # Если устройства еще не инициализированы, инициализируем их
        if not self.available_devices:
            self._init_audio_devices()
            
        return self.available_devices
    
    def set_device(self, device_index: int) -> bool:
        """
        Установить устройство ввода по индексу.
        
        Args:
            device_index: Индекс устройства 
            
        Returns:
            True, если устройство успешно установлено, иначе False
        """
        # Находим устройство по индексу
        device = None
        for dev in self.available_devices:
            if dev['index'] == device_index:
                device = dev
                break
        
        if not device:
            logger.error(f"Устройство с индексом {device_index} не найдено")
            return False
        
        # Сохраняем индекс текущего устройства
        self.current_device_index = device_index
        logger.info(f"Выбрано устройство ввода: {device['name']}")
        
        # Перезапускаем запись, если она была активна
        was_recording = self.is_recording
        if was_recording:
            self.stop_recording()
            
        # Применяем настройки устройства
        self.channels = min(device.get('channels', 1), 1)  # Ограничиваем до 1 канала для распознавания речи
        
        # Если нужно, возобновляем запись
        if was_recording:
            self.start_recording()
            
        return True
    
    def start_recording(self) -> bool:
        """
        Начать запись аудио с использованием QRunnable в пуле потоков.
        
        Returns:
            True, если запись успешно начата, иначе False
        """
        if self.is_recording:
            logger.warning("Запись уже идет")
            return False
        
        try:
            # Принудительно очищаем предыдущий объект записи для предотвращения
            # накопления данных от предыдущих записей
            if self.audio_capture_runnable:
                self.audio_capture_runnable = None
                logger.debug("Предыдущий объект AudioCaptureRunnable очищен")
            
            # Создаем новый объект для записи аудио в отдельном потоке
            self.audio_capture_runnable = AudioCaptureRunnable(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                chunk=self.chunk_size,
                max_buffer_seconds=60.0  # Максимальная длительность записи
            )
            
            # Подключаем сигналы
            self.audio_capture_runnable.signals.started.connect(self._on_recording_started)
            self.audio_capture_runnable.signals.stopped.connect(self._on_recording_stopped)
            self.audio_capture_runnable.signals.error.connect(self._on_recording_error)
            self.audio_capture_runnable.signals.volume_changed.connect(self.volume_changed)
            
            # Запускаем задачу в пуле потоков
            self.thread_pool.start(self.audio_capture_runnable)
            
            # Отмечаем начало записи
            self.is_recording = True
            self.start_time = time.time()
            logger.info("Запись начата в пуле потоков")
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при начале записи: {e}")
            return False
    
    @Slot()
    def _on_recording_started(self):
        """Обработчик сигнала о начале записи"""
        logger.debug("Получен сигнал: запись началась")
        self.recording_started.emit()
    
    @Slot()
    def _on_recording_stopped(self):
        """Обработчик сигнала о завершении записи"""
        logger.debug("Получен сигнал: запись завершена")
        self.is_recording = False
        self.recording_stopped.emit()
    
    @Slot(str)
    def _on_recording_error(self, error_message):
        """Обработчик сигнала об ошибке записи"""
        logger.error(f"[ДИАГНОСТИКА] Ошибка записи аудио: {error_message}")
        
        # Логируем состояние перед очисткой
        if self.audio_capture_runnable:
            frames_count = len(getattr(self.audio_capture_runnable, 'frames', [])) 
            buffer_exists = hasattr(self.audio_capture_runnable, 'audio_buffer') and self.audio_capture_runnable.audio_buffer is not None
            logger.warning(f"[ДИАГНОСТИКА] Перед очисткой runnable из-за ошибки: frames={frames_count}, buffer_exists={buffer_exists}")
        
        self.is_recording = False
        # Очищаем объект записи при ошибке
        logger.warning(f"[ДИАГНОСТИКА] Очищаем audio_capture_runnable из-за ошибки: {error_message}")
        self.audio_capture_runnable = None
        self.recording_stopped.emit()
    
    def stop_recording(self) -> bool:
        """
        Остановить запись аудио.
        
        Returns:
            True, если запись успешно остановлена, иначе False
        """
        if not self.is_recording:
            logger.warning("[ДИАГНОСТИКА] Запись не идет")
            return False
        
        try:
            # Останавливаем запись в потоке
            if self.audio_capture_runnable:
                # Логируем состояние перед остановкой
                frames_count = len(getattr(self.audio_capture_runnable, 'frames', []))
                buffer_exists = hasattr(self.audio_capture_runnable, 'audio_buffer') and self.audio_capture_runnable.audio_buffer is not None
                runnable_running = getattr(self.audio_capture_runnable, '_is_running', 'неизвестно')
                logger.info(f"[ДИАГНОСТИКА] Перед остановкой: frames={frames_count}, buffer_exists={buffer_exists}, _is_running={runnable_running}")
                
                self.audio_capture_runnable.stop()
                logger.info(f"[ДИАГНОСТИКА] Вызван stop() для runnable")
                
                # Вычисляем длительность записи
                duration = time.time() - self.start_time
                logger.info(f"[ДИАГНОСТИКА] Запрошена остановка записи, длительность: {duration:.2f} сек")
                
                # Логируем состояние после остановки, но перед очисткой
                frames_count_after = len(getattr(self.audio_capture_runnable, 'frames', []))
                logger.info(f"[ДИАГНОСТИКА] После остановки, перед очисткой: frames={frames_count_after}")
                
                # Кэшируем данные перед очисткой runnable
                self._cache_audio_data()
                
                # ПРИЧИНА ОЧИСТКИ runnable:
                # 1. Предотвращение накопления данных между записями
                # 2. Освобождение ресурсов (PyAudio stream, буферы)
                # 3. Гарантия чистого состояния для следующей записи
                # 4. Избежание утечек памяти при многократных записях
                logger.warning(f"[ДИАГНОСТИКА] Очищаем audio_capture_runnable после нормальной остановки (освобождение ресурсов)")
                self.audio_capture_runnable = None
                logger.debug("[ДИАГНОСТИКА] Объект AudioCaptureRunnable очищен после остановки")
                
                return True
            else:
                logger.error("[ДИАГНОСТИКА] Объект записи не инициализирован")
                logger.warning(f"[ДИАГНОСТИКА] audio_capture_runnable уже None при вызове stop_recording")
                self.is_recording = False
                self.recording_stopped.emit()
                return False
            
        except Exception as e:
            logger.error(f"[ДИАГНОСТИКА] Ошибка при остановке записи: {e}")
            self.is_recording = False
            # Очищаем объект записи при ошибке остановки
            self.audio_capture_runnable = None
            self.recording_stopped.emit()
            return False
    
    def _cache_audio_data(self):
        """Кэширует аудиоданные из runnable перед его очисткой"""
        if not self.audio_capture_runnable:
            logger.warning("[ДИАГНОСТИКА] Нет runnable для кэширования данных")
            return
            
        try:
            # Получаем параметры аудио
            rate = self.audio_capture_runnable.rate
            channels = self.audio_capture_runnable.channels
            sample_width = self.audio_capture_runnable.sample_width
            self._cached_metadata = (rate, channels, sample_width)
            
            # Пробуем получить данные из frames
            if hasattr(self.audio_capture_runnable, 'frames') and self.audio_capture_runnable.frames:
                frames_count = len(self.audio_capture_runnable.frames)
                self._cached_audio_data = b''.join(self.audio_capture_runnable.frames)
                logger.info(f"[ДИАГНОСТИКА] Кэшированы данные из {frames_count} фреймов, размер: {len(self._cached_audio_data)} байт")
            # Если frames пустой, пробуем буфер
            elif hasattr(self.audio_capture_runnable, 'audio_buffer') and self.audio_capture_runnable.audio_buffer:
                buffer_data = self.audio_capture_runnable.audio_buffer.get_all_bytes()
                self._cached_audio_data = buffer_data
                logger.info(f"[ДИАГНОСТИКА] Кэшированы данные из буфера, размер: {len(self._cached_audio_data)} байт")
            else:
                self._cached_audio_data = b''
                logger.warning("[ДИАГНОСТИКА] Нет данных для кэширования")
                
        except Exception as e:
            logger.error(f"[ДИАГНОСТИКА] Ошибка при кэшировании данных: {e}")
            self._cached_audio_data = b''
    
    def get_recorded_data(self) -> tuple:
        """
        Получить записанные аудиоданные с метаданными о формате.
        
        Returns:
            tuple: Кортеж (raw_data, sample_rate, channels, sample_width) с аудиоданными и их параметрами:
                raw_data (bytes): Сырые байты аудиозаписи
                sample_rate (int): Частота дискретизации в Гц
                channels (int): Количество каналов
                sample_width (int): Ширина сэмпла в байтах (2 для int16)
        """
        logger.debug(f"[ДИАГНОСТИКА] get_recorded_data вызван. audio_capture_runnable: {self.audio_capture_runnable is not None}")
        
        # Если runnable еще существует, получаем данные напрямую
        if self.audio_capture_runnable:
            logger.debug("[ДИАГНОСТИКА] Получаем данные напрямую из runnable")
            return self._get_data_from_runnable()
        
        # Если runnable очищен, используем кэшированные данные
        logger.info(f"[ДИАГНОСТИКА] Используем кэшированные данные, размер: {len(self._cached_audio_data)} байт")
        rate, channels, sample_width = self._cached_metadata
        return (self._cached_audio_data, rate, channels, sample_width)
    
    def _get_data_from_runnable(self) -> tuple:
        """Получает данные напрямую из runnable"""
        if not self.audio_capture_runnable:
            logger.warning("[ДИАГНОСТИКА] Объект AudioCaptureRunnable отсутствует, возвращаем пустые данные")
            return (b'', 16000, 1, 2)
        
        # Получаем параметры аудио
        rate = self.audio_capture_runnable.rate
        channels = self.audio_capture_runnable.channels
        sample_width = self.audio_capture_runnable.sample_width
        
        # Пробуем получить данные из frames
        if hasattr(self.audio_capture_runnable, 'frames') and self.audio_capture_runnable.frames:
            frames_count = len(self.audio_capture_runnable.frames)
            logger.info(f"[ДИАГНОСТИКА] Получаем данные из {frames_count} фреймов")
            raw_data = b''.join(self.audio_capture_runnable.frames)
            logger.info(f"[ДИАГНОСТИКА] Размер данных из frames: {len(raw_data)} байт")
            return (raw_data, rate, channels, sample_width)
        
        # Если frames пустой или отсутствует, пробуем буфер
        if hasattr(self.audio_capture_runnable, 'audio_buffer') and self.audio_capture_runnable.audio_buffer:
            logger.info("[ДИАГНОСТИКА] frames пустой/отсутствует, пробуем получить данные из audio_buffer")
            buffer_data = self.audio_capture_runnable.audio_buffer.get_all_bytes()
            logger.info(f"[ДИАГНОСТИКА] Размер данных из буфера: {len(buffer_data)} байт")
            return (buffer_data, rate, channels, sample_width)
        
        # Если оба источника недоступны
        logger.warning("[ДИАГНОСТИКА] Ни frames, ни audio_buffer не содержат данных")
        logger.warning(f"[ДИАГНОСТИКА] frames доступен: {hasattr(self.audio_capture_runnable, 'frames')}")
        logger.warning(f"[ДИАГНОСТИКА] audio_buffer доступен: {hasattr(self.audio_capture_runnable, 'audio_buffer')}")
        
        if hasattr(self.audio_capture_runnable, 'frames'):
            logger.warning(f"[ДИАГНОСТИКА] frames пустой: {len(self.audio_capture_runnable.frames) == 0}")
        if hasattr(self.audio_capture_runnable, 'audio_buffer'):
            logger.warning(f"[ДИАГНОСТИКА] audio_buffer пустой: {self.audio_capture_runnable.audio_buffer is None}")
        
        return (b'', rate, channels, sample_width)
    
    def save_to_wav(self, file_path: str) -> bool:
        """
        Сохранить записанные аудиоданные в WAV-файл.
        
        Args:
            file_path: Путь к файлу для сохранения
            
        Returns:
            True, если файл успешно сохранен, иначе False
        """
        # Получаем записанные данные
        audio_data = self.get_recorded_data()
        
        if not audio_data:
            logger.warning("Нет данных для сохранения")
            return False
        
        try:
            # Создаем директорию, если нужно
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            # Открываем файл для записи
            with wave.open(file_path, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.sample_size // 8)  # Переводим биты в байты
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_data)
                
            logger.info(f"Аудио сохранено в файл: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении в WAV: {e}")
            return False
    
    def get_recording_duration(self) -> float:
        """
        Получить текущую длительность записи в секундах.
        
        Returns:
            Длительность записи в секундах или 0, если запись не идет
        """
        if not self.is_recording:
            return 0.0
        
        return time.time() - self.start_time
    
    def get_last_seconds(self, seconds: float) -> bytearray:
        """
        Получить последние N секунд записи.
        
        Args:
            seconds: Количество секунд для получения
            
        Returns:
            Последние N секунд записи в виде bytearray
        """
        if not self.audio_capture_runnable or not self.is_recording:
            return bytearray()
        
        # Получаем данные из буфера аудио
        return bytearray(self.audio_capture_runnable.audio_buffer.get_last_seconds(seconds))


# Пример использования
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    
    # Создаем приложение Qt
    app = QApplication(sys.argv)
    
    # Настройка логирования через глобальную конфигурацию
    try:
        from logging_config import configure_logging
        configure_logging()
    except ImportError:
        # Fallback на базовую настройку, если глобальная конфигурация недоступна
        logging.basicConfig(level=logging.INFO)
    
    # Создаем объект для захвата аудио
    audio_capture = QtAudioCapture()
    
    # Получаем список доступных устройств
    devices = audio_capture.get_available_devices()
    for device in devices:
        print(f"Индекс: {device['index']}, Имя: {device['name']}")
    
    # Выбираем первое устройство
    if devices:
        audio_capture.set_device(devices[0]['index'])
    
    # Начинаем запись
    audio_capture.start_recording()
    
    # Ждем 5 секунд
    time.sleep(5)
    
    # Останавливаем запись
    audio_capture.stop_recording()
    
    # Выходим из приложения
    sys.exit(0)
