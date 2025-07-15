"""
Модуль для распознавания речи с использованием Яндекс SpeechKit.
"""
import os
import sys
import logging
import tempfile
import subprocess
import wave
from typing import Dict, Any, List, Optional, Tuple, Union

# Импортируем библиотеку Яндекс SpeechKit
from speechkit import model_repository, configure_credentials, creds
from speechkit.stt import AudioProcessingType

from .base_recognizer import BaseRecognizer # Added import for BaseRecognizer

# Настройка логирования
logger = logging.getLogger(__name__)

class YandexSpeechRecognizer(BaseRecognizer):
    def __init__(self, config: Dict[str, Any]):
        """
        Инициализация распознавателя речи Yandex.

        Args:
            config: Словарь с конфигурацией.
                    Обязательные ключи: 'api_key'.
                    Опциональные ключи: 'language_code' (default 'ru-RU'), 
                                       'model' (default 'general'), 
                                       'audio_format_hint' (default 'lpcm'),
                                       'sample_rate_hertz' (default 16000).
        """
        super().__init__(config)
        self.config = config  # Store config for access to parameters
        self.api_key = self.config.get('api_key')
        logger.info(f"YandexSpeechRecognizer: Инициализация с API-ключом: {'*' * (len(self.api_key) - 4) + self.api_key[-4:] if self.api_key else 'None'}")
        if not self.api_key:
            logger.error("API-ключ ('api_key') не был предоставлен в конфигурации.")
            raise ValueError("API-ключ ('api_key') должен быть указан в конфигурации.")

        lang_full_code = self.config.get('language_code', "ru-RU")
        self.language = lang_full_code.split('-')[0] # Use 'ru' from 'ru-RU'

        self.model_name = self.config.get('model', "general")
        self.audio_format_hint = self.config.get('audio_format_hint', "lpcm")
        self.sample_rate_hertz = self.config.get('sample_rate_hertz', 16000)

        self.logger = logger # Use module-level logger
        # self.logger.setLevel(logging.INFO) # Level set by application's logging config

        try:
            configure_credentials(
                yandex_credentials=creds.YandexCredentials(
                    api_key=self.api_key
                )
            )
        except Exception as e:
            self.logger.error(f"Ошибка конфигурации учетных данных Yandex: {e}")
            raise ConnectionError(f"Ошибка конфигурации учетных данных Yandex: {e}")

        self.recognizer_model = self._create_model()
    
    def _create_model(self):
        """Создание модели распознавания."""
        try:
            model_instance = model_repository.recognition_model()
            
            model_instance.model = self.model_name
            # Map language codes like 'ru' to Yandex specific 'ru-RU', 'en-EN' etc.
            if self.language == "ru":
                model_instance.language = "ru-RU"
            elif self.language == "en":
                model_instance.language = "en-EN"
            elif self.language == "tr":
                model_instance.language = "tr-TR"
            elif self.language == "kk":
                model_instance.language = "kk-KK"
            else:
                self.logger.warning(f"Неизвестный код языка '{self.language}' для модели Yandex, используется как есть.")
                model_instance.language = self.language 
            
            # AudioProcessingType is not directly set on the model for transcribe_file in SDK v3
            # It's more relevant for streaming or specific session configurations.
            # We rely on transcribe_file defaults.
            return model_instance
        except Exception as e:
            self.logger.error(f"Ошибка при создании модели Yandex: {e}")
            raise RuntimeError(f"Ошибка при создании модели Yandex: {e}")
    
    def _convert_audio_if_needed(self, file_path: str, target_sample_rate: Optional[int] = None) -> str:
        """
        Конвертирует аудиофайл в нужный формат, если необходимо.
        
        Args:
            file_path: Путь к аудиофайлу
            target_sample_rate: Целевая частота дискретизации. Если None, используется self.sample_rate.
            
        Returns:
            str: Путь к конвертированному файлу
        """
        current_target_sample_rate = target_sample_rate if target_sample_rate is not None else self.sample_rate_hertz
        # Проверяем, совпадает ли формат файла с требуемым
        need_conversion = True
        
        # Проверяем, является ли файл WAV-файлом с нужными параметрами
        if file_path.lower().endswith('.wav') and self.audio_format_hint == 'lpcm':
            try:
                with wave.open(file_path, 'rb') as wf:
                    channels = wf.getnchannels()
                    samplewidth = wf.getsampwidth()
                    samplerate = wf.getframerate()
                    
                    # Проверяем, совпадают ли параметры с требуемыми
                    if (channels == 1 and 
                        samplewidth == 2 and 
                        abs(samplerate - current_target_sample_rate) <= 100):
                        self.logger.info(f"Файл {file_path} уже имеет подходящий формат: {samplerate} Hz, {channels} канал, {samplewidth*8} бит для целевой частоты {current_target_sample_rate} Hz")
                        # Файл уже в нужном формате, конвертация не требуется
                        need_conversion = False
                        return file_path
                    else:
                        self.logger.info(f"Файл {file_path} требует конвертации: {samplerate} Hz vs {current_target_sample_rate} Hz, " 
                                      f"{channels} vs 1 канал, {samplewidth*8} vs 16 бит")
            except Exception as e:
                self.logger.warning(f"Ошибка при проверке WAV-файла: {e}")
        
        # Если конвертация всё же нужна
        if need_conversion:
            # Создаем временный файл для конвертированного аудио
            output_ext = ".wav" if self.audio_format_hint == "lpcm" else ".ogg"
            fd, output_file = tempfile.mkstemp(suffix=output_ext)
            os.close(fd)
            
            # Конвертируем аудио с помощью ffmpeg
            if self.audio_format_hint == "lpcm":
                # Конвертируем в WAV PCM 16-bit
                cmd = [
                    "ffmpeg", "-y", "-i", file_path, 
                    "-acodec", "pcm_s16le", 
                    "-ar", str(current_target_sample_rate), 
                    "-ac", "1", 
                    output_file
                ]
            else:
                # Конвертируем в OGG Opus
                cmd = [
                    "ffmpeg", "-y", "-i", file_path, 
                    "-c:a", "libopus", 
                    "-ar", str(current_target_sample_rate), 
                    "-ac", "1", 
                    output_file
                ]
            
            try:
                self.logger.info(f"Запуск конвертации файла {file_path} в {output_file}")
                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                self.logger.info(f"Успешная конвертация в {output_file}, размер: {os.path.getsize(output_file)} байт")
                return output_file
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Ошибка при конвертации аудио: {e.stderr.decode('utf-8') if e.stderr else str(e)}")
                return file_path 
        
        return file_path
    
    def recognize_audio_data(self, audio_data: bytes) -> List[Dict[str, Union[str, float, List[Dict[str, Union[str, float]]]]]]:
        """
        Распознавание речи напрямую из аудиоданных.
        Предполагается, что audio_data - это сырые PCM данные.

        Args:
            audio_data: Байты аудиоданных (raw PCM).

        Returns:
            Список словарей с результатами распознавания.
        """
        self.logger.debug(f"YandexSpeechRecognizer.recognize_audio_data: Получены данные типа {type(audio_data)}")
        self.logger.info("Распознавание аудиоданных из памяти")

        if not audio_data:
            self.logger.error("YandexSpeechRecognizer.recognize_audio_data: Пустые аудиоданные для распознавания.")
            raise ValueError("Пустые аудиоданные для распознавания.")
        
        if hasattr(audio_data, '__len__'):
            data_size = len(audio_data)
            self.logger.info(f"Размер аудиоданных: {data_size} байт")
            if data_size == 0:
                self.logger.error("YandexSpeechRecognizer.recognize_audio_data: Размер аудиоданных равен 0")
                raise ValueError("Входные аудиоданные имеют нулевой размер")
        else:
            self.logger.warning(f"YandexSpeechRecognizer.recognize_audio_data: Неожиданный тип данных без __len__: {type(audio_data)}")
                
        channels = self.config.get('channels', 1)
        sample_width = self.config.get('sample_width_bytes', 2)
        # self.sample_rate_hertz is used from config

        self.logger.info(f"Получены данные: {len(audio_data)} байт. Используются параметры: {self.sample_rate_hertz} Гц, {channels} канал(ов), {sample_width} байт/сэмпл")

        temp_wav_file = None
        converted_file = None
        try:
            fd, temp_wav_file = tempfile.mkstemp(suffix=".wav")
            os.close(fd)

            with wave.open(temp_wav_file, 'wb') as wav_file:
                wav_file.setnchannels(channels)
                wav_file.setsampwidth(sample_width)
                wav_file.setframerate(self.sample_rate_hertz)
                wav_file.writeframes(audio_data)
            
            self.logger.info(f"Создан временный WAV файл: {temp_wav_file}, размер: {os.path.getsize(temp_wav_file)} байт")

            converted_file = self._convert_audio_if_needed(temp_wav_file, target_sample_rate=self.sample_rate_hertz)
            if converted_file != temp_wav_file:
                 self.logger.info(f"Аудио было конвертировано в: {converted_file}, размер: {os.path.getsize(converted_file)} байт")
            else:
                self.logger.info(f"Аудио не требовало конвертации, используется: {converted_file}")

            if not os.path.exists(converted_file) or os.path.getsize(converted_file) == 0:
                self.logger.error(f"Конвертированный файл не существует или пуст: {converted_file}")
                raise IOError(f"Конвертированный файл не существует или пуст: {converted_file}")
            
            self.logger.info(f"Запуск распознавания файла: {converted_file} с моделью {self.model_name}, язык {self.language}")
            
            raw_transcriptions: List[Any] = self.recognizer_model.transcribe_file(
                audio_path=converted_file,
            )
            
            self.logger.info(f"Распознавание успешно, получено {len(raw_transcriptions) if raw_transcriptions else 0} объектов транскрипции.")
            processed_results = self._process_transcriptions_base(raw_transcriptions)
            
            # Формируем результат в ожидаемом формате
            if processed_results:
                full_text = " ".join([result.get("text", "") for result in processed_results if result.get("text")])
                return {
                    "success": True,
                    "results": processed_results,
                    "text": full_text,
                    "normalized_text": full_text
                }
            else:
                return {
                    "success": False,
                    "error": "Не удалось получить результаты распознавания"
                }

        except subprocess.CalledProcessError as e:
            error_msg = f"Ошибка ffmpeg при обработке аудиоданных: {e.stderr.decode('utf-8') if e.stderr else str(e)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
        except Exception as e:
            error_msg = f"Ошибка при распознавании аудиоданных: {e}"
            self.logger.error(error_msg)
            # Проверяем, является ли ошибка связанной с API SpeechKit
            if "SpeechKit" in str(type(e)) or "speechkit" in str(e).lower():
                error_msg = f"Ошибка API Yandex SpeechKit: {e}"
            return {
                "success": False,
                "error": error_msg
            }
        finally:
            for f_path in [temp_wav_file, converted_file]:
                if f_path and os.path.exists(f_path) and (f_path == temp_wav_file or f_path != temp_wav_file): # ensure converted_file is deleted if different
                    try:
                        os.unlink(f_path)
                    except Exception as e_del:
                        self.logger.warning(f"Ошибка при удалении временного файла {f_path}: {e_del}")

    def recognize_file(self, file_path: str) -> List[Dict[str, Union[str, float, List[Dict[str, Union[str, float]]]]]]:
        """
        Распознавание речи из аудиофайла.

        Args:
            file_path: Путь к аудиофайлу

        Returns:
            Список словарей с результатами распознавания.
        """
        self.logger.info(f"Распознавание аудиофайла: {file_path}")

        if not os.path.exists(file_path):
            self.logger.error(f"Файл не найден: {file_path}")
            raise FileNotFoundError(f"Файл не найден: {file_path}")

        converted_file = None
        try:
            converted_file = self._convert_audio_if_needed(file_path, target_sample_rate=self.sample_rate_hertz)
            if converted_file != file_path:
                self.logger.info(f"Аудио было конвертировано в: {converted_file}, размер: {os.path.getsize(converted_file)} байт")
            else:
                self.logger.info(f"Аудио не требовало конвертации, используется: {file_path}")

            if not os.path.exists(converted_file) or os.path.getsize(converted_file) == 0:
                self.logger.error(f"Конвертированный файл не существует или пуст: {converted_file}")
                raise IOError(f"Конвертированный файл не существует или пуст: {converted_file}")

            self.logger.info(f"Запуск распознавания файла: {converted_file} с моделью {self.model_name}, язык {self.language}")
            
            raw_transcriptions: List[Any] = self.recognizer_model.transcribe_file(
                audio_path=converted_file,
            )
            
            self.logger.info(f"Распознавание успешно, получено {len(raw_transcriptions) if raw_transcriptions else 0} объектов транскрипции.")
            return self._process_transcriptions_base(raw_transcriptions)
        
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Ошибка ffmpeg при конвертации файла {file_path}: {e.stderr.decode('utf-8') if e.stderr else str(e)}")
            raise IOError(f"Ошибка ffmpeg: {e.stderr.decode('utf-8') if e.stderr else str(e)}")
        except Exception as e:
            self.logger.error(f"Ошибка при распознавании файла {file_path}: {e}")
            # Проверяем, является ли ошибка связанной с API SpeechKit
            if "SpeechKit" in str(type(e)) or "speechkit" in str(e).lower():
                 raise ConnectionError(f"Ошибка API Yandex SpeechKit: {e}")
            raise RuntimeError(f"Общая ошибка распознавания файла {file_path}: {e}")
        finally:
            if converted_file and converted_file != file_path and os.path.exists(converted_file):
                try:
                    os.unlink(converted_file)
                except Exception as e_del:
                    self.logger.warning(f"Ошибка при удалении временного файла {converted_file}: {e_del}")

    def _process_transcriptions_base(self, raw_transcriptions: Optional[List[Any]]) -> List[Dict[str, Union[str, float, List[Dict[str, Union[str, float]]]]]]:
        """
        Обработка результатов распознавания от Yandex SDK v3 в формат BaseRecognizer.

        Args:
            raw_transcriptions: Результаты распознавания от API (список объектов транскрипции).

        Returns:
            Список словарей, где каждый словарь представляет один вариант распознавания.
        """
        self.logger.info(f"Начало обработки {len(raw_transcriptions) if raw_transcriptions else 0} транскрипций от Yandex.")
        
        if not raw_transcriptions:
            self.logger.warning("Ответ от Yandex не содержит транскрипций.")
            return []

        processed_results = []

        for response_item in raw_transcriptions:
            try:
                # Извлекаем текст с проверкой атрибутов
                raw_text = getattr(response_item, 'text', 
                               getattr(response_item, 'raw_text', 
                                       str(response_item)))
                
                # Обрабатываем слова, если они есть
                words_list = []
                if hasattr(response_item, "words") and response_item.words:
                    for word_obj in response_item.words:
                        try:
                            word_text = getattr(word_obj, 'text', str(word_obj))
                            start_time = getattr(word_obj, 'start_time_ms', 0)
                            end_time = getattr(word_obj, 'end_time_ms', 0)
                            confidence = getattr(word_obj, 'confidence', 0.0)
                            
                            words_list.append({
                                "text": word_text,
                                "start_time_ms": start_time,
                                "end_time_ms": end_time,
                                "confidence": round(confidence, 4) if confidence is not None else 0.0
                            })
                        except Exception as word_error:
                            self.logger.warning(f"Ошибка обработки слова: {word_error}")
                            continue
                
                # Получаем уверенность
                confidence = getattr(response_item, 'confidence', 0.0)
                
                processed_results.append({
                    "text": raw_text or "",
                    "confidence": round(confidence, 4) if confidence is not None else 0.0,
                    "words": words_list,
                })
                self.logger.debug(f"Добавлена транскрипция: '{raw_text[:50] if raw_text else ''}...' с уверенностью {confidence}")
                
            except Exception as item_error:
                self.logger.warning(f"Ошибка обработки объекта транскрипции: {item_error}")
                continue

        if not processed_results:
             self.logger.info("После обработки не найдено валидных результатов транскрипции.")

        self.logger.info(f"Обработка транскрипций завершена, получено {len(processed_results)} результатов.")
        return processed_results

    @staticmethod
    def get_supported_languages() -> List[Dict[str, str]]:
        """Возвращает список поддерживаемых языков."""
        return [
            {"code": "ru-RU", "name": "Русский"},
            {"code": "en-US", "name": "Английский (США)"},
            {"code": "tr-TR", "name": "Турецкий"},
            {"code": "kk-KZ", "name": "Казахский"}
        ]

    @staticmethod
    def get_available_models(language_code: Optional[str] = None) -> List[Dict[str, str]]: # language_code is optional now
        """Возвращает список доступных моделей."""
        # Yandex models are generally language-agnostic in terms of listing
        models = [
            {"id": "general", "name": "Основная модель (general)"},
            {"id": "deferred-general", "name": "Отложенная основная модель (deferred-general)"},
            {"id": "telephony", "name": "Модель для телефонии (telephony)"},
            {"id": "telephony-hd", "name": "Модель для телефонии HD (telephony-hd)"}
        ]
        return models

    @staticmethod
    def get_config_schema() -> Dict[str, Any]:
        """Возвращает JSON-схему для конфигурационных параметров этого распознавателя."""
        return {
            "type": "object",
            "properties": {
                "api_key": {"type": "string", "description": "API-ключ Яндекс SpeechKit."},
                "language_code": {
                    "type": "string", 
                    "description": "Код языка (например, 'ru-RU', 'en-US').",
                    "default": "ru-RU",
                    "enum": [lang['code'] for lang in YandexSpeechRecognizer.get_supported_languages()]
                },
                "model": {
                    "type": "string", 
                    "description": "Идентификатор модели распознавания.",
                    "default": "general",
                    "enum": [model['id'] for model in YandexSpeechRecognizer.get_available_models()] 
                },
                "sample_rate_hertz": {
                    "type": "integer",
                    "description": "Предпочтительная частота дискретизации для аудио (Гц).",
                    "default": 16000,
                    "enum": [8000, 16000, 48000]
                },
                "audio_format_hint": {
                    "type": "string",
                    "description": "Подсказка о формате аудио для конвертера (lpcm, oggopus).",
                    "default": "lpcm",
                    "enum": ["lpcm", "oggopus"]
                },
                "channels": {
                    "type": "integer",
                    "description": "Количество каналов в сырых аудиоданных (для recognize_audio_data).",
                    "default": 1,
                    "enum": [1, 2]
                },
                "sample_width_bytes": {
                    "type": "integer",
                    "description": "Ширина сэмпла в байтах в сырых аудиоданных (для recognize_audio_data).",
                    "default": 2, 
                    "enum": [1, 2, 3, 4]
                }
            },
            "required": ["api_key"]
        }

    @staticmethod
    def get_audio_format_requirements() -> Dict[str, Any]:
        """
        Возвращает предпочтительные требования к формату аудио для Yandex SpeechKit.
        """
        return {
            "description": "Yandex SpeechKit prefers LPCM (WAV) or OggOpus. For LPCM, common parameters are 16kHz, mono, 16-bit signed-integer little-endian.",
            "formats": [
                {
                    "container": "wav",
                    "encoding": "pcm_s16le",
                    "sample_rate_hz": [8000, 16000, 48000], # Yandex supports multiple rates
                    "channels": 1
                },
                {
                    "container": "ogg",
                    "encoding": "opus",
                    "sample_rate_hz": [8000, 16000, 48000],
                    "channels": 1
                }
            ],
            "preferred_sample_rates_hz": [16000, 48000, 8000],
            "preferred_channels": [1]
        }

