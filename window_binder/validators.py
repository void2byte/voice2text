"""Модуль для валидации данных привязок окон"""

import logging
import pygetwindow as gw
from typing import Tuple, Optional
from window_binder.models.binding_model import IdentificationMethod
from window_binder.config import config


class BindingValidator:
    """Класс для валидации данных привязок"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def validate_binding_data(self, identifier: 'WindowIdentifier', x: str, y: str, pos_x: str, pos_y: str) -> Tuple[bool, str, dict]:
        """Полная валидация данных привязки"""
        try:
            validated_data = {
                'identifier': identifier,
                'x': int(x),
                'y': int(y),
                'pos_x': int(pos_x),
                'pos_y': int(pos_y)
            }
            return True, "", validated_data
        except (ValueError, TypeError):
            return False, "Координаты и позиция должны быть числами", {}
