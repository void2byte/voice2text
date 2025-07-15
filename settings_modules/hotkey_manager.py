import logging
from PySide6.QtCore import QObject, Signal
from utils.global_hotkey import GlobalHotkey

logger = logging.getLogger(__name__)

class HotkeyManager(QObject):
    hotkey_pressed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.hotkeys = {}
        self.callbacks = {}

    def register_hotkey(self, name, hotkey_str, callback):
        if name in self.hotkeys:
            self.unregister_hotkey(name)
        
        try:
            hotkey = GlobalHotkey(hotkey_str)
            hotkey.press.connect(callback)
            hotkey.start()
            self.hotkeys[name] = hotkey
            self.callbacks[name] = callback
            logger.info(f"Hotkey '{name}' registered with sequence '{hotkey_str}'.")
            return True
        except Exception as e:
            logger.error(f"Failed to register hotkey '{name}' with sequence '{hotkey_str}': {e}")
            return False

    def unregister_hotkey(self, name):
        if name in self.hotkeys:
            try:
                self.hotkeys[name].stop()
                del self.hotkeys[name]
                if name in self.callbacks:
                    del self.callbacks[name]
                logger.info(f"Hotkey '{name}' unregistered.")
            except Exception as e:
                logger.error(f"Failed to unregister hotkey '{name}': {e}")

    def unregister_all(self):
        for name in list(self.hotkeys.keys()):
            self.unregister_hotkey(name)