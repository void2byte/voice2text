"""Диалог покупки минут для Screph"""

import logging
from typing import List, Dict, Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QListWidgetItem, QMessageBox, QProgressBar,
    QGroupBox, QGridLayout, QTextEdit, QFrame, QSpacerItem,
    QSizePolicy, QScrollArea, QWidget
)
from PySide6.QtCore import Qt, Signal, QThread, QTimer
from PySide6.QtGui import QFont, QPixmap, QIcon

# Импорты для интеграции с монетизацией
try:
    from monetization.in_app_monetization.backend_integration.api_client import MonetizationApiClient
    from monetization.in_app_monetization.core.monetization_service import MonetizationService
except ImportError:
    # Заглушки для случая, если модули недоступны
    MonetizationApiClient = None
    MonetizationService = None

logger = logging.getLogger(__name__)

class PackageWidget(QFrame):
    """Виджет для отображения одного пакета минут"""
    
    package_selected = Signal(dict)
    
    def __init__(self, package_data: Dict, parent=None):
        super().__init__(parent)
        self.package_data = package_data
        self.selected = False
        self.setup_ui()
        
    def setup_ui(self):
        """Настройка интерфейса виджета пакета"""
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet("""
            PackageWidget {
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: #f9f9f9;
                margin: 5px;
                padding: 10px;
            }
            PackageWidget:hover {
                border-color: #007acc;
                background-color: #f0f8ff;
            }
            PackageWidget[selected="true"] {
                border-color: #007acc;
                background-color: #e6f3ff;
                border-width: 3px;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # Название пакета
        name_label = QLabel(self.package_data.get('name', 'Пакет минут'))
        name_font = QFont()
        name_font.setBold(True)
        name_font.setPointSize(12)
        name_label.setFont(name_font)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_label)
        
        # Количество минут
        minutes_label = QLabel(f"{self.package_data.get('minutes', 0)} минут")
        minutes_font = QFont()
        minutes_font.setPointSize(14)
        minutes_font.setBold(True)
        minutes_label.setFont(minutes_font)
        minutes_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        minutes_label.setStyleSheet("color: #007acc;")
        layout.addWidget(minutes_label)
        
        # Цена
        price_label = QLabel(f"{self.package_data.get('price', 0)} ₽")
        price_font = QFont()
        price_font.setPointSize(16)
        price_font.setBold(True)
        price_label.setFont(price_font)
        price_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        price_label.setStyleSheet("color: #d32f2f;")
        layout.addWidget(price_label)
        
        # Описание (если есть)
        if 'description' in self.package_data:
            desc_label = QLabel(self.package_data['description'])
            desc_label.setWordWrap(True)
            desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            desc_label.setStyleSheet("color: #666; font-size: 10px;")
            layout.addWidget(desc_label)
        
        # Кнопка выбора
        self.select_button = QPushButton("Выбрать")
        self.select_button.setStyleSheet("""
            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:pressed {
                background-color: #004080;
            }
        """)
        self.select_button.clicked.connect(self.select_package)
        layout.addWidget(self.select_button)
        
        self.setFixedSize(200, 180)
        
    def select_package(self):
        """Обработчик выбора пакета"""
        self.set_selected(True)
        self.package_selected.emit(self.package_data)
        
    def set_selected(self, selected: bool):
        """Устанавливает состояние выбора пакета"""
        self.selected = selected
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)
        
        if selected:
            self.select_button.setText("Выбрано")
            self.select_button.setEnabled(False)
        else:
            self.select_button.setText("Выбрать")
            self.select_button.setEnabled(True)

class PurchaseWorker(QThread):
    """Рабочий поток для выполнения покупки"""
    
    purchase_completed = Signal(bool, str)  # success, message
    
    def __init__(self, package_data: Dict, monetization_service: Optional[object] = None):
        super().__init__()
        self.package_data = package_data
        self.monetization_service = monetization_service
        
    def run(self):
        """Выполнение покупки в отдельном потоке"""
        try:
            # Здесь должна быть реальная логика покупки
            # Пока что имитируем процесс покупки
            import time
            time.sleep(2)  # Имитация обработки платежа
            
            # В реальном приложении здесь будет:
            # 1. Обращение к платежной системе
            # 2. Подтверждение платежа
            # 3. Обновление баланса через API
            
            if self.monetization_service:
                # Обновляем баланс после покупки
                self.monetization_service.refresh_balance()
            
            success_message = f"Успешно приобретен пакет '{self.package_data.get('name')}' на {self.package_data.get('minutes')} минут"
            self.purchase_completed.emit(True, success_message)
            
        except Exception as e:
            logger.error(f"Ошибка при покупке: {e}")
            self.purchase_completed.emit(False, f"Ошибка при покупке: {str(e)}")

class PurchaseDialog(QDialog):
    """Диалог покупки минут"""
    
    purchase_completed = Signal(bool, str)  # success, message
    
    def __init__(self, monetization_service: Optional[object] = None, parent=None):
        super().__init__(parent)
        self.monetization_service = monetization_service
        self.selected_package = None
        self.package_widgets = []
        self.purchase_worker = None
        
        self.setWindowTitle("Покупка минут - Screph")
        self.setModal(True)
        self.resize(800, 600)
        
        self.setup_ui()
        self.load_packages()
        
    def setup_ui(self):
        """Настройка интерфейса диалога"""
        layout = QVBoxLayout(self)
        
        # Заголовок
        title_label = QLabel("Выберите пакет минут")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #333; margin: 10px;")
        layout.addWidget(title_label)
        
        # Информация о текущем балансе
        self.balance_label = QLabel("Текущий баланс: загрузка...")
        self.balance_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.balance_label.setStyleSheet("color: #666; font-size: 12px; margin-bottom: 20px;")
        layout.addWidget(self.balance_label)
        
        # Область прокрутки для пакетов
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        self.packages_layout = QHBoxLayout(scroll_widget)
        self.packages_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setMinimumHeight(200)
        layout.addWidget(scroll_area)
        
        # Информация о выбранном пакете
        self.selection_info = QLabel("Выберите пакет для покупки")
        self.selection_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.selection_info.setStyleSheet("color: #666; font-size: 14px; margin: 20px;")
        layout.addWidget(self.selection_info)
        
        # Прогресс-бар для покупки
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Кнопки
        button_layout = QHBoxLayout()
        
        self.buy_button = QPushButton("Купить")
        self.buy_button.setEnabled(False)
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
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.buy_button.clicked.connect(self.start_purchase)
        
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.buy_button)
        
        layout.addLayout(button_layout)
        
        # Обновляем баланс
        self.update_balance_display()
        
    def load_packages(self):
        """Загружает доступные пакеты минут"""
        # Пример пакетов (в реальном приложении загружается с сервера)
        packages = [
            {
                'id': 1,
                'name': 'Стартовый',
                'minutes': 100,
                'price': 299,
                'description': 'Идеально для начинающих'
            },
            {
                'id': 2,
                'name': 'Стандартный',
                'minutes': 300,
                'price': 699,
                'description': 'Популярный выбор'
            },
            {
                'id': 3,
                'name': 'Премиум',
                'minutes': 600,
                'price': 1199,
                'description': 'Максимальная выгода'
            },
            {
                'id': 4,
                'name': 'Профессиональный',
                'minutes': 1200,
                'price': 1999,
                'description': 'Для профессионалов'
            }
        ]
        
        for package in packages:
            package_widget = PackageWidget(package)
            package_widget.package_selected.connect(self.on_package_selected)
            self.package_widgets.append(package_widget)
            self.packages_layout.addWidget(package_widget)
            
    def on_package_selected(self, package_data: Dict):
        """Обработчик выбора пакета"""
        # Сбрасываем выбор у всех пакетов
        for widget in self.package_widgets:
            widget.set_selected(False)
            
        # Устанавливаем выбор для текущего пакета
        for widget in self.package_widgets:
            if widget.package_data['id'] == package_data['id']:
                widget.set_selected(True)
                break
                
        self.selected_package = package_data
        self.buy_button.setEnabled(True)
        
        # Обновляем информацию о выборе
        self.selection_info.setText(
            f"Выбран пакет '{package_data['name']}': {package_data['minutes']} минут за {package_data['price']} ₽"
        )
        
    def update_balance_display(self):
        """Обновляет отображение текущего баланса"""
        if self.monetization_service:
            try:
                balance = self.monetization_service.get_current_balance()
                self.balance_label.setText(f"Текущий баланс: {balance} минут")
            except Exception as e:
                logger.error(f"Ошибка при получении баланса: {e}")
                self.balance_label.setText("Текущий баланс: недоступен")
        else:
            self.balance_label.setText("Текущий баланс: недоступен")
            
    def start_purchase(self):
        """Начинает процесс покупки"""
        if not self.selected_package:
            QMessageBox.warning(self, "Ошибка", "Выберите пакет для покупки")
            return
            
        # Подтверждение покупки
        reply = QMessageBox.question(
            self, 
            "Подтверждение покупки",
            f"Вы действительно хотите купить пакет '{self.selected_package['name']}' "
            f"на {self.selected_package['minutes']} минут за {self.selected_package['price']} ₽?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.execute_purchase()
            
    def execute_purchase(self):
        """Выполняет покупку"""
        # Отключаем кнопки и показываем прогресс
        self.buy_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Неопределенный прогресс
        
        # Запускаем покупку в отдельном потоке
        self.purchase_worker = PurchaseWorker(self.selected_package, self.monetization_service)
        self.purchase_worker.purchase_completed.connect(self.on_purchase_completed)
        self.purchase_worker.start()
        
    def on_purchase_completed(self, success: bool, message: str):
        """Обработчик завершения покупки"""
        # Скрываем прогресс и включаем кнопки
        self.progress_bar.setVisible(False)
        self.buy_button.setEnabled(True)
        self.cancel_button.setEnabled(True)
        
        if success:
            QMessageBox.information(self, "Успех", message)
            self.update_balance_display()  # Обновляем баланс
            self.purchase_completed.emit(True, message)
            self.accept()  # Закрываем диалог
        else:
            QMessageBox.critical(self, "Ошибка", message)
            self.purchase_completed.emit(False, message)
            
        # Очищаем рабочий поток
        if self.purchase_worker:
            self.purchase_worker.deleteLater()
            self.purchase_worker = None

# Функция для удобного вызова диалога
def show_purchase_dialog(monetization_service=None, parent=None):
    """Показывает диалог покупки минут"""
    dialog = PurchaseDialog(monetization_service, parent)
    return dialog.exec()

if __name__ == '__main__':
    # Тестирование диалога
    from PySide6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # Создаем тестовый диалог
    dialog = PurchaseDialog()
    dialog.show()
    
    sys.exit(app.exec())