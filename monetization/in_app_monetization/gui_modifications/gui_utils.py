# gui_utils.py

import logging
from typing import Optional
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import QObject

# Импорт диалога покупки
try:
    from .purchase_dialog import PurchaseDialog, show_purchase_dialog
except ImportError:
    PurchaseDialog = None
    show_purchase_dialog = None

logger = logging.getLogger(__name__)

def find_main_window():
    """Находит главное окно приложения.
    
    Ищет среди всех виджетов верхнего уровня окно с заголовком,
    содержащим 'Screph' или 'MainWindow'.
    """
    app = QApplication.instance()
    if not app:
        logger.warning("QApplication instance not found")
        return None
        
    # Ищем главное окно среди виджетов верхнего уровня
    for widget in app.topLevelWidgets():
        if widget.isWindow() and widget.isVisible():
            window_title = widget.windowTitle().lower()
            class_name = widget.__class__.__name__.lower()
            
            # Проверяем по заголовку окна или имени класса
            if ('Screph' in window_title or 
                'mainwindow' in class_name or 
                'main_window' in class_name):
                logger.info(f"Found main window: {widget.__class__.__name__}")
                return widget
                
    # Если не нашли специфичное окно, возвращаем первое видимое
    for widget in app.topLevelWidgets():
        if widget.isWindow() and widget.isVisible():
            logger.info(f"Using fallback main window: {widget.__class__.__name__}")
            return widget
            
    logger.warning("No suitable main window found")
    return None

def show_monetization_view(parent_window=None, monetization_service=None):
    """Открывает диалог покупки минут.

    Args:
        parent_window: Родительское окно для диалога
        monetization_service: Сервис монетизации для работы с API
        
    Returns:
        bool: True если покупка была совершена, False если отменена
    """
    if parent_window is None:
        parent_window = find_main_window()
    
    if not PurchaseDialog:
        logger.error("PurchaseDialog not available - import failed")
        return False
        
    try:
        # Создаем и показываем диалог покупки
        dialog = PurchaseDialog(monetization_service, parent_window)
        result = dialog.exec()
        
        # Возвращаем True если диалог был принят (покупка совершена)
        return result == PurchaseDialog.DialogCode.Accepted
        
    except Exception as e:
        logger.error(f"Error showing monetization dialog: {e}")
        return False

if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton
    import sys

    app = QApplication(sys.argv)

    # Создадим простое главное окно для теста
    class MockMainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Mock Main Window")
            button = QPushButton("Открыть окно покупки", self)
            button.clicked.connect(lambda: show_monetization_view(self))
            self.setCentralWidget(button)

    main_win = MockMainWindow()
    main_win.show()

    # Тест без явного родителя (будет использован placeholder find_main_window)
    # show_monetization_view()

    sys.exit(app.exec())