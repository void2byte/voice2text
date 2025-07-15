import keyboard
from PySide6.QtCore import QObject, Signal

class GlobalHotkey(QObject):
    press = Signal()

    def __init__(self, hotkey, parent=None):
        super().__init__(parent)
        self.hotkey = hotkey
        self._is_running = False

    def start(self):
        if not self._is_running:
            keyboard.add_hotkey(self.hotkey, self.press.emit)
            self._is_running = True

    def stop(self):
        if self._is_running:
            keyboard.remove_hotkey(self.hotkey)
            self._is_running = False