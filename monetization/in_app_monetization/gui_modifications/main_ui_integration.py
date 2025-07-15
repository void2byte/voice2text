# main_ui_integration.py
"""
Интеграция UI монетизации с главным окном Screph
"""

import logging
from typing import Optional
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFrame
from PySide6.QtCore import QObject, Signal, QTimer

# Импорт компонентов монетизации
try:
    from .balance_widget import BalanceWidget
    from .monetization_dialogs import show_low_balance_dialog, show_no_minutes_dialog
    from .purchase_dialog import PurchaseDialog
    from .gui_utils import find_main_window, show_monetization_view
    from ..core.monetization_service import MonetizationService
    from ..ui.ui_integration import MonetizationUIManager, get_ui_manager
except ImportError as e:
    logging.error(f"Failed to import monetization components: {e}")
    BalanceWidget = None
    MonetizationService = None
    MonetizationUIManager = None
    get_ui_manager = None

logger = logging.getLogger(__name__)

class ScrephMonetizationIntegration(QObject):
    """Класс для интеграции монетизации с главным окном Screph"""
    
    # Сигналы
    balance_changed = Signal(int)
    purchase_completed = Signal(str, int)
    minutes_consumed = Signal(int)
    
    def __init__(self, main_window: Optional[QMainWindow] = None):
        super().__init__()
        self.main_window = main_window or find_main_window()
        self.monetization_service = None
        self.ui_manager = None
        self.balance_widget = None
        self.is_integrated = False
        
        # Таймер для периодической проверки баланса
        self.balance_check_timer = QTimer()
        self.balance_check_timer.timeout.connect(self._periodic_balance_check)
        
    def initialize(self, monetization_service: Optional[MonetizationService] = None) -> bool:
        """Инициализирует интеграцию монетизации
        
        Args:
            monetization_service: Сервис монетизации
            
        Returns:
            bool: True если инициализация успешна
        """
        try:
            # Инициализируем сервис монетизации
            if monetization_service:
                self.monetization_service = monetization_service
            elif MonetizationService:
                self.monetization_service = MonetizationService()
            else:
                logger.error("MonetizationService not available")
                return False
            
            # Инициализируем UI менеджер
            if get_ui_manager:
                self.ui_manager = get_ui_manager()
                self.ui_manager.set_monetization_service(self.monetization_service)
                self.ui_manager.initialize_ui()
                
                # Подключаем сигналы
                self._connect_signals()
            
            # Интегрируем с главным окном
            if self.main_window:
                self._integrate_with_main_window()
            
            # Запускаем периодическую проверку баланса
            self.balance_check_timer.start(60000)  # Каждую минуту
            
            self.is_integrated = True
            logger.info("Monetization integration initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize monetization integration: {e}")
            return False
    
    def _connect_signals(self):
        """Подключает сигналы UI менеджера"""
        if self.ui_manager:
            self.ui_manager.balance_updated.connect(self.balance_changed.emit)
            self.ui_manager.purchase_completed.connect(self.purchase_completed.emit)
    
    def _integrate_with_main_window(self):
        """Интегрирует виджеты монетизации с главным окном"""
        try:
            if not self.main_window or not BalanceWidget:
                return
            
            # Создаем виджет баланса
            current_balance = self.monetization_service.get_user_balance() if self.monetization_service else 0
            self.balance_widget = BalanceWidget(balance=current_balance, parent=self.main_window)
            
            # Подключаем сигналы виджета баланса
            self.balance_widget.purchase_requested.connect(self._handle_purchase_request)
            self.balance_widget.low_balance_warning.connect(self._handle_low_balance_warning)
            
            # Ищем подходящее место для размещения виджета баланса
            self._add_balance_widget_to_main_window()
            
            logger.info("Balance widget integrated with main window")
            
        except Exception as e:
            logger.error(f"Failed to integrate with main window: {e}")
    
    def _add_balance_widget_to_main_window(self):
        """Добавляет виджет баланса в главное окно"""
        try:
            # Попытка найти статус-бар или создать область для виджета баланса
            status_bar = getattr(self.main_window, 'statusBar', None)
            if status_bar and callable(status_bar):
                # Добавляем в статус-бар
                status_bar().addPermanentWidget(self.balance_widget)
            else:
                # Ищем центральный виджет и добавляем в него
                central_widget = self.main_window.centralWidget()
                if central_widget:
                    layout = central_widget.layout()
                    if layout:
                        # Создаем контейнер для виджета баланса
                        balance_frame = QFrame()
                        balance_frame.setFrameStyle(QFrame.Shape.StyledPanel)
                        balance_layout = QHBoxLayout(balance_frame)
                        balance_layout.addStretch()
                        balance_layout.addWidget(self.balance_widget)
                        
                        # Добавляем в начало layout'а
                        if hasattr(layout, 'insertWidget'):
                            layout.insertWidget(0, balance_frame)
                        elif hasattr(layout, 'addWidget'):
                            layout.addWidget(balance_frame)
            
        except Exception as e:
            logger.error(f"Failed to add balance widget to main window: {e}")
    
    def _handle_purchase_request(self):
        """Обрабатывает запрос на покупку минут"""
        try:
            if self.ui_manager:
                success = self.ui_manager.show_purchase_dialog(parent=self.main_window)
                if success:
                    # Обновляем баланс после покупки
                    self._update_balance_display()
        except Exception as e:
            logger.error(f"Error handling purchase request: {e}")
    
    def _handle_low_balance_warning(self, balance: int):
        """Обрабатывает предупреждение о низком балансе"""
        try:
            if self.ui_manager:
                self.ui_manager.show_low_balance_warning(
                    balance=balance,
                    parent=self.main_window
                )
        except Exception as e:
            logger.error(f"Error handling low balance warning: {e}")
    
    def _periodic_balance_check(self):
        """Периодическая проверка баланса"""
        try:
            if self.monetization_service:
                current_balance = self.monetization_service.get_user_balance()
                if self.balance_widget:
                    self.balance_widget.update_balance(current_balance)
                
                # Проверяем критические пороги
                if current_balance == 0:
                    self._show_no_minutes_dialog()
                elif current_balance <= 5:  # Критический порог
                    self._handle_low_balance_warning(current_balance)
                    
        except Exception as e:
            logger.error(f"Error in periodic balance check: {e}")
    
    def _show_no_minutes_dialog(self):
        """Показывает диалог об отсутствии минут"""
        try:
            if self.ui_manager:
                self.ui_manager.show_no_minutes_warning(parent=self.main_window)
        except Exception as e:
            logger.error(f"Error showing no minutes dialog: {e}")
    
    def _update_balance_display(self):
        """Обновляет отображение баланса"""
        try:
            if self.monetization_service and self.balance_widget:
                current_balance = self.monetization_service.get_user_balance()
                self.balance_widget.update_balance(current_balance)
                self.balance_changed.emit(current_balance)
        except Exception as e:
            logger.error(f"Error updating balance display: {e}")
    
    def consume_minutes(self, minutes: int) -> bool:
        """Потребляет минуты и обновляет UI
        
        Args:
            minutes: Количество минут для потребления
            
        Returns:
            bool: True если минуты успешно потреблены
        """
        try:
            if not self.monetization_service:
                return False
            
            # Проверяем достаточность минут
            if not self.monetization_service.check_minutes_available(minutes):
                self._show_no_minutes_dialog()
                return False
            
            # Потребляем минуты
            success = self.monetization_service.consume_minutes(minutes)
            if success:
                self.minutes_consumed.emit(minutes)
                self._update_balance_display()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error consuming minutes: {e}")
            return False
    
    def get_current_balance(self) -> int:
        """Возвращает текущий баланс
        
        Returns:
            int: Текущий баланс минут
        """
        try:
            if self.monetization_service:
                return self.monetization_service.get_user_balance()
            return 0
        except Exception as e:
            logger.error(f"Error getting current balance: {e}")
            return 0
    
    def show_purchase_dialog(self) -> bool:
        """Показывает диалог покупки минут
        
        Returns:
            bool: True если покупка была совершена
        """
        try:
            if self.ui_manager:
                return self.ui_manager.show_purchase_dialog(parent=self.main_window)
            return False
        except Exception as e:
            logger.error(f"Error showing purchase dialog: {e}")
            return False
    
    def cleanup(self):
        """Очищает ресурсы интеграции"""
        try:
            if self.balance_check_timer:
                self.balance_check_timer.stop()
            
            if self.balance_widget:
                self.balance_widget.close()
                self.balance_widget = None
            
            if self.ui_manager:
                self.ui_manager.cleanup()
            
            self.is_integrated = False
            logger.info("Monetization integration cleaned up")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

