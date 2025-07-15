# Система переводов Qt в Screph

Этот документ описывает, как работает система интернационализации (i18n) в проекте Screph с использованием инструментов Qt, централизованного менеджера переводов и паттерна `retranslate_ui`.

## Структура файлов переводов

```
i18n/
├── en_US_auto.ts    # Исходный файл перевода английского языка (XML)
├── en_US_auto.qm    # Скомпилированный файл перевода английского языка (бинарный)
├── ru_RU_auto.ts    # Исходный файл перевода русского языка (XML)
├── ru_RU_auto.qm    # Скомпилированный файл перевода русского языка (бинарный)
└── README_TRANSLATION.md  # Эта документация
```

## Менеджер переводов

Проект использует централизованный `TranslationManager` (файл `translation_manager.py`) для управления переводами:

- Автоматическое определение доступных языков
- Динамическая смена языка интерфейса
- Регистрация виджетов для автоматического обновления переводов
- Приоритетная загрузка файлов с суффиксом `_auto`

## Как добавить новые строки для перевода

### 1. Использование `self.tr()` и `retranslate_ui`

В коде Python все строки, которые должны быть переведены, оборачиваются в вызов `self.tr()`. Однако, для динамического обновления интерфейса при смене языка, используется специальный метод `retranslate_ui`.

#### Паттерн `retranslate_ui`

В каждом виджете (классе, унаследованном от `QWidget`) создается метод `retranslate_ui`. В этот метод переносятся все присвоения текста виджетам (заголовки, метки, кнопки и т.д.).

```python
# a_widget.py

class MyWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui() # Инициализация UI

    def _init_ui(self):
        self.my_label = QLabel()
        self.my_button = QPushButton()
        
        # Первоначальная установка текста
        self.retranslate_ui()

    def retranslate_ui(self):
        self.my_label.setText(self.tr("My Label Text"))
        self.my_button.setText(self.tr("My Button Text"))
```

Метод `retranslate_ui` вызывается:
1. В конце метода инициализации UI (`__init__` или `_init_ui`) для установки текста при создании виджета.
2. Автоматически `TranslationManager` при смене языка для всех зарегистрированных виджетов.

### 2. Обновление файлов перевода

Поскольку `lupdate` не работает корректно(требует уточнения) в данной среде, файлы `*_auto.ts` нужно обновлять вручную:

```xml
<message>
    <location filename="../gui/main_window.py" line="59"/>
    <source>Screph - Screen Element Management</source>
    <translation>Screph - Screen Element Management</translation>
</message>
```

### 3. Компиляция переводов

После обновления файла `.ts` скомпилируйте его в `.qm` с помощью `lrelease.exe`:

```bash
# Для английского языка
c:\Users\abvgd\CursorProject\Screph_new_en\venv\Lib\site-packages\PySide6\lrelease.exe i18n/en_US_auto.ts -qm i18n/en_US_auto.qm

# Для русского языка
c:\Users\abvgd\CursorProject\Screph_new_en\venv\Lib\site-packages\PySide6\lrelease.exe i18n/ru_RU_auto.ts -qm i18n/ru_RU_auto.qm
```

**Примечание:** При компиляции могут появляться предупреждения о дублирующихся записях - это нормально и не влияет на работу переводов.

## Как добавить новый язык

### 1. Создать новый файл перевода

Скопируйте `en_US_auto.ts` и переименуйте его, например, в `de_DE_auto.ts` для немецкого языка.

### 2. Перевести строки

В новом файле замените содержимое тегов `<translation>` на переводы:

```xml
<message>
    <location filename="../gui/main_window.py" line="59"/>
    <source>Screph - Screen Element Management</source>
    <translation>Screph - Bildschirmelement-Verwaltung</translation>
</message>
```

### 3. Скомпилировать новый перевод

```bash
c:\Users\abvgd\CursorProject\Screph_new_en\venv\Lib\site-packages\PySide6\lrelease.exe i18n/de_DE_auto.ts -qm i18n/de_DE_auto.qm
```

