"""File Helper for voice control system.

Помощник для работы с файлами системы голосового управления
с поддержкой различных операций, безопасности и мониторинга.
"""

import os
import shutil
import hashlib
import mimetypes
import tempfile
import zipfile
import tarfile
import json
import pickle
from typing import Any, Dict, List, Optional, Union, Iterator, Callable, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import threading
import time
from contextlib import contextmanager
import stat
import fnmatch


class FileOperation(Enum):
    """Типы файловых операций."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    COPY = "copy"
    MOVE = "move"
    CREATE = "create"
    COMPRESS = "compress"
    EXTRACT = "extract"


class CompressionFormat(Enum):
    """Форматы сжатия."""
    ZIP = "zip"
    TAR = "tar"
    TAR_GZ = "tar.gz"
    TAR_BZ2 = "tar.bz2"


@dataclass
class FileInfo:
    """Информация о файле."""
    path: str
    name: str
    size: int
    created: float
    modified: float
    accessed: float
    is_directory: bool
    permissions: str
    mime_type: Optional[str]
    checksum: Optional[str]
    owner: Optional[str]
    group: Optional[str]


@dataclass
class FileOperationResult:
    """Результат файловой операции."""
    success: bool
    operation: FileOperation
    source_path: str
    target_path: Optional[str]
    error_message: Optional[str]
    duration: float
    bytes_processed: int


class FileError(Exception):
    """Исключение файловых операций."""
    pass


class FileHelper:
    """Помощник для работы с файлами.
    
    Обеспечивает безопасные операции с файлами, мониторинг,
    сжатие, валидацию и другие утилиты.
    """
    
    def __init__(self, 
                 base_directory: Optional[str] = None,
                 enable_logging: bool = True,
                 max_file_size: int = 100 * 1024 * 1024,  # 100MB
                 allowed_extensions: Optional[List[str]] = None,
                 forbidden_paths: Optional[List[str]] = None):
        """Инициализация помощника файлов.
        
        Args:
            base_directory: Базовая директория для операций
            enable_logging: Включить логирование операций
            max_file_size: Максимальный размер файла
            allowed_extensions: Разрешенные расширения файлов
            forbidden_paths: Запрещенные пути
        """
        self._base_directory = Path(base_directory) if base_directory else None
        self._enable_logging = enable_logging
        self._max_file_size = max_file_size
        self._allowed_extensions = allowed_extensions or []
        self._forbidden_paths = forbidden_paths or []
        
        # Логирование операций
        self._operation_log: List[FileOperationResult] = []
        self._lock = threading.RLock()
        
        # Временные файлы для отслеживания
        self._temp_files: List[str] = []
        
        # Кэш информации о файлах
        self._file_info_cache: Dict[str, Tuple[FileInfo, float]] = {}
        self._cache_ttl = 60  # 1 минута
    
    def _validate_path(self, file_path: str) -> str:
        """Валидация пути к файлу.
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            Нормализованный путь
            
        Raises:
            FileError: При недопустимом пути
        """
        # Нормализация пути
        normalized_path = os.path.normpath(os.path.abspath(file_path))
        
        # Проверка базовой директории
        if self._base_directory:
            base_abs = os.path.abspath(self._base_directory)
            if not normalized_path.startswith(base_abs):
                raise FileError(f"Path outside base directory: {file_path}")
        
        # Проверка запрещенных путей
        for forbidden in self._forbidden_paths:
            if fnmatch.fnmatch(normalized_path, forbidden):
                raise FileError(f"Access to forbidden path: {file_path}")
        
        # Проверка расширения
        if self._allowed_extensions:
            ext = Path(file_path).suffix.lower()
            if ext not in self._allowed_extensions:
                raise FileError(f"File extension not allowed: {ext}")
        
        return normalized_path
    
    def _log_operation(self, result: FileOperationResult) -> None:
        """Логирование файловой операции.
        
        Args:
            result: Результат операции
        """
        if self._enable_logging:
            with self._lock:
                self._operation_log.append(result)
                
                # Ограничение размера лога
                if len(self._operation_log) > 1000:
                    self._operation_log = self._operation_log[-500:]
    
    @contextmanager
    def _operation_timer(self, operation: FileOperation, 
                        source_path: str, 
                        target_path: Optional[str] = None):
        """Контекстный менеджер для измерения времени операций.
        
        Args:
            operation: Тип операции
            source_path: Исходный путь
            target_path: Целевой путь
        """
        start_time = time.time()
        bytes_processed = 0
        error_message = None
        
        try:
            yield lambda size: setattr(self, '_current_bytes', 
                                      getattr(self, '_current_bytes', 0) + size)
        except Exception as e:
            error_message = str(e)
            raise
        finally:
            duration = time.time() - start_time
            bytes_processed = getattr(self, '_current_bytes', 0)
            setattr(self, '_current_bytes', 0)
            
            result = FileOperationResult(
                success=error_message is None,
                operation=operation,
                source_path=source_path,
                target_path=target_path,
                error_message=error_message,
                duration=duration,
                bytes_processed=bytes_processed
            )
            
            self._log_operation(result)
    
    def get_file_info(self, file_path: str, use_cache: bool = True) -> FileInfo:
        """Получение информации о файле.
        
        Args:
            file_path: Путь к файлу
            use_cache: Использовать кэш
            
        Returns:
            Информация о файле
        """
        validated_path = self._validate_path(file_path)
        
        # Проверка кэша
        if use_cache and validated_path in self._file_info_cache:
            cached_info, cached_time = self._file_info_cache[validated_path]
            if time.time() - cached_time < self._cache_ttl:
                return cached_info
        
        if not os.path.exists(validated_path):
            raise FileError(f"File not found: {file_path}")
        
        try:
            stat_info = os.stat(validated_path)
            
            # Базовая информация
            file_info = FileInfo(
                path=validated_path,
                name=os.path.basename(validated_path),
                size=stat_info.st_size,
                created=stat_info.st_ctime,
                modified=stat_info.st_mtime,
                accessed=stat_info.st_atime,
                is_directory=os.path.isdir(validated_path),
                permissions=stat.filemode(stat_info.st_mode),
                mime_type=mimetypes.guess_type(validated_path)[0],
                checksum=None,
                owner=None,
                group=None
            )
            
            # Дополнительная информация для файлов
            if not file_info.is_directory and file_info.size < self._max_file_size:
                file_info.checksum = self.calculate_checksum(validated_path)
            
            # Кэширование
            if use_cache:
                self._file_info_cache[validated_path] = (file_info, time.time())
            
            return file_info
            
        except Exception as e:
            raise FileError(f"Failed to get file info: {str(e)}")
    
    def read_file(self, file_path: str, 
                  encoding: str = 'utf-8', 
                  binary: bool = False) -> Union[str, bytes]:
        """Чтение файла.
        
        Args:
            file_path: Путь к файлу
            encoding: Кодировка (для текстовых файлов)
            binary: Бинарный режим
            
        Returns:
            Содержимое файла
        """
        validated_path = self._validate_path(file_path)
        
        with self._operation_timer(FileOperation.READ, validated_path) as log_bytes:
            try:
                # Проверка размера файла
                file_size = os.path.getsize(validated_path)
                if file_size > self._max_file_size:
                    raise FileError(f"File too large: {file_size} bytes")
                
                mode = 'rb' if binary else 'r'
                kwargs = {} if binary else {'encoding': encoding}
                
                with open(validated_path, mode, **kwargs) as f:
                    content = f.read()
                    log_bytes(len(content) if binary else len(content.encode(encoding)))
                    return content
                    
            except Exception as e:
                raise FileError(f"Failed to read file: {str(e)}")
    
    def write_file(self, file_path: str, 
                   content: Union[str, bytes], 
                   encoding: str = 'utf-8',
                   create_dirs: bool = True,
                   backup: bool = False) -> None:
        """Запись файла.
        
        Args:
            file_path: Путь к файлу
            content: Содержимое
            encoding: Кодировка (для текстовых файлов)
            create_dirs: Создать директории
            backup: Создать резервную копию
        """
        validated_path = self._validate_path(file_path)
        
        with self._operation_timer(FileOperation.WRITE, validated_path) as log_bytes:
            try:
                # Создание директорий
                if create_dirs:
                    os.makedirs(os.path.dirname(validated_path), exist_ok=True)
                
                # Создание резервной копии
                if backup and os.path.exists(validated_path):
                    backup_path = f"{validated_path}.backup"
                    shutil.copy2(validated_path, backup_path)
                
                # Определение режима записи
                binary = isinstance(content, bytes)
                mode = 'wb' if binary else 'w'
                kwargs = {} if binary else {'encoding': encoding}
                
                # Проверка размера содержимого
                content_size = len(content) if binary else len(content.encode(encoding))
                if content_size > self._max_file_size:
                    raise FileError(f"Content too large: {content_size} bytes")
                
                with open(validated_path, mode, **kwargs) as f:
                    f.write(content)
                    log_bytes(content_size)
                    
            except Exception as e:
                raise FileError(f"Failed to write file: {str(e)}")
    
    def copy_file(self, source_path: str, target_path: str, 
                  preserve_metadata: bool = True) -> None:
        """Копирование файла.
        
        Args:
            source_path: Исходный путь
            target_path: Целевой путь
            preserve_metadata: Сохранить метаданные
        """
        validated_source = self._validate_path(source_path)
        validated_target = self._validate_path(target_path)
        
        with self._operation_timer(FileOperation.COPY, validated_source, validated_target) as log_bytes:
            try:
                if not os.path.exists(validated_source):
                    raise FileError(f"Source file not found: {source_path}")
                
                # Создание целевой директории
                os.makedirs(os.path.dirname(validated_target), exist_ok=True)
                
                if preserve_metadata:
                    shutil.copy2(validated_source, validated_target)
                else:
                    shutil.copy(validated_source, validated_target)
                
                # Логирование размера
                file_size = os.path.getsize(validated_target)
                log_bytes(file_size)
                
            except Exception as e:
                raise FileError(f"Failed to copy file: {str(e)}")
    
    def move_file(self, source_path: str, target_path: str) -> None:
        """Перемещение файла.
        
        Args:
            source_path: Исходный путь
            target_path: Целевой путь
        """
        validated_source = self._validate_path(source_path)
        validated_target = self._validate_path(target_path)
        
        with self._operation_timer(FileOperation.MOVE, validated_source, validated_target) as log_bytes:
            try:
                if not os.path.exists(validated_source):
                    raise FileError(f"Source file not found: {source_path}")
                
                # Создание целевой директории
                os.makedirs(os.path.dirname(validated_target), exist_ok=True)
                
                file_size = os.path.getsize(validated_source)
                shutil.move(validated_source, validated_target)
                log_bytes(file_size)
                
            except Exception as e:
                raise FileError(f"Failed to move file: {str(e)}")
    
    def delete_file(self, file_path: str, secure: bool = False) -> None:
        """Удаление файла.
        
        Args:
            file_path: Путь к файлу
            secure: Безопасное удаление (перезапись)
        """
        validated_path = self._validate_path(file_path)
        
        with self._operation_timer(FileOperation.DELETE, validated_path) as log_bytes:
            try:
                if not os.path.exists(validated_path):
                    raise FileError(f"File not found: {file_path}")
                
                file_size = os.path.getsize(validated_path) if os.path.isfile(validated_path) else 0
                
                if secure and os.path.isfile(validated_path):
                    # Безопасное удаление - перезапись случайными данными
                    with open(validated_path, 'r+b') as f:
                        length = f.seek(0, 2)
                        f.seek(0)
                        f.write(os.urandom(length))
                        f.flush()
                        os.fsync(f.fileno())
                
                if os.path.isdir(validated_path):
                    shutil.rmtree(validated_path)
                else:
                    os.remove(validated_path)
                
                log_bytes(file_size)
                
                # Удаление из кэша
                if validated_path in self._file_info_cache:
                    del self._file_info_cache[validated_path]
                
            except Exception as e:
                raise FileError(f"Failed to delete file: {str(e)}")
    
    def calculate_checksum(self, file_path: str, algorithm: str = 'sha256') -> str:
        """Вычисление контрольной суммы файла.
        
        Args:
            file_path: Путь к файлу
            algorithm: Алгоритм хэширования
            
        Returns:
            Контрольная сумма
        """
        validated_path = self._validate_path(file_path)
        
        try:
            hash_obj = hashlib.new(algorithm)
            
            with open(validated_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_obj.update(chunk)
            
            return hash_obj.hexdigest()
            
        except Exception as e:
            raise FileError(f"Failed to calculate checksum: {str(e)}")
    
    def find_files(self, directory: str, 
                   pattern: str = "*",
                   recursive: bool = True,
                   include_dirs: bool = False) -> List[str]:
        """Поиск файлов по шаблону.
        
        Args:
            directory: Директория для поиска
            pattern: Шаблон поиска
            recursive: Рекурсивный поиск
            include_dirs: Включить директории
            
        Returns:
            Список найденных файлов
        """
        validated_dir = self._validate_path(directory)
        
        try:
            found_files = []
            
            if recursive:
                for root, dirs, files in os.walk(validated_dir):
                    # Файлы
                    for file in files:
                        if fnmatch.fnmatch(file, pattern):
                            found_files.append(os.path.join(root, file))
                    
                    # Директории
                    if include_dirs:
                        for dir_name in dirs:
                            if fnmatch.fnmatch(dir_name, pattern):
                                found_files.append(os.path.join(root, dir_name))
            else:
                for item in os.listdir(validated_dir):
                    item_path = os.path.join(validated_dir, item)
                    
                    if fnmatch.fnmatch(item, pattern):
                        if os.path.isfile(item_path) or (include_dirs and os.path.isdir(item_path)):
                            found_files.append(item_path)
            
            return found_files
            
        except Exception as e:
            raise FileError(f"Failed to find files: {str(e)}")
    
    def compress_files(self, file_paths: List[str], 
                      archive_path: str,
                      format: CompressionFormat = CompressionFormat.ZIP,
                      compression_level: int = 6) -> None:
        """Сжатие файлов в архив.
        
        Args:
            file_paths: Список путей к файлам
            archive_path: Путь к архиву
            format: Формат сжатия
            compression_level: Уровень сжатия
        """
        validated_archive = self._validate_path(archive_path)
        validated_files = [self._validate_path(fp) for fp in file_paths]
        
        with self._operation_timer(FileOperation.COMPRESS, 
                                 ",".join(file_paths), validated_archive) as log_bytes:
            try:
                total_size = 0
                
                if format == CompressionFormat.ZIP:
                    with zipfile.ZipFile(validated_archive, 'w', 
                                        compression=zipfile.ZIP_DEFLATED,
                                        compresslevel=compression_level) as zf:
                        for file_path in validated_files:
                            if os.path.exists(file_path):
                                arcname = os.path.relpath(file_path, 
                                                         os.path.commonpath(validated_files))
                                zf.write(file_path, arcname)
                                total_size += os.path.getsize(file_path)
                
                elif format in [CompressionFormat.TAR, CompressionFormat.TAR_GZ, CompressionFormat.TAR_BZ2]:
                    mode_map = {
                        CompressionFormat.TAR: 'w',
                        CompressionFormat.TAR_GZ: 'w:gz',
                        CompressionFormat.TAR_BZ2: 'w:bz2'
                    }
                    
                    with tarfile.open(validated_archive, mode_map[format]) as tf:
                        for file_path in validated_files:
                            if os.path.exists(file_path):
                                arcname = os.path.relpath(file_path,
                                                         os.path.commonpath(validated_files))
                                tf.add(file_path, arcname)
                                total_size += os.path.getsize(file_path)
                
                log_bytes(total_size)
                
            except Exception as e:
                raise FileError(f"Failed to compress files: {str(e)}")
    
    def extract_archive(self, archive_path: str, 
                       extract_to: str,
                       format: Optional[CompressionFormat] = None) -> List[str]:
        """Извлечение архива.
        
        Args:
            archive_path: Путь к архиву
            extract_to: Директория для извлечения
            format: Формат архива (автоопределение если None)
            
        Returns:
            Список извлеченных файлов
        """
        validated_archive = self._validate_path(archive_path)
        validated_extract_to = self._validate_path(extract_to)
        
        with self._operation_timer(FileOperation.EXTRACT, 
                                 validated_archive, validated_extract_to) as log_bytes:
            try:
                extracted_files = []
                total_size = 0
                
                # Автоопределение формата
                if format is None:
                    if archive_path.endswith('.zip'):
                        format = CompressionFormat.ZIP
                    elif archive_path.endswith('.tar.gz') or archive_path.endswith('.tgz'):
                        format = CompressionFormat.TAR_GZ
                    elif archive_path.endswith('.tar.bz2'):
                        format = CompressionFormat.TAR_BZ2
                    elif archive_path.endswith('.tar'):
                        format = CompressionFormat.TAR
                    else:
                        raise FileError(f"Cannot determine archive format: {archive_path}")
                
                # Создание директории для извлечения
                os.makedirs(validated_extract_to, exist_ok=True)
                
                if format == CompressionFormat.ZIP:
                    with zipfile.ZipFile(validated_archive, 'r') as zf:
                        for member in zf.namelist():
                            extracted_path = zf.extract(member, validated_extract_to)
                            extracted_files.append(extracted_path)
                            if os.path.isfile(extracted_path):
                                total_size += os.path.getsize(extracted_path)
                
                elif format in [CompressionFormat.TAR, CompressionFormat.TAR_GZ, CompressionFormat.TAR_BZ2]:
                    mode_map = {
                        CompressionFormat.TAR: 'r',
                        CompressionFormat.TAR_GZ: 'r:gz',
                        CompressionFormat.TAR_BZ2: 'r:bz2'
                    }
                    
                    with tarfile.open(validated_archive, mode_map[format]) as tf:
                        for member in tf.getmembers():
                            tf.extract(member, validated_extract_to)
                            extracted_path = os.path.join(validated_extract_to, member.name)
                            extracted_files.append(extracted_path)
                            if member.isfile():
                                total_size += member.size
                
                log_bytes(total_size)
                return extracted_files
                
            except Exception as e:
                raise FileError(f"Failed to extract archive: {str(e)}")
    
    @contextmanager
    def temporary_file(self, suffix: str = "", prefix: str = "tmp", 
                      directory: Optional[str] = None, text: bool = True):
        """Контекстный менеджер для временного файла.
        
        Args:
            suffix: Суффикс имени файла
            prefix: Префикс имени файла
            directory: Директория для временного файла
            text: Текстовый режим
        """
        temp_dir = directory or tempfile.gettempdir()
        
        # Валидация директории
        if self._base_directory:
            temp_dir = os.path.join(self._base_directory, "temp")
            os.makedirs(temp_dir, exist_ok=True)
        
        temp_file = None
        try:
            temp_file = tempfile.NamedTemporaryFile(
                suffix=suffix,
                prefix=prefix,
                dir=temp_dir,
                delete=False,
                mode='w+' if text else 'w+b'
            )
            
            self._temp_files.append(temp_file.name)
            yield temp_file
            
        finally:
            if temp_file:
                temp_file.close()
                
                # Удаление временного файла
                try:
                    os.unlink(temp_file.name)
                    if temp_file.name in self._temp_files:
                        self._temp_files.remove(temp_file.name)
                except OSError:
                    pass
    
    def cleanup_temp_files(self) -> None:
        """Очистка временных файлов."""
        with self._lock:
            for temp_file in self._temp_files[:]:
                try:
                    if os.path.exists(temp_file):
                        os.unlink(temp_file)
                    self._temp_files.remove(temp_file)
                except OSError:
                    pass
    
    def get_directory_size(self, directory: str) -> int:
        """Получение размера директории.
        
        Args:
            directory: Путь к директории
            
        Returns:
            Размер в байтах
        """
        validated_dir = self._validate_path(directory)
        
        try:
            total_size = 0
            
            for dirpath, dirnames, filenames in os.walk(validated_dir):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(file_path)
                    except OSError:
                        pass
            
            return total_size
            
        except Exception as e:
            raise FileError(f"Failed to calculate directory size: {str(e)}")
    
    def save_json(self, file_path: str, data: Any, indent: int = 2) -> None:
        """Сохранение данных в JSON файл.
        
        Args:
            file_path: Путь к файлу
            data: Данные для сохранения
            indent: Отступ для форматирования
        """
        try:
            json_content = json.dumps(data, indent=indent, ensure_ascii=False)
            self.write_file(file_path, json_content)
        except Exception as e:
            raise FileError(f"Failed to save JSON: {str(e)}")
    
    def load_json(self, file_path: str) -> Any:
        """Загрузка данных из JSON файла.
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            Загруженные данные
        """
        try:
            content = self.read_file(file_path)
            return json.loads(content)
        except Exception as e:
            raise FileError(f"Failed to load JSON: {str(e)}")
    
    def save_pickle(self, file_path: str, data: Any) -> None:
        """Сохранение данных в Pickle файл.
        
        Args:
            file_path: Путь к файлу
            data: Данные для сохранения
        """
        try:
            pickle_content = pickle.dumps(data)
            self.write_file(file_path, pickle_content, binary=True)
        except Exception as e:
            raise FileError(f"Failed to save Pickle: {str(e)}")
    
    def load_pickle(self, file_path: str) -> Any:
        """Загрузка данных из Pickle файла.
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            Загруженные данные
        """
        try:
            content = self.read_file(file_path, binary=True)
            return pickle.loads(content)
        except Exception as e:
            raise FileError(f"Failed to load Pickle: {str(e)}")
    
    def get_operation_log(self, limit: Optional[int] = None) -> List[FileOperationResult]:
        """Получение лога операций.
        
        Args:
            limit: Ограничение количества записей
            
        Returns:
            Список операций
        """
        with self._lock:
            log = self._operation_log[:]
            if limit:
                log = log[-limit:]
            return log
    
    def clear_operation_log(self) -> None:
        """Очистка лога операций."""
        with self._lock:
            self._operation_log.clear()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики операций.
        
        Returns:
            Статистика
        """
        with self._lock:
            if not self._operation_log:
                return {}
            
            # Подсчет операций по типам
            operation_counts = {}
            total_bytes = 0
            total_duration = 0
            successful_operations = 0
            
            for op in self._operation_log:
                op_type = op.operation.value
                operation_counts[op_type] = operation_counts.get(op_type, 0) + 1
                total_bytes += op.bytes_processed
                total_duration += op.duration
                
                if op.success:
                    successful_operations += 1
            
            return {
                'total_operations': len(self._operation_log),
                'successful_operations': successful_operations,
                'success_rate': successful_operations / len(self._operation_log) * 100,
                'operation_counts': operation_counts,
                'total_bytes_processed': total_bytes,
                'total_duration': total_duration,
                'average_duration': total_duration / len(self._operation_log),
                'cache_size': len(self._file_info_cache),
                'temp_files_count': len(self._temp_files)
            }
    
    def __del__(self):
        """Деструктор - очистка временных файлов."""
        try:
            self.cleanup_temp_files()
        except Exception:
            pass