# Глобальный экземпляр интеграции
_integration_instance = None

def get_monetization_integration() -> Optional[ScrephMonetizationIntegration]:
    """Получает глобальный экземпляр интеграции монетизации
    
    Returns:
        ScrephMonetizationIntegration или None
    """
    global _integration_instance
    return _integration_instance

def initialize_monetization_integration(
    main_window: Optional[QMainWindow] = None,
    monetization_service: Optional[MonetizationService] = None
) -> bool:
    """Инициализирует глобальную интеграцию монетизации
    
    Args:
        main_window: Главное окно приложения
        monetization_service: Сервис монетизации
        
    Returns:
        bool: True если инициализация успешна
    """
    global _integration_instance
    
    try:
        if _integration_instance is None:
            _integration_instance = ScrephMonetizationIntegration(main_window)
        
        return _integration_instance.initialize(monetization_service)
        
    except Exception as e:
        logger.error(f"Failed to initialize global monetization integration: {e}")
        return False

def cleanup_monetization_integration():
    """Очищает глобальную интеграцию монетизации"""
    global _integration_instance
    
    if _integration_instance:
        _integration_instance.cleanup()
        _integration_instance = None

# Функции-обертки для удобства использования
def consume_minutes_from_integration(minutes: int) -> bool:
    """Потребляет минуты через интеграцию
    
    Args:
        minutes: Количество минут
        
    Returns:
        bool: True если успешно
    """
    integration = get_monetization_integration()
    if integration:
        return integration.consume_minutes(minutes)
    return False

def get_balance_from_integration() -> int:
    """Получает баланс через интеграцию
    
    Returns:
        int: Текущий баланс
    """
    integration = get_monetization_integration()
    if integration:
        return integration.get_current_balance()
    return 0

def show_purchase_dialog_from_integration() -> bool:
    """Показывает диалог покупки через интеграцию
    
    Returns:
        bool: True если покупка совершена
    """
    integration = get_monetization_integration()
    if integration:
        return integration.show_purchase_dialog()
    return False