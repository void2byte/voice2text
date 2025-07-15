from .base_recognizer import BaseRecognizer
import json
import os
import wave
from typing import List, Dict, Union
from .base_recognizer import BaseRecognizer
from voice_control.utils.vosk_model_loader import VoskModelManager

# Попытка импортировать vosk, если не установлен, будет ошибка при создании экземпляра
try:
    from vosk import Model, KaldiRecognizer, SetLogLevel
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False

class VoskSpeechRecognizer(BaseRecognizer):
    """
    Реализация распознавателя речи с использованием Vosk API для локального распознавания.
    """

    def __init__(self, config: dict, parent_widget=None):
        """
        Инициализирует VoskSpeechRecognizer.

        Args:
            config (dict): Словарь конфигурации.
                           Ожидаемые ключи:
                           - "model_path": Путь к директории с моделью Vosk.
                           - "language": Код языка (например, "ru", "en-us").
                                         Этот параметр используется для выбора модели, если model_path не указан
                                         или для дополнительной информации, но основная модель определяется model_path.
                           - "sample_rate" (int, optional): Частота дискретизации аудио. По умолчанию 16000.
            parent_widget: Родительский виджет для отображения диалогов (опционально)
        """
        if not VOSK_AVAILABLE:
            raise RuntimeError("Библиотека Vosk не установлена. Пожалуйста, установите ее: pip install vosk")

        self.model_path = config.get("model_path")
        self.language = config.get("language", "ru") # По умолчанию русский, если не указан
        self.sample_rate = config.get("sample_rate", 16000)
        self.parent_widget = parent_widget

        if not self.model_path:
            # Попытка найти модель по языку в стандартном месте (требует доработки для реального использования)
            # Например, можно иметь словарь путей к моделям по умолчанию
            # self.model_path = self._find_default_model_path(self.language)
            raise ValueError("Путь к модели Vosk ('model_path') должен быть указан в конфигурации.")

        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Директория с моделью Vosk не найдена: {self.model_path}")

        # Отключаем логирование Vosk, чтобы не засорять вывод
        SetLogLevel(-1)

        # Используем VoskModelManager для загрузки модели
        self.model_manager = VoskModelManager()

        try:
            # Загружаем модель с возможностью отображения диалога прогресса
            success = self.model_manager.load_model(
                self.model_path, 
                self.parent_widget, 
                show_dialog=True
            )
            
            if not success:
                raise RuntimeError("Загрузка модели была отменена или произошла ошибка")
            
            # Получаем загруженные объекты из менеджера
            self.model = self.model_manager.current_model
            self.recognizer = self.model_manager.get_recognizer()
                
            self.recognizer.SetWords(True) # Включаем возврат информации по словам
        except Exception as e:
            raise RuntimeError(f"Ошибка инициализации модели Vosk из {self.model_path}: {e}")

    def recognize_audio_data(self, audio_data: bytes) -> dict:
        """
        Распознает речь из аудиоданных (в формате WAV PCM 16-bit mono).

        Args:
            audio_data (bytes): Аудиоданные.

        Returns:
            dict: Словарь с результатами распознавания в формате:
                  {"success": True/False, "text": "распознанный текст", "results": [...]}
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Принудительно устанавливаем уровень логирования для диагностики
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        try:
            # Диагностическое логирование входных данных
            logger.info(f"VoskSpeechRecognizer: Получены аудиоданные размером {len(audio_data)} байт")
            logger.info(f"VoskSpeechRecognizer: Sample rate модели: {self.sample_rate}")
            print(f"[DEBUG] VoskSpeechRecognizer: Получены аудиоданные размером {len(audio_data)} байт")  # Дублируем в print для гарантии
            
            # Проверяем, что данные не пустые
            if not audio_data:
                logger.warning("VoskSpeechRecognizer: Получены пустые аудиоданные")
                return {
                    "success": False,
                    "error": "Пустые аудиоданные"
                }
            
            # Логируем первые несколько байт для диагностики формата
            if len(audio_data) >= 44:  # Минимальный размер WAV заголовка
                header_info = audio_data[:44]
                logger.info(f"VoskSpeechRecognizer: Первые 12 байт аудиоданных: {header_info[:12]}")
                # Проверяем WAV заголовок
                if header_info[:4] == b'RIFF' and header_info[8:12] == b'WAVE':
                    logger.info("VoskSpeechRecognizer: Обнаружен корректный WAV заголовок")
                else:
                    logger.warning("VoskSpeechRecognizer: WAV заголовок не обнаружен или некорректен")
            else:
                logger.warning(f"VoskSpeechRecognizer: Размер данных ({len(audio_data)} байт) меньше минимального WAV заголовка (44 байта)")
            
            # Попытка распознавания: передаем все аудиоданные и получаем финальный результат
            logger.info("VoskSpeechRecognizer: Передаем все аудиоданные в распознаватель с AcceptWaveform")
            self.recognizer.AcceptWaveform(audio_data)
            
            result_json = self.recognizer.FinalResult()
            result_data = json.loads(result_json)
            logger.info(f"VoskSpeechRecognizer: Распознан текст: {result_data.get('text')}")
            
            result = json.loads(result_json)
            logger.info(f"VoskSpeechRecognizer: Распарсенный результат: {result}")

            # В финальном результате текст находится в ключе 'text'
            text = result.get("text", "").strip()
            logger.info(f"VoskSpeechRecognizer: Извлеченный текст: '{text}'")

            if not text:
                logger.warning(f"VoskSpeechRecognizer: Текст не распознан. Полный результат: {result}")
                return {
                    "success": False,
                    "error": "Текст не распознан"
                }

            # Формируем словари слов с временем начала и конца
            # FinalResult() возвращает 'result' ключ со словами, если SetWords(True)
            words_info = []
            if "result" in result and isinstance(result["result"], list):
                words_info = [
                    {
                        "word": word_data["word"],
                        "start_time": word_data["start"],
                        "end_time": word_data["end"],
                        "confidence": word_data.get("conf", 1.0) # Уверенность для слова
                    }
                    for word_data in result["result"]
                ]
            
            # Формируем результат в том же формате, что и Yandex
            result_item = {
                "text": text,
                "confidence": 1.0, # Общая уверенность для финального результата не всегда доступна
                "words": words_info
            }

            return {
                "success": True,
                "text": text,
                "normalized_text": text,
                "results": [result_item]
            }
        except Exception as e:
            # Логирование ошибки
            print(f"Ошибка во время распознавания аудиоданных Vosk: {e}")
            return {
                "success": False,
                "error": f"Ошибка распознавания: {e}"
            }

    def recognize_file(self, file_path: str) -> dict:
        """
        Распознает речь из аудиофайла (ожидается WAV PCM 16-bit mono).

        Args:
            file_path (str): Путь к аудиофайлу.

        Returns:
            dict: Словарь с результатами распознавания в формате:
                  {"success": True/False, "text": "распознанный текст", "results": [...]}
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Аудиофайл не найден: {file_path}")

        try:
            with wave.open(file_path, "rb") as wf:
                if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
                    # TODO: Добавить конвертацию, если формат не поддерживается
                    # Пока что просто вызываем ошибку или предупреждение
                    raise ValueError(
                        f"Аудиофайл {file_path} должен быть в формате WAV PCM 16-bit mono. "
                        f"Текущий формат: каналы={wf.getnchannels()}, ширина сэмпла={wf.getsampwidth()}, "
                        f"компрессия={wf.getcomptype()}"
                    )
                
                # Проверяем sample_rate, если он отличается от ожидаемого моделью
                if wf.getframerate() != self.sample_rate:
                    # TODO: Реализовать ресемплинг или предупреждать пользователя
                    # print(f"Предупреждение: Частота дискретизации файла {wf.getframerate()} Hz "
                    #       f"отличается от ожидаемой моделью {self.sample_rate} Hz.")
                    # Пока что будем пытаться распознать как есть, но это может повлиять на качество
                    # Для корректной работы Vosk требует совпадения sample_rate
                    # Пересоздадим распознаватель с частотой файла, если это возможно и модель поддерживает
                    # Это упрощение, в реальности лучше конвертировать аудио.
                    try:
                        temp_recognizer = KaldiRecognizer(self.model, wf.getframerate())
                        temp_recognizer.SetWords(True)
                    except Exception as e:
                         raise ValueError(f"Модель Vosk не поддерживает частоту дискретизации {wf.getframerate()} Hz файла {file_path}. Ошибка: {e}")
                else:
                    temp_recognizer = self.recognizer # Используем основной распознаватель

                results = []
                while True:
                    data = wf.readframes(4000) # Читаем порциями
                    if len(data) == 0:
                        break
                    if temp_recognizer.AcceptWaveform(data):
                        result_json = temp_recognizer.Result()
                        # print(f"Vosk Result: {result_json}") # Для отладки
                        res = json.loads(result_json)
                        if res.get("text"):
                            words_info = []
                            if "result" in res and isinstance(res["result"], list):
                                words_info = [
                                    {
                                        "word": word_data["word"],
                                        "start_time": word_data["start"],
                                        "end_time": word_data["end"],
                                        "confidence": word_data.get("conf", 1.0)
                                    }
                                    for word_data in res["result"]
                                ]
                            results.append({
                                "text": res["text"],
                                "confidence": 1.0, 
                                "words": words_info
                            })
                
                # Получаем финальный результат после окончания файла
                final_result_json = temp_recognizer.FinalResult()
                # print(f"Vosk Final Result: {final_result_json}") # Для отладки
                final_res = json.loads(final_result_json)
                if final_res.get("text") and (not results or results[-1]["text"] != final_res["text"]):
                    words_info = []
                    if "result" in final_res and isinstance(final_res["result"], list):
                        words_info = [
                            {
                                "word": word_data["word"],
                                "start_time": word_data["start"],
                                "end_time": word_data["end"],
                                "confidence": word_data.get("conf", 1.0)
                            }
                            for word_data in final_res["result"]
                        ]
                    results.append({
                        "text": final_res["text"],
                        "confidence": 1.0,
                        "words": words_info
                    })
                
                # Формируем результат в том же формате, что и Yandex
                if results:
                    full_text = " ".join([result.get("text", "") for result in results if result.get("text")])
                    return {
                        "success": True,
                        "text": full_text,
                        "normalized_text": full_text,
                        "results": results
                    }
                else:
                    return {
                        "success": False,
                        "error": "Текст не распознан"
                    }
        except wave.Error as e:
            raise ValueError(f"Ошибка чтения WAV файла {file_path}: {e}")
        except Exception as e:
            # Логирование ошибки
            print(f"Ошибка во время распознавания файла Vosk ({file_path}): {e}")
            return {
                "success": False,
                "error": f"Ошибка распознавания файла: {e}"
            }

    @staticmethod
    def get_supported_languages() -> List[Dict[str, str]]:
        """
        Возвращает список кодов поддерживаемых языков.
        Зависит от доступных моделей Vosk.
        """
        # Это примерный список. Реальный список зависит от того, какие модели пользователь скачал/установил.
        # Можно сканировать директорию с моделями или предоставить пользователю возможность указать их.
        return [
            {'code': 'ru', 'name': 'Русский'},
            {'code': 'en-us', 'name': 'English (US)'},
            {'code': 'de', 'name': 'Deutsch'},
            {'code': 'fr', 'name': 'Français'},
            {'code': 'es', 'name': 'Español'},
            {'code': 'pt', 'name': 'Português'},
            {'code': 'zh', 'name': '中文'},
            {'code': 'ja', 'name': '日本語'},
            {'code': 'ko', 'name': '한국어'},
            {'code': 'it', 'name': 'Italiano'},
            {'code': 'nl', 'name': 'Nederlands'},
            {'code': 'pl', 'name': 'Polski'},
            {'code': 'uk', 'name': 'Українська'}
        ]

    @staticmethod
    def get_available_models(language: str = None) -> list[str]:
        """
        Возвращает список доступных моделей для указанного языка.
        Для Vosk, "модель" - это обычно путь к директории модели.
        Пользователь должен сам скачать и указать путь к модели.
        Этот метод может быть использован для отображения списка "известных" путей или имен моделей.
        """
        # Vosk не имеет централизованного списка моделей как облачные API.
        # Модели скачиваются пользователем. Этот метод может быть заглушкой
        # или пытаться найти модели в предопределенной директории.
        # Пример: return ["vosk-model-ru-0.22", "vosk-model-small-en-us-0.15"]
        # На данном этапе, мы ожидаем, что пользователь укажет полный путь в 'model_path'.
        if language:
            return [f"model_for_{language}"] # Заглушка
        return ["general_model"] # Заглушка

    @staticmethod
    def get_config_schema() -> dict:
        """
        Возвращает JSON-схему для конфигурационного словаря этого распознавателя.
        """
        return {
            "type": "object",
            "properties": {
                "model_path": {
                    "type": "string",
                    "description": "Путь к директории с моделью Vosk (например, /path/to/vosk-model-ru-0.22)."
                },
                "language": {
                    "type": "string",
                    "description": "Код языка (например, 'ru', 'en-us'). Используется для информации, основная модель определяется model_path.",
                    "default": "ru"
                },
                "sample_rate": {
                    "type": "integer",
                    "description": "Ожидаемая частота дискретизации аудио (Гц). По умолчанию 16000.",
                    "default": 16000
                }
            },
            "required": ["model_path"]
        }

    @staticmethod
    def get_audio_format_requirements() -> dict:
        """
        Возвращает словарь с требованиями к аудиоформату.
        """
        return {
            "format": "WAV",
            "encoding": "PCM_S16LE", # 16-bit Signed Little Endian PCM
            "channels": 1, # Mono
            "sample_rate_hertz": "Зависит от модели, обычно 8000, 16000 или 48000. Указывается в config['sample_rate']"
        }

    def cleanup(self):
        """
        Освобождает ресурсы, используемые распознавателем.
        """
        # Выгружаем модель через менеджер
        if hasattr(self, 'model_manager'):
            self.model_manager.unload_model()
        
        self.model = None
        self.recognizer = None

