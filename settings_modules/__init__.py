"""
Пакет для работы с настройками приложения.
"""

from .settings_manager import SettingsManager
from .settings_applicator import SettingsApplicator
from .hotkey_widget import HotkeyEditor
from .tabs.base_settings_tab import BaseSettingsTab
from .tabs.voice_settings_tab import VoiceSettingsTab
from .tabs.notification_settings_tab import NotificationSettingsTab
from .tabs.file_settings_tab import FileSettingsTab

__all__ = [
    'SettingsManager', 
    'SettingsApplicator', 
    'HotkeyEditor',
    'BaseSettingsTab',
    'VoiceSettingsTab',
    'NotificationSettingsTab',
    'FileSettingsTab'
]