# Пример использования (для отладки, будет удален или закомментирован)
if __name__ == '__main__':
    # Настройка логирования через глобальную конфигурацию
    try:
        from logging_config import configure_logging
        configure_logging()
    except ImportError:
        # Fallback на базовую настройку, если глобальная конфигурация недоступна
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.info("Запуск примера YandexSpeechRecognizer")

    api_key_from_env = os.environ.get("YANDEX_API_KEY")
    if not api_key_from_env:
        logger.error("Переменная окружения YANDEX_API_KEY не установлена. Пропуск теста.")
        sys.exit(1)

    config_test = {
        "api_key": api_key_from_env,
        "language_code": "ru-RU",
        "model": "general",
        "sample_rate_hertz": 16000,
        "audio_format_hint": "lpcm" # Добавлено для полноты конфига
    }

    try:
        recognizer = YandexSpeechRecognizer(config_test)
        logger.info("Распознаватель Yandex создан.")

        logger.info(f"Поддерживаемые языки: {YandexSpeechRecognizer.get_supported_languages()}")
        logger.info(f"Доступные модели: {YandexSpeechRecognizer.get_available_models()}")
        # logger.info(f"Схема конфигурации: {YandexSpeechRecognizer.get_config_schema()}") # Может быть многословно
        logger.info(f"Требования к формату аудио: {YandexSpeechRecognizer.get_audio_format_requirements()}")

        test_audio_path = "test_audio_yandex.wav"
        if not os.path.exists(test_audio_path):
            try:
                import numpy as np
                sample_rate = 16000
                duration = 2
                frequency = 440
                t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
                audio_signal = 0.5 * np.sin(2 * np.pi * frequency * t)
                audio_pcm = (audio_signal * 32767).astype(np.int16)
                with wave.open(test_audio_path, 'w') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(sample_rate)
                    wf.writeframes(audio_pcm.tobytes())
                logger.info(f"Создан тестовый аудиофайл: {test_audio_path}")
            except ImportError:
                logger.warning("NumPy не установлен, не удалось создать тестовый WAV.")
            except Exception as e_create_wav:
                logger.error(f"Не удалось создать тестовый WAV: {e_create_wav}")

        if os.path.exists(test_audio_path):
            logger.info(f"Тестирование recognize_file с {test_audio_path}...")
            try:
                results = recognizer.recognize_file(test_audio_path)
                logger.info(f"Результаты распознавания файла ({test_audio_path}):")
                for res_idx, result_alt in enumerate(results):
                    logger.info(f"  Альтернатива #{res_idx + 1}: Текст: {result_alt.get('text')}, Уверенность: {result_alt.get('confidence')}")
            except Exception as e_rec_file:
                logger.error(f"Ошибка при распознавании файла: {e_rec_file}")
        else:
            logger.warning(f"Тестовый файл {test_audio_path} не найден, пропуск теста recognize_file.")

        if os.path.exists(test_audio_path):
            try:
                with wave.open(test_audio_path, 'rb') as wf:
                    raw_pcm_data = wf.readframes(wf.getnframes())
                    if raw_pcm_data:
                        logger.info(f"Тестирование recognize_audio_data с {len(raw_pcm_data)} байт аудио...")
                        # Для recognize_audio_data нужны параметры из config, они уже там
                        results_data = recognizer.recognize_audio_data(raw_pcm_data)
                        logger.info(f"Результаты распознавания аудиоданных:")
                        for res_idx, result_alt in enumerate(results_data):
                            logger.info(f"  Альтернатива #{res_idx + 1}: Текст: {result_alt.get('text')}, Уверенность: {result_alt.get('confidence')}")
                    else:
                        logger.warning("Не удалось прочитать аудиоданные из тестового файла.")
            except Exception as e_rec_data:
                logger.error(f"Ошибка при распознавании аудиоданных: {e_rec_data}")

    except ValueError as ve:
        logger.error(f"Ошибка конфигурации: {ve}")
    except ConnectionError as ce:
        logger.error(f"Ошибка соединения с Yandex: {ce}")
    except RuntimeError as rte:
        logger.error(f"Общая ошибка выполнения: {rte}")
    except Exception as e:
        logger.error(f"Непредвиденная ошибка в примере: {e}")

    logger.info("Завершение примера YandexSpeechRecognizer.")

# Алиас для обратной совместимости
SpeechRecognizer = YandexSpeechRecognizer

# Конец файла
