# Настройка проекта Voice2Text

## Быстрый старт после копирования venv

Если вы скопировали папку `venv` с зависимостями в проект, выполните следующие шаги:

### 1. Активация виртуального окружения

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/macOS:**
```bash
source venv/bin/activate
```

### 2. Проверка зависимостей

Проверьте, что все необходимые пакеты установлены:
```bash
python install_dependencies.py
```

Или вручную:
```bash
pip install -r requirements.txt
```

### 3. Установка недостающих зависимостей

Если Google Cloud Speech API недоступен:
```bash
pip install google-cloud-speech google-auth
```

Для локального распознавания Vosk:
```bash
pip install vosk
```

### 4. Запуск приложения

**Основное GUI приложение:**
```bash
python main.py
```

**Приложение распознавания речи:**
```bash
python run_speech_recognition.py
```

**Системный трей:**
```bash
python run_tray_app.py
```

## Структура проекта

```
voice2text/
├── venv/                          # Виртуальное окружение (скопированное)
├── voice_control/                 # Основной модуль
│   ├── speech_recognition/        # Модули распознавания речи
│   │   ├── google_recognizer.py   # Google Cloud Speech API
│   │   ├── yandex_recognizer.py   # Yandex SpeechKit
│   │   ├── vosk_recognizer.py     # Локальное распознавание
│   │   └── settings_tab.py        # GUI настроек
│   └── ...
├── requirements.txt               # Список зависимостей
├── setup.py                       # Установочный скрипт
├── install_dependencies.py        # Автоматическая установка
├── main.py                        # Основная точка входа
└── README_SETUP.md               # Этот файл
```

## Настройка API ключей

### Yandex SpeechKit
1. Получите API ключ в [Yandex Cloud Console](https://console.cloud.yandex.ru/)
2. Введите ключ в настройках приложения

### Google Cloud Speech
1. Создайте проект в [Google Cloud Console](https://console.cloud.google.com/)
2. Включите Speech-to-Text API
3. Создайте сервисный аккаунт и скачайте JSON файл с ключами
4. Укажите путь к файлу в настройках приложения

### Vosk (локальное распознавание)
1. Скачайте модель с [официального сайта](https://alphacephei.com/vosk/models)
2. Распакуйте в папку `models/`
3. Укажите путь к модели в настройках

## Устранение проблем

### ModuleNotFoundError: No module named 'google.cloud'

**Решение:**
```bash
pip install google-cloud-speech google-auth
```

### Ошибки с аудио устройствами

**Windows:**
```bash
pip install sounddevice soundfile
```

**Linux:**
```bash
sudo apt-get install portaudio19-dev python3-pyaudio
pip install sounddevice soundfile
```

### Проблемы с Qt/PySide6

```bash
pip install --upgrade PySide6
```

### Ошибки импорта модулей

Убедитесь, что вы находитесь в корневой директории проекта и виртуальное окружение активировано.

## Дополнительные возможности

### Установка всех опциональных зависимостей
```bash
pip install -e .[all]
```

### Установка только Google Cloud Speech
```bash
pip install -e .[google]
```

### Установка только Vosk
```bash
pip install -e .[vosk]
```

### Разработка
```bash
pip install -e .[dev]
```

## Проверка работоспособности

Запустите тест всех компонентов:
```bash
python -c "from voice_control.ui.settings_tab import *; print('✓ Все модули загружены успешно')"
```

## Поддержка

Если у вас возникли проблемы:
1. Проверьте, что виртуальное окружение активировано
2. Убедитесь, что все зависимости установлены
3. Проверьте логи приложения
4. Обратитесь к документации API провайдеров

---

**Примечание:** Этот проект поддерживает условные импорты, поэтому отсутствие некоторых библиотек (например, google-cloud-speech) не помешает запуску основного функционала.