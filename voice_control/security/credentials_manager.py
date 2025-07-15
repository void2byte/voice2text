"""Secure Credentials Manager for voice control services.

Безопасный менеджер учетных данных для сервисов голосового управления
с поддержкой шифрования, ротации ключей и аудита доступа.
"""

import os
import json
import base64
import hashlib
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path
import threading
import time

from .encryption import EncryptionManager
from .audit_logger import AuditLogger
from ..utils.logger import PerformanceLogger


@dataclass
class CredentialInfo:
    """Информация об учетных данных."""
    service_name: str
    credential_type: str
    created_at: float
    last_accessed: float
    access_count: int = 0
    expires_at: Optional[float] = None
    metadata: Dict[str, Any] = None


class SecureCredentialsManager:
    """Безопасный менеджер учетных данных.
    
    Обеспечивает безопасное хранение, получение и управление
    учетными данными для различных сервисов распознавания речи.
    """
    
    def __init__(self, 
                 credentials_dir: Optional[str] = None,
                 master_key: Optional[str] = None):
        """Инициализация менеджера учетных данных.
        
        Args:
            credentials_dir: Директория для хранения учетных данных
            master_key: Мастер-ключ для шифрования
        """
        self._logger = PerformanceLogger("SecureCredentialsManager")
        self._audit_logger = AuditLogger("credentials_access")
        
        # Настройка директории
        if credentials_dir:
            self._credentials_dir = Path(credentials_dir)
        else:
            self._credentials_dir = Path.home() / ".voice_control" / "credentials"
        
        self._credentials_dir.mkdir(parents=True, exist_ok=True)
        
        # Инициализация шифрования
        self._encryption_manager = EncryptionManager(master_key)
        
        # Кэш учетных данных
        self._credentials_cache: Dict[str, Any] = {}
        self._credentials_info: Dict[str, CredentialInfo] = {}
        self._cache_lock = threading.RLock()
        
        # Настройки безопасности
        self._max_cache_age = 3600  # 1 час
        self._max_access_attempts = 5
        self._access_attempts: Dict[str, int] = {}
        
        # Загрузка существующих учетных данных
        self._load_credentials_info()
        
        self._logger.info(f"SecureCredentialsManager initialized with dir: {self._credentials_dir}")
    
    def _get_credentials_file_path(self, service_name: str) -> Path:
        """Получение пути к файлу учетных данных.
        
        Args:
            service_name: Название сервиса
            
        Returns:
            Путь к файлу
        """
        # Хэширование имени сервиса для безопасности
        service_hash = hashlib.sha256(service_name.encode()).hexdigest()[:16]
        return self._credentials_dir / f"{service_hash}.cred"
    
    def _get_info_file_path(self) -> Path:
        """Получение пути к файлу информации об учетных данных.
        
        Returns:
            Путь к файлу информации
        """
        return self._credentials_dir / "credentials_info.json"
    
    def _load_credentials_info(self) -> None:
        """Загрузка информации об учетных данных."""
        info_file = self._get_info_file_path()
        
        if info_file.exists():
            try:
                with open(info_file, 'r', encoding='utf-8') as f:
                    info_data = json.load(f)
                
                for service_name, info_dict in info_data.items():
                    self._credentials_info[service_name] = CredentialInfo(
                        service_name=info_dict['service_name'],
                        credential_type=info_dict['credential_type'],
                        created_at=info_dict['created_at'],
                        last_accessed=info_dict['last_accessed'],
                        access_count=info_dict.get('access_count', 0),
                        expires_at=info_dict.get('expires_at'),
                        metadata=info_dict.get('metadata', {})
                    )
                
                self._logger.info(f"Loaded info for {len(self._credentials_info)} credential sets")
                
            except Exception as e:
                self._logger.error(f"Failed to load credentials info: {e}")
                self._credentials_info = {}
    
    def _save_credentials_info(self) -> None:
        """Сохранение информации об учетных данных."""
        info_file = self._get_info_file_path()
        
        try:
            info_data = {}
            for service_name, info in self._credentials_info.items():
                info_data[service_name] = {
                    'service_name': info.service_name,
                    'credential_type': info.credential_type,
                    'created_at': info.created_at,
                    'last_accessed': info.last_accessed,
                    'access_count': info.access_count,
                    'expires_at': info.expires_at,
                    'metadata': info.metadata or {}
                }
            
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(info_data, f, indent=2)
            
            # Установка безопасных прав доступа
            os.chmod(info_file, 0o600)
            
        except Exception as e:
            self._logger.error(f"Failed to save credentials info: {e}")
    
    def _check_access_attempts(self, service_name: str) -> bool:
        """Проверка количества попыток доступа.
        
        Args:
            service_name: Название сервиса
            
        Returns:
            True если доступ разрешен
        """
        attempts = self._access_attempts.get(service_name, 0)
        if attempts >= self._max_access_attempts:
            self._audit_logger.log_security_event(
                "access_denied",
                f"Too many access attempts for service: {service_name}",
                {"service": service_name, "attempts": attempts}
            )
            return False
        return True
    
    def _increment_access_attempts(self, service_name: str) -> None:
        """Увеличение счетчика попыток доступа.
        
        Args:
            service_name: Название сервиса
        """
        self._access_attempts[service_name] = self._access_attempts.get(service_name, 0) + 1
    
    def _reset_access_attempts(self, service_name: str) -> None:
        """Сброс счетчика попыток доступа.
        
        Args:
            service_name: Название сервиса
        """
        if service_name in self._access_attempts:
            del self._access_attempts[service_name]
    
    async def store_credentials(self, 
                              service_name: str,
                              credentials: Dict[str, Any],
                              credential_type: str = "api_key",
                              expires_at: Optional[float] = None,
                              metadata: Optional[Dict[str, Any]] = None) -> None:
        """Сохранение учетных данных.
        
        Args:
            service_name: Название сервиса
            credentials: Учетные данные
            credential_type: Тип учетных данных
            expires_at: Время истечения (timestamp)
            metadata: Дополнительные метаданные
            
        Raises:
            ValueError: При некорректных данных
            RuntimeError: При ошибке сохранения
        """
        if not service_name or not credentials:
            raise ValueError("Service name and credentials are required")
        
        try:
            # Шифрование учетных данных
            credentials_json = json.dumps(credentials)
            encrypted_data = self._encryption_manager.encrypt(credentials_json)
            
            # Сохранение в файл
            credentials_file = self._get_credentials_file_path(service_name)
            with open(credentials_file, 'wb') as f:
                f.write(encrypted_data)
            
            # Установка безопасных прав доступа
            os.chmod(credentials_file, 0o600)
            
            # Обновление информации
            current_time = time.time()
            self._credentials_info[service_name] = CredentialInfo(
                service_name=service_name,
                credential_type=credential_type,
                created_at=current_time,
                last_accessed=current_time,
                expires_at=expires_at,
                metadata=metadata or {}
            )
            
            self._save_credentials_info()
            
            # Очистка кэша
            with self._cache_lock:
                if service_name in self._credentials_cache:
                    del self._credentials_cache[service_name]
            
            # Сброс попыток доступа
            self._reset_access_attempts(service_name)
            
            self._audit_logger.log_security_event(
                "credentials_stored",
                f"Credentials stored for service: {service_name}",
                {"service": service_name, "type": credential_type}
            )
            
            self._logger.info(f"Credentials stored for service: {service_name}")
            
        except Exception as e:
            self._logger.error(f"Failed to store credentials for {service_name}: {e}")
            raise RuntimeError(f"Failed to store credentials: {e}")
    
    async def get_credentials(self, service_name: str) -> Dict[str, Any]:
        """Получение учетных данных.
        
        Args:
            service_name: Название сервиса
            
        Returns:
            Учетные данные
            
        Raises:
            ValueError: При некорректном названии сервиса
            RuntimeError: При ошибке получения или отсутствии данных
        """
        if not service_name:
            raise ValueError("Service name is required")
        
        # Проверка попыток доступа
        if not self._check_access_attempts(service_name):
            raise RuntimeError(f"Access denied for service: {service_name}")
        
        try:
            # Проверка кэша
            with self._cache_lock:
                if service_name in self._credentials_cache:
                    cache_entry = self._credentials_cache[service_name]
                    if (time.time() - cache_entry['timestamp']) < self._max_cache_age:
                        self._update_access_info(service_name)
                        return cache_entry['data']
                    else:
                        # Удаление устаревшего кэша
                        del self._credentials_cache[service_name]
            
            # Проверка существования файла
            credentials_file = self._get_credentials_file_path(service_name)
            if not credentials_file.exists():
                self._increment_access_attempts(service_name)
                raise RuntimeError(f"Credentials not found for service: {service_name}")
            
            # Проверка срока действия
            if service_name in self._credentials_info:
                info = self._credentials_info[service_name]
                if info.expires_at and time.time() > info.expires_at:
                    self._increment_access_attempts(service_name)
                    raise RuntimeError(f"Credentials expired for service: {service_name}")
            
            # Загрузка и расшифровка
            with open(credentials_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self._encryption_manager.decrypt(encrypted_data)
            credentials = json.loads(decrypted_data)
            
            # Кэширование
            with self._cache_lock:
                self._credentials_cache[service_name] = {
                    'data': credentials,
                    'timestamp': time.time()
                }
            
            # Обновление информации о доступе
            self._update_access_info(service_name)
            
            # Сброс попыток доступа
            self._reset_access_attempts(service_name)
            
            self._audit_logger.log_security_event(
                "credentials_accessed",
                f"Credentials accessed for service: {service_name}",
                {"service": service_name}
            )
            
            return credentials
            
        except json.JSONDecodeError as e:
            self._increment_access_attempts(service_name)
            self._logger.error(f"Invalid credentials format for {service_name}: {e}")
            raise RuntimeError(f"Invalid credentials format: {e}")
        except Exception as e:
            self._increment_access_attempts(service_name)
            self._logger.error(f"Failed to get credentials for {service_name}: {e}")
            raise RuntimeError(f"Failed to get credentials: {e}")
    
    def _update_access_info(self, service_name: str) -> None:
        """Обновление информации о доступе.
        
        Args:
            service_name: Название сервиса
        """
        if service_name in self._credentials_info:
            info = self._credentials_info[service_name]
            info.last_accessed = time.time()
            info.access_count += 1
            self._save_credentials_info()
    
    def delete_credentials(self, service_name: str) -> None:
        """Удаление учетных данных.
        
        Args:
            service_name: Название сервиса
        """
        try:
            # Удаление файла
            credentials_file = self._get_credentials_file_path(service_name)
            if credentials_file.exists():
                credentials_file.unlink()
            
            # Удаление из кэша
            with self._cache_lock:
                if service_name in self._credentials_cache:
                    del self._credentials_cache[service_name]
            
            # Удаление информации
            if service_name in self._credentials_info:
                del self._credentials_info[service_name]
                self._save_credentials_info()
            
            # Сброс попыток доступа
            self._reset_access_attempts(service_name)
            
            self._audit_logger.log_security_event(
                "credentials_deleted",
                f"Credentials deleted for service: {service_name}",
                {"service": service_name}
            )
            
            self._logger.info(f"Credentials deleted for service: {service_name}")
            
        except Exception as e:
            self._logger.error(f"Failed to delete credentials for {service_name}: {e}")
            raise RuntimeError(f"Failed to delete credentials: {e}")
    
    def list_services(self) -> List[str]:
        """Получение списка сервисов с сохраненными учетными данными.
        
        Returns:
            Список названий сервисов
        """
        return list(self._credentials_info.keys())
    
    def get_service_info(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Получение информации о сервисе.
        
        Args:
            service_name: Название сервиса
            
        Returns:
            Информация о сервисе или None
        """
        if service_name not in self._credentials_info:
            return None
        
        info = self._credentials_info[service_name]
        return {
            "service_name": info.service_name,
            "credential_type": info.credential_type,
            "created_at": info.created_at,
            "last_accessed": info.last_accessed,
            "access_count": info.access_count,
            "expires_at": info.expires_at,
            "is_expired": info.expires_at and time.time() > info.expires_at,
            "metadata": info.metadata or {}
        }
    
    def rotate_master_key(self, new_master_key: str) -> None:
        """Ротация мастер-ключа.
        
        Args:
            new_master_key: Новый мастер-ключ
            
        Raises:
            RuntimeError: При ошибке ротации
        """
        try:
            # Создание нового менеджера шифрования
            new_encryption_manager = EncryptionManager(new_master_key)
            
            # Перешифровка всех учетных данных
            for service_name in self.list_services():
                # Получение данных со старым ключом
                credentials_file = self._get_credentials_file_path(service_name)
                with open(credentials_file, 'rb') as f:
                    old_encrypted_data = f.read()
                
                # Расшифровка старым ключом
                decrypted_data = self._encryption_manager.decrypt(old_encrypted_data)
                
                # Шифрование новым ключом
                new_encrypted_data = new_encryption_manager.encrypt(decrypted_data)
                
                # Сохранение
                with open(credentials_file, 'wb') as f:
                    f.write(new_encrypted_data)
                
                os.chmod(credentials_file, 0o600)
            
            # Замена менеджера шифрования
            self._encryption_manager = new_encryption_manager
            
            # Очистка кэша
            with self._cache_lock:
                self._credentials_cache.clear()
            
            self._audit_logger.log_security_event(
                "master_key_rotated",
                "Master key rotated successfully",
                {"services_count": len(self.list_services())}
            )
            
            self._logger.info("Master key rotated successfully")
            
        except Exception as e:
            self._logger.error(f"Failed to rotate master key: {e}")
            raise RuntimeError(f"Failed to rotate master key: {e}")
    
    def cleanup_expired_credentials(self) -> int:
        """Очистка истекших учетных данных.
        
        Returns:
            Количество удаленных записей
        """
        current_time = time.time()
        expired_services = []
        
        for service_name, info in self._credentials_info.items():
            if info.expires_at and current_time > info.expires_at:
                expired_services.append(service_name)
        
        for service_name in expired_services:
            try:
                self.delete_credentials(service_name)
            except Exception as e:
                self._logger.error(f"Failed to delete expired credentials for {service_name}: {e}")
        
        if expired_services:
            self._logger.info(f"Cleaned up {len(expired_services)} expired credential sets")
        
        return len(expired_services)
    
    def clear_cache(self) -> None:
        """Очистка кэша учетных данных."""
        with self._cache_lock:
            self._credentials_cache.clear()
        
        self._logger.info("Credentials cache cleared")
    
    def get_security_status(self) -> Dict[str, Any]:
        """Получение статуса безопасности.
        
        Returns:
            Информация о статусе безопасности
        """
        current_time = time.time()
        total_services = len(self._credentials_info)
        expired_services = sum(
            1 for info in self._credentials_info.values()
            if info.expires_at and current_time > info.expires_at
        )
        
        return {
            "total_services": total_services,
            "expired_services": expired_services,
            "cached_services": len(self._credentials_cache),
            "access_attempts": self._access_attempts.copy(),
            "credentials_dir": str(self._credentials_dir),
            "encryption_enabled": True
        }