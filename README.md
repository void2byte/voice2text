# Модуль управления голосом (Voice Control)

Универсальный модуль для работы с микрофоном, записи аудио и распознавания речи с поддержкой множественных провайдеров: Яндекс SpeechKit, Vosk (локальное распознавание) и Google Cloud(отключен) Speech-to-Text. Включает современный графический интерфейс с гибкими настройками и расширенными возможностями управления моделями.

## Структура модуля

```
voice_control/
├── __init__.py                      # Инициализация модуля
├── README.md                        # Документация модуля
├── run_speech_recognition.py        # Скрипт запуска графического интерфейса распознавания речи
├── recognition_worker.py            # Воркер для обработки распознавания речи в отдельном потоке
├── voice_annotation_widget.py       # Виджет голосовой аннотации (контроллер)
├── voice_annotation_view.py         # Представление голосовой аннотации
├── voice_annotation_model.py        # Модель данных голосовой аннотации
├── voice_annotation_runnable.py     # Реализация задачи голосовой аннотации через QRunnable
├── microphone/                      # Подмодуль для работы с микрофоном
│   ├── __init__.py                  # Инициализация подмодуля
│   ├── qt_audio_capture.py          # Класс для захвата аудио с микрофона
│   ├── qt_audio_runnable.py         # Реализация захвата аудио через QRunnable
│   ├── audio_buffer.py              # Кольцевой буфер для хранения аудиоданных
│   └── qt_mic_gui.py                # Графический интерфейс для управления микрофоном
├── speech_recognition/              # Подмодуль для распознавания речи
│   ├── __init__.py                  # Инициализация подмодуля
│   ├── README.md                    # Документация по модулю распознавания речи
│   ├── USER_GUIDE.md                # Руководство пользователя
│   ├── expansion_plan.md            # План расширения функциональности
│   ├── yandex_speechkit_guide.md    # Руководство по Яндекс SpeechKit
│   ├── base_recognizer.py           # Базовый абстрактный класс для распознавателей
│   ├── yandex_recognizer.py         # Реализация распознавателя Яндекс SpeechKit
│   ├── vosk_recognizer.py           # Реализация распознавателя Vosk (локальный)
│   ├── google_recognizer.py         # Реализация распознавателя Google Cloud Speech-to-Text
│   ├── speech_recognition_gui.py    # Главный графический интерфейс
│   ├── main_window.py               # Главное окно приложения
│   ├── gui_components.py            # Общие компоненты интерфейса
│   ├── settings_tab.py              # Основная вкладка настроек
│   ├── recognition_tab.py           # Вкладка распознавания
│   ├── info_tab.py                  # Информационная вкладка
│   └── settings_tabs/               # Специализированные вкладки настроек
│       ├── yandex_settings_tab.py   # Настройки Яндекс SpeechKit
│       ├── vosk_settings_tab.py     # Настройки Vosk
│       ├── google_settings_tab.py   # Настройки Google Cloud Speech-to-Text
│       ├── vosk_model_downloader.py # Загрузчик моделей Vosk
│       └── vosk_model_loader.py     # Загрузчик и валидатор моделей Vosk
└── voice_control/                   # Дополнительная папка (legacy)
    └── speech_recognition/          # Устаревшая структура
```

## Требования

### Базовые требования

- Python 3.7+
- PyQt6 >= 6.6.0
- PyQt6-Qt6 >= 6.6.0
- PyQt6-sip >= 13.10.0
- sounddevice >= 0.4.6
- scipy >= 1.12.0
- ffmpeg-python >= 0.2.0
- requests >= 2.25.0

### Для Яндекс SpeechKit

- yandex-speechkit >= 2.4.0

### Для Vosk (локальное распознавание)

- vosk >= 0.3.45
- vosk-model (модели загружаются автоматически)

### Для Google Cloud Speech-to-Text

- google-cloud-speech >= 2.0.0
- google-auth >= 2.0.0

### Дополнительные инструменты

- FFmpeg (для конвертации аудио)

## Установка

### Базовая установка

```bash
pip install PyQt6>=6.6.0 PyQt6-Qt6>=6.6.0 PyQt6-sip>=13.10.0 sounddevice>=0.4.6 scipy>=1.12.0 ffmpeg-python>=0.2.0 requests>=2.25.0
```

### Установка провайдеров (по выбору)

```bash
# Для Яндекс SpeechKit
pip install yandex-speechkit>=2.4.0

# Для Vosk
pip install vosk>=0.3.45

# Для Google Cloud Speech-to-Text
pip install google-cloud-speech>=2.0.0 google-auth>=2.0.0
```

### Установка FFmpeg

**Windows:**
1. Скачайте FFmpeg с официального сайта
2. Добавьте путь к FFmpeg в переменную PATH

**Linux:**
```bash
sudo apt-get install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

## Использование

### Запуск графического интерфейса распознавания речи

```bash
python voice_control/run_speech_recognition.py
```

### Запуск отдельного интерфейса микрофона (устарело)

```bash
python voice_control/microphone/qt_mic_gui.py
```

### Программное использование микрофона

```python
from voice_control.microphone.qt_audio_capture import QtAudioCapture

