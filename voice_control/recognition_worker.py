import os
import logging
from PySide6.QtCore import QObject, Signal, Slot

logger = logging.getLogger(__name__)

class RecognitionWorker(QObject):
    recognition_finished = Signal(dict)  # Сигнал с результатом распознавания (словарь от SpeechRecognizer)
    recognition_error = Signal(str)    # Сигнал об ошибке

    def __init__(self, recognizer, audio_file_path=None, audio_data_tuple=None):
        super().__init__()
        self.recognizer = recognizer
        self.audio_file_path = audio_file_path
        self.audio_data_tuple = audio_data_tuple # Кортеж (raw_data, sample_rate, channels, sample_width)

    @Slot()
    def run(self):
        try:
            logger.debug(f"RecognitionWorker.run: Начало работы, recognizer={type(self.recognizer).__name__ if self.recognizer else None}")
            
            if not self.recognizer:
                logger.error("RecognitionWorker.run: Распознаватель речи не инициализирован")
                self.recognition_error.emit("Распознаватель речи не инициализирован.")
                return

            result = None
            if self.audio_data_tuple and hasattr(self.recognizer, 'recognize_audio_data'):
                logger.info("Worker: Распознавание аудиоданных...")
                logger.debug(f"RecognitionWorker.run: audio_data_tuple тип: {type(self.audio_data_tuple)}, длина: {len(self.audio_data_tuple) if hasattr(self.audio_data_tuple, '__len__') else 'N/A'}")
                
                # Извлекаем только raw_data из кортежа (raw_data, sample_rate, channels, sample_width)
                raw_audio_data = self.audio_data_tuple[0] if isinstance(self.audio_data_tuple, tuple) else self.audio_data_tuple
                
                if raw_audio_data is None:
                    logger.error("RecognitionWorker.run: raw_audio_data равно None")
                    self.recognition_error.emit("Аудиоданные отсутствуют (None).")
                    return
                elif hasattr(raw_audio_data, '__len__'):
                    data_size = len(raw_audio_data)
                    logger.info(f"RecognitionWorker.run: Передаем в recognizer.recognize_audio_data данные размером {data_size} байт")
                    if data_size == 0:
                        logger.error("RecognitionWorker.run: Размер аудиоданных равен 0")
                        self.recognition_error.emit("Аудиоданные пусты (размер 0).")
                        return
                else:
                    logger.warning(f"RecognitionWorker.run: raw_audio_data неожиданного типа: {type(raw_audio_data)}")
                
                result = self.recognizer.recognize_audio_data(raw_audio_data)
            elif self.audio_file_path and os.path.exists(self.audio_file_path) and hasattr(self.recognizer, 'recognize_file'):
                logger.info(f"Worker: Распознавание файла {self.audio_file_path}...")
                result = self.recognizer.recognize_file(self.audio_file_path)
            elif self.audio_file_path:
                self.recognition_error.emit(f"Аудиофайл не найден: {self.audio_file_path}")
                return
            else:
                self.recognition_error.emit("Не предоставлены ни аудиоданные, ни путь к файлу для распознавания.")
                return
            
            if result:
                self.recognition_finished.emit(result)
            else:
                # Это условие не должно срабатывать, если recognize_audio_data/recognize_file всегда возвращают dict
                self.recognition_error.emit("Результат распознавания отсутствует.")
                
        except Exception as e:
            logger.error(f"Ошибка в потоке распознавания: {e}", exc_info=True)
            self.recognition_error.emit(f"Внутренняя ошибка распознавания: {e}")
