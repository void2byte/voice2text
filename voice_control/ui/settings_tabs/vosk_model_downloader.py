"""Модуль для скачивания и управления моделями Vosk."""
import logging
import os
import requests
import zipfile
import shutil
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QMessageBox

logger = logging.getLogger(__name__)

class VoskModelDownloader(QThread):
    """Поток для скачивания моделей Vosk."""
    
    progress = Signal(int)
    finished_signal = Signal(str)  # Путь к распакованной модели
    error_signal = Signal(str)

    def __init__(self, model_url, download_dir, model_display_name, model_internal_name):
        super().__init__()
        self.model_url = model_url
        self.download_dir = download_dir
        self.model_display_name = model_display_name  # Имя для отображения
        self.model_internal_name = model_internal_name  # Имя папки модели
        self.zip_path = os.path.join(self.download_dir, os.path.basename(self.model_url))
        self.extract_path = os.path.join(self.download_dir, self.model_internal_name)

    def run(self):
        try:
            logger.info(f"Начало скачивания модели '{self.model_display_name}' с {self.model_url}")
            response = requests.get(self.model_url, stream=True, timeout=300)  # Таймаут 5 минут
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0

            with open(self.zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:  # filter out keep-alive new chunks
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if total_size > 0:
                            progress_percentage = int((downloaded_size / total_size) * 100)
                            self.progress.emit(progress_percentage)
            
            self.progress.emit(100)  # Убедимся, что прогресс дошел до 100%
            logger.info(f"Модель '{self.model_display_name}' скачана: {self.zip_path}")

            # Распаковка архива
            logger.info(f"Распаковка архива {self.zip_path} в {self.download_dir}")
            if os.path.exists(self.extract_path):
                logger.warning(f"Папка для распаковки {self.extract_path} уже существует. Удаление перед распаковкой.")
                shutil.rmtree(self.extract_path)
            
            with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
                # Извлекаем все в download_dir
                zip_ref.extractall(self.download_dir)
                
                # Ищем папку, которую создал zip
                archived_folder_name_candidate1 = os.path.splitext(os.path.basename(self.zip_path))[0]
                
                # Проверяем различные варианты извлеченных папок
                potential_extracted_folder_path1 = os.path.join(self.download_dir, self.model_internal_name)
                potential_extracted_folder_path2 = os.path.join(self.download_dir, archived_folder_name_candidate1)

                actual_extracted_path = None
                if os.path.isdir(potential_extracted_folder_path1) and self.model_internal_name != archived_folder_name_candidate1:
                    if self.extract_path == potential_extracted_folder_path1:
                        actual_extracted_path = self.extract_path
                    else:
                        if os.path.exists(self.extract_path):
                            shutil.rmtree(self.extract_path)
                        shutil.move(potential_extracted_folder_path1, self.extract_path)
                        actual_extracted_path = self.extract_path
                elif os.path.isdir(potential_extracted_folder_path2):
                    if self.extract_path == potential_extracted_folder_path2:
                        actual_extracted_path = self.extract_path
                    else:
                        if os.path.exists(self.extract_path):
                            shutil.rmtree(self.extract_path)
                        shutil.move(potential_extracted_folder_path2, self.extract_path)
                        actual_extracted_path = self.extract_path
                else:
                    if not os.path.isdir(self.extract_path):
                        raise FileNotFoundError(f"Ожидаемая папка модели {self.extract_path} не найдена после распаковки.")
                    actual_extracted_path = self.extract_path

            logger.info(f"Модель успешно распакована в: {actual_extracted_path}")
            self.finished_signal.emit(actual_extracted_path)

        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка скачивания модели '{self.model_display_name}': {e}")
            self.error_signal.emit(f"Ошибка HTTP: {e}")
        except zipfile.BadZipFile as e:
            logger.error(f"Ошибка распаковки модели '{self.model_display_name}': Файл поврежден или не является ZIP-архивом. {e}")
            self.error_signal.emit(f"Ошибка ZIP: {e}")
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при скачивании/распаковке модели '{self.model_display_name}': {e}")
            self.error_signal.emit(f"Произошла ошибка: {e}")
        finally:
            # Удаляем zip-архив после распаковки или в случае ошибки
            if os.path.exists(self.zip_path):
                try:
                    os.remove(self.zip_path)
                    logger.info(f"Удален временный ZIP-файл: {self.zip_path}")
                except OSError as e:
                    logger.error(f"Не удалось удалить временный ZIP-файл {self.zip_path}: {e}")


class VoskModelRegistry:
    """Реестр доступных моделей Vosk."""
    
    MODELS_URL = "https://alphacephei.com/vosk/models/model-list.json"
    
    # Встроенный список моделей как fallback
    AVAILABLE_MODELS_FALLBACK = [
        {
            "name": "vosk-model-small-ru-0.22 (45MB)",
            "url": "https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip",
            "lang": "ru",
            "model_dir_name": "vosk-model-small-ru-0.22",
            "size_mb": 45
        },
        {
            "name": "vosk-model-small-en-us-0.15 (40MB)",
            "url": "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip",
            "lang": "en-us",
            "model_dir_name": "vosk-model-small-en-us-0.15",
            "size_mb": 40
        },
        {
            "name": "vosk-model-ru-0.42 (1.8GB)",
            "url": "https://alphacephei.com/vosk/models/vosk-model-ru-0.42.zip",
            "lang": "ru",
            "model_dir_name": "vosk-model-ru-0.42",
            "size_mb": 1800
        },
        {
            "name": "vosk-model-en-us-0.22 (1.8GB)",
            "url": "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip",
            "lang": "en-us",
            "model_dir_name": "vosk-model-en-us-0.22",
            "size_mb": 1800
        }
    ]
    
    @classmethod
    def get_available_models(cls):
        """Возвращает список доступных моделей."""
        try:
            # Попытка загрузить JSON со списком моделей
            response = requests.get(cls.MODELS_URL, timeout=10)
            response.raise_for_status()
            models = response.json()
            
            # Обрабатываем данные с сервера, добавляя недостающие поля
            processed_models = []
            for model in models:
                processed_model = model.copy()
                
                # Если нет model_dir_name, извлекаем из URL или имени
                if 'model_dir_name' not in processed_model:
                    if 'url' in processed_model:
                        # Извлекаем имя файла из URL и убираем расширение
                        url = processed_model['url']
                        filename = url.split('/')[-1]
                        if filename.endswith('.zip'):
                            processed_model['model_dir_name'] = filename[:-4]
                        else:
                            processed_model['model_dir_name'] = filename
                    elif 'name' in processed_model:
                        # Используем имя модели как директорию
                        processed_model['model_dir_name'] = processed_model['name']
                    else:
                        # Пропускаем модели без достаточной информации
                        logger.warning(f"Пропускаем модель без достаточной информации: {model}")
                        continue
                
                processed_models.append(processed_model)
            
            logger.info(f"Загружен список из {len(processed_models)} моделей Vosk.")
            return processed_models
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при загрузке списка моделей Vosk: {e}")
            return cls.AVAILABLE_MODELS_FALLBACK
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при загрузке списка моделей Vosk: {e}")
            return cls.AVAILABLE_MODELS_FALLBACK
    
    @classmethod
    def get_model_by_name(cls, model_name):
        """Возвращает информацию о модели по имени."""
        models = cls.get_available_models()
        for model in models:
            if model["model_dir_name"] == model_name:
                return model
        return None
    
    @classmethod
    def get_models_by_language(cls, language):
        """Возвращает список моделей для указанного языка."""
        models = cls.get_available_models()
        return [model for model in models if model.get("lang", "").startswith(language)]
    
    @classmethod
    def get_project_models_dir(cls):
        """Возвращает путь к директории моделей проекта."""
        # Корень проекта
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        return os.path.join(project_root, "models", "vosk")
    
    @classmethod
    def get_installed_models(cls):
        """Возвращает список установленных моделей."""
        models_dir = cls.get_project_models_dir()
        if not os.path.exists(models_dir):
            return []
        
        installed_models = []
        for item in os.listdir(models_dir):
            model_path = os.path.join(models_dir, item)
            if os.path.isdir(model_path):
                # Проверяем, что это действительно модель Vosk
                if cls._is_valid_vosk_model(model_path):
                    installed_models.append({
                        "name": item,
                        "path": model_path,
                        "size_mb": cls._get_directory_size_mb(model_path)
                    })
        return installed_models
    
    @classmethod
    def _is_valid_vosk_model(cls, model_path):
        """Проверяет, является ли директория валидной моделью Vosk."""
        required_components = ["am", "graph", "ivector"]
        for component in required_components:
            component_path = os.path.join(model_path, component)
            if not os.path.exists(component_path):
                return False
        return True
    
    @classmethod
    def _get_directory_size_mb(cls, directory_path):
        """Возвращает размер директории в мегабайтах."""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(directory_path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except (OSError, IOError):
                    pass
        return round(total_size / (1024 * 1024), 1)