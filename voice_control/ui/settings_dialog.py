"""
Диалоговое окно для настроек распознавания речи.
"""

from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton
from PySide6.QtCore import Signal

from .settings_tab import SettingsTabRecognizer
from .base_recognizer import BaseRecognizer

class SettingsDialog(QDialog):
    """Диалоговое окно настроек."""
    
    settings_applied = Signal(BaseRecognizer)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Настройки распознавания речи"))
        
        self.settings_tab = SettingsTabRecognizer()
        self.settings_tab.settings_applied.connect(self.on_settings_applied)

        self.close_button = QPushButton(self.tr("Закрыть"))
        self.close_button.clicked.connect(self.accept)

        layout = QVBoxLayout()
        layout.addWidget(self.settings_tab)
        layout.addWidget(self.close_button)
        self.setLayout(layout)

    def on_settings_applied(self, recognizer: BaseRecognizer):
        self.settings_applied.emit(recognizer)