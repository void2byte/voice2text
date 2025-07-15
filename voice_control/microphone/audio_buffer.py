#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Модуль с кольцевым буфером для аудиоданных.
Обеспечивает эффективное хранение и обработку аудиопотока в реальном времени.
"""

import logging
from collections import deque
import numpy as np
from typing import Optional, Union, Deque

# Настройка логгера
logger = logging.getLogger(__name__)

class CircularAudioBuffer:
    """
    Кольцевой буфер для эффективного хранения и обработки аудиоданных.
    
    Использует deque с фиксированным максимальным размером для автоматического
    удаления старых данных при добавлении новых, без дополнительного копирования.
    """
    
    def __init__(self, max_seconds: float = 60.0, sample_rate: int = 16000, 
                channels: int = 1, sample_width: int = 2):
        """
        Инициализация кольцевого буфера аудиоданных.
        
        Args:
            max_seconds (float): Максимальная длительность аудио в секундах.
            sample_rate (int): Частота дискретизации в Гц.
            channels (int): Количество аудиоканалов.
            sample_width (int): Ширина сэмпла в байтах (1, 2, 4 и т.д.).
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.sample_width = sample_width
        
        # Вычисляем максимальный размер буфера в байтах
        bytes_per_second = sample_rate * channels * sample_width
        max_size = int(max_seconds * bytes_per_second)
        
        # Создаём кольцевой буфер фиксированного размера
        # Используем Union[bytes, int] для поддержки разных типов данных
        self.buffer: Deque[Union[bytes, bytearray, int]] = deque(maxlen=max_size)
        
        # Общее количество добавленных байтов (для отслеживания позиции)
        self.total_bytes_added = 0
        
        logger.debug(f"Создан кольцевой аудиобуфер размером {max_size} байт "
                    f"({max_seconds:.1f} сек, {sample_rate} Гц, {channels} канал(ов), "
                    f"{sample_width} байт/сэмпл)")
    
    def add_bytes(self, audio_data: bytes) -> int:
        """
        Добавляет бинарные аудиоданные в буфер.
        
        Args:
            audio_data (bytes): Бинарные аудиоданные для добавления.
            
        Returns:
            int: Количество добавленных байтов.
        """
        # Счетчик для группировки логов (статическая переменная)
        if not hasattr(self, '_add_bytes_call_count'):
            self._add_bytes_call_count = 0
            self._add_bytes_total_size = 0
        
        self._add_bytes_call_count += 1
        data_size = len(audio_data) if audio_data else 0
        self._add_bytes_total_size += data_size
        
        # Логируем только каждые 50 вызовов или при пустых данных
        if not audio_data or self._add_bytes_call_count % 50 == 0:
            if not audio_data:
                logger.debug(f"CircularAudioBuffer.add_bytes: получены пустые данные (вызов #{self._add_bytes_call_count})")
            else:
                logger.debug(f"CircularAudioBuffer.add_bytes: обработано {self._add_bytes_call_count} вызовов, общий размер: {self._add_bytes_total_size} байт")
        
        if not audio_data:
            return 0
        
        # Добавляем данные как единый блок байтов
        if isinstance(audio_data, (bytes, bytearray)):
            # Добавляем целый блок байтов (для предотвращения преобразования в int)
            self.buffer.append(audio_data)
            data_len = len(audio_data)
        else:
            # Для обратной совместимости с старым методом
            try:
                # Преобразуем в байты и добавляем как блок
                audio_bytes = bytes(audio_data)
                self.buffer.append(audio_bytes)
                data_len = len(audio_bytes)
            except Exception as e:
                logger.warning(f"Ошибка при преобразовании данных в байты: {e}")
                return 0
        
        # Обновляем счетчик байтов
        self.total_bytes_added += data_len
        
        # Проверяем, не превышен ли максимальный размер deque
        while len(self.buffer) > 0 and self.total_bytes_added > self.buffer.maxlen:
            # Удаляем старые блоки данных
            removed = self.buffer.popleft()
            self.total_bytes_added -= len(removed)
        
        # Логируем состояние буфера только каждые 50 вызовов
        if self._add_bytes_call_count % 50 == 0:
            logger.debug(f"CircularAudioBuffer.add_bytes: добавлено {data_len} байт, общий размер буфера: {len(self.buffer)} блоков, всего байт: {self.total_bytes_added}")
        
        return data_len
    
    def add_numpy_array(self, audio_array: np.ndarray) -> int:
        """
        Добавляет аудиоданные из numpy массива в буфер.
        
        Args:
            audio_array (np.ndarray): Массив аудиоданных для добавления.
            
        Returns:
            int: Количество добавленных байтов.
        """
        if audio_array is None or audio_array.size == 0:
            return 0
        
        # Преобразуем numpy массив в байты и добавляем
        audio_bytes = audio_array.tobytes()
        return self.add_bytes(audio_bytes)
    
    def get_all_bytes(self) -> bytes:
        """
        Получает все данные из буфера как байты.
        
        Returns:
            bytes: Все аудиоданные из буфера.
        """
        logger.debug(f"CircularAudioBuffer.get_all_bytes: запрос данных, буфер содержит {len(self.buffer)} блоков")
        
        try:
            # В новой реализации буфер содержит только блоки байтов
            # Объединяем все блоки в один большой массив байтов
            if len(self.buffer) == 0:
                logger.debug("CircularAudioBuffer.get_all_bytes: буфер пуст, возвращаем пустые байты")
                return b''
                
            # Если в буфере только один элемент, возвращаем его напрямую
            if len(self.buffer) == 1:
                # Если это уже bytes/bytearray - возвращаем как есть
                if isinstance(self.buffer[0], (bytes, bytearray)):
                    result_bytes = bytes(self.buffer[0])
                    logger.debug(f"CircularAudioBuffer.get_all_bytes: возвращаем {len(result_bytes)} байт данных (один блок)")
                    return result_bytes
                
            # Собираем все блоки в одну последовательность
            try:
                # Пробуем быстрый метод объединения
                result_bytes = b''.join(self.buffer)
                logger.debug(f"CircularAudioBuffer.get_all_bytes: возвращаем {len(result_bytes)} байт данных (быстрый метод)")
                return result_bytes
            except TypeError as e:
                logger.warning(f"Ошибка при быстром объединении буфера: {e}. Используем альтернативный метод...")
                
                # Используем bytearray для эффективного добавления данных
                result = bytearray()
                
                # Копируем буфер для избегания ошибки 'deque mutated during iteration'
                buffer_copy = list(self.buffer)
                
                # Обрабатываем элементы буфера по одному
                for item in buffer_copy:
                    # Проверяем тип элемента
                    if isinstance(item, (bytes, bytearray)):
                        # Если это байты, добавляем как есть
                        result.extend(item)
                    else:
                        # Пытаемся преобразовать в байты
                        try:
                            result.extend(bytes(item))
                        except Exception as convert_error:
                            logger.warning(f"Не удалось преобразовать элемент {type(item)} в байты: {convert_error}")
                
                # Возвращаем результат как bytes
                result_bytes = bytes(result)
                logger.debug(f"CircularAudioBuffer.get_all_bytes: возвращаем {len(result_bytes)} байт данных (альтернативный метод)")
                return result_bytes
                
        except Exception as e:
            # В случае любой ошибки логируем и возвращаем пустой массив
            logger.error(f"Критическая ошибка при получении данных из буфера: {e}")
            return b''
    
    def get_all_numpy(self, dtype=np.int16) -> np.ndarray:
        """
        Получает все данные из буфера как numpy массив.
        
        Args:
            dtype: Тип данных для numpy массива.
            
        Returns:
            np.ndarray: Все аудиоданные из буфера как numpy массив.
        """
        # Получаем байты и преобразуем в numpy массив
        audio_bytes = self.get_all_bytes()
        if not audio_bytes:
            return np.array([], dtype=dtype)
        
        # Преобразуем с учётом параметров аудио
        audio_array = np.frombuffer(audio_bytes, dtype=dtype)
        
        # Если многоканальное аудио, преобразуем в правильную форму
        if self.channels > 1:
            audio_array = audio_array.reshape(-1, self.channels)
            
        return audio_array
    
    def get_last_seconds(self, seconds: float) -> bytes:
        """
        Получает последние N секунд аудио из буфера.
        
        Args:
            seconds (float): Количество секунд для получения.
            
        Returns:
            bytes: Аудиоданные за указанный период.
        """
        if seconds <= 0:
            return b''
        
        # Вычисляем размер N секунд в байтах
        bytes_per_second = self.sample_rate * self.channels * self.sample_width
        bytes_needed = int(seconds * bytes_per_second)
        
        # Получаем все байты и берём только нужное количество с конца
        all_bytes = self.get_all_bytes()
        if len(all_bytes) <= bytes_needed:
            return all_bytes
        
        return all_bytes[-bytes_needed:]
    
    def clear(self) -> None:
        """Очищает буфер"""
        self.buffer.clear()
        
    def get_duration_seconds(self) -> float:
        """
        Получает текущую длительность аудио в буфере в секундах.
        
        Returns:
            float: Длительность аудио в секундах.
        """
        bytes_per_second = self.sample_rate * self.channels * self.sample_width
        return len(self.get_all_bytes()) / bytes_per_second if bytes_per_second > 0 else 0
    
    def __len__(self) -> int:
        """
        Возвращает текущий размер буфера в байтах.
        
        Returns:
            int: Размер буфера в байтах.
        """
        return len(self.get_all_bytes())
