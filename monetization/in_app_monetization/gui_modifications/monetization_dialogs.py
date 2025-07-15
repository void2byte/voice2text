# monetization_dialogs.py

import logging
from PySide6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QIcon

# Импорт функций для показа диалога покупки
try:
    from .gui_utils import show_monetization_view
except ImportError:
    show_monetization_view = None

logger = logging.getLogger(__name__)

class LowBalanceDialog(QDialog):
    """Диалог предупреждения о низком балансе"""
    
    purchase_requested = Signal()
    
    def __init__(self, current_balance=0, threshold=10, parent=None):
        super().__init__(parent)
        self.current_balance = current_balance
        self.threshold = threshold
        self.monetization_service = None
        self.setup_ui()
        
    def setup_ui(self):
        """Настройка интерфейса диалога"""
        self.setWindowTitle("Низкий баланс - Screph")
        self.setModal(True)
        self.resize(400, 200)
        
        layout = QVBoxLayout(self)
        
        # Иконка предупреждения и заголовок
        title_layout = QHBoxLayout()
        
        # Заголовок
        title_label = QLabel("⚠️ Низкий баланс минут")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #ff9800; margin: 10px;")
        title_layout.addWidget(title_label)
        layout.addLayout(title_layout)
        
        # Сообщение
        message_text = (
            f"У вас осталось {self.current_balance} минут.\n"
            f"Рекомендуем пополнить баланс для бесперебойной работы."
        )
        message_label = QLabel(message_text)
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setStyleSheet("color: #333; font-size: 12px; margin: 10px;")
        layout.addWidget(message_label)
        
        # Кнопки
        button_layout = QHBoxLayout()
        
        self.later_button = QPushButton("Напомнить позже")
        self.later_button.setStyleSheet("""
            QPushButton {
                background-color: #9e9e9e;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #757575;
            }
        """)
        self.later_button.clicked.connect(self.reject)
        
        self.buy_button = QPushButton("Купить минуты")
        self.buy_button.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.buy_button.clicked.connect(self.open_purchase_dialog)
        
        button_layout.addWidget(self.later_button)
        button_layout.addWidget(self.buy_button)
        layout.addLayout(button_layout)
        
    def set_monetization_service(self, service):
        """Устанавливает сервис монетизации"""
        self.monetization_service = service
        
    def open_purchase_dialog(self):
        """Открывает диалог покупки минут"""
        if show_monetization_view:
            try:
                # Скрываем текущий диалог
                self.hide()
                
                # Показываем диалог покупки
                purchase_made = show_monetization_view(
                    parent_window=self.parent(),
                    monetization_service=self.monetization_service
                )
                
                if purchase_made:
                    self.purchase_requested.emit()
                    self.accept()  # Закрываем диалог предупреждения
                else:
                    self.show()  # Показываем диалог предупреждения снова
                    
            except Exception as e:
                logger.error(f"Error opening purchase dialog: {e}")
                self.show()
        else:
            logger.error("Purchase dialog not available")
            self.accept()

class NoMinutesDialog(QDialog):
    """Диалог об отсутствии минут"""
    
    purchase_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.monetization_service = None
        self.setup_ui()
        
    def setup_ui(self):
        """Настройка интерфейса диалога"""
        self.setWindowTitle("Нет минут - Screph")
        self.setModal(True)
        self.resize(450, 250)
        
        layout = QVBoxLayout(self)
        
        # Иконка ошибки и заголовок
        title_layout = QHBoxLayout()
        
        # Заголовок
        title_label = QLabel("🚫 Минуты закончились")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #f44336; margin: 10px;")
        title_layout.addWidget(title_label)
        layout.addLayout(title_layout)
        
        # Сообщение
        message_text = (
            "У вас закончились минуты.\n"
            "Для продолжения работы с Screph необходимо пополнить баланс.\n\n"
            "Выберите подходящий пакет минут и продолжайте использовать все возможности приложения."
        )
        message_label = QLabel(message_text)
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setStyleSheet("color: #333; font-size: 12px; margin: 15px;")
        layout.addWidget(message_label)
        
        # Кнопки
        button_layout = QHBoxLayout()
        
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #9e9e9e;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #757575;
            }
        """)
        self.cancel_button.clicked.connect(self.reject)
        
        self.buy_button = QPushButton("Купить минуты")
        self.buy_button.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.buy_button.clicked.connect(self.open_purchase_dialog)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.buy_button)
        layout.addLayout(button_layout)
        
    def set_monetization_service(self, service):
        """Устанавливает сервис монетизации"""
        self.monetization_service = service
        
    def open_purchase_dialog(self):
        """Открывает диалог покупки минут"""
        if show_monetization_view:
            try:
                # Скрываем текущий диалог
                self.hide()
                
                # Показываем диалог покупки
                purchase_made = show_monetization_view(
                    parent_window=self.parent(),
                    monetization_service=self.monetization_service
                )
                
                if purchase_made:
                    self.purchase_requested.emit()
                    self.accept()  # Закрываем диалог
                else:
                    self.show()  # Показываем диалог снова
                    
            except Exception as e:
                logger.error(f"Error opening purchase dialog: {e}")
                self.show()
        else:
            logger.error("Purchase dialog not available")
            self.accept()

def show_low_balance_dialog(current_balance=0, threshold=10, monetization_service=None, parent=None):
    """Показывает диалог предупреждения о низком балансе
    
    Args:
        current_balance: Текущий баланс минут
        threshold: Порог для предупреждения
        monetization_service: Сервис монетизации
        parent: Родительское окно
        
    Returns:
        bool: True если пользователь хочет купить минуты
    """
    dialog = LowBalanceDialog(current_balance, threshold, parent)
    if monetization_service:
        dialog.set_monetization_service(monetization_service)
    return dialog.exec() == QDialog.DialogCode.Accepted

def show_no_minutes_dialog(monetization_service=None, parent=None):
    """Показывает диалог об отсутствии минут
    
    Args:
        monetization_service: Сервис монетизации
        parent: Родительское окно
        
    Returns:
        bool: True если пользователь хочет купить минуты
    """
    dialog = NoMinutesDialog(parent)
    if monetization_service:
        dialog.set_monetization_service(monetization_service)
    return dialog.exec() == QDialog.DialogCode.Accepted

if __name__ == '__main__':
    # Пример использования (для тестирования)
    from PySide6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    if show_low_balance_dialog():
        print("Пользователь хочет купить минуты (из LowBalanceDialog)")
    else:
        print("Пользователь решил пополнить позже (из LowBalanceDialog)")

    if show_no_minutes_dialog():
        print("Пользователь хочет купить минуты (из NoMinutesDialog)")
    else:
        print("Пользователь отменил покупку (из NoMinutesDialog)")

    sys.exit(app.exec())