from abc import ABC, abstractmethod
from typing import List, Dict, Any, Union

class BaseRecognizer(ABC):
    """Абстрактный базовый класс для всех распознавателей речи."""

    @abstractmethod
    def __init__(self, config: Dict[str, Any]):
        """
        Инициализирует распознаватель с заданной конфигурацией.

        :param config: Словарь с конфигурационными параметрами.
        """
        pass

    @abstractmethod
    def recognize_file(self, file_path: str) -> List[Dict[str, Union[str, float, List[Dict[str, Union[str, float]]]]]]:
        """
        Распознает речь из аудиофайла.

        :param file_path: Путь к аудиофайлу.
        :return: Список словарей, где каждый словарь представляет один вариант распознавания.
                 Каждый вариант содержит 'text' (распознанный текст),
                 'confidence' (уверенность, если доступно),
                 и опционально 'words' (список слов с временными метками).
        """
        pass

    @abstractmethod
    def recognize_audio_data(self, audio_data: bytes) -> List[Dict[str, Union[str, float, List[Dict[str, Union[str, float]]]]]]:
        """
        Распознает речь из аудиоданных в памяти.

        :param audio_data: Аудиоданные в виде байтов.
        :return: Список словарей, аналогичный возвращаемому `recognize_file`.
        """
        pass

    @staticmethod
    @abstractmethod
    def get_supported_languages() -> List[Dict[str, str]]:
        """
        Возвращает список поддерживаемых языков.

        :return: Список словарей, где каждый словарь содержит 'code' (код языка, например, 'ru-RU')
                 и 'name' (название языка, например, 'Русский').
        """
        pass

    @staticmethod
    @abstractmethod
    def get_available_models(language_code: str) -> List[Dict[str, str]]:
        """
        Возвращает список доступных моделей для указанного языка.

        :param language_code: Код языка.
        :return: Список словарей, где каждый словарь содержит 'id' (идентификатор модели)
                 и 'name' (описание модели).
        """
        pass

    @staticmethod
    @abstractmethod
    def get_config_schema() -> Dict[str, Any]:
        """
        Возвращает JSON-схему для конфигурационных параметров этого распознавателя.

        :return: Словарь, представляющий JSON-схему.
        """
        pass

    @staticmethod
    @abstractmethod
    def get_audio_format_requirements() -> Dict[str, Any]:
        """
        Возвращает требования к формату аудио.

        :return: Словарь с описанием требований, например:
                 {'format': 'wav', 'sample_rate_hz': 16000, 'channels': 1, 'encoding': 'pcm_s16le'}
        """
        pass