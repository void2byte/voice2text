"""Диалог загрузки модели Vosk с прогрессом и возможностью отмены."""
import logging
import os
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QProgressBar, QPushButton, QMessageBox)
from PySide6.QtCore import Signal, QThread, QTimer
from vosk import Model, KaldiRecognizer
import json

logger = logging.getLogger(__name__)

class ModelLoadingDialog(QDialog):
    """Диалог для отображения прогресса загрузки модели Vosk."""
    
    def __init__(self, model_path, parent=None):
        super().__init__(parent)
        self.model_path = model_path
        self.model = None
        self.recognizer = None
        self.loading_thread = None
        self.cancelled = False
        
        self.setWindowTitle("Загрузка модели Vosk")
        self.setModal(True)
        self.setFixedSize(400, 150)
        
        self._init_ui()
        self._start_loading()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Информационная метка
        self.info_label = QLabel(f"Загрузка модели: {os.path.basename(self.model_path)}")
        layout.addWidget(self.info_label)
        
        # Прогресс-бар (неопределенный)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Неопределенный прогресс
        layout.addWidget(self.progress_bar)
        
        # Кнопки
        button_layout = QHBoxLayout()
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self._cancel_loading)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
    
    def _start_loading(self):
        """Запускает загрузку модели в отдельном потоке."""
        self.loading_thread = ModelLoadingThread(self.model_path)
        self.loading_thread.model_loaded.connect(self._on_model_loaded)
        self.loading_thread.loading_error.connect(self._on_loading_error)
        self.loading_thread.start()
    
    def _cancel_loading(self):
        """Отменяет загрузку модели."""
        self.cancelled = True
        if self.loading_thread and self.loading_thread.isRunning():
            self.loading_thread.terminate()
            self.loading_thread.wait(3000)  # Ждем 3 секунды
        self.reject()
    
    def _on_model_loaded(self, model, recognizer):
        """Обработчик успешной загрузки модели."""
        if not self.cancelled:
            self.model = model
            self.recognizer = recognizer
            self.accept()
    
    def _on_loading_error(self, error_message):
        """Обработчик ошибки загрузки модели."""
        if not self.cancelled:
            QMessageBox.critical(self, "Ошибка загрузки модели", 
                               f"Не удалось загрузить модель Vosk:\n{error_message}")
            self.reject()
    
    def get_model_and_recognizer(self):
        """Возвращает загруженную модель и распознаватель."""
        return self.model, self.recognizer


class ModelLoadingThread(QThread):
    """Поток для загрузки модели Vosk."""
    
    model_loaded = Signal(object, object)  # model, recognizer
    loading_error = Signal(str)
    
    def __init__(self, model_path):
        super().__init__()
        self.model_path = model_path
    
    def run(self):
        """Загружает модель Vosk в отдельном потоке."""
        try:
            logger.info(f"Начало загрузки модели Vosk: {self.model_path}")
            
            # Проверяем существование пути
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Путь к модели не существует: {self.model_path}")
            
            if not os.path.isdir(self.model_path):
                raise ValueError(f"Путь к модели должен быть директорией: {self.model_path}")
            
            # Загружаем модель (это может занять много времени)
            model = Model(self.model_path)
            
            # Создаем распознаватель с частотой дискретизации 16000 Гц
            recognizer = KaldiRecognizer(model, 16000)
            
            logger.info(f"Модель Vosk успешно загружена: {self.model_path}")
            self.model_loaded.emit(model, recognizer)
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Ошибка при загрузке модели Vosk: {error_msg}")
            self.loading_error.emit(error_msg)


class VoskModelTester:
    """Класс для тестирования загрузки модели Vosk."""
    
    @staticmethod
    def test_model_loading(model_path, parent_widget=None):
        """
        Тестирует загрузку модели Vosk с отображением диалога прогресса.
        
        Args:
            model_path (str): Путь к модели Vosk
            parent_widget: Родительский виджет для диалога
            
        Returns:
            tuple: (success, model, recognizer) где success - bool, 
                   model и recognizer - объекты Vosk или None при ошибке
        """
        dialog = ModelLoadingDialog(model_path, parent_widget)
        result = dialog.exec()
        
        if result == QDialog.Accepted:
            model, recognizer = dialog.get_model_and_recognizer()
            return True, model, recognizer
        else:
            return False, None, None
    
    @staticmethod
    def validate_model_path(model_path):
        """
        Проверяет корректность пути к модели Vosk.
        
        Args:
            model_path (str): Путь к модели
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not model_path or not model_path.strip():
            return False, "Путь к модели не указан"
        
        if not os.path.exists(model_path):
            return False, f"Путь к модели не существует: {model_path}"
        
        if not os.path.isdir(model_path):
            return False, f"Путь к модели должен быть директорией: {model_path}"
        
        # Проверяем наличие основных файлов модели
        required_files = ["am", "graph", "ivector"]  # Основные компоненты модели Vosk
        missing_components = []
        
        for component in required_files:
            component_path = os.path.join(model_path, component)
            if not os.path.exists(component_path):
                missing_components.append(component)
        
        if missing_components:
            return False, f"В модели отсутствуют компоненты: {', '.join(missing_components)}"
        
        return True, ""


class VoskModelManager:
    """Менеджер для работы с моделями Vosk."""
    
    def __init__(self):
        self.current_model = None
        self.current_recognizer = None
        self.current_model_path = None
    
    def load_model(self, model_path, parent_widget=None, show_dialog=True):
        """
        Загружает модель Vosk.
        
        Args:
            model_path (str): Путь к модели
            parent_widget: Родительский виджет для диалогов
            show_dialog (bool): Показывать ли диалог прогресса
            
        Returns:
            bool: True если модель успешно загружена
        """
        # Проверяем валидность пути
        is_valid, error_msg = VoskModelTester.validate_model_path(model_path)
        if not is_valid:
            if parent_widget:
                QMessageBox.warning(parent_widget, "Ошибка модели", error_msg)
            return False
        
        # Если модель уже загружена и путь тот же, не перезагружаем
        if (self.current_model and self.current_recognizer and 
            self.current_model_path == model_path):
            logger.info(f"Модель уже загружена: {model_path}")
            return True
        
        if show_dialog:
            success, model, recognizer = VoskModelTester.test_model_loading(
                model_path, parent_widget)
        else:
            try:
                model = Model(model_path)
                recognizer = KaldiRecognizer(model, 16000)
                success = True
            except Exception as e:
                logger.error(f"Ошибка загрузки модели: {e}")
                success = False
                model = None
                recognizer = None
        
        if success:
            self.current_model = model
            self.current_recognizer = recognizer
            self.current_model_path = model_path
            logger.info(f"Модель Vosk успешно загружена: {model_path}")
            return True
        else:
            return False
    
    def get_model_info(self):
        """Возвращает информацию о текущей модели."""
        if self.current_model_path:
            return {
                "path": self.current_model_path,
                "name": os.path.basename(self.current_model_path),
                "loaded": self.current_model is not None
            }
        return None
    
    def is_model_loaded(self):
        """Проверяет, загружена ли модель."""
        return self.current_model is not None and self.current_recognizer is not None
    
    def get_recognizer(self):
        """Возвращает текущий распознаватель."""
        return self.current_recognizer
    
    def unload_model(self):
        """Выгружает текущую модель."""
        self.current_model = None
        self.current_recognizer = None
        self.current_model_path = None
        logger.info("Модель Vosk выгружена")