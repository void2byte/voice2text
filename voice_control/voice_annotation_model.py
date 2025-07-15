import logging
from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)

class VoiceAnnotationModel(QObject):
    # Сигналы для уведомления об изменениях
    text_changed = Signal(str)
    is_recording_changed = Signal(bool)
    is_recognizing_changed = Signal(bool)
    error_message_changed = Signal(str)
    settings_loaded = Signal()

    def __init__(self, settings_manager=None, parent=None):
        super().__init__(parent)
        self._current_text = ""
        self._is_recording = False
        self._is_recognizing = False
        self._error_message = ""
        self._annotation_emitted_once = False

        # Настройки по умолчанию (будут перезаписаны при загрузке)
        self.max_duration_sec = 60
        self.auto_recognition_enabled = True
        self.audio_quality = "medium"
        self.voice_command_timeout_sec = 5 
        self.vosk_model_size = "small"

        if settings_manager:
            self.load_settings(settings_manager)

    @property
    def current_text(self) -> str:
        return self._current_text

    @current_text.setter
    def current_text(self, value: str):
        if self._current_text != value:
            self._current_text = value
            self.text_changed.emit(self._current_text)

    @property
    def is_recording(self) -> bool:
        return self._is_recording

    @is_recording.setter
    def is_recording(self, value: bool):
        if self._is_recording != value:
            self._is_recording = value
            self.is_recording_changed.emit(self._is_recording)

    @property
    def is_recognizing(self) -> bool:
        return self._is_recognizing

    @is_recognizing.setter
    def is_recognizing(self, value: bool):
        if self._is_recognizing != value:
            self._is_recognizing = value
            self.is_recognizing_changed.emit(self._is_recognizing)
    
    @property
    def error_message(self) -> str:
        return self._error_message

    @error_message.setter
    def error_message(self, value: str):
        if self._error_message != value:
            self._error_message = value
            self.error_message_changed.emit(self._error_message)

    @property
    def annotation_emitted_once(self) -> bool:
        return self._annotation_emitted_once

    @annotation_emitted_once.setter
    def annotation_emitted_once(self, value: bool):
        self._annotation_emitted_once = value

    def load_settings(self, settings_manager):
        if not settings_manager:
            logger.warning(self.tr("VoiceAnnotationModel: Менеджер настроек не предоставлен. Используются значения по умолчанию."))
            self.settings_loaded.emit() # Сообщаем, что настройки (по умолчанию) 'загружены'
            return
        try:
            self.max_duration_sec = settings_manager.get_setting("voice_annotation/max_duration", self.max_duration_sec, expected_type=int)
            self.auto_recognition_enabled = settings_manager.get_setting("voice_annotation/auto_recognition", self.auto_recognition_enabled, expected_type=bool)
            self.voice_command_timeout_sec = settings_manager.get_setting("voice_recognition/voice_command_timeout", self.voice_command_timeout_sec, expected_type=int)
            self.vosk_model_size = settings_manager.get_setting("voice_recognition/model_size", self.vosk_model_size, expected_type=str)
            
            logger.info(self.tr("VoiceAnnotationModel: Настройки загружены: max_duration={}, auto_rec={}").format(self.max_duration_sec, self.auto_recognition_enabled))
            self.settings_loaded.emit()
        except Exception as e:
            # Метод get_setting уже логирует ошибки, но можно оставить и общий лог
            logger.error(self.tr("VoiceAnnotationModel: Ошибка при загрузке настроек (общая): {}").format(e))
            # В случае ошибки, атрибуты сохранят свои значения по умолчанию, заданные в __init__
            self.settings_loaded.emit() # Все равно эмитируем, чтобы UI мог продолжить работу

    def reset_state(self):
        """Resets model state to default values."""
        self.current_text = ""
        self.is_recording = False
        self.is_recognizing = False
        self.error_message = ""
        self.annotation_emitted_once = False
        logger.debug(self.tr("VoiceAnnotationModel: Состояние сброшено."))
