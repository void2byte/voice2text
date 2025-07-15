#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовый скрипт для проверки исправления проблемы с накоплением аудиоданных
между записями в AudioCaptureRunnable.

Этот скрипт проверяет:
1. Что объект AudioCaptureRunnable корректно очищается при начале новой записи
2. Что данные от предыдущих записей не накапливаются
3. Что каждая запись содержит только свои данные
"""

import sys
import os
import time
import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

# Добавляем путь к модулям проекта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from voice_control.microphone.qt_audio_capture import AudioCapture

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AudioDataTester:
    """Класс для тестирования исправления проблемы с аудиоданными"""
    
    def __init__(self):
        self.audio_capture = AudioCapture()
        self.test_results = []
        self.current_test = 0
        self.max_tests = 3
        
    def run_test(self):
        """Запуск теста записи аудио"""
        logger.info(f"\n=== ТЕСТ {self.current_test + 1}/{self.max_tests} ===")
        
        # Начинаем запись
        logger.info("Начинаем запись...")
        success = self.audio_capture.start_recording()
        
        if not success:
            logger.error("Не удалось начать запись")
            return
            
        # Записываем 2 секунды
        QTimer.singleShot(2000, self.stop_and_check)
        
    def stop_and_check(self):
        """Остановка записи и проверка данных"""
        logger.info("Останавливаем запись...")
        self.audio_capture.stop_recording()
        
        # Небольшая задержка для завершения операций
        QTimer.singleShot(500, self.check_data)
        
    def check_data(self):
        """Проверка полученных аудиоданных"""
        try:
            # Получаем данные
            audio_data = self.audio_capture.get_recorded_data()
            
            if audio_data and len(audio_data) >= 4:
                raw_data, sample_rate, channels, sample_width = audio_data
                data_size = len(raw_data)
                
                logger.info(f"Получены данные: {data_size} байт")
                logger.info(f"Параметры: {sample_rate}Гц, {channels} канал(ов), {sample_width} байт/сэмпл")
                
                # Сохраняем результат
                self.test_results.append({
                    'test_number': self.current_test + 1,
                    'data_size': data_size,
                    'sample_rate': sample_rate,
                    'channels': channels,
                    'sample_width': sample_width
                })
                
                # Ожидаемый размер данных для 2 секунд записи
                expected_size = sample_rate * channels * sample_width * 2  # 2 секунды
                size_ratio = data_size / expected_size if expected_size > 0 else 0
                
                logger.info(f"Ожидаемый размер: ~{expected_size} байт")
                logger.info(f"Соотношение: {size_ratio:.2f}")
                
                if size_ratio > 1.5:
                    logger.warning("⚠️  ВОЗМОЖНО НАКОПЛЕНИЕ ДАННЫХ! Размер больше ожидаемого в 1.5 раза")
                elif 0.5 <= size_ratio <= 1.5:
                    logger.info("✅ Размер данных в норме")
                else:
                    logger.warning("⚠️  Размер данных меньше ожидаемого")
                    
            else:
                logger.warning("Получены пустые или некорректные данные")
                self.test_results.append({
                    'test_number': self.current_test + 1,
                    'data_size': 0,
                    'error': 'Пустые данные'
                })
                
        except Exception as e:
            logger.error(f"Ошибка при проверке данных: {e}")
            self.test_results.append({
                'test_number': self.current_test + 1,
                'error': str(e)
            })
            
        # Переходим к следующему тесту или завершаем
        self.current_test += 1
        if self.current_test < self.max_tests:
            logger.info("Пауза 1 секунда перед следующим тестом...")
            QTimer.singleShot(1000, self.run_test)
        else:
            self.show_results()
            
    def show_results(self):
        """Показ результатов всех тестов"""
        logger.info("\n" + "="*50)
        logger.info("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
        logger.info("="*50)
        
        data_sizes = []
        for result in self.test_results:
            test_num = result['test_number']
            if 'error' in result:
                logger.info(f"Тест {test_num}: ОШИБКА - {result['error']}")
            else:
                data_size = result['data_size']
                data_sizes.append(data_size)
                logger.info(f"Тест {test_num}: {data_size} байт")
                
        # Анализ накопления данных
        if len(data_sizes) >= 2:
            logger.info("\nАНАЛИЗ НАКОПЛЕНИЯ ДАННЫХ:")
            
            # Проверяем, увеличиваются ли размеры данных
            increasing = all(data_sizes[i] <= data_sizes[i+1] for i in range(len(data_sizes)-1))
            
            if increasing and max(data_sizes) > min(data_sizes) * 1.5:
                logger.warning("❌ ОБНАРУЖЕНО НАКОПЛЕНИЕ ДАННЫХ!")
                logger.warning("Размеры данных увеличиваются между записями")
            else:
                logger.info("✅ НАКОПЛЕНИЕ ДАННЫХ НЕ ОБНАРУЖЕНО")
                logger.info("Размеры данных стабильны между записями")
                
        logger.info("\nТестирование завершено.")
        QApplication.quit()

def main():
    """Главная функция"""
    app = QApplication(sys.argv)
    
    logger.info("Запуск тестирования исправления проблемы с аудиоданными")
    logger.info("Будет выполнено 3 записи по 2 секунды каждая")
    logger.info("Проверяем, что данные не накапливаются между записями\n")
    
    tester = AudioDataTester()
    
    # Запускаем первый тест через 1 секунду
    QTimer.singleShot(1000, tester.run_test)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()