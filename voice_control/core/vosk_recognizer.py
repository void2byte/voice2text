import json
import os
import wave
import logging
from typing import Union, Optional
from pathlib import Path
import numpy as np

from .voice_recognizer import BaseRecognizer, RecognitionResult, RecognitionConfig, RecognitionEngine, RecognitionStatus

# Попытка импортировать vosk
try:
    from vosk import Model, KaldiRecognizer, SetLogLevel
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False
    Model = None
    KaldiRecognizer = None
    SetLogLevel = None


class VoskModelManager:
    """Менеджер для загрузки и управления моделями Vosk."""
    
    def __init__(self):
        self.current_model = None
        self.current_recognizer = None
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def load_model(self, model_path: str, parent_widget=None, show_dialog=False) -> bool:
        """Загружает модель Vosk."""
        try:
            if not os.path.exists(model_path):
                self.logger.error(f"Путь к модели не существует: {model_path}")
                return False
            
            self.logger.info(f"Загрузка модели Vosk: {model_path}")
            self.current_model = Model(model_path)
            self.logger.info("Модель Vosk успешно загружена")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки модели Vosk: {e}")
            return False
    
    def get_recognizer(self, sample_rate: int = 16000) -> Optional[KaldiRecognizer]:
        """Создает распознаватель для текущей модели."""
        if not self.current_model:
            return None
        
        try:
            self.current_recognizer = KaldiRecognizer(self.current_model, sample_rate)
            return self.current_recognizer
        except Exception as e:
            self.logger.error(f"Ошибка создания распознавателя: {e}")
            return None


