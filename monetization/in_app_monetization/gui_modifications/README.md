# Модификации GUI Screph

Эта директория предназначена для хранения файлов или фрагментов кода, которые модифицируют графический интерфейс пользователя (GUI) приложения Screph для интеграции системы монетизации.

Примеры изменений:

*   Добавление виджетов для отображения баланса минут пользователя.
*   Интеграция кнопок или ссылок "Купить минуты".
*   Отображение уведомлений о низком балансе или невозможности выполнить действие из-за нехватки минут.
*   Модификация существующих окон или диалогов для отображения информации, связанной с монетизацией.

Конкретная структура и содержимое файлов будут зависеть от используемого UI-фреймворка (например, PyQt, Tkinter, веб-фреймворк) и архитектуры GUI основного приложения Screph.

## Структура модуля

*   `__init__.py`: Инициализационный файл, делающий директорию пакетом Python.
*   `balance_widget.py`: Содержит класс `BalanceWidget` (на основе PySide6 `QWidget`) для отображения текущего баланса минут пользователя. 
*   `monetization_dialogs.py`: Предоставляет диалоговые окна (на основе PySide6 `QDialog` и `QMessageBox`) для уведомления пользователя о низком балансе или отсутствии минут, а также предлагает варианты действий (например, покупка минут).
*   `gui_utils.py`: Включает вспомогательные функции, такие как `show_monetization_view` для отображения интерфейса покупки минут и `find_main_window` (плейсхолдер) для поиска главного окна приложения.

## Примеры интеграции

### 1. Отображение баланса в главном окне

```python
# В main_window.py или аналогичном файле
from monetization.in_app_monetization.gui_modifications.balance_widget import BalanceWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # ... другая инициализация ...
        self.balance_widget = BalanceWidget(self)
        # Добавление виджета в какой-либо layout или status bar
        # self.statusBar().addPermanentWidget(self.balance_widget)
        # ...

    def update_user_balance(self, minutes):
        self.balance_widget.update_balance(minutes)
```

### 2. Показ диалога при нехватке минут

```python
# В месте, где проверяется возможность выполнения платного действия
from monetization.in_app_monetization.gui_modifications.monetization_dialogs import show_no_minutes_dialog
from monetization.in_app_monetization.gui_modifications.gui_utils import show_monetization_view

def perform_paid_action():
    user_has_minutes = check_user_balance() # Ваша функция проверки баланса
    if not user_has_minutes:
        if show_no_minutes_dialog(): # Предложить купить
            show_monetization_view() # Открыть окно покупки
        return
    # ... выполнение платного действия ...
```

### 3. Уведомление о низком балансе

```python
# Может быть вызвано после каждого списания минут или при запуске приложения
from monetization.in_app_monetization.gui_modifications.monetization_dialogs import show_low_balance_dialog
from monetization.in_app_monetization.gui_modifications.gui_utils import show_monetization_view

def check_and_notify_low_balance():
    current_minutes = get_current_balance() # Ваша функция получения баланса
    threshold = 10 # Порог для уведомления
    if 0 < current_minutes <= threshold:
        if show_low_balance_dialog():
            show_monetization_view()
```