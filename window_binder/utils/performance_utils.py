"""Утилиты для оптимизации производительности"""

import logging
from typing import List, Callable
from window_binder.config import config


class PerformanceUtils:
    """Утилиты для оптимизации производительности"""
    
    @staticmethod
    def batch_window_operations(operations: List[Callable]) -> List[any]:
        """Выполнить операции с окнами в пакетном режиме"""
        if not config.performance.batch_operations:
            return [op() for op in operations]
        
        results = []
        try:
            # Здесь можно добавить оптимизации для пакетных операций
            for operation in operations:
                results.append(operation())
        except Exception as e:
            logging.error(f"Error in batch operations: {e}")
        
        return results
    
    @staticmethod
    def debounce_function(func: Callable, delay: float = 0.1):
        """Создать debounced версию функции"""
        import threading
        import time
        
        last_called = [0]
        timer = [None]
        
        def debounced(*args, **kwargs):
            now = time.time()
            if now - last_called[0] > delay:
                if timer[0] is not None:
                    timer[0].cancel()
                last_called[0] = now
                func(*args, **kwargs)
            else:
                if timer[0] is not None:
                    timer[0].cancel()
                timer[0] = threading.Timer(delay, func, args=args, kwargs=kwargs)
                timer[0].start()
        
        return debounced