# Создаем объект для захвата аудио
audio_capture = QtAudioCapture()

# Получаем список доступных устройств
devices = audio_capture.get_available_devices()
for device in devices:
    print(f"Индекс: {device['index']}, Имя: {device['name']}")

# Выбираем первое устройство
if devices:
    audio_capture.set_device(devices[0]['index'])

# Начинаем запись
audio_capture.start_recording()

# Ждем 5 секунд
import time
time.sleep(5)

# Останавливаем запись
audio_capture.stop_recording()

# Сохраняем в WAV-файл
audio_capture.save_to_wav("test_recording.wav")
```

### Программное использование распознавания речи

#### Яндекс SpeechKit

```python
from voice_control.recognizers.yandex_recognizer import YandexSpeechRecognizer

# Создаем распознаватель Яндекс SpeechKit
recognizer = YandexSpeechRecognizer(
    api_key="ваш_api_ключ",
    language="ru",
    model="general",
    audio_format="lpcm",
    sample_rate=16000
)

# Распознаем речь из файла
result = recognizer.recognize_file("путь_к_аудиофайлу.wav")
print(f"Результат: {result}")
```

#### Vosk (локальное распознавание)

```python
from voice_control.recognizers.vosk_recognizer import VoskSpeechRecognizer

# Создаем локальный распознаватель Vosk
recognizer = VoskSpeechRecognizer(
    model_path="путь_к_модели_vosk",
    sample_rate=16000
)

# Распознаем речь из файла
result = recognizer.recognize_file("путь_к_аудиофайлу.wav")
print(f"Результат: {result}")
```

#### Google Cloud Speech-to-Text

```python
from voice_control.recognizers.google_recognizer import GoogleSpeechRecognizer

# Создаем распознаватель Google Cloud
recognizer = GoogleSpeechRecognizer(
    credentials_path="путь_к_credentials.json",
    language="ru-RU",
    model="latest_long",
    sample_rate=16000
)

