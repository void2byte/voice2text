import json
import os
import uuid
import logging
from typing import Dict, List, Optional
from window_binder.error_handlers import ErrorHandler, FileOperationError, with_error_handling


class BindingStorage:
    """Класс для управления сохранением и загрузкой привязок"""
    
    def __init__(self, bindings_file: str):
        self.bindings_file = bindings_file
        self.logger = logging.getLogger(__name__)
        self.error_handler = ErrorHandler()
    
    @with_error_handling(context="BindingStorage.save_bindings")
    def save_bindings(self, bindings: Dict[str, Dict]) -> bool:
        """Сохранить привязки в файл"""
        try:
            self.logger.info(f"BindingStorage: [SAVE_START] Starting to save {len(bindings)} bindings to {self.bindings_file}")
            
            os.makedirs(os.path.dirname(self.bindings_file), exist_ok=True)
            bindings_list = []
            
            for binding_id, binding_data in bindings.items():
                binding_copy = binding_data.copy()
                binding_copy['id'] = binding_id
                bindings_list.append(binding_copy)
                
                # Логируем данные перед сохранением
                app_name = binding_data.get('app_name', 'unknown')
                x, y = binding_data.get('x', 'unknown'), binding_data.get('y', 'unknown')
                pos_x, pos_y = binding_data.get('pos_x', 'unknown'), binding_data.get('pos_y', 'unknown')
                self.logger.debug(f"BindingStorage: [SAVING_BINDING] ID: {binding_id}, App: '{app_name}', Window: ({x}, {y}), Position: ({pos_x}, {pos_y})")
            
            with open(self.bindings_file, "w", encoding='utf-8') as f:
                json.dump(bindings_list, f, indent=4, ensure_ascii=False)
            
            self.logger.info(f"BindingStorage: [SAVE_SUCCESS] Successfully saved {len(bindings_list)} bindings to {self.bindings_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"BindingStorage: [SAVE_ERROR] Failed to save bindings: {e}")
            self.error_handler.handle_file_operation_error("сохранения", self.bindings_file, e)
            raise FileOperationError(f"Failed to save bindings: {e}")
    
    @with_error_handling(context="BindingStorage.load_bindings")
    def load_bindings(self) -> Dict[str, Dict]:
        """Загрузить привязки из файла"""
        bindings = {}
        
        if not os.path.exists(self.bindings_file):
            self.logger.info(f"BindingStorage: [LOAD_INFO] Bindings file {self.bindings_file} not found, starting with empty bindings")
            return bindings
        
        try:
            with open(self.bindings_file, "r", encoding='utf-8') as f:
                bindings_list = json.load(f)
                
            for binding in bindings_list:
                # Для обратной совместимости добавляем id если его нет
                if 'id' not in binding:
                    binding['id'] = str(uuid.uuid4())
                
                binding_id = binding.pop('id')
                bindings[binding_id] = binding
            
            self.logger.info(f"BindingStorage: [LOAD_SUCCESS] Loaded {len(bindings)} bindings from {self.bindings_file}")
            
            # Логируем детали каждой загруженной привязки
            for binding_id, binding_data in bindings.items():
                app_name = binding_data.get('app_name', 'unknown')
                x, y = binding_data.get('x', 'unknown'), binding_data.get('y', 'unknown')
                pos_x, pos_y = binding_data.get('pos_x', 'unknown'), binding_data.get('pos_y', 'unknown')
                self.logger.debug(f"BindingStorage: [LOADED_BINDING] ID: {binding_id}, App: '{app_name}', Window: ({x}, {y}), Position: ({pos_x}, {pos_y})")
            
        except (json.JSONDecodeError, FileNotFoundError) as e:
            self.error_handler.handle_file_operation_error("загрузки", self.bindings_file, e, show_dialog=False)
            self.logger.warning(f"BindingStorage: [LOAD_ERROR] Starting with empty bindings due to load error")
            bindings = {}
        
        return bindings
    
    def add_binding(self, bindings: Dict[str, Dict], app_name: str, x: int, y: int, pos_x: int, pos_y: int) -> str:
        """Добавить новую привязку"""
        binding_id = str(uuid.uuid4())
        binding_data = {
            "app_name": app_name,
            "x": x,
            "y": y,
            "pos_x": pos_x,
            "pos_y": pos_y
        }
        
        bindings[binding_id] = binding_data
        self.logger.info(f"BindingStorage: [ADD_BINDING] Created new binding - ID: {binding_id}, App: '{app_name}', Window: ({x}, {y}), Position: ({pos_x}, {pos_y})")
        self.logger.debug(f"BindingStorage: [BINDING_DATA] Full binding data: {binding_data}")
        
        return binding_id
    
    def update_binding_position(self, bindings: Dict[str, Dict], binding_id: str, pos_x: int, pos_y: int) -> bool:
        """Обновить позицию привязки"""
        if binding_id not in bindings:
            self.logger.error(f"BindingStorage: [UPDATE_ERROR] Binding {binding_id} not found for position update")
            return False
        
        old_pos_x = bindings[binding_id].get('pos_x', 'unknown')
        old_pos_y = bindings[binding_id].get('pos_y', 'unknown')
        
        bindings[binding_id]['pos_x'] = pos_x
        bindings[binding_id]['pos_y'] = pos_y
        
        self.logger.info(f"BindingStorage: [UPDATE_POSITION] Updated position for binding {binding_id} - Old: ({old_pos_x}, {old_pos_y}) -> New: ({pos_x}, {pos_y})")
        return True
    
    def remove_binding(self, bindings: Dict[str, Dict], binding_id: str) -> bool:
        """Удалить привязку"""
        if binding_id not in bindings:
            self.logger.warning(f"BindingStorage: [REMOVE_ERROR] Binding {binding_id} not found for removal")
            return False
        
        binding_data = bindings[binding_id]
        app_name = binding_data.get('app_name', 'unknown')
        x, y = binding_data.get('x', 'unknown'), binding_data.get('y', 'unknown')
        pos_x, pos_y = binding_data.get('pos_x', 'unknown'), binding_data.get('pos_y', 'unknown')
        
        self.logger.info(f"BindingStorage: [REMOVE_BINDING] Removing binding - ID: {binding_id}, App: '{app_name}', Window: ({x}, {y}), Position: ({pos_x}, {pos_y})")
        
        bindings.pop(binding_id)
        self.logger.info(f"BindingStorage: [REMOVE_SUCCESS] Successfully removed binding {binding_id}")
        return True
    
    def update_binding(self, bindings: Dict[str, Dict], binding_id: str, **kwargs) -> bool:
        """Обновить данные привязки"""
        if binding_id not in bindings:
            self.logger.error(f"BindingStorage: [UPDATE_ERROR] Binding {binding_id} not found for update")
            return False
        
        # Логируем старые значения
        old_data = bindings[binding_id].copy()
        app_name = old_data.get('app_name', 'unknown')
        
        self.logger.info(f"BindingStorage: [UPDATE_START] Updating binding {binding_id} for app '{app_name}'")
        self.logger.debug(f"BindingStorage: [UPDATE_OLD] Old data: {old_data}")
        self.logger.debug(f"BindingStorage: [UPDATE_CHANGES] Changes to apply: {kwargs}")
        
        for key, value in kwargs.items():
            if key in ['app_name', 'x', 'y', 'pos_x', 'pos_y']:
                old_value = bindings[binding_id].get(key, 'not_set')
                bindings[binding_id][key] = value
                self.logger.debug(f"BindingStorage: [UPDATE_FIELD] Field '{key}': {old_value} -> {value}")
        
        new_data = bindings[binding_id]
        self.logger.info(f"BindingStorage: [UPDATE_SUCCESS] Successfully updated binding {binding_id}")
        self.logger.debug(f"BindingStorage: [UPDATE_NEW] New data: {new_data}")
        return True