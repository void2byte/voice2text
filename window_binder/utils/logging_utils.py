"""Утилиты для логирования"""

import logging
from window_binder.config import config
from window_binder.utils.file_utils import FileUtils


class LoggingUtils:
    """Утилиты для логирования"""
    
    @staticmethod
    def setup_logger(name: str, level: str = None) -> logging.Logger:
        """Настроить логгер"""
        logger = logging.getLogger(name)
        
        if level is None:
            level = config.logging.log_level
        
        logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        
        # Проверяем, есть ли уже обработчики
        if not logger.handlers:
            # Консольный обработчик
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # Файловый обработчик (если включен)
            if config.logging.log_to_file:
                FileUtils.ensure_directory_exists(config.logging.log_file)
                file_handler = logging.FileHandler(config.logging.log_file, encoding='utf-8')
                file_handler.setLevel(logging.DEBUG)
                
                # Форматтер
                formatter = logging.Formatter(config.logging.log_format)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
            
            # Простой форматтер для консоли
            console_formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
        
        return logger