# Распознаем речь из файла
result = recognizer.recognize_file("путь_к_аудиофайлу.wav")
print(f"Результат: {result}")
```

## Описание компонентов

### Модуль microphone

#### QtAudioCapture

Класс для захвата аудио с микрофона с использованием PyQt6.QtMultimedia.

##### Основные методы:

- `get_available_devices()` - Получить список доступных устройств ввода аудио
- `set_device(device_index)` - Установить устройство ввода по индексу
- `start_recording()` - Начать запись аудио
- `start_recording_with_callback(callback)` - Начать запись с функцией обратного вызова для обработки аудиоданных
- `stop_recording()` - Остановить запись аудио
- `get_recording_duration()` - Получить длительность текущей записи в секундах
- `get_recorded_data()` - Получить записанные аудиоданные с метаданными формата (raw_bytes, sample_rate, channels, sample_width)

##### Сигналы:

- `recording_started` - Сигнал о начале записи
- `recording_stopped` - Сигнал о завершении записи
- `volume_changed(float)` - Сигнал об изменении громкости (0.0 - 1.0)
- `audio_data_ready(bytearray)` - Сигнал о готовности нового блока аудиоданных

#### QtAudioRunnable

Реализация задачи захвата аудио в отдельном потоке. Основные возможности:

- Запись аудио в фиксированном формате (16 кГц, моно, 16 бит)
- Обработка записанных данных через callback-функции
- Расчет и отправка информации о громкости аудио

#### AudioBuffer

Кольцевой буфер для эффективного хранения и обработки аудиоданных:

- Хранение аудиоданных как целых блоков байтов вместо отдельных сэмплов
- Эффективное добавление и извлечение данных без копирования байтов
- Методы для получения всех данных или только последних нескольких секунд
- Поддержка четкого контроля длительности записи с учетом формата аудио

#### MicrophoneControlWidget

Виджет для управления микрофоном. Включает в себя:

- Выбор устройства записи из списка доступных микрофонов
- Кнопки управления записью (старт, стоп, сохранение в WAV)
- Индикатор громкости с динамическим обновлением
- Статус и таймер записи

##### Основные методы:

- `refresh_devices()` - Обновить список доступных устройств ввода
- `toggle_recording()` - Переключение состояния записи (начать/остановить)
- `save_recording()` - Сохранить запись в выбранный пользователем файл

##### Сигналы:

- `recording_started` - Сигнал о начале записи
- `recording_stopped(str)` - Сигнал о завершении записи (с путем к файлу)

### Модуль speech_recognition

#### BaseRecognizer

Базовый абстрактный класс для всех распознавателей речи. Определяет единый интерфейс для работы с различными провайдерами.

##### Основные методы

- `recognize_file(file_path)` - Распознать речь из аудиофайла
- `recognize_audio_data(audio_data)` - Распознать речь из аудиоданных в памяти
- `is_available()` - Проверить доступность распознавателя
- `get_supported_formats()` - Получить список поддерживаемых форматов

#### YandexSpeechRecognizer

Реализация распознавателя для Яндекс SpeechKit API.

##### Особенности

- Облачное распознавание с высокой точностью
- Поддержка множественных языков и моделей
- Настраиваемые параметры обработки
- Автоматическая конвертация аудио

##### Параметры

- `api_key` - API-ключ Яндекс SpeechKit
- `language` - Язык распознавания (ru, en, tr)
- `model` - Модель распознавания (general, maps, dates, names, numbers)
- `audio_format` - Формат аудио (lpcm, oggopus)
- `sample_rate` - Частота дискретизации (8000, 16000, 48000)

#### VoskSpeechRecognizer

Реализация локального распознавателя на основе Vosk.

##### Особенности

- Полностью локальное распознавание без интернета
- Поддержка множественных языковых моделей
- Автоматическая загрузка и управление моделями
- Высокая скорость обработки

##### Параметры

- `model_path` - Путь к модели Vosk
- `sample_rate` - Частота дискретизации (обычно 16000)

#### GoogleSpeechRecognizer

Реализация распознавателя для Google Cloud Speech-to-Text.

##### Особенности

- Высокая точность распознавания
- Поддержка множественных языков и диалектов
- Расширенные возможности настройки
- Интеграция с Google Cloud Platform

##### Параметры

- `credentials_path` - Путь к файлу учетных данных JSON
- `language` - Код языка (например, "ru-RU", "en-US")
- `model` - Модель распознавания (latest_long, latest_short)
- `sample_rate` - Частота дискретизации

#### RecognitionWorker

Воркер для обработки распознавания речи в отдельном потоке.

##### Основные возможности

- Асинхронное распознавание без блокировки UI
- Поддержка всех типов распознавателей
- Обработка ошибок и уведомления о статусе
- Эмиссия сигналов о завершении или ошибке

##### Сигналы

- `recognition_finished(str)` - Сигнал о завершении распознавания с результатом
- `recognition_error(str)` - Сигнал об ошибке распознавания

#### VoiceAnnotationWidget

Контроллер для голосовой аннотации, объединяющий модель и представление.

##### Архитектура MVC

- **Model** (`VoiceAnnotationModel`) - Управление данными и бизнес-логикой
- **View** (`VoiceAnnotationView`) - Пользовательский интерфейс
- **Controller** (`VoiceAnnotationWidget`) - Координация между моделью и представлением

##### Основные возможности

- Запись аудио с индикатором громкости
- Выбор провайдера распознавания
- Редактирование и сохранение результатов
- Загрузка аудиофайлов для распознавания

#### Графический интерфейс

##### SpeechRecognitionGUI

Главное окно приложения с вкладочным интерфейсом:

- **Вкладка "Настройки"** - Выбор и настройка провайдеров
- **Вкладка "Распознавание"** - Основной интерфейс для работы
- **Вкладка "Информация"** - Справочная информация

##### Специализированные настройки

- **YandexSettingsTab** - Настройки API-ключа, языка и модели
- **VoskSettingsTab** - Управление моделями, загрузка и валидация
- **GoogleSettingsTab** - Настройки учетных данных и параметров

#### Управление моделями Vosk

##### VoskModelDownloader

- Автоматическая загрузка моделей из репозитория
- Проверка целостности загруженных файлов
- Управление кэшем моделей

##### VoskModelLoader

- Валидация и загрузка моделей в память
- Проверка совместимости моделей
- Диалоги загрузки с индикатором прогресса

## Настройка провайдеров

### Яндекс SpeechKit

1. Получите API-ключ в Яндекс.Облаке
2. Откройте вкладку "Настройки" → "Яндекс SpeechKit"
3. Введите API-ключ и выберите параметры
4. Нажмите "Тест соединения" для проверки

### Vosk

1. Откройте вкладку "Настройки" → "Vosk"
2. Выберите модель из списка или загрузите новую
3. Дождитесь завершения загрузки и валидации
4. Модель готова к использованию

### Google Cloud Speech-to-Text

1. Создайте проект в Google Cloud Console
2. Включите Speech-to-Text API
3. Создайте сервисный аккаунт и скачайте JSON-ключ
4. Укажите путь к файлу ключа в настройках

## Дополнительные возможности

### Горячие клавиши

- `Ctrl+R` - Начать/остановить запись
- `Ctrl+S` - Сохранить результаты
- `Ctrl+O` - Открыть аудиофайл
- `Ctrl+Del` - Очистить результаты

### Поддерживаемые форматы

- **Входные**: WAV, MP3, FLAC, OGG, M4A
- **Выходные**: Текстовые файлы (TXT), JSON

### Системные требования

- **ОС**: Windows 10+, macOS 10.14+, Linux Ubuntu 18.04+
- **ОЗУ**: Минимум 4 ГБ (рекомендуется 8 ГБ для Vosk)
- **Место на диске**: 500 МБ + место для моделей Vosk (1-8 ГБ)
- **Интернет**: Требуется для Яндекс и Google (не требуется для Vosk)

## Лицензия

Этот проект распространяется под лицензией MIT. Подробности в файле LICENSE.