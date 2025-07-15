#!/usr/bin/env python3
"""Тестовый скрипт для проверки UI диалога настроек"""

import sys
from PySide6.QtWidgets import QApplication
from window_binder.settings_dialog import SettingsDialog

def main():
    """Запуск тестового диалога настроек"""
    app = QApplication(sys.argv)
    
    # Создаем и показываем диалог настроек
    dialog = SettingsDialog()
    dialog.setWindowTitle("Тест переключателя режимов")
    dialog.resize(400, 500)
    dialog.show()
    
    # Запускаем приложение
    sys.exit(app.exec())

if __name__ == "__main__":
    main()