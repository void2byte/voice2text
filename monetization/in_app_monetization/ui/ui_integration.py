# ui_integration.py

import logging
from typing import Optional, Dict, Any
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import QObject, Signal, QTimer

# Импорт компонентов UI
try:
    from ..gui_modifications.balance_widget import BalanceWidget
    from ..gui_modifications.monetization_dialogs import (
        show_low_balance_dialog, 
        show_no_minutes_dialog,
        LowBalanceDialog,
        NoMinutesDialog
    )
    from ..gui_modifications.purchase_dialog import PurchaseDialog
    from ..gui_modifications.gui_utils import find_main_window, show_monetization_view
except ImportError as e:
    logging.error(f"Failed to import UI components: {e}")
    BalanceWidget = None
    show_low_balance_dialog = None
    show_no_minutes_dialog = None
    PurchaseDialog = None
    find_main_window = None
    show_monetization_view = None

logger = logging.getLogger(__name__)

class MonetizationUIManager(QObject):
    """Менеджер UI для системы монетизации"""
    
    balance_updated = Signal(int)  # Сигнал обновления баланса
    purchase_completed = Signal(str, int)  # Сигнал завершения покупки (package_id, minutes)
    low_balance_warning = Signal(int, int)  # Сигнал предупреждения о низком балансе
    no_minutes_warning = Signal()  # Сигнал об отсутствии минут
    
    def __init__(self, monetization_service=None):
        super().__init__()
        self.monetization_service = monetization_service
        self.balance_widget = None
        self.main_window = None
        self.current_balance = 0
        self.low_balance_threshold = 10
        self.warning_timer = QTimer()
        self.warning_timer.timeout.connect(self._check_balance_warnings)
        self.warning_timer.start(30000)  # Проверка каждые 30 секунд
        
    def set_monetization_service(self, service):
        """Устанавливает сервис монетизации"""
        self.monetization_service = service
        
    def initialize_ui(self):
        """Инициализирует UI компоненты"""
        try:
            self.main_window = find_main_window() if find_main_window else None
            if self.main_window and BalanceWidget:
                self.balance_widget = BalanceWidget(parent=self.main_window)
                self._setup_balance_widget()
            return True
        except Exception as e:
            logger.error(f"Failed to initialize UI: {e}")
            return False
            
    def _setup_balance_widget(self):
        """Настраивает виджет баланса"""
        if self.balance_widget:
            # Подключаем сигналы
            self.balance_widget.purchase_requested.connect(self.show_purchase_dialog)
            self.balance_updated.connect(self.balance_widget.update_balance)
            
    def show_balance_widget(self, balance: int, parent: Optional[QWidget] = None) -> Optional[BalanceWidget]:
        """Показывает виджет баланса
        
        Args:
            balance: Текущий баланс минут
            parent: Родительский виджет
            
        Returns:
            BalanceWidget или None если не удалось создать
        """
        try:
            if not BalanceWidget:
                logger.error("BalanceWidget not available")
                return None
                
            if not self.balance_widget:
                parent_widget = parent or self.main_window
                self.balance_widget = BalanceWidget(balance=balance, parent=parent_widget)
                self._setup_balance_widget()
            
            self.current_balance = balance
            self.balance_widget.update_balance(balance)
            self.balance_widget.show()
            
            return self.balance_widget
            
        except Exception as e:
            logger.error(f"Error showing balance widget: {e}")
            return None
    
    def show_low_balance_warning(self, balance: int, threshold: int = 10, parent: Optional[QWidget] = None) -> bool:
        """Показывает предупреждение о низком балансе
        
        Args:
            balance: Текущий баланс минут
            threshold: Порог для предупреждения
            parent: Родительское окно
            
        Returns:
            bool: True если пользователь хочет купить минуты
        """
        try:
            if not show_low_balance_dialog:
                logger.error("Low balance dialog not available")
                return False
                
            parent_window = parent or self.main_window
            
            result = show_low_balance_dialog(
                current_balance=balance,
                threshold=threshold,
                monetization_service=self.monetization_service,
                parent=parent_window
            )
            
            if result:
                self.low_balance_warning.emit(balance, threshold)
                
            return result
            
        except Exception as e:
            logger.error(f"Error showing low balance warning: {e}")
            return False
    
    def show_no_minutes_warning(self, parent: Optional[QWidget] = None) -> bool:
        """Показывает предупреждение об отсутствии минут
        
        Args:
            parent: Родительское окно
            
        Returns:
            bool: True если пользователь хочет купить минуты
        """
        try:
            if not show_no_minutes_dialog:
                logger.error("No minutes dialog not available")
                return False
                
            parent_window = parent or self.main_window
            
            result = show_no_minutes_dialog(
                monetization_service=self.monetization_service,
                parent=parent_window
            )
            
            if result:
                self.no_minutes_warning.emit()
                
            return result
            
        except Exception as e:
            logger.error(f"Error showing no minutes warning: {e}")
            return False
    
    def show_purchase_dialog(self, parent: Optional[QWidget] = None) -> bool:
        """Показывает диалог покупки минут
        
        Args:
            parent: Родительское окно
            
        Returns:
            bool: True если покупка была совершена
        """
        try:
            if not show_monetization_view:
                logger.error("Purchase dialog not available")
                return False
                
            parent_window = parent or self.main_window
            
            result = show_monetization_view(
                parent_window=parent_window,
                monetization_service=self.monetization_service
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error showing purchase dialog: {e}")
            return False
    
    def show_purchase_options(self, parent: Optional[QWidget] = None) -> Optional[PurchaseDialog]:
        """Показывает опции покупки
        
        Args:
            parent: Родительское окно
            
        Returns:
            PurchaseDialog или None
        """
        try:
            if not PurchaseDialog:
                logger.error("PurchaseDialog not available")
                return None
                
            parent_window = parent or self.main_window
            
            dialog = PurchaseDialog(
                monetization_service=self.monetization_service,
                parent=parent_window
            )
            
            # Подключаем сигналы
            dialog.purchase_completed.connect(
                lambda package_id, minutes: self.purchase_completed.emit(package_id, minutes)
            )
            
            dialog.show()
            return dialog
            
        except Exception as e:
            logger.error(f"Error showing purchase options: {e}")
            return None
    
    def handle_purchase_action(self, package_id: str, parent: Optional[QWidget] = None) -> bool:
        """Обрабатывает действие покупки
        
        Args:
            package_id: ID пакета для покупки
            parent: Родительское окно
            
        Returns:
            bool: True если покупка была успешной
        """
        try:
            if not self.monetization_service:
                logger.error("Monetization service not available")
                return False
                
            # Получаем информацию о пакете
            packages = self.monetization_service.get_available_packages()
            package = next((p for p in packages if p['id'] == package_id), None)
            
            if not package:
                logger.error(f"Package {package_id} not found")
                return False
                
            # Показываем диалог покупки для конкретного пакета
            dialog = self.show_purchase_options(parent)
            if dialog:
                # Выбираем нужный пакет в диалоге
                dialog.select_package(package_id)
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error handling purchase action: {e}")
            return False
    
    def update_balance_display(self, new_balance: int):
        """Обновляет отображение баланса
        
        Args:
            new_balance: Новый баланс минут
        """
        self.current_balance = new_balance
        self.balance_updated.emit(new_balance)
        
        if self.balance_widget:
            self.balance_widget.update_balance(new_balance)
    
    def _check_balance_warnings(self):
        """Проверяет необходимость показа предупреждений о балансе"""
        if not self.monetization_service:
            return
            
        try:
            current_balance = self.monetization_service.get_user_balance()
            
            if current_balance == 0:
                # Показываем предупреждение об отсутствии минут
                self.show_no_minutes_warning()
            elif current_balance <= self.low_balance_threshold:
                # Показываем предупреждение о низком балансе
                self.show_low_balance_warning(current_balance, self.low_balance_threshold)
                
        except Exception as e:
            logger.error(f"Error checking balance warnings: {e}")
    
    def set_low_balance_threshold(self, threshold: int):
        """Устанавливает порог для предупреждения о низком балансе
        
        Args:
            threshold: Новый порог в минутах
        """
        self.low_balance_threshold = threshold
    
    def cleanup(self):
        """Очищает ресурсы"""
        if self.warning_timer:
            self.warning_timer.stop()
        
        if self.balance_widget:
            self.balance_widget.close()
            self.balance_widget = None

# Глобальный экземпляр менеджера UI
_ui_manager = None

def get_ui_manager() -> MonetizationUIManager:
    """Получает глобальный экземпляр менеджера UI"""
    global _ui_manager
    if _ui_manager is None:
        _ui_manager = MonetizationUIManager()
    return _ui_manager

def initialize_monetization_ui(monetization_service=None) -> bool:
    """Инициализирует UI системы монетизации
    
    Args:
        monetization_service: Сервис монетизации
        
    Returns:
        bool: True если инициализация успешна
    """
    ui_manager = get_ui_manager()
    if monetization_service:
        ui_manager.set_monetization_service(monetization_service)
    return ui_manager.initialize_ui()

# Функции-обертки для обратной совместимости
def show_balance_widget(balance: int, parent: Optional[QWidget] = None) -> Optional[BalanceWidget]:
    """Показывает виджет баланса"""
    return get_ui_manager().show_balance_widget(balance, parent)

def show_low_balance_warning(balance: int, threshold: int = 10, parent: Optional[QWidget] = None) -> bool:
    """Показывает предупреждение о низком балансе"""
    return get_ui_manager().show_low_balance_warning(balance, threshold, parent)

def show_purchase_options(parent: Optional[QWidget] = None) -> Optional[PurchaseDialog]:
    """Показывает опции покупки"""
    return get_ui_manager().show_purchase_options(parent)

def handle_purchase_action(package_id: str, parent: Optional[QWidget] = None) -> bool:
    """Обрабатывает действие покупки"""
    return get_ui_manager().handle_purchase_action(package_id, parent)

# Глобальные переменные или классы для управления UI элементами, связанными с монетизацией.
# Это сильно зависит от используемого UI фреймворка (PyQt, Tkinter, Kivy, веб-интерфейс и т.д.)

# --- Заглушки UI функций --- #
# В реальном приложении здесь будут вызовы функций конкретного UI фреймворка

def display_user_balance(minutes: int, package_info: list = None):
    """
    Отображает текущий баланс минут пользователя в UI.
    :param minutes: Количество доступных минут.
    :param package_info: Дополнительная информация о пакетах (например, сроки действия).
    """
    # Пример: обновление текстового поля, метки и т.д.
    logger.info(f"UI: Displaying user balance: {minutes} minutes.")
    if package_info:
        logger.info(f"UI: Active package details: {package_info}")
    # print(f"[UI STUB] User Balance: {minutes} minutes")
    # if package_info:
    # print(f"[UI STUB] Active packages: {package_info}")
    pass

def show_low_balance_warning(threshold_minutes: int):
    """
    Показывает предупреждение пользователю, что его баланс скоро закончится.
    :param threshold_minutes: Порог, при котором показывается предупреждение.
    """
    logger.info(f"UI: Showing low balance warning. Threshold: {threshold_minutes} minutes.")
    # print(f"[UI STUB] WARNING: Your balance is below {threshold_minutes} minutes. Please top up soon!")
    pass

def show_no_balance_error_and_prompt_purchase():
    """
    Показывает сообщение об ошибке (нет минут) и предлагает пользователю приобрести пакет.
    """
    logger.info("UI: Showing no balance error. Prompting for purchase.")
    # print("[UI STUB] ERROR: You have run out of minutes. Please purchase a package to continue.")
    # print("[UI STUB] [Button: Purchase Minutes]")
    pass

def display_purchase_options(packages: list):
    """
    Отображает доступные для покупки пакеты минут.
    :param packages: Список пакетов (например, из бэкенда или конфигурации).
    """
    logger.info(f"UI: Displaying purchase options: {packages}")
    # print("[UI STUB] Available minute packages:")
    # for pkg in packages:
    # print(f"[UI STUB] - {pkg.get('name', 'Unnamed Package')}: {pkg.get('minutes', 0)} minutes for ${pkg.get('price', 0)}")
    # print("[UI STUB] [Button: Select Package]")
    pass

def show_purchase_confirmation(success: bool, message: str = ""):
    """
    Показывает результат попытки покупки.
    :param success: True, если покупка успешна, иначе False.
    :param message: Дополнительное сообщение (например, об ошибке).
    """
    if success:
        logger.info(f"UI: Purchase successful. {message}")
        # print(f"[UI STUB] SUCCESS: Purchase confirmed! {message}")
    else:
        logger.error(f"UI: Purchase failed. {message}")
        # print(f"[UI STUB] ERROR: Purchase failed. {message}")
    pass

def update_monetization_ui_elements(monetization_service_instance):
    """
    Обновляет все UI элементы, связанные с монетизацией, используя данные из MonetizationService.
    :param monetization_service_instance: Экземпляр MonetizationService.
    """
    if not monetization_service_instance:
        logger.error("MonetizationService instance not provided to update_monetization_ui_elements.")
        return

    current_balance = monetization_service_instance.get_current_balance()
    active_packages = monetization_service_instance.get_active_packages_info()
    display_user_balance(current_balance, active_packages)

    # Пример логики для предупреждений (пороги должны быть настраиваемыми)
    low_balance_threshold = 10 # Например, 10 минут
    if 0 < current_balance <= low_balance_threshold:
        show_low_balance_warning(low_balance_threshold)
    elif current_balance == 0:
        # Это может быть вызвано не здесь, а при попытке использовать фичу
        # show_no_balance_error_and_prompt_purchase()
        pass 

# --- Функции-обработчики для действий пользователя (заглушки) --- #

def handle_purchase_button_click():
    """
    Обработчик нажатия кнопки "Купить минуты".
    Должен инициировать процесс отображения пакетов и покупки.
    """
    logger.info("UI: 'Purchase Minutes' button clicked.")
    # 1. Получить доступные пакеты (возможно, через MonetizationService или напрямую ApiClient)
    #    api_client = MonetizationApiClient() # Нужен способ получить токен или использовать гостевой доступ для списка пакетов
    #    packages = api_client.get_available_packages() # Предполагаемый метод
    #    if packages and 'error' not in packages:
    #        display_purchase_options(packages.get('data', []))
    #    else:
    #        show_purchase_confirmation(False, "Could not load packages.")
    # Для заглушки:
    dummy_packages = [
        {'id': 1, 'name': 'Starter Pack', 'minutes': 60, 'price': 5.00},
        {'id': 2, 'name': 'Pro Pack', 'minutes': 300, 'price': 20.00},
    ]
    display_purchase_options(dummy_packages)
    pass

def handle_select_package_for_purchase(package_id):
    """
    Обработчик выбора конкретного пакета для покупки.
    :param package_id: ID выбранного пакета.
    """
    logger.info(f"UI: Package with ID {package_id} selected for purchase.")
    # Здесь должна быть логика перехода к платежному шлюзу
    # Например, вызов метода в MonetizationService, который инициирует платеж через ApiClient
    # monetization_service.initiate_purchase(package_id)
    # print(f"[UI STUB] Initiating purchase for package ID: {package_id}...")
    # print("[UI STUB] Redirecting to payment gateway...")
    # После ответа от платежной системы:
    # result_success = True # или False
    # result_message = "Payment processed successfully." # или сообщение об ошибке
    # show_purchase_confirmation(result_success, result_message)
    # if result_success:
    # monetization_service.refresh_balance()
    # update_monetization_ui_elements(monetization_service)
    pass

# Пример того, как это может быть инициализировано или использовано в приложении Screph
# if __name__ == '__main__':
# # Нужен экземпляр MonetizationService
# # user_token = get_current_user_token() # Функция для получения токена
# # if user_token:
# #     service = MonetizationService(user_token=user_token)
# #     update_monetization_ui_elements(service)
# #     handle_purchase_button_click() # Симулировать нажатие кнопки
# # else:
# #     print("[UI STUB] User not logged in. Monetization UI cannot be initialized.")
#
# # Просто для демонстрации вызовов заглушек:
#     print("--- UI Integration Stubs Demo ---")
#     display_user_balance(100, [{'name': 'Active Pack 1', 'expires': '2024-12-31'}])
#     show_low_balance_warning(10)
#     show_no_balance_error_and_prompt_purchase()
#     handle_purchase_button_click()
#     handle_select_package_for_purchase(1)
#     show_purchase_confirmation(True, "Test purchase successful.")
#     show_purchase_confirmation(False, "Test purchase failed: Insufficient funds.")