# Пример использования (для тестирования):
if __name__ == '__main__':
    if not VOSK_AVAILABLE:
        print("Vosk не доступен, пример не может быть запущен.")
    else:
        # Укажите корректный путь к вашей модели Vosk
        # Например, скачайте модель отсюда: https://alphacephei.com/vosk/models
        # и распакуйте ее.
        MODEL_DIR = "C:/path/to/your/vosk-model-small-ru-0.22" # <--- ЗАМЕНИТЕ НА ВАШ ПУТЬ

        if not os.path.exists(MODEL_DIR) or "ЗАМЕНИТЕ НА ВАШ ПУТЬ" in MODEL_DIR:
            print(f"Пожалуйста, укажите корректный путь к модели Vosk в переменной MODEL_DIR.")
            print(f"Текущий путь: {MODEL_DIR}")
            exit()

        config_vosk = {
            "model_path": MODEL_DIR,
            "language": "ru",
            "sample_rate": 16000
        }

        try:
            recognizer = VoskSpeechRecognizer(config_vosk)
            print("Vosk Recognizer инициализирован.")
            print(f"Поддерживаемые языки (примерный список): {VoskSpeechRecognizer.get_supported_languages()}")
            print(f"Схема конфигурации: {json.dumps(VoskSpeechRecognizer.get_config_schema(), indent=2, ensure_ascii=False)}")
            print(f"Требования к аудио: {json.dumps(VoskSpeechRecognizer.get_audio_format_requirements(), indent=2, ensure_ascii=False)}")

            # Создадим тестовый WAV файл для распознавания
            test_wav_path = "test_vosk_audio.wav"
            sample_rate = 16000
            duration = 2  # секунды
            frequency = 440 # Hz (нота Ля)
            n_frames = int(sample_rate * duration)
            
            # Простые синусоидальные данные (не реальная речь, просто для теста формата)
            # В реальности используйте файл с реальной речью
            # Этот блок создаст тишину, т.к. синусоида не является речью
            # Замените это на чтение реального аудиофайла для теста распознавания
            # audio_content = b'\x00\x00' * n_frames # Тишина

            # Для реального теста, вам нужен файл test.wav в формате PCM 16kHz 16bit mono
            # Пример: скачайте тестовый файл или запишите свой.
            # Если у вас есть файл 'test.wav' в текущей директории:
            # test_wav_path = "test.wav"
            # if os.path.exists(test_wav_path):
            #     print(f"\nРаспознавание файла: {test_wav_path}")
            #     results = recognizer.recognize_file(test_wav_path)
            #     if results:
            #         for res in results:
            #             print(f"  Текст: {res['text']}")
            #             if res['words']:
            #                 print(f"  Слова: {res['words']}")
            #     else:
            #         print("  Ничего не распознано или произошла ошибка.")
            # else:
            #     print(f"Тестовый файл {test_wav_path} не найден. Пропустим тест распознавания файла.")

            print("\nСоздайте или укажите путь к реальному аудиофайлу (WAV, 16kHz, 16-bit, mono) для тестирования.")
            print("Например, поместите файл 'test.wav' в директорию скрипта и раскомментируйте блок выше.")

        except RuntimeError as e:
            print(f"Ошибка примера Vosk: {e}")
        except FileNotFoundError as e:
            print(f"Ошибка пути к модели: {e}")
        except ValueError as e:
            print(f"Ошибка значения: {e}")