class VoskRecognizer(BaseRecognizer):
    """Распознаватель на основе Vosk для локального распознавания речи."""
    
    def __init__(self, config: RecognitionConfig):
        super().__init__(config)
        self._model = None
        self._recognizer = None
        self._model_manager = None
        self._model_path = None
    
    def initialize(self) -> bool:
        """Инициализация Vosk распознавателя."""
        if not VOSK_AVAILABLE:
            self.logger.error("Библиотека Vosk не установлена. Установите: pip install vosk")
            return False
        
        # Получаем путь к модели из конфигурации или используем значение по умолчанию
        self._model_path = getattr(self.config, 'model_path', None)
        if not self._model_path:
            # Попытка найти модель в стандартных местах
            possible_paths = [
                f"models/vosk-model-{self.config.language}",
                f"vosk-model-{self.config.language}",
                f"models/vosk-model-small-{self.config.language}",
                f"vosk-model-small-{self.config.language}"
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    self._model_path = path
                    break
            
            if not self._model_path:
                self.logger.error("Путь к модели Vosk не указан и не найден автоматически")
                self.logger.info("Укажите model_path в конфигурации или скачайте модель")
                return False
        
        if not os.path.exists(self._model_path):
            self.logger.error(f"Модель Vosk не найдена: {self._model_path}")
            return False
        
        try:
            # Отключаем логирование Vosk
            SetLogLevel(-1)
            
            # Создаем менеджер модели
            self._model_manager = VoskModelManager()
            
            # Загружаем модель
            if not self._model_manager.load_model(self._model_path):
                return False
            
            self._model = self._model_manager.current_model
            
            # Создаем распознаватель
            self._recognizer = self._model_manager.get_recognizer(self.config.sample_rate)
            if not self._recognizer:
                return False
            
            # Включаем возврат информации по словам
            self._recognizer.SetWords(True)
            
            self._is_initialized = True
            self.logger.info(f"Vosk распознаватель инициализирован с моделью: {self._model_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка инициализации Vosk: {e}")
            return False
    
    def recognize_speech(self, audio_data: Union[np.ndarray, bytes]) -> RecognitionResult:
        """Распознавание речи из аудиоданных."""
        if not self._is_initialized:
            raise RuntimeError("Распознаватель не инициализирован")
        
        self._status = RecognitionStatus.PROCESSING
        self._trigger_callback('on_start')
        
        try:
            # Конвертация аудиоданных в bytes для Vosk
            if isinstance(audio_data, np.ndarray):
                # Конвертируем в 16-bit PCM
                if audio_data.dtype != np.int16:
                    if audio_data.max() <= 1.0:
                        # Нормализованные данные
                        audio_data = (audio_data * 32767).astype(np.int16)
                    else:
                        audio_data = audio_data.astype(np.int16)
                audio_bytes = audio_data.tobytes()
            else:
                audio_bytes = audio_data
            
            # Распознавание через Vosk
            if self._recognizer.AcceptWaveform(audio_bytes):
                result_json = self._recognizer.Result()
            else:
                result_json = self._recognizer.PartialResult()
            
            result = json.loads(result_json)
            
            # Извлекаем текст
            text = result.get("text", result.get("partial", "")).strip()
            
            # Извлекаем информацию о словах
            words_info = []
            if "result" in result and isinstance(result["result"], list):
                words_info = [
                    {
                        "word": word_data["word"],
                        "start_time": word_data["start"],
                        "end_time": word_data["end"],
                        "confidence": word_data.get("conf", 1.0)
                    }
                    for word_data in result["result"]
                ]
            
            # Вычисляем общую уверенность
            confidence = 1.0
            if words_info:
                confidence = sum(word["confidence"] for word in words_info) / len(words_info)
            
            recognition_result = RecognitionResult(
                text=text,
                confidence=confidence,
                language=self.config.language,
                duration=len(audio_data) / self.config.sample_rate if isinstance(audio_data, np.ndarray) else 0,
                engine=RecognitionEngine.VOSK,
                metadata={
                    'words': words_info,
                    'model_path': self._model_path,
                    'raw_result': result
                }
            )
            
            self._status = RecognitionStatus.COMPLETED
            self._trigger_callback('on_result', recognition_result)
            return recognition_result
            
        except Exception as e:
            self._status = RecognitionStatus.ERROR
            self.logger.error(f"Ошибка распознавания Vosk: {e}")
            self._trigger_callback('on_error', e)
            raise
    
    def recognize_from_file(self, file_path: Union[str, Path]) -> RecognitionResult:
        """Распознавание речи из WAV файла."""
        if not self._is_initialized:
            raise RuntimeError("Распознаватель не инициализирован")
        
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Аудиофайл не найден: {file_path}")
        
        try:
            with wave.open(str(file_path), "rb") as wf:
                # Проверяем формат файла
                if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
                    raise ValueError(
                        f"Файл должен быть в формате WAV PCM 16-bit mono. "
                        f"Текущий: каналы={wf.getnchannels()}, ширина={wf.getsampwidth()}, "
                        f"компрессия={wf.getcomptype()}"
                    )
                
                # Создаем временный распознаватель для частоты файла, если нужно
                file_sample_rate = wf.getframerate()
                if file_sample_rate != self.config.sample_rate:
                    temp_recognizer = KaldiRecognizer(self._model, file_sample_rate)
                    temp_recognizer.SetWords(True)
                else:
                    temp_recognizer = self._recognizer
                
                # Читаем и распознаем файл по частям
                results = []
                full_text = ""
                
                while True:
                    data = wf.readframes(4000)
                    if len(data) == 0:
                        break
                    
                    if temp_recognizer.AcceptWaveform(data):
                        result_json = temp_recognizer.Result()
                        result = json.loads(result_json)
                        if result.get("text"):
                            results.append(result)
                            full_text += result["text"] + " "
                
                # Получаем финальный результат
                final_result_json = temp_recognizer.FinalResult()
                final_result = json.loads(final_result_json)
                if final_result.get("text"):
                    full_text += final_result["text"]
                
                full_text = full_text.strip()
                
                # Собираем информацию о словах из всех результатов
                all_words = []
                for result in results:
                    if "result" in result and isinstance(result["result"], list):
                        all_words.extend(result["result"])
                
                # Добавляем слова из финального результата
                if "result" in final_result and isinstance(final_result["result"], list):
                    all_words.extend(final_result["result"])
                
                words_info = [
                    {
                        "word": word_data["word"],
                        "start_time": word_data["start"],
                        "end_time": word_data["end"],
                        "confidence": word_data.get("conf", 1.0)
                    }
                    for word_data in all_words
                ]
                
                # Вычисляем общую уверенность
                confidence = 1.0
                if words_info:
                    confidence = sum(word["confidence"] for word in words_info) / len(words_info)
                
                duration = wf.getnframes() / wf.getframerate()
                
                return RecognitionResult(
                    text=full_text,
                    confidence=confidence,
                    language=self.config.language,
                    duration=duration,
                    engine=RecognitionEngine.VOSK,
                    metadata={
                        'words': words_info,
                        'model_path': self._model_path,
                        'file_path': str(file_path),
                        'sample_rate': file_sample_rate,
                        'all_results': results
                    }
                )
                
        except Exception as e:
            self.logger.error(f"Ошибка распознавания файла: {e}")
            raise
    
    def cleanup(self):
        """Очистка ресурсов."""
        super().cleanup()
        self._model = None
        self._recognizer = None
        self._model_manager = None
        self._model_path = None
    
    @property
    def model_path(self) -> Optional[str]:
        """Путь к текущей модели."""
        return self._model_path
    
    def set_model_path(self, model_path: str) -> bool:
        """Устанавливает новый путь к модели и переинициализирует распознаватель."""
        self._model_path = model_path
        return self.initialize()