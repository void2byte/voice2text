#!/usr/bin/env python3
"""
Основной файл для запуска виджета голосовой аннотации.
"""

with open('startup_test.log', 'w') as f:
    f.write('main.py execution started')

import logging
import sys
from PySide6.QtWidgets import QApplication
from logging_config import configure_logging

# Настраиваем логирование
configure_logging()
logger = logging.getLogger(__name__)

logger.debug("main.py: Script started")


logger.debug("main.py: Attempting to import TrayApplication")
try:
    from tray_app import TrayApplication
    logger.debug("main.py: TrayApplication imported successfully")
except ImportError as e:
    logger.error(f"main.py: Failed to import TrayApplication: {e}", exc_info=True)
    sys.exit(1)
except Exception as e:
    logger.error(f"main.py: An unexpected error occurred during import: {e}", exc_info=True)
    sys.exit(1)

if __name__ == "__main__":
    logger.info("main.py: Starting application...")
    try:
        logger.debug("main.py: __main__ block reached")
        logging.info("ЗАПУСК ЛОГГИРОВАНИЯ")
        app = TrayApplication(sys.argv)
        logger.info("Приложение создано, запускаем exec().")
        exit_code = app.exec()
        logger.info(f"main.py: Application finished with exit code {exit_code}")
        sys.exit(exit_code)
    except Exception as e:
        logger.critical(f"main.py: A critical error occurred: {e}", exc_info=True)
        sys.exit(1)