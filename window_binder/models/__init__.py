"""Модели данных для модуля привязок окон"""

from window_binder.models.binding_model import WindowBinding, WindowIdentifier

from .binding_model import IdentificationMethod

__all__ = ['WindowBinding', 'WindowIdentifier', 'IdentificationMethod']