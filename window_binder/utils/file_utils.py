"""Утилиты для работы с файлами"""

import os
import logging
import shutil
import json
from datetime import datetime
from typing import Optional, Dict, Any

def load_bindings(file_path: str) -> Dict[str, Any]:
    """Загружает привязки из JSON-файла."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

def save_bindings(file_path: str, bindings: Dict[str, Any]) -> None:
    """Сохраняет привязки в JSON-файл."""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(bindings, f, indent=4, ensure_ascii=False)


class FileUtils:
    """Утилиты для работы с файлами"""
    
    @staticmethod
    def ensure_directory_exists(file_path: str) -> bool:
        """Убедиться, что директория для файла существует"""
        try:
            directory = os.path.dirname(file_path)
            if directory:
                os.makedirs(directory, exist_ok=True)
            return True
        except Exception as e:
            logging.error(f"Error creating directory for {file_path}: {e}")
            return False
    
    @staticmethod
    def create_backup(file_path: str, backup_dir: str = None) -> Optional[str]:
        """Создать резервную копию файла"""
        if not os.path.exists(file_path):
            return None
        
        try:
            if backup_dir is None:
                backup_dir = os.path.join(os.path.dirname(file_path), "backups")
            
            FileUtils.ensure_directory_exists(backup_dir)
            
            # Создаем имя файла с временной меткой
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.basename(file_path)
            name, ext = os.path.splitext(filename)
            backup_filename = f"{name}_{timestamp}{ext}"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            shutil.copy2(file_path, backup_path)
            logging.info(f"Created backup: {backup_path}")
            return backup_path
            
        except Exception as e:
            logging.error(f"Error creating backup for {file_path}: {e}")
            return None
    
    @staticmethod
    def cleanup_old_backups(backup_dir: str, max_backups: int = 5) -> None:
        """Удалить старые резервные копии"""
        try:
            if not os.path.exists(backup_dir):
                return
            
            # Получаем список файлов резервных копий
            backup_files = []
            for filename in os.listdir(backup_dir):
                file_path = os.path.join(backup_dir, filename)
                if os.path.isfile(file_path):
                    backup_files.append((file_path, os.path.getmtime(file_path)))
            
            # Сортируем по времени модификации (новые первыми)
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            # Удаляем старые файлы
            for file_path, _ in backup_files[max_backups:]:
                try:
                    os.remove(file_path)
                    logging.info(f"Removed old backup: {file_path}")
                except Exception as e:
                    logging.error(f"Error removing backup {file_path}: {e}")
                    
        except Exception as e:
            logging.error(f"Error cleaning up backups in {backup_dir}: {e}")