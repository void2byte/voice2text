# balance_widget.py

import logging
from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QPushButton, QHBoxLayout, 
    QFrame, QProgressBar, QToolTip
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QPalette, QColor, QPixmap, QPainter, QBrush

logger = logging.getLogger(__name__)

class BalanceWidget(QWidget):
    """Виджет для отображения баланса пользователя"""
    
    # Сигналы
    purchase_requested = Signal()  # Сигнал запроса покупки
    balance_updated = Signal(int)  # Сигнал обновления баланса
    low_balance_warning = Signal(int)  # Сигнал предупреждения о низком балансе
    
    def __init__(self, balance=0, low_threshold=10, critical_threshold=5, parent=None):
        super().__init__(parent)
        self.balance = balance
        self.low_threshold = low_threshold
        self.critical_threshold = critical_threshold
        self.last_balance = balance
        
        # Таймер для анимации
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self._update_animation)
        
        self.setup_ui()
        self.update_balance_display()
        
    def setup_ui(self):
        """Настройка интерфейса виджета"""
        self.setFixedSize(280, 120)
        self.setStyleSheet("""
            BalanceWidget {
                background-color: #f8f9fa;
                border: 2px solid #e9ecef;
                border-radius: 10px;
            }
        """)
        
        # Основной layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 10, 15, 10)
        main_layout.setSpacing(8)
        
        # Заголовок
        header_layout = QHBoxLayout()
        
        self.title_label = QLabel("💰 Баланс минут")
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet("color: #495057; margin-bottom: 5px;")
        header_layout.addWidget(self.title_label)
        
        # Кнопка обновления
        self.refresh_button = QPushButton("🔄")
        self.refresh_button.setFixedSize(25, 25)
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        self.refresh_button.clicked.connect(self.refresh_balance)
        self.refresh_button.setToolTip("Обновить баланс")
        header_layout.addWidget(self.refresh_button)
        
        main_layout.addLayout(header_layout)
        
        # Баланс
        balance_layout = QHBoxLayout()
        
        self.balance_label = QLabel(f"{self.balance}")
        balance_font = QFont()
        balance_font.setPointSize(18)
        balance_font.setBold(True)
        self.balance_label.setFont(balance_font)
        self.balance_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        balance_layout.addWidget(self.balance_label)
        
        self.minutes_label = QLabel("минут")
        minutes_font = QFont()
        minutes_font.setPointSize(10)
        self.minutes_label.setFont(minutes_font)
        self.minutes_label.setStyleSheet("color: #6c757d; margin-left: 5px;")
        balance_layout.addWidget(self.minutes_label)
        
        balance_layout.addStretch()
        main_layout.addLayout(balance_layout)
        
        # Индикатор состояния
        self.status_bar = QProgressBar()
        self.status_bar.setFixedHeight(6)
        self.status_bar.setTextVisible(False)
        self.status_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 3px;
                background-color: #e9ecef;
            }
            QProgressBar::chunk {
                border-radius: 3px;
            }
        """)
        main_layout.addWidget(self.status_bar)
        
        # Кнопка покупки
        self.buy_button = QPushButton("Купить минуты")
        self.buy_button.setFixedHeight(32)
        self.buy_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        self.buy_button.clicked.connect(self.on_buy_clicked)
        main_layout.addWidget(self.buy_button)
        
    def update_balance(self, new_balance: int):
        """Обновляет баланс с анимацией
        
        Args:
            new_balance: Новый баланс минут
        """
        if new_balance != self.balance:
            self.last_balance = self.balance
            self.balance = new_balance
            self.update_balance_display()
            self.balance_updated.emit(new_balance)
            
            # Проверяем пороги предупреждений
            self._check_balance_warnings()
    
    def update_balance_display(self):
        """Обновляет отображение баланса"""
        self.balance_label.setText(f"{self.balance}")
        
        # Определяем цвет и стиль в зависимости от баланса
        if self.balance <= self.critical_threshold:
            # Критически низкий баланс
            color = "#dc3545"  # Красный
            status_color = "#dc3545"
            self.status_bar.setValue(20)
            self.buy_button.setText("⚠️ Срочно купить!")
            self.buy_button.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #c82333;
                }
            """)
        elif self.balance <= self.low_threshold:
            # Низкий баланс
            color = "#fd7e14"  # Оранжевый
            status_color = "#fd7e14"
            self.status_bar.setValue(50)
            self.buy_button.setText("Пополнить баланс")
            self.buy_button.setStyleSheet("""
                QPushButton {
                    background-color: #fd7e14;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #e8690b;
                }
            """)
        else:
            # Нормальный баланс
            color = "#28a745"  # Зеленый
            status_color = "#28a745"
            progress = min(100, (self.balance / (self.low_threshold * 2)) * 100)
            self.status_bar.setValue(int(progress))
            self.buy_button.setText("Купить минуты")
            self.buy_button.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
            """)
        
        # Применяем цвет к балансу
        self.balance_label.setStyleSheet(f"color: {color};")
        
        # Обновляем стиль прогресс-бара
        self.status_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                border-radius: 3px;
                background-color: #e9ecef;
            }}
            QProgressBar::chunk {{
                border-radius: 3px;
                background-color: {status_color};
            }}
        """)
    
    def _check_balance_warnings(self):
        """Проверяет необходимость показа предупреждений"""
        if self.balance <= self.critical_threshold:
            self.low_balance_warning.emit(self.balance)
        elif self.balance <= self.low_threshold and self.last_balance > self.low_threshold:
            # Показываем предупреждение только при переходе через порог
            self.low_balance_warning.emit(self.balance)
    
    def on_buy_clicked(self):
        """Обработчик нажатия кнопки покупки"""
        try:
            self.purchase_requested.emit()
            logger.info("Purchase request emitted from balance widget")
        except Exception as e:
            logger.error(f"Error in buy button click handler: {e}")
    
    def refresh_balance(self):
        """Обновляет баланс (запрос к сервису)"""
        try:
            # Анимация кнопки обновления
            self.refresh_button.setText("⟳")
            QTimer.singleShot(500, lambda: self.refresh_button.setText("🔄"))
            
            # Эмитируем сигнал для обновления баланса
            self.balance_updated.emit(self.balance)
            logger.info("Balance refresh requested")
        except Exception as e:
            logger.error(f"Error refreshing balance: {e}")
    
    def set_thresholds(self, low_threshold: int, critical_threshold: int):
        """Устанавливает пороги предупреждений
        
        Args:
            low_threshold: Порог низкого баланса
            critical_threshold: Порог критически низкого баланса
        """
        self.low_threshold = low_threshold
        self.critical_threshold = critical_threshold
        self.update_balance_display()
    
    def get_balance_status(self) -> str:
        """Возвращает статус баланса
        
        Returns:
            str: 'critical', 'low', или 'normal'
        """
        if self.balance <= self.critical_threshold:
            return 'critical'
        elif self.balance <= self.low_threshold:
            return 'low'
        else:
            return 'normal'
    
    def _update_animation(self):
        """Обновляет анимацию (если необходимо)"""
        pass
    
    def show_tooltip(self, message: str):
        """Показывает всплывающую подсказку
        
        Args:
            message: Текст подсказки
        """
        QToolTip.showText(self.mapToGlobal(self.rect().center()), message)
    
    def closeEvent(self, event):
        """Обработчик закрытия виджета"""
        if self.animation_timer:
            self.animation_timer.stop()
        super().closeEvent(event)

if __name__ == '__main__':
    # Пример использования (для тестирования)
    from PySide6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    widget = BalanceWidget()
    widget.update_balance(120)
    widget.show()
    sys.exit(app.exec())