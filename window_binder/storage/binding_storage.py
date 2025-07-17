import json
import os
import uuid
import logging
from typing import Dict, List, Optional
from window_binder.models.binding_model import WindowBinding


class BindingStorage:
    """Класс для управления сохранением и загрузкой привязок"""
    
    def __init__(self, bindings_file: str):
        self.bindings_file = bindings_file
        self.logger = logging.getLogger(__name__)
    
    def save_bindings(self, bindings: Dict[str, WindowBinding]) -> bool:
        """Сохранить привязки в файл"""
        try:
            self.logger.info(f"BindingStorage: [SAVE_START] Starting to save {len(bindings)} bindings to {self.bindings_file}")
            
            os.makedirs(os.path.dirname(self.bindings_file), exist_ok=True)
            
            bindings_to_save = [b.to_dict() for b in bindings.values()]
            
            for binding_data in bindings_to_save:
                display_name = binding_data.get('window_identifier', {}).get('title', 'unknown')
                self.logger.debug(f"BindingStorage: [SAVING_BINDING] ID: {binding_data['id']}, Name: '{display_name}'")

            with open(self.bindings_file, "w", encoding='utf-8') as f:
                json.dump(bindings_to_save, f, indent=4, ensure_ascii=False)
            
            self.logger.info(f"BindingStorage: [SAVE_SUCCESS] Successfully saved {len(bindings_to_save)} bindings to {self.bindings_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"BindingStorage: [SAVE_ERROR] Failed to save bindings to {self.bindings_file}: {e}")
            raise
    
    def load_bindings(self) -> Dict[str, WindowBinding]:
        """Загрузить привязки из файла"""
        bindings: Dict[str, WindowBinding] = {}
        
        if not os.path.exists(self.bindings_file):
            self.logger.info(f"BindingStorage: [LOAD_INFO] Bindings file {self.bindings_file} not found, starting with empty bindings")
            return bindings
        
        try:
            with open(self.bindings_file, "r", encoding='utf-8') as f:
                bindings_list = json.load(f)
                
            for binding_data in bindings_list:
                binding = WindowBinding.from_dict(binding_data)
                bindings[binding.id] = binding
            
            self.logger.info(f"BindingStorage: [LOAD_SUCCESS] Loaded {len(bindings)} bindings from {self.bindings_file}")
            
            # Логируем детали каждой загруженной привязки
            for binding_id, binding in bindings.items():
                self.logger.debug(f"BindingStorage: [LOADED_BINDING] ID: {binding_id}, Name: '{binding.get_display_name()}'")
            
        except (json.JSONDecodeError, FileNotFoundError, TypeError) as e:
            self.logger.warning(f"BindingStorage: [LOAD_ERROR] Failed to load bindings from {self.bindings_file}: {e}. Starting with empty bindings.")
            bindings = {}
        
        return bindings
    
    def add_binding(self, bindings: Dict[str, WindowBinding], binding: WindowBinding) -> str:
        """Добавить новую привязку"""
        binding.update_timestamp()
        bindings[binding.id] = binding
        self.logger.info(f"BindingStorage: [ADD_BINDING] Created new binding - ID: {binding.id}, Name: {binding.get_display_name()}")
        return binding.id
    
    def update_binding_position(self, bindings: Dict[str, WindowBinding], binding_id: str, pos_x: int, pos_y: int) -> bool:
        """Обновить позицию привязки"""
        if binding_id not in bindings:
            self.logger.error(f"BindingStorage: [UPDATE_ERROR] Binding {binding_id} not found for position update")
            return False
        
        binding = bindings[binding_id]
        old_pos_x = binding.pos_x
        old_pos_y = binding.pos_y
        
        binding.pos_x = pos_x
        binding.pos_y = pos_y
        binding.update_timestamp()
        
        self.logger.info(f"BindingStorage: [UPDATE_POSITION] Updated position for binding {binding_id} - Old: ({old_pos_x}, {old_pos_y}) -> New: ({pos_x}, {pos_y})")
        return True
    
    def remove_binding(self, bindings: Dict[str, WindowBinding], binding_id: str) -> bool:
        """Удалить привязку"""
        if binding_id not in bindings:
            self.logger.warning(f"BindingStorage: [REMOVE_ERROR] Binding {binding_id} not found for removal")
            return False
        
        binding = bindings.pop(binding_id)
        self.logger.info(f"BindingStorage: [REMOVE_BINDING] Removing binding - ID: {binding_id}, Name: '{binding.get_display_name()}'")
        self.logger.info(f"BindingStorage: [REMOVE_SUCCESS] Successfully removed binding {binding_id}")
        return True
    
    def update_binding(self, bindings: Dict[str, WindowBinding], binding_id: str, updated_binding: WindowBinding) -> bool:
        """Обновить данные привязки"""
        if binding_id not in bindings:
            self.logger.error(f"BindingStorage: [UPDATE_ERROR] Binding {binding_id} not found for update")
            return False
        
        updated_binding.update_timestamp()
        bindings[binding_id] = updated_binding
        
        self.logger.info(f"BindingStorage: [UPDATE_SUCCESS] Successfully updated binding {binding_id}")
        self.logger.debug(f"BindingStorage: [UPDATE_NEW] New data: {updated_binding.to_dict()}")
        return True