#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Модуль с реализацией QRunnable для захвата аудио в отдельном потоке.
Позволяет выполнять захват аудио без блокировки основного потока GUI.
"""

import logging
import time
import numpy as np
from typing import Optional, Callable, Dict, Any
import threading

from PySide6.QtCore import QRunnable, QObject, Signal, QThread

from voice_control.microphone.audio_buffer import CircularAudioBuffer
import pyaudio

# Настройка логгера
logger = logging.getLogger(__name__)

class AudioCaptureSignals(QObject):
    """Класс с сигналами для QRunnable, т.к. сам QRunnable не может иметь сигналы"""
    
    # Сигналы
    started = Signal()
    stopped = Signal()
    error = Signal(str)
    volume_changed = Signal(float)  # Сигнал об изменении громкости (0.0 - 1.0)
    audio_buffer_updated = Signal(object)  # Сигнал с новыми аудио данными

class AudioCaptureRunnable(QRunnable):
    """
    Реализация захвата аудио как QRunnable для использования в QThreadPool.
    
    Преимущества перед QThread:
    - Нет необходимости создавать отдельный поток для каждого захвата
    - Задачи автоматически распределяются по доступным потокам
    - Меньше накладных расходов и более эффективное использование ресурсов
    """
    
    def __init__(self, 
                 format: int = pyaudio.paInt16,
                 channels: int = 1,
                 rate: int = 16000,
                 chunk: int = 1024,
                 max_buffer_seconds: float = 60.0):
        """
        Инициализация захвата аудио
        
        Args:
            format: Формат аудио (по умолчанию paInt16)
            channels: Количество каналов (по умолчанию 1 - моно)
            rate: Частота дискретизации (по умолчанию 16кГц)
            chunk: Размер буфера для считывания (по умолчанию 1024)
            max_buffer_seconds: Максимальная длительность буфера в секундах
        """
        super().__init__()
        
        # Параметры аудио - фиксируем формат для распознавания
        self.format = pyaudio.paInt16  # Фиксируем на 16 бит
        self.channels = 1              # Фиксируем на моно
        self.rate = 16000              # Фиксируем на 16 кГц
        self.chunk = chunk
        self.sample_width = 2          # Ширина сэмпла в байтах для paInt16
        
        # Сигналы
        self.signals = AudioCaptureSignals()
        
        # Флаги состояния и блокировка
        self._lock = threading.Lock()
        self._stop_requested = False
        self._is_running = False
        
        # Кэшированные объекты
        self._pyaudio = None
        self._stream = None
        
        # Список для хранения целых фреймов аудио
        max_frames = int(max_buffer_seconds * self.rate / self.chunk) + 1
        self.frames = []
        
        # Кольцевой буфер для аудиоданных (сохраняем для обратной совместимости)
        self.audio_buffer = CircularAudioBuffer(
            max_seconds=max_buffer_seconds,
            sample_rate=self.rate,
            channels=self.channels,
            sample_width=self.sample_width
        )
        
        # Метаданные для захвата
        self.metadata = {
            "format": self.format,
            "channels": self.channels,
            "rate": self.rate,
            "chunk": self.chunk,
        }
        
        # Замеры громкости
        self.volume_measure_interval = 0.1  # Секунды между замерами громкости
        self.last_volume_time = 0
        self.current_volume = 0.0
        
        # Счетчики для оптимизации логирования
        self._audio_data_call_count = 0
        self._total_data_received = 0
    
    def _on_audio_data(self, in_data, frame_count, time_info, status):
        """
        Коллбэк-функция для обработки аудиоданных в реальном времени
        
        Args:
            in_data: Входные данные с микрофона (bytes)
            frame_count: Количество фреймов
            time_info: Временная информация
            status: Статус потока
        
        Returns:
            Кортеж (None, pyaudio.paContinue) для продолжения записи
        """
        # Если объект сигналов уже обнулен, или runnable не активен, или запрошена остановка - выходим.
        if not hasattr(self, 'signals') or self.signals is None or not self._is_running or self._stop_requested:
            logger.debug(f"_on_audio_data: Выход из коллбэка. signals={hasattr(self, 'signals') and self.signals is not None}, _is_running={self._is_running}, _stop_requested={self._stop_requested}")
            return (None, pyaudio.paComplete)
            
        try:
            # Оптимизированное логирование с счетчиком
            data_size = len(in_data) if in_data else 0
            self._audio_data_call_count += 1
            self._total_data_received += data_size
            
            # Логируем каждые 50 вызовов или при пустых данных
            if self._audio_data_call_count % 50 == 0 or data_size == 0:
                logger.debug(f"_on_audio_data: Вызов #{self._audio_data_call_count}, данные {data_size} байт, общий объем {self._total_data_received} байт, frame_count={frame_count}")
            
            # Добавляем данные в список фреймов и буфер
            self.frames.append(in_data)
            self.audio_buffer.add_bytes(in_data)
            
            # Логируем состояние буферов только каждые 50 вызовов
            if self._audio_data_call_count % 50 == 0:
                frames_count = len(self.frames)
                buffer_size = self.audio_buffer.get_size() if hasattr(self.audio_buffer, 'get_size') else 'unknown'
                logger.debug(f"_on_audio_data: frames={frames_count}, buffer размер={buffer_size}")
            
            # Измеряем громкость звука
            self._calculate_volume(in_data)
            
            # Повторная проверка состояния перед эмиссией сигналов
            if not self.signals or not self._is_running or self._stop_requested:
                return (None, pyaudio.paComplete)

            current_time = time.time()
            if current_time - self.last_volume_time >= self.volume_measure_interval:
                self.last_volume_time = current_time
                if self.signals: # Дополнительная проверка перед непосредственным вызовом emit
                    try:
                        self.signals.volume_changed.emit(self.current_volume)
                    except RuntimeError:
                        logger.warning("AudioCaptureSignals (C++) удален при попытке emit volume_changed. Обнуляем self.signals.")
                        self.signals = None # Критически важно для предотвращения дальнейших ошибок
                        self._is_running = False 
                        return (None, pyaudio.paComplete)
            
            # Еще одна проверка перед следующей эмиссией
            if not self.signals or not self._is_running or self._stop_requested:
                return (None, pyaudio.paComplete)

            if self.signals: # Дополнительная проверка
                try:
                    self.signals.audio_buffer_updated.emit(self.audio_buffer)
                except RuntimeError:
                    logger.warning("AudioCaptureSignals (C++) удален при попытке emit audio_buffer_updated. Обнуляем self.signals.")
                    self.signals = None # Критически важно
                    self._is_running = False
                    return (None, pyaudio.paComplete)
            
        except Exception as e:
            # Логируем ошибку только если мы не в процессе остановки и signals еще существует
            if hasattr(self, 'signals') and self.signals and self._is_running and not self._stop_requested:
                logger.error(f"Ошибка в обработчике аудио: {e}")
        
        # Финальная проверка перед возвратом
        if not hasattr(self, 'signals') or self.signals is None or not self._is_running or self._stop_requested:
            return (None, pyaudio.paComplete)
        else:
            return (None, pyaudio.paContinue)
    
    def _calculate_volume(self, audio_data):
        """
        Рассчитывает уровень громкости из аудиоданных
        
        Args:
            audio_data: Байтовые аудиоданные (bytes)
        """
        try:
            # Преобразование байтов в numpy массив
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Расчет уровня громкости (RMS)
            if len(audio_array) > 0:
                # Преобразование в диапазон от -1 до 1
                normalized = audio_array.astype(np.float32) / 32768.0
                
                # Расчет среднеквадратичного значения
                rms = np.sqrt(np.mean(normalized**2))
                
                # Нормализация в диапазон 0-1 с логарифмической шкалой
                if rms > 0:
                    log_volume = np.log10(rms * 9 + 1)  # Масштабирование для лучшего отображения
                    self.current_volume = min(1.0, max(0.0, log_volume))
                else:
                    self.current_volume = 0.0
        except Exception as e:
            logger.error(f"Ошибка при расчете громкости: {e}")
    
    def run(self):
        """Запуск захвата аудио в отдельном потоке"""
        try:
            # Очистка списка фреймов
            logger.info(f"[ДИАГНОСТИКА] Запуск AudioCaptureRunnable. Очищаем frames (было {len(getattr(self, 'frames', []))} фреймов)")
            self.frames = []
            self._audio_data_call_count = 0  # Сброс счетчика
            self._total_data_received = 0    # Сброс общего объема
            self._is_running = True # Устанавливаем флаг активности
            self._stop_requested = False # Сбрасываем флаг запроса на остановку
            
            # Инициализация PyAudio
            self._initialize_audio()
            
            # Запуск потока аудио через callback
            self._start_audio_stream_with_callback()
            
            if self.signals: # Проверяем перед emit
                self.signals.started.emit()
            
            while self._is_running:
                with self._lock:
                    if self._stop_requested:
                        self._is_running = False
                        break 
                QThread.msleep(50)
            
            self._is_running = False 
            
            # Диагностика перед остановкой
            frames_count = len(self.frames) if hasattr(self, 'frames') else 0
            buffer_size = self.audio_buffer.get_size() if hasattr(self.audio_buffer, 'get_size') else 'unknown'
            logger.info(f"[ДИАГНОСТИКА] Остановка AudioCaptureRunnable. Собрано {frames_count} фреймов, размер буфера: {buffer_size}, всего данных: {self._total_data_received} байт")
            
            self._stop_audio_stream() 
            
            if self.signals: # Проверяем перед emit
                try:
                    self.signals.stopped.emit()
                except RuntimeError:
                    logger.warning("AudioCaptureSignals (C++) удален перед signals.stopped.")
            
        except Exception as e:
            logger.error(f"Ошибка в потоке захвата аудио: {e}", exc_info=True)
            self._is_running = False 
            if self.signals: # Проверяем перед emit
                try:
                    self.signals.error.emit(str(e))
                except RuntimeError:
                     logger.warning(f"AudioCaptureSignals (C++) удален перед signals.error для '{e}'.")
        finally:
            self._is_running = False
            self._stop_requested = True # Убеждаемся, что остановка запрошена для любых оставшихся коллбэков
            # Критически важно: обнуляем ссылку на объект сигналов.
            # Это предотвратит использование self.signals в _on_audio_data, если коллбэк вызван после выхода из run().
            if hasattr(self, 'signals'): # Проверяем, что атрибут вообще существует
                self.signals = None 
    
    def stop(self):
        """Запрос на остановку захвата аудио."""
        with self._lock: # Потокобезопасная установка флага
            self._stop_requested = True
        logger.info("Запрос на остановку AudioCaptureRunnable получен.")

    def _initialize_audio(self):
        """Инициализация PyAudio и аудиопотока."""
        try:
            self._pyaudio = pyaudio.PyAudio()
        except Exception as e:
            logger.error(f"Не удалось инициализировать PyAudio: {e}")
            raise RuntimeError(f"Не удалось инициализировать PyAudio: {e}")
    
    def _start_audio_stream(self):
        """Запуск потока для захвата аудио (блокирующий режим)"""
        try:
            self._stream = self._pyaudio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk
            )
        except Exception as e:
            logger.error(f"Не удалось открыть аудиопоток: {e}")
            raise RuntimeError(f"Не удалось открыть аудиопоток: {e}")
    
    def _start_audio_stream_with_callback(self):
        """Запуск потока аудио с использованием callback-функции"""
        try:
            logger.info("Attempting to open audio stream with callback.")
            if self._pyaudio is None:
                logger.error("PyAudio instance (self._pyaudio) is None before opening stream. Attempting to initialize.")
                self._initialize_audio() # Попытка инициализации, если еще не было
                if self._pyaudio is None:
                    logger.error("PyAudio instance is still None after re-attempting initialization. Aborting stream opening.")
                    raise RuntimeError("PyAudio not initialized.")

            logger.info("Available input audio devices:")
            try:
                default_input_device_index = self._pyaudio.get_default_input_device_info()['index']
                logger.info(f"Default input device index: {default_input_device_index}")
                for i in range(self._pyaudio.get_device_count()):
                    dev_info = self._pyaudio.get_device_info_by_index(i)
                    # if dev_info.get('maxInputChannels') > 0:
                        # logger.info(f"  Device {i}: {dev_info.get('name')}, "
                        #             f"Max Input Channels: {dev_info.get('maxInputChannels')}, "
                        #             f"Default Sample Rate: {dev_info.get('defaultSampleRate')}, "
                        #             f"Host API: {self._pyaudio.get_host_api_info_by_index(dev_info.get('hostApi'))['name']}")
            except Exception as e_dev_log:
                logger.error(f"Error logging audio devices: {e_dev_log}")

            logger.info(f"Opening stream with parameters: format={self.format}, channels={self.channels}, "
                        f"rate={self.rate}, chunk_size={self.chunk}, input=True, input_device_index=None (default)")
            
            # Используем callback-функцию для обработки аудиоданных в реальном времени
            self._stream = self._pyaudio.open(
                format=self.format,          # Фиксированный формат 16-бит
                channels=self.channels,      # Фиксированно 1 канал (моно)
                rate=self.rate,              # Фиксированная частота 16кГц
                input=True,                 # Входной поток (захват с микрофона)
                frames_per_buffer=self.chunk,# Размер буфера
                stream_callback=self._on_audio_data  # Коллбэк-функция
            )
            logger.info(f"Запущен поток аудио с параметрами: {self.rate} Гц, {self.channels} канал(ов), формат {self.format}")
            # Запускаем поток
            self._stream.start_stream()
        except Exception as e:
            logger.error(f"Не удалось открыть аудиопоток с callback: {e}")
            raise RuntimeError(f"Не удалось открыть аудиопоток с callback: {e}")
    
    def _stop_audio_stream(self):
        """Остановка и очистка потока аудио"""
        if self._stream:
            try:
                self._stream.stop_stream()
                self._stream.close()
                self._stream = None
            except Exception as e:
                logger.warning(f"Ошибка при закрытии аудиопотока: {e}")
        
        if self._pyaudio:
            try:
                self._pyaudio.terminate()
                self._pyaudio = None
            except Exception as e:
                logger.warning(f"Ошибка при завершении работы PyAudio: {e}")
    
    def _measure_and_emit_volume(self, audio_data):
        """Измерение громкости и отправка сигнала"""
        try:
            # Преобразование байтов в numpy массив
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Расчет уровня громкости (RMS)
            if len(audio_array) > 0:
                # Преобразование в диапазон от -1 до 1
                normalized = audio_array.astype(np.float32) / 32768.0
                
                # Расчет среднеквадратичного значения
                rms = np.sqrt(np.mean(normalized**2))
                
                # Нормализация в диапазон 0-1 с логарифмической шкалой
                # (более естественно для восприятия человеком)
                if rms > 0:
                    log_volume = np.log10(rms * 9 + 1)  # Масштабирование для лучшего отображения
                    volume_level = min(1.0, max(0.0, log_volume))
                else:
                    volume_level = 0.0
                
                # Отправка сигнала с уровнем громкости
                self.signals.volume_changed.emit(volume_level)
        except Exception as e:
            logger.warning(f"Ошибка при измерении громкости: {e}")
            # Не пробрасываем исключение дальше, чтобы не прерывать запись
