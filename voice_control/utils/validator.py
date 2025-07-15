"""Input Validator for voice control system.

Валидатор входных данных для системы голосового управления
с поддержкой различных типов валидации и настраиваемых правил.
"""

import re
import os
import json
import ipaddress
from typing import Any, Dict, List, Optional, Union, Callable, Tuple
from pathlib import Path
from urllib.parse import urlparse
from dataclasses import dataclass
from enum import Enum
import mimetypes


class ValidationLevel(Enum):
    """Уровни валидации."""
    STRICT = "strict"
    NORMAL = "normal"
    LENIENT = "lenient"


class ValidationError(Exception):
    """Исключение валидации."""
    
    def __init__(self, message: str, field: str = None, value: Any = None):
        super().__init__(message)
        self.field = field
        self.value = value
        self.message = message


@dataclass
class ValidationRule:
    """Правило валидации."""
    name: str
    validator: Callable[[Any], bool]
    error_message: str
    required: bool = True
    level: ValidationLevel = ValidationLevel.NORMAL


@dataclass
class ValidationResult:
    """Результат валидации."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    field_errors: Dict[str, List[str]]
    validated_data: Optional[Dict[str, Any]] = None


class InputValidator:
    """Валидатор входных данных для системы голосового управления.
    
    Обеспечивает валидацию различных типов данных с поддержкой
    настраиваемых правил и уровней строгости.
    """
    
    def __init__(self, validation_level: ValidationLevel = ValidationLevel.NORMAL):
        """Инициализация валидатора.
        
        Args:
            validation_level: Уровень валидации
        """
        self._validation_level = validation_level
        self._custom_rules: Dict[str, List[ValidationRule]] = {}
        self._global_rules: List[ValidationRule] = []
        
        # Предустановленные паттерны
        self._patterns = {
            'email': re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
            'phone': re.compile(r'^[+]?[1-9]?[0-9]{7,15}$'),
            'url': re.compile(r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?)?$'),
            'ipv4': re.compile(r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'),
            'mac_address': re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'),
            'uuid': re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$', re.IGNORECASE),
            'api_key': re.compile(r'^[A-Za-z0-9_-]{16,}$'),
            'filename': re.compile(r'^[^<>:"/\\|?*\x00-\x1f]+$'),
            'version': re.compile(r'^\d+\.\d+\.\d+(?:-[a-zA-Z0-9]+)?$')
        }
        
        # Настройки по умолчанию
        self._default_settings = {
            'max_string_length': 10000,
            'max_list_length': 1000,
            'max_dict_size': 1000,
            'max_file_size': 100 * 1024 * 1024,  # 100MB
            'allowed_file_extensions': ['.txt', '.json', '.wav', '.mp3', '.mp4', '.avi'],
            'forbidden_patterns': [r'<script', r'javascript:', r'vbscript:', r'onload='],
            'min_password_length': 8,
            'max_password_length': 128
        }
    
    def add_custom_rule(self, field_name: str, rule: ValidationRule) -> None:
        """Добавление пользовательского правила валидации.
        
        Args:
            field_name: Название поля
            rule: Правило валидации
        """
        if field_name not in self._custom_rules:
            self._custom_rules[field_name] = []
        self._custom_rules[field_name].append(rule)
    
    def add_global_rule(self, rule: ValidationRule) -> None:
        """Добавление глобального правила валидации.
        
        Args:
            rule: Правило валидации
        """
        self._global_rules.append(rule)
    
    def validate_data(self, data: Dict[str, Any], schema: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Валидация данных по схеме.
        
        Args:
            data: Данные для валидации
            schema: Схема валидации
            
        Returns:
            Результат валидации
        """
        errors = []
        warnings = []
        field_errors = {}
        validated_data = {}
        
        try:
            # Валидация по схеме
            if schema:
                for field_name, field_config in schema.items():
                    field_errors[field_name] = []
                    
                    # Проверка обязательности поля
                    if field_config.get('required', False) and field_name not in data:
                        field_errors[field_name].append(f"Field '{field_name}' is required")
                        continue
                    
                    if field_name in data:
                        field_value = data[field_name]
                        
                        # Валидация типа
                        expected_type = field_config.get('type')
                        if expected_type and not self._validate_type(field_value, expected_type):
                            field_errors[field_name].append(f"Field '{field_name}' must be of type {expected_type}")
                            continue
                        
                        # Валидация значения
                        validation_result = self._validate_field_value(field_name, field_value, field_config)
                        if not validation_result[0]:
                            field_errors[field_name].extend(validation_result[1])
                        else:
                            validated_data[field_name] = field_value
            
            # Применение пользовательских правил
            for field_name, value in data.items():
                if field_name in self._custom_rules:
                    for rule in self._custom_rules[field_name]:
                        if rule.level.value <= self._validation_level.value:
                            try:
                                if not rule.validator(value):
                                    if field_name not in field_errors:
                                        field_errors[field_name] = []
                                    field_errors[field_name].append(rule.error_message)
                            except Exception as e:
                                if field_name not in field_errors:
                                    field_errors[field_name] = []
                                field_errors[field_name].append(f"Validation error: {str(e)}")
            
            # Применение глобальных правил
            for rule in self._global_rules:
                if rule.level.value <= self._validation_level.value:
                    try:
                        if not rule.validator(data):
                            errors.append(rule.error_message)
                    except Exception as e:
                        errors.append(f"Global validation error: {str(e)}")
            
            # Сбор всех ошибок
            for field, field_error_list in field_errors.items():
                errors.extend(field_error_list)
            
            # Удаление пустых списков ошибок
            field_errors = {k: v for k, v in field_errors.items() if v}
            
            is_valid = len(errors) == 0
            
            return ValidationResult(
                is_valid=is_valid,
                errors=errors,
                warnings=warnings,
                field_errors=field_errors,
                validated_data=validated_data if is_valid else None
            )
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"Validation failed: {str(e)}"],
                warnings=[],
                field_errors={}
            )
    
    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """Валидация типа значения.
        
        Args:
            value: Значение для проверки
            expected_type: Ожидаемый тип
            
        Returns:
            True если тип корректен
        """
        type_mapping = {
            'str': str,
            'string': str,
            'int': int,
            'integer': int,
            'float': float,
            'number': (int, float),
            'bool': bool,
            'boolean': bool,
            'list': list,
            'array': list,
            'dict': dict,
            'object': dict,
            'none': type(None),
            'null': type(None)
        }
        
        expected_python_type = type_mapping.get(expected_type.lower())
        if expected_python_type:
            return isinstance(value, expected_python_type)
        
        return True
    
    def _validate_field_value(self, field_name: str, value: Any, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Валидация значения поля.
        
        Args:
            field_name: Название поля
            value: Значение поля
            config: Конфигурация валидации
            
        Returns:
            Кортеж (валидно, список ошибок)
        """
        errors = []
        
        # Валидация длины строки
        if isinstance(value, str):
            min_length = config.get('min_length')
            max_length = config.get('max_length', self._default_settings['max_string_length'])
            
            if min_length and len(value) < min_length:
                errors.append(f"Field '{field_name}' must be at least {min_length} characters long")
            
            if max_length and len(value) > max_length:
                errors.append(f"Field '{field_name}' must be no more than {max_length} characters long")
        
        # Валидация диапазона чисел
        if isinstance(value, (int, float)):
            min_value = config.get('min_value')
            max_value = config.get('max_value')
            
            if min_value is not None and value < min_value:
                errors.append(f"Field '{field_name}' must be at least {min_value}")
            
            if max_value is not None and value > max_value:
                errors.append(f"Field '{field_name}' must be no more than {max_value}")
        
        # Валидация паттерна
        pattern = config.get('pattern')
        if pattern and isinstance(value, str):
            if isinstance(pattern, str):
                if pattern in self._patterns:
                    if not self._patterns[pattern].match(value):
                        errors.append(f"Field '{field_name}' does not match required pattern")
                else:
                    try:
                        if not re.match(pattern, value):
                            errors.append(f"Field '{field_name}' does not match required pattern")
                    except re.error:
                        errors.append(f"Invalid pattern for field '{field_name}'")
        
        # Валидация списка допустимых значений
        allowed_values = config.get('allowed_values')
        if allowed_values and value not in allowed_values:
            errors.append(f"Field '{field_name}' must be one of: {', '.join(map(str, allowed_values))}")
        
        # Валидация запрещенных значений
        forbidden_values = config.get('forbidden_values')
        if forbidden_values and value in forbidden_values:
            errors.append(f"Field '{field_name}' cannot be one of: {', '.join(map(str, forbidden_values))}")
        
        return len(errors) == 0, errors
    
    def validate_string(self, value: str, 
                       min_length: Optional[int] = None,
                       max_length: Optional[int] = None,
                       pattern: Optional[str] = None,
                       forbidden_patterns: Optional[List[str]] = None) -> ValidationResult:
        """Валидация строки.
        
        Args:
            value: Строка для валидации
            min_length: Минимальная длина
            max_length: Максимальная длина
            pattern: Паттерн для проверки
            forbidden_patterns: Запрещенные паттерны
            
        Returns:
            Результат валидации
        """
        errors = []
        warnings = []
        
        if not isinstance(value, str):
            errors.append("Value must be a string")
            return ValidationResult(False, errors, warnings, {})
        
        # Проверка длины
        if min_length and len(value) < min_length:
            errors.append(f"String must be at least {min_length} characters long")
        
        max_len = max_length or self._default_settings['max_string_length']
        if len(value) > max_len:
            errors.append(f"String must be no more than {max_len} characters long")
        
        # Проверка паттерна
        if pattern:
            if pattern in self._patterns:
                if not self._patterns[pattern].match(value):
                    errors.append(f"String does not match required pattern: {pattern}")
            else:
                try:
                    if not re.match(pattern, value):
                        errors.append(f"String does not match required pattern")
                except re.error:
                    errors.append("Invalid pattern provided")
        
        # Проверка запрещенных паттернов
        forbidden = forbidden_patterns or self._default_settings['forbidden_patterns']
        for forbidden_pattern in forbidden:
            if re.search(forbidden_pattern, value, re.IGNORECASE):
                errors.append(f"String contains forbidden pattern: {forbidden_pattern}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            field_errors={}
        )
    
    def validate_email(self, email: str) -> ValidationResult:
        """Валидация email адреса.
        
        Args:
            email: Email для валидации
            
        Returns:
            Результат валидации
        """
        errors = []
        warnings = []
        
        if not isinstance(email, str):
            errors.append("Email must be a string")
        elif not self._patterns['email'].match(email):
            errors.append("Invalid email format")
        elif len(email) > 254:  # RFC 5321 limit
            errors.append("Email address is too long")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            field_errors={}
        )
    
    def validate_url(self, url: str, allowed_schemes: Optional[List[str]] = None) -> ValidationResult:
        """Валидация URL.
        
        Args:
            url: URL для валидации
            allowed_schemes: Разрешенные схемы (http, https, ftp, etc.)
            
        Returns:
            Результат валидации
        """
        errors = []
        warnings = []
        
        if not isinstance(url, str):
            errors.append("URL must be a string")
            return ValidationResult(False, errors, warnings, {})
        
        try:
            parsed = urlparse(url)
            
            if not parsed.scheme:
                errors.append("URL must have a scheme (http, https, etc.)")
            
            if not parsed.netloc:
                errors.append("URL must have a domain")
            
            if allowed_schemes and parsed.scheme not in allowed_schemes:
                errors.append(f"URL scheme must be one of: {', '.join(allowed_schemes)}")
            
            # Дополнительная проверка с помощью регулярного выражения
            if not self._patterns['url'].match(url):
                warnings.append("URL format may be invalid")
                
        except Exception as e:
            errors.append(f"Invalid URL format: {str(e)}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            field_errors={}
        )
    
    def validate_file_path(self, file_path: str, 
                          must_exist: bool = False,
                          allowed_extensions: Optional[List[str]] = None,
                          max_size: Optional[int] = None) -> ValidationResult:
        """Валидация пути к файлу.
        
        Args:
            file_path: Путь к файлу
            must_exist: Файл должен существовать
            allowed_extensions: Разрешенные расширения
            max_size: Максимальный размер файла в байтах
            
        Returns:
            Результат валидации
        """
        errors = []
        warnings = []
        
        if not isinstance(file_path, str):
            errors.append("File path must be a string")
            return ValidationResult(False, errors, warnings, {})
        
        try:
            path = Path(file_path)
            
            # Проверка на недопустимые символы
            if not self._patterns['filename'].match(path.name):
                errors.append("File name contains invalid characters")
            
            # Проверка существования
            if must_exist and not path.exists():
                errors.append(f"File does not exist: {file_path}")
            
            # Проверка расширения
            extensions = allowed_extensions or self._default_settings['allowed_file_extensions']
            if extensions and path.suffix.lower() not in [ext.lower() for ext in extensions]:
                errors.append(f"File extension must be one of: {', '.join(extensions)}")
            
            # Проверка размера
            if path.exists() and path.is_file():
                file_size = path.stat().st_size
                max_file_size = max_size or self._default_settings['max_file_size']
                
                if file_size > max_file_size:
                    errors.append(f"File size ({file_size} bytes) exceeds maximum ({max_file_size} bytes)")
                
                # Проверка MIME типа
                mime_type, _ = mimetypes.guess_type(file_path)
                if mime_type and mime_type.startswith('application/') and 'executable' in mime_type:
                    warnings.append("File appears to be executable")
                    
        except Exception as e:
            errors.append(f"Invalid file path: {str(e)}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            field_errors={}
        )
    
    def validate_ip_address(self, ip: str, version: Optional[int] = None) -> ValidationResult:
        """Валидация IP адреса.
        
        Args:
            ip: IP адрес для валидации
            version: Версия IP (4 или 6)
            
        Returns:
            Результат валидации
        """
        errors = []
        warnings = []
        
        if not isinstance(ip, str):
            errors.append("IP address must be a string")
            return ValidationResult(False, errors, warnings, {})
        
        try:
            ip_obj = ipaddress.ip_address(ip)
            
            if version and ip_obj.version != version:
                errors.append(f"IP address must be version {version}")
            
            # Проверка на приватные адреса
            if ip_obj.is_private:
                warnings.append("IP address is private")
            
            # Проверка на loopback
            if ip_obj.is_loopback:
                warnings.append("IP address is loopback")
                
        except ValueError as e:
            errors.append(f"Invalid IP address: {str(e)}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            field_errors={}
        )
    
    def validate_json(self, json_string: str, schema: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Валидация JSON строки.
        
        Args:
            json_string: JSON строка для валидации
            schema: Схема для валидации структуры
            
        Returns:
            Результат валидации
        """
        errors = []
        warnings = []
        validated_data = None
        
        if not isinstance(json_string, str):
            errors.append("JSON must be a string")
            return ValidationResult(False, errors, warnings, {})
        
        try:
            validated_data = json.loads(json_string)
            
            # Валидация по схеме
            if schema:
                schema_result = self.validate_data(validated_data, schema)
                errors.extend(schema_result.errors)
                warnings.extend(schema_result.warnings)
                
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON format: {str(e)}")
        except Exception as e:
            errors.append(f"JSON validation error: {str(e)}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            field_errors={},
            validated_data=validated_data
        )
    
    def validate_password(self, password: str, 
                         min_length: Optional[int] = None,
                         require_uppercase: bool = True,
                         require_lowercase: bool = True,
                         require_digits: bool = True,
                         require_special: bool = True) -> ValidationResult:
        """Валидация пароля.
        
        Args:
            password: Пароль для валидации
            min_length: Минимальная длина
            require_uppercase: Требовать заглавные буквы
            require_lowercase: Требовать строчные буквы
            require_digits: Требовать цифры
            require_special: Требовать специальные символы
            
        Returns:
            Результат валидации
        """
        errors = []
        warnings = []
        
        if not isinstance(password, str):
            errors.append("Password must be a string")
            return ValidationResult(False, errors, warnings, {})
        
        min_len = min_length or self._default_settings['min_password_length']
        max_len = self._default_settings['max_password_length']
        
        # Проверка длины
        if len(password) < min_len:
            errors.append(f"Password must be at least {min_len} characters long")
        
        if len(password) > max_len:
            errors.append(f"Password must be no more than {max_len} characters long")
        
        # Проверка требований к символам
        if require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if require_digits and not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")
        
        if require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        # Проверка на простые пароли
        common_passwords = ['password', '123456', 'qwerty', 'admin', 'letmein']
        if password.lower() in common_passwords:
            errors.append("Password is too common")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            field_errors={}
        )
    
    def sanitize_string(self, value: str, 
                       remove_html: bool = True,
                       remove_scripts: bool = True,
                       max_length: Optional[int] = None) -> str:
        """Санитизация строки.
        
        Args:
            value: Строка для санитизации
            remove_html: Удалить HTML теги
            remove_scripts: Удалить скрипты
            max_length: Максимальная длина
            
        Returns:
            Санитизированная строка
        """
        if not isinstance(value, str):
            return str(value)
        
        result = value
        
        # Удаление HTML тегов
        if remove_html:
            result = re.sub(r'<[^>]+>', '', result)
        
        # Удаление скриптов
        if remove_scripts:
            for pattern in self._default_settings['forbidden_patterns']:
                result = re.sub(pattern, '', result, flags=re.IGNORECASE)
        
        # Обрезка по длине
        if max_length and len(result) > max_length:
            result = result[:max_length]
        
        # Удаление лишних пробелов
        result = result.strip()
        
        return result
    
    def get_validation_summary(self, results: List[ValidationResult]) -> Dict[str, Any]:
        """Получение сводки по результатам валидации.
        
        Args:
            results: Список результатов валидации
            
        Returns:
            Сводка валидации
        """
        total_validations = len(results)
        successful_validations = sum(1 for r in results if r.is_valid)
        total_errors = sum(len(r.errors) for r in results)
        total_warnings = sum(len(r.warnings) for r in results)
        
        return {
            'total_validations': total_validations,
            'successful_validations': successful_validations,
            'failed_validations': total_validations - successful_validations,
            'success_rate': (successful_validations / total_validations * 100) if total_validations > 0 else 0,
            'total_errors': total_errors,
            'total_warnings': total_warnings,
            'validation_level': self._validation_level.value
        }