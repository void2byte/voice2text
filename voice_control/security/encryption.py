"""Encryption Manager for secure data handling.

Менеджер шифрования для безопасной обработки данных
с поддержкой различных алгоритмов и ключей.
"""

import os
import base64
import hashlib
import secrets
from typing import Union, Optional, Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import json

from ..utils.logger import PerformanceLogger


class EncryptionManager:
    """Менеджер шифрования для безопасной обработки данных.
    
    Поддерживает различные алгоритмы шифрования и методы
    генерации ключей для обеспечения безопасности данных.
    """
    
    def __init__(self, master_key: Optional[str] = None, algorithm: str = "fernet"):
        """Инициализация менеджера шифрования.
        
        Args:
            master_key: Мастер-ключ для шифрования
            algorithm: Алгоритм шифрования (fernet, aes256)
        """
        self._logger = PerformanceLogger("EncryptionManager")
        self._algorithm = algorithm
        
        # Генерация или использование мастер-ключа
        if master_key:
            self._master_key = master_key.encode('utf-8')
        else:
            self._master_key = self._generate_master_key()
        
        # Инициализация шифровальщика
        self._cipher_key = self._derive_key(self._master_key)
        
        if algorithm == "fernet":
            self._fernet = Fernet(self._cipher_key)
        elif algorithm == "aes256":
            self._setup_aes256()
        else:
            raise ValueError(f"Unsupported encryption algorithm: {algorithm}")
        
        self._logger.info(f"EncryptionManager initialized with algorithm: {algorithm}")
    
    def _generate_master_key(self) -> bytes:
        """Генерация случайного мастер-ключа.
        
        Returns:
            Сгенерированный мастер-ключ
        """
        # Генерация криптографически стойкого ключа
        key = secrets.token_bytes(32)  # 256 бит
        
        # Сохранение в переменную окружения для восстановления
        encoded_key = base64.b64encode(key).decode('utf-8')
        os.environ['VOICE_CONTROL_MASTER_KEY'] = encoded_key
        
        self._logger.info("Generated new master key")
        return key
    
    def _derive_key(self, master_key: bytes, salt: Optional[bytes] = None) -> bytes:
        """Вывод ключа шифрования из мастер-ключа.
        
        Args:
            master_key: Мастер-ключ
            salt: Соль для вывода ключа
            
        Returns:
            Выведенный ключ шифрования
        """
        if salt is None:
            # Использование фиксированной соли для совместимости
            salt = b'voice_control_salt_2024'
        
        # PBKDF2 для вывода ключа
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        derived_key = kdf.derive(master_key)
        
        if self._algorithm == "fernet":
            # Fernet требует base64-кодированный ключ
            return base64.urlsafe_b64encode(derived_key)
        
        return derived_key
    
    def _setup_aes256(self) -> None:
        """Настройка AES-256 шифрования."""
        self._aes_key = self._cipher_key
        self._logger.info("AES-256 encryption setup completed")
    
    def encrypt(self, data: Union[str, bytes]) -> bytes:
        """Шифрование данных.
        
        Args:
            data: Данные для шифрования
            
        Returns:
            Зашифрованные данные
            
        Raises:
            ValueError: При некорректных данных
            RuntimeError: При ошибке шифрования
        """
        try:
            # Преобразование в bytes если необходимо
            if isinstance(data, str):
                data_bytes = data.encode('utf-8')
            else:
                data_bytes = data
            
            if self._algorithm == "fernet":
                return self._encrypt_fernet(data_bytes)
            elif self._algorithm == "aes256":
                return self._encrypt_aes256(data_bytes)
            else:
                raise ValueError(f"Unsupported algorithm: {self._algorithm}")
                
        except Exception as e:
            self._logger.error(f"Encryption failed: {e}")
            raise RuntimeError(f"Encryption failed: {e}")
    
    def decrypt(self, encrypted_data: bytes) -> str:
        """Расшифровка данных.
        
        Args:
            encrypted_data: Зашифрованные данные
            
        Returns:
            Расшифрованные данные как строка
            
        Raises:
            ValueError: При некорректных данных
            RuntimeError: При ошибке расшифровки
        """
        try:
            if self._algorithm == "fernet":
                decrypted_bytes = self._decrypt_fernet(encrypted_data)
            elif self._algorithm == "aes256":
                decrypted_bytes = self._decrypt_aes256(encrypted_data)
            else:
                raise ValueError(f"Unsupported algorithm: {self._algorithm}")
            
            return decrypted_bytes.decode('utf-8')
            
        except Exception as e:
            self._logger.error(f"Decryption failed: {e}")
            raise RuntimeError(f"Decryption failed: {e}")
    
    def _encrypt_fernet(self, data: bytes) -> bytes:
        """Шифрование с использованием Fernet.
        
        Args:
            data: Данные для шифрования
            
        Returns:
            Зашифрованные данные
        """
        return self._fernet.encrypt(data)
    
    def _decrypt_fernet(self, encrypted_data: bytes) -> bytes:
        """Расшифровка с использованием Fernet.
        
        Args:
            encrypted_data: Зашифрованные данные
            
        Returns:
            Расшифрованные данные
        """
        return self._fernet.decrypt(encrypted_data)
    
    def _encrypt_aes256(self, data: bytes) -> bytes:
        """Шифрование с использованием AES-256.
        
        Args:
            data: Данные для шифрования
            
        Returns:
            Зашифрованные данные с IV
        """
        # Генерация случайного IV
        iv = secrets.token_bytes(16)  # 128 бит для AES
        
        # Создание шифра
        cipher = Cipher(
            algorithms.AES(self._aes_key),
            modes.CBC(iv),
            backend=default_backend()
        )
        
        encryptor = cipher.encryptor()
        
        # Добавление padding для выравнивания по блокам
        padded_data = self._add_padding(data)
        
        # Шифрование
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        
        # Возврат IV + зашифрованные данные
        return iv + encrypted_data
    
    def _decrypt_aes256(self, encrypted_data: bytes) -> bytes:
        """Расшифровка с использованием AES-256.
        
        Args:
            encrypted_data: Зашифрованные данные с IV
            
        Returns:
            Расшифрованные данные
        """
        # Извлечение IV и данных
        iv = encrypted_data[:16]
        ciphertext = encrypted_data[16:]
        
        # Создание шифра
        cipher = Cipher(
            algorithms.AES(self._aes_key),
            modes.CBC(iv),
            backend=default_backend()
        )
        
        decryptor = cipher.decryptor()
        
        # Расшифровка
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()
        
        # Удаление padding
        return self._remove_padding(padded_data)
    
    def _add_padding(self, data: bytes) -> bytes:
        """Добавление PKCS7 padding.
        
        Args:
            data: Исходные данные
            
        Returns:
            Данные с padding
        """
        block_size = 16  # AES block size
        padding_length = block_size - (len(data) % block_size)
        padding = bytes([padding_length] * padding_length)
        return data + padding
    
    def _remove_padding(self, padded_data: bytes) -> bytes:
        """Удаление PKCS7 padding.
        
        Args:
            padded_data: Данные с padding
            
        Returns:
            Данные без padding
        """
        padding_length = padded_data[-1]
        return padded_data[:-padding_length]
    
    def encrypt_json(self, data: Dict[str, Any]) -> bytes:
        """Шифрование JSON данных.
        
        Args:
            data: Данные для шифрования
            
        Returns:
            Зашифрованные данные
        """
        json_string = json.dumps(data, ensure_ascii=False)
        return self.encrypt(json_string)
    
    def decrypt_json(self, encrypted_data: bytes) -> Dict[str, Any]:
        """Расшифровка JSON данных.
        
        Args:
            encrypted_data: Зашифрованные данные
            
        Returns:
            Расшифрованные данные
        """
        decrypted_string = self.decrypt(encrypted_data)
        return json.loads(decrypted_string)
    
    def generate_hash(self, data: Union[str, bytes], algorithm: str = "sha256") -> str:
        """Генерация хэша данных.
        
        Args:
            data: Данные для хэширования
            algorithm: Алгоритм хэширования
            
        Returns:
            Хэш в hex формате
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        if algorithm == "sha256":
            hash_obj = hashlib.sha256(data)
        elif algorithm == "sha512":
            hash_obj = hashlib.sha512(data)
        elif algorithm == "md5":
            hash_obj = hashlib.md5(data)
        else:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")
        
        return hash_obj.hexdigest()
    
    def verify_hash(self, data: Union[str, bytes], expected_hash: str, algorithm: str = "sha256") -> bool:
        """Проверка хэша данных.
        
        Args:
            data: Данные для проверки
            expected_hash: Ожидаемый хэш
            algorithm: Алгоритм хэширования
            
        Returns:
            True если хэш совпадает
        """
        actual_hash = self.generate_hash(data, algorithm)
        return secrets.compare_digest(actual_hash, expected_hash)
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Генерация безопасного токена.
        
        Args:
            length: Длина токена в байтах
            
        Returns:
            Токен в base64 формате
        """
        token_bytes = secrets.token_bytes(length)
        return base64.urlsafe_b64encode(token_bytes).decode('utf-8')
    
    def encrypt_file(self, file_path: str, output_path: Optional[str] = None) -> str:
        """Шифрование файла.
        
        Args:
            file_path: Путь к исходному файлу
            output_path: Путь к зашифрованному файлу
            
        Returns:
            Путь к зашифрованному файлу
        """
        if output_path is None:
            output_path = file_path + ".encrypted"
        
        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            encrypted_data = self.encrypt(file_data)
            
            with open(output_path, 'wb') as f:
                f.write(encrypted_data)
            
            # Установка безопасных прав доступа
            os.chmod(output_path, 0o600)
            
            self._logger.info(f"File encrypted: {file_path} -> {output_path}")
            return output_path
            
        except Exception as e:
            self._logger.error(f"File encryption failed: {e}")
            raise RuntimeError(f"File encryption failed: {e}")
    
    def decrypt_file(self, encrypted_file_path: str, output_path: Optional[str] = None) -> str:
        """Расшифровка файла.
        
        Args:
            encrypted_file_path: Путь к зашифрованному файлу
            output_path: Путь к расшифрованному файлу
            
        Returns:
            Путь к расшифрованному файлу
        """
        if output_path is None:
            if encrypted_file_path.endswith('.encrypted'):
                output_path = encrypted_file_path[:-10]  # Удаление .encrypted
            else:
                output_path = encrypted_file_path + ".decrypted"
        
        try:
            with open(encrypted_file_path, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.decrypt(encrypted_data)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(decrypted_data)
            
            self._logger.info(f"File decrypted: {encrypted_file_path} -> {output_path}")
            return output_path
            
        except Exception as e:
            self._logger.error(f"File decryption failed: {e}")
            raise RuntimeError(f"File decryption failed: {e}")
    
    def get_key_info(self) -> Dict[str, Any]:
        """Получение информации о ключах.
        
        Returns:
            Информация о ключах и алгоритмах
        """
        return {
            "algorithm": self._algorithm,
            "key_length": len(self._cipher_key),
            "master_key_hash": self.generate_hash(self._master_key),
            "supported_algorithms": ["fernet", "aes256"],
            "supported_hash_algorithms": ["sha256", "sha512", "md5"]
        }
    
    def rotate_key(self, new_master_key: str) -> None:
        """Ротация ключей шифрования.
        
        Args:
            new_master_key: Новый мастер-ключ
        """
        try:
            # Сохранение старого ключа для миграции
            old_cipher_key = self._cipher_key
            
            # Генерация нового ключа
            self._master_key = new_master_key.encode('utf-8')
            self._cipher_key = self._derive_key(self._master_key)
            
            # Обновление шифровальщика
            if self._algorithm == "fernet":
                self._fernet = Fernet(self._cipher_key)
            elif self._algorithm == "aes256":
                self._setup_aes256()
            
            self._logger.info("Encryption key rotated successfully")
            
        except Exception as e:
            self._logger.error(f"Key rotation failed: {e}")
            raise RuntimeError(f"Key rotation failed: {e}")
    
    def secure_delete(self, data: Union[str, bytes]) -> None:
        """Безопасное удаление данных из памяти.
        
        Args:
            data: Данные для удаления
        """
        # Примечание: В Python сложно гарантировать полное удаление из памяти
        # Это базовая реализация для демонстрации концепции
        if isinstance(data, str):
            # Перезапись строки
            data = '\x00' * len(data)
        elif isinstance(data, bytes):
            # Перезапись байтов
            data = b'\x00' * len(data)
        
        # Принудительная сборка мусора
        import gc
        gc.collect()