import logging
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QKeySequenceEdit
from PySide6.QtGui import QKeySequence

logger = logging.getLogger(__name__)

class HotkeySettingsDialog(QDialog):
    def __init__(self, hotkey_manager, parent=None):
        super().__init__(parent)
        self.hotkey_manager = hotkey_manager
        self.setWindowTitle("Настройка горячих клавиш")

        self.layout = QVBoxLayout(self)

        self.hotkey_edits = {}

        for name, hotkey in self.hotkey_manager.hotkeys.items():
            h_layout = QHBoxLayout()
            label = QLabel(f"Действие: {name}")
            key_sequence_edit = QKeySequenceEdit(self)
            key_sequence_edit.setKeySequence(QKeySequence.fromString(hotkey.hotkey))
            
            h_layout.addWidget(label)
            h_layout.addWidget(key_sequence_edit)
            self.layout.addLayout(h_layout)
            self.hotkey_edits[name] = key_sequence_edit

        self.save_button = QPushButton("Сохранить")
        self.save_button.clicked.connect(self.save_hotkeys)
        self.layout.addWidget(self.save_button)

    def save_hotkeys(self):
        for name, key_sequence_edit in self.hotkey_edits.items():
            new_hotkey_str = key_sequence_edit.keySequence().toString()
            callback = self.hotkey_manager.callbacks.get(name)
            if callback:
                self.hotkey_manager.register_hotkey(name, new_hotkey_str, callback)
            else:
                logger.warning(f"No callback found for hotkey '{name}'. Cannot re-register.")
        self.accept()