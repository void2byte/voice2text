# Window Binder Module

Модуль для создания и управления привязками окон в приложении распознавания речи.

## Описание

Window Binder позволяет создавать виджеты, привязанные к определенным окнам приложений. Эти виджеты могут использоваться для запуска распознавания речи в контексте конкретного приложения.

## Архитектура

Модуль состоит из следующих компонентов:

### Основные классы

- **BinderManager** - главный менеджер для координации работы с привязками
- **SettingsDialog** - диалог для создания новых привязок
- **BinderWidget** - виджет привязки, отображаемый поверх окна
- **PickerWidget** - виджет для выбора координат на экране

### Компоненты архитектуры

- **storage/BindingStorage** - управление сохранением и загрузкой привязок
- **managers/WidgetManager** - управление виджетами привязок
- **validators** - валидация данных привязок

- **config** - конфигурация модуля
- **utils** - утилиты для работы с окнами и файлами

## Использование

### Создание привязки

```python
from window_binder.binder_manager import BinderManager

# Создание менеджера
binder_manager = BinderManager(tray_app)

# Показ диалога настроек для создания новой привязки
binder_manager.show_settings()
```

### Управление привязками

```python
# Получение всех привязок
bindings = binder_manager.get_all_bindings()

# Удаление привязки
binder_manager.remove_binding(binding_id)

# Обновление привязки
binder_manager.update_binding(binding_id, app_name="New Name")

# Скрытие/показ всех виджетов
binder_manager.hide_all_binders()
binder_manager.show_all_binders()
```

### Конфигурация

```python
from window_binder.config import config

# Изменение настроек валидации
config.validation.validate_window_existence = False
config.validation.max_coordinate_value = 5000

# Изменение настроек UI
config.ui.show_success_messages = False

# Сохранение конфигурации
config.save_to_file("settings/window_binder_config.json")
```

## Структура файлов

```
window_binder/
├── __init__.py
├── README.md
├── config.py                 # Конфигурация модуля
├── validators.py             # Валидация данных

├── utils.py                  # Утилиты
├── binder_manager.py         # Главный менеджер
├── settings_dialog.py        # Диалог настроек
├── binder_widget.py          # Виджет привязки
├── picker_widget.py          # Виджет выбора координат
├── storage/
│   ├── __init__.py
│   └── binding_storage.py    # Управление хранением
├── managers/
│   ├── __init__.py
│   └── widget_manager.py     # Управление виджетами
└── tests/
    ├── __init__.py
    └── test_validators.py     # Тесты валидации
```

## Конфигурация

Модуль поддерживает гибкую конфигурацию через файл `settings/window_binder_config.json`:

### Секции конфигурации

- **widget** - настройки виджетов (размер, позиция, прозрачность)
- **validation** - настройки валидации данных
- **storage** - настройки хранения данных
- **ui** - настройки пользовательского интерфейса
- **logging** - настройки логирования
- **performance** - настройки производительности

## Валидация

Модуль включает комплексную систему валидации:

- Проверка названий приложений
- Валидация координат и позиций
- Проверка существования окон
- Валидация границ экрана
- Проверка корректности данных привязок

## Обработка ошибок

Централизованная система обработки ошибок:

- Обработка ошибок поиска окон
- Обработка файловых операций
- Обработка ошибок создания виджетов
- Обработка ошибок валидации
- Логирование и отображение ошибок пользователю

## Логирование

Модуль ведет подробное логирование всех операций:

- Создание и удаление привязок
- Операции с виджетами
- Валидация данных
- Ошибки и предупреждения
- Файловые операции

## Тестирование

Включены unit-тесты для основных компонентов:

```bash
# Запуск тестов валидации
python -m window_binder.tests.test_validators
```

## Расширение функциональности

### Добавление новых валидаторов

```python
from window_binder.validators import BindingValidator

class CustomValidator(BindingValidator):
    def validate_custom_field(self, value):
        # Ваша логика валидации
        return True, ""
```

### Добавление новых обработчиков ошибок

```python


class CustomErrorHandler(ErrorHandler):
    def handle_custom_error(self, error):
        # Ваша логика обработки ошибок
        pass
```

### Добавление новых утилит

```python
from window_binder.utils.window_identifier import window_identification_service

# Пример использования сервиса идентификации окон
windows = window_identification_service.get_all_windows_with_details()
# Ваша логика работы с окнами
```

## Зависимости

- PySide6 - для GUI компонентов
- pygetwindow - для работы с окнами
- pyautogui - для получения информации об экране

## Лицензия

Этот модуль является частью приложения распознавания речи.