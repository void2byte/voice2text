#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для автоматической установки зависимостей проекта.
"""

import subprocess
import sys
import os
import logging
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_python_version():
    """Проверяет версию Python."""
    if sys.version_info < (3, 8):
        logger.error("Требуется Python 3.8 или выше")
        sys.exit(1)
    logger.info(f"Python версия: {sys.version}")

def install_package(package_name):
    """Устанавливает пакет через pip."""
    try:
        logger.info(f"Установка {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        logger.info(f"✓ {package_name} успешно установлен")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"✗ Ошибка установки {package_name}: {e}")
        return False

def install_requirements():
    """Устанавливает зависимости из requirements.txt."""
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        logger.error(f"Файл {requirements_file} не найден")
        return False
    
    try:
        logger.info("Установка зависимостей из requirements.txt...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ])
        logger.info("✓ Все зависимости успешно установлены")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"✗ Ошибка установки зависимостей: {e}")
        return False

def install_optional_dependencies():
    """Устанавливает опциональные зависимости."""
    optional_packages = {
        "google-cloud-speech": "Google Cloud Speech API",
        "vosk": "Локальное распознавание речи Vosk"
    }
    
    logger.info("\nУстановка опциональных зависимостей:")
    
    for package, description in optional_packages.items():
        response = input(f"Установить {package} ({description})? [y/N]: ").strip().lower()
        if response in ['y', 'yes', 'да']:
            install_package(package)
        else:
            logger.info(f"Пропуск {package}")

def check_installation():
    """Проверяет успешность установки основных пакетов."""
    logger.info("\nПроверка установленных пакетов:")
    
    required_packages = [
        "PySide6",
        "yandex-speechkit", 
        "sounddevice",
        "requests"
    ]
    
    all_installed = True
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_').lower())
            logger.info(f"✓ {package} установлен")
        except ImportError:
            logger.error(f"✗ {package} не установлен")
            all_installed = False
    
    # Проверка опциональных пакетов
    optional_packages = {
        "google.cloud.speech": "Google Cloud Speech",
        "vosk": "Vosk"
    }
    
    for module, name in optional_packages.items():
        try:
            __import__(module)
            logger.info(f"✓ {name} установлен (опционально)")
        except ImportError:
            logger.warning(f"⚠ {name} не установлен (опционально)")
    
    return all_installed

def main():
    """Основная функция установки."""
    logger.info("=== Установка зависимостей Voice2Text ===")
    
    # Проверка версии Python
    check_python_version()
    
    # Обновление pip
    logger.info("Обновление pip...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        logger.info("✓ pip обновлен")
    except subprocess.CalledProcessError:
        logger.warning("⚠ Не удалось обновить pip")
    
    # Установка основных зависимостей
    if not install_requirements():
        logger.error("Не удалось установить основные зависимости")
        sys.exit(1)
    
    # Установка опциональных зависимостей
    install_optional_dependencies()
    
    # Проверка установки
    if check_installation():
        logger.info("\n✓ Все основные зависимости успешно установлены!")
        logger.info("Теперь вы можете запустить приложение:")
        logger.info("  python main.py")
        logger.info("  python run_speech_recognition.py")
    else:
        logger.error("\n✗ Некоторые зависимости не установлены")
        logger.info("Попробуйте установить их вручную:")
        logger.info("  pip install -r requirements.txt")

if __name__ == "__main__":
    main()