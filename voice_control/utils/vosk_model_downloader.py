#!/usr/bin/env python3
"""
Скрипт для скачивания моделей Vosk.

Использование:
    python vosk_model_downloader.py --language ru --size small
    python vosk_model_downloader.py --language en --size large
"""

import os
import sys
import argparse
import requests
import zipfile
import shutil
from pathlib import Path
from typing import Dict, Optional

# Доступные модели Vosk
VOSK_MODELS = {
    'ru': {
        'small': {
            'url': 'https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip',
            'name': 'vosk-model-small-ru-0.22',
            'size': '45MB'
        },
        'large': {
            'url': 'https://alphacephei.com/vosk/models/vosk-model-ru-0.42.zip',
            'name': 'vosk-model-ru-0.42',
            'size': '1.5GB'
        }
    },
    'en': {
        'small': {
            'url': 'https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip',
            'name': 'vosk-model-small-en-us-0.15',
            'size': '40MB'
        },
        'large': {
            'url': 'https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip',
            'name': 'vosk-model-en-us-0.22',
            'size': '1.8GB'
        }
    }
}


def download_file(url: str, filepath: Path, chunk_size: int = 8192) -> bool:
    """Скачивает файл с отображением прогресса."""
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    
                    if total_size > 0:
                        progress = (downloaded_size / total_size) * 100
                        print(f"\rСкачано: {progress:.1f}% ({downloaded_size // 1024 // 1024}MB)", end='', flush=True)
        
        print()  # Новая строка после завершения
        return True
        
    except Exception as e:
        print(f"\nОшибка скачивания: {e}")
        return False


def extract_archive(archive_path: Path, extract_to: Path) -> Optional[Path]:
    """Извлекает архив и возвращает путь к модели."""
    try:
        print(f"Извлечение архива: {archive_path}")
        
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        
        # Ищем папку модели
        for item in extract_to.iterdir():
            if item.is_dir() and 'vosk-model' in item.name:
                return item
        
        return None
        
    except Exception as e:
        print(f"Ошибка извлечения: {e}")
        return None


def download_vosk_model(language: str, size: str, models_dir: Path) -> Optional[Path]:
    """Скачивает и устанавливает модель Vosk."""
    if language not in VOSK_MODELS:
        print(f"Язык '{language}' не поддерживается. Доступные: {list(VOSK_MODELS.keys())}")
        return None
    
    if size not in VOSK_MODELS[language]:
        print(f"Размер '{size}' не доступен для языка '{language}'. Доступные: {list(VOSK_MODELS[language].keys())}")
        return None
    
    model_info = VOSK_MODELS[language][size]
    model_name = model_info['name']
    model_url = model_info['url']
    model_size = model_info['size']
    
    # Создаем директорию для моделей
    models_dir.mkdir(parents=True, exist_ok=True)
    
    # Проверяем, не установлена ли уже модель
    model_path = models_dir / model_name
    if model_path.exists():
        print(f"Модель уже установлена: {model_path}")
        return model_path
    
    print(f"Скачивание модели Vosk:")
    print(f"  Язык: {language}")
    print(f"  Размер: {size} ({model_size})")
    print(f"  URL: {model_url}")
    print(f"  Путь установки: {model_path}")
    print()
    
    # Скачиваем архив
    archive_name = f"{model_name}.zip"
    archive_path = models_dir / archive_name
    
    print(f"Скачивание {archive_name}...")
    if not download_file(model_url, archive_path):
        return None
    
    # Извлекаем архив
    extracted_path = extract_archive(archive_path, models_dir)
    if not extracted_path:
        print("Не удалось найти модель в архиве")
        return None
    
    # Переименовываем папку, если нужно
    if extracted_path.name != model_name:
        final_path = models_dir / model_name
        if final_path.exists():
            shutil.rmtree(final_path)
        extracted_path.rename(final_path)
        extracted_path = final_path
    
    # Удаляем архив
    archive_path.unlink()
    
    print(f"\nМодель успешно установлена: {extracted_path}")
    return extracted_path


def list_available_models():
    """Выводит список доступных моделей."""
    print("Доступные модели Vosk:")
    print()
    
    for language, models in VOSK_MODELS.items():
        print(f"Язык: {language}")
        for size, info in models.items():
            print(f"  {size}: {info['name']} ({info['size']})")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Скачивание моделей Vosk для распознавания речи",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s --language ru --size small
  %(prog)s --language en --size large
  %(prog)s --list
"""
    )
    
    parser.add_argument(
        '--language', '-l',
        choices=list(VOSK_MODELS.keys()),
        help='Язык модели'
    )
    
    parser.add_argument(
        '--size', '-s',
        choices=['small', 'large'],
        help='Размер модели'
    )
    
    parser.add_argument(
        '--models-dir', '-d',
        type=Path,
        default=Path('models'),
        help='Директория для установки моделей (по умолчанию: models)'
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='Показать список доступных моделей'
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_available_models()
        return
    
    if not args.language or not args.size:
        parser.print_help()
        print("\nОшибка: необходимо указать --language и --size")
        sys.exit(1)
    
    # Скачиваем модель
    model_path = download_vosk_model(args.language, args.size, args.models_dir)
    
    if model_path:
        print(f"\nДля использования модели в коде:")
        print(f"config.model_path = r'{model_path}'")
        print(f"config.engine = RecognitionEngine.VOSK")
    else:
        print("\nНе удалось скачать модель")
        sys.exit(1)


if __name__ == '__main__':
    main()