### 4. Обновить TranslationManager (опционально)

В `translation_manager.py` в методе `get_available_languages()` добавьте название нового языка в словарь `language_names`:

```python
language_names = {
    'ru_RU': 'Русский (Россия)',
    'de_DE': 'Deutsch (Deutschland)',  # Добавить эту строку
    'fr_FR': 'Français (France)',
    # ... остальные языки
}
```

**Примечание:** TranslationManager автоматически обнаружит новый язык по наличию файла `.qm` в папке `i18n/`.

## Текущее состояние переводов

### Статистика файлов переводов:

- **en_US_auto.ts/qm**: 642 перевода (81,300 байт)
- **ru_RU_auto.ts/qm**: 630 переводов (83,560 байт)

### Переведенные компоненты:

1. **MainWindow** (`gui/main_window.py`):
   - Заголовок окна
   - Названия вкладок
   - Кнопки
   - Статусная строка

2. **SettingsTab** (`gui/settings_tab.py`):
   - Заголовки групп настроек
   - Настройки записи и распознавания
   - Настройки Yandex SpeechKit
   - Настройки Vosk

3. **VoiceRecognitionTab** (`gui/voice_recognition_tab.py`):
   - Интерфейс настроек распознавания голоса
   - Сообщения об ошибках
   - Статусные сообщения

### Файлы, требующие перевода:

- `gui/ide_interaction_tab.py`
- `gui/tray_app_tab.py`
- `gui/yolo_models_tab.py`
- Другие GUI компоненты

### Известные проблемы:

- Дублирующиеся записи в файлах переводов (не влияют на функциональность)
- Некоторые строки содержат нечитаемые символы в исходном тексте

## Использование TranslationManager

### Инициализация в приложении

```python
from translation_manager import TranslationManager

# В главном окне или приложении
self.translation_manager = TranslationManager()

# Регистрация виджета для автоматического обновления
self.translation_manager.register_widget(self)

# Смена языка
self.translation_manager.change_language("ru_RU")
```

### Получение доступных языков

```python
available_languages = self.translation_manager.get_available_languages()
# Возвращает: [('English (US)', 'en_US'), ('Русский (Россия)', 'ru_RU')]
```

## Рекомендации

1.  **Централизуйте установку текста** в методе `retranslate_ui` для каждого виджета.
2.  **Вызывайте `retranslate_ui()`** в конце инициализации UI для первоначальной настройки.
3.  **Всегда используйте `self.tr()`** для всех строк, отображаемых пользователю.
4.  **Регистрируйте виджеты** в `TranslationManager` для автоматического обновления при смене языка.
5.  **Группируйте переводы по контексту** (классам) для лучшей организации.
6.  **Используйте суффикс `_auto`** для файлов переводов, чтобы они автоматически подхватывались системой.
7.  **Регулярно тестируйте переводы**, переключая языки в приложении.

## Устранение неполадок

### Переводы не загружаются

1. Проверьте, что файл `*_auto.qm` существует в папке `i18n/`
2. Проверьте логи TranslationManager
3. Убедитесь, что TranslationManager инициализирован

### Строки не переводятся

1. Убедитесь, что строка обернута в `self.tr()`
2. Проверьте, что перевод добавлен в файл `*_auto.ts`
3. Перекомпилируйте файл `.qm` с помощью `lrelease.exe`
4. Проверьте, что виджет зарегистрирован в TranslationManager

### Смена языка не работает

1.  Убедитесь, что используется `TranslationManager.change_language()`.
2.  Проверьте, что виджет зарегистрирован в `TranslationManager`.
3.  Убедитесь, что в виджете реализован метод `retranslate_ui`, и он корректно обновляет все необходимые текстовые элементы.
4.  Проверьте логи на наличие ошибок загрузки переводов.

### lupdate не работает

В данной среде `lupdate` имеет проблемы с кодировкой. Используйте ручное редактирование файлов `*_auto.ts` или создайте скрипт для автоматизации этого процесса.