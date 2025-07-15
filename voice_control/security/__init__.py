"""Security module for voice control system.

Модуль безопасности для системы голосового управления,
включающий управление учетными данными, шифрование и аудит.
"""

from .credentials_manager import SecureCredentialsManager, CredentialInfo
from .encryption import EncryptionManager
from .audit_logger import AuditLogger, SecurityEvent, SecurityEventType, SecurityLevel

__all__ = [
    # Credentials Management
    'SecureCredentialsManager',
    'CredentialInfo',
    
    # Encryption
    'EncryptionManager',
    
    # Audit Logging
    'AuditLogger',
    'SecurityEvent',
    'SecurityEventType',
    'SecurityLevel'
]

__version__ = '1.0.0'
__author__ = 'Voice Control Security Team'
__description__ = 'Security components for voice control system'