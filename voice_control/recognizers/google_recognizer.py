from voice_control.recognizers.base_recognizer import BaseRecognizer
# from google.cloud import speech
from typing import List, Dict, Union
import os

class GoogleSpeechRecognizer(BaseRecognizer):
    """Google Cloud Speech-to-Text Recognizer."""

    def __init__(self, config: dict):
        """Initializes the Google Cloud Speech-to-Text recognizer.

        Args:
            config: Configuration dictionary containing 'api_key' or 'google_credentials_path'.
        """
        super().__init__(config)
        self.client = None
        
        # Поддерживаем как api_key, так и google_credentials_path для совместимости
        if self.config.get('google_credentials_path'):
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.config['google_credentials_path']
            self.client = speech.SpeechClient()
        elif self.config.get('api_key'):
            # Для упрощения, пока что выводим предупреждение
            # В реальной реализации здесь должна быть настройка аутентификации через API ключ
            print(f"Warning: API key authentication not fully implemented. Use service account JSON file.")
            print(f"Provided API key: {self.config['api_key'][:10]}...")
            # TODO: Реализовать аутентификацию через API ключ
            # Возможно, потребуется создать credentials объект из API ключа
        else:
            print("Warning: Neither Google Cloud credentials path nor API key provided. Recognizer will not function.")

    def recognize_audio_data(self, audio_data: bytes, language: str = 'en-US', sample_rate: int = 16000, **kwargs) -> List[Dict[str, Union[str, float, List[Dict[str, Union[str, float]]]]]]:
        """Recognizes speech from audio data.

        Args:
            audio_data: Raw audio data.
            language: Language code (e.g., 'en-US', 'ru-RU').
            sample_rate: Sample rate of the audio.
            **kwargs: Additional keyword arguments for recognition config.

        Returns:
            Recognized text or an empty string if recognition fails.
        """
        if not self.client:
            return []

        recognition_config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,  # Assuming PCM16
            sample_rate_hertz=sample_rate,
            language_code=language,
            **kwargs
        )
        audio = speech.RecognitionAudio(content=audio_data)

        try:
            response = self.client.recognize(config=recognition_config, audio=audio)
            if response.results and response.results[0].alternatives:
                return [{
                    "text": response.results[0].alternatives[0].transcript,
                    "confidence": response.results[0].alternatives[0].confidence if hasattr(response.results[0].alternatives[0], 'confidence') else 1.0,
                    "words": []
                }]
            return []
        except Exception as e:
            print(f"Google Cloud recognition error: {e}")
            return []

    def recognize_file(self, file_path: str, language: str = 'en-US', **kwargs) -> List[Dict[str, Union[str, float, List[Dict[str, Union[str, float]]]]]]:
        """Recognizes speech from an audio file.

        Args:
            file_path: Path to the audio file.
            language: Language code.
            **kwargs: Additional keyword arguments for recognition config.

        Returns:
            Recognized text or an empty string if recognition fails.
        """
        if not self.client:
            return "Error: Google Cloud client not initialized. Check credentials."

        try:
            with open(file_path, 'rb') as audio_file:
                content = audio_file.read()
            
            # Determine encoding and sample rate from file if possible, or require them
            # For simplicity, assuming LINEAR16 and requiring sample_rate_hertz in kwargs if not default
            sample_rate = kwargs.pop('sample_rate_hertz', 16000) # Default or from kwargs

            recognition_config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16, # Or determine from file type
                sample_rate_hertz=sample_rate,
                language_code=language,
                **kwargs
            )
            audio = speech.RecognitionAudio(content=content)

            response = self.client.recognize(config=recognition_config, audio=audio)
            if response.results and response.results[0].alternatives:
                return [{
                    "text": response.results[0].alternatives[0].transcript,
                    "confidence": response.results[0].alternatives[0].confidence if hasattr(response.results[0].alternatives[0], 'confidence') else 1.0,
                    "words": []
                }]
            return []
        except FileNotFoundError:
            print(f"Error: File not found at {file_path}")
            return []
        except Exception as e:
            print(f"Google Cloud file recognition error: {e}")
            return []

    @staticmethod
    def get_supported_languages() -> List[Dict[str, str]]:
        """Returns a list of supported language codes."""
        # This list can be extensive. Refer to Google Cloud documentation for a full list.
        # https://cloud.google.com/speech-to-text/docs/languages
        return [
            {'code': 'en-US', 'name': 'English (US)'},
            {'code': 'en-GB', 'name': 'English (UK)'},
            {'code': 'es-ES', 'name': 'Spanish (Spain)'},
            {'code': 'fr-FR', 'name': 'French (France)'},
            {'code': 'de-DE', 'name': 'German (Germany)'},
            {'code': 'it-IT', 'name': 'Italian (Italy)'},
            {'code': 'ja-JP', 'name': 'Japanese (Japan)'},
            {'code': 'ko-KR', 'name': 'Korean (Korea)'},
            {'code': 'pt-BR', 'name': 'Portuguese (Brazil)'},
            {'code': 'ru-RU', 'name': 'Russian (Russia)'},
            {'code': 'zh-CN', 'name': 'Chinese (Simplified)'},
            {'code': 'zh-TW', 'name': 'Chinese (Traditional)'}
        ]

    @staticmethod
    def get_available_models(language: str = None) -> list:
        """Returns a list of available models, optionally filtered by language."""
        # Google Cloud Speech-to-Text uses a default model based on language and context.
        # Specific model selection is more nuanced (e.g., 'medical', 'phone_call').
        # For simplicity, we can return a generic list or indicate that model selection is implicit.
        # https://cloud.google.com/speech-to-text/docs/speech-to-text-models
        return ['default', 'command_and_search', 'phone_call', 'video', 'medical'] # Example models

    @staticmethod
    def get_config_schema() -> dict:
        """Returns the JSON schema for the recognizer's configuration."""
        return {
            "type": "object",
            "properties": {
                "google_credentials_path": {
                    "type": "string",
                    "description": "Path to the Google Cloud JSON credentials file."
                },
                "language": {
                    "type": "string",
                    "description": "Default language code (e.g., en-US).",
                    "default": "en-US",
                    "enum": GoogleSpeechRecognizer.get_supported_languages()
                },
                "model": {
                    "type": "string",
                    "description": "Recognition model to use.",
                    "default": "default",
                    "enum": GoogleSpeechRecognizer.get_available_models()
                }
                # Add other Google-specific config options here if needed
            },
            "required": ["google_credentials_path"]
        }

    @staticmethod
    def get_audio_requirements() -> dict:
        """Returns the audio format requirements for this recognizer."""
        return {
            "format": ["LINEAR16", "FLAC", "MULAW", "AMR", "AMR_WB", "OGG_OPUS", "SPEEX_WITH_HEADER_BYTE", "WEBM_OPUS"],
            "channels": "Mono (Stereo may be downmixed or only first channel processed depending on config)",
            "sample_rate": "8000-48000 Hz (16000 Hz recommended for best results)"
            # Refer to https://cloud.google.com/speech-to-text/docs/basics#audio-encodings
        }

    def is_available(self) -> bool:
        """Checks if the recognizer is available (e.g., credentials are set and valid)."""
        return self.client is not None