#!/bin/bash

# Установка кодировки UTF-8
export LANG=ru_RU.UTF-8
export LC_ALL=ru_RU.UTF-8

echo "========================================"
echo "       Voice2Text - Запуск приложения"
echo "========================================"
echo

# Проверка существования виртуального окружения
if [ ! -f "venv/bin/activate" ]; then
    echo "❌ Виртуальное окружение не найдено!"
    echo "Убедитесь, что папка venv скопирована в проект."
    echo
    read -p "Нажмите Enter для выхода..."
    exit 1
fi

# Активация виртуального окружения
echo "🔄 Активация виртуального окружения..."
source venv/bin/activate

if [ $? -ne 0 ]; then
    echo "❌ Ошибка активации виртуального окружения!"
    read -p "Нажмите Enter для выхода..."
    exit 1
fi

echo "✅ Виртуальное окружение активировано"
echo

# Проверка Python
echo "🔍 Проверка Python..."
python3 --version
if [ $? -ne 0 ]; then
    echo "❌ Python не найден!"
    read -p "Нажмите Enter для выхода..."
    exit 1
fi
echo

# Проверка основных зависимостей
echo "🔍 Проверка зависимостей..."
python3 -c "import PySide6; print('✅ PySide6 найден')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  PySide6 не найден, попытка установки..."
    pip install PySide6
fi

python3 -c "import requests; print('✅ requests найден')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  requests не найден, попытка установки..."
    pip install requests
fi

# Проверка Google Cloud Speech (опционально)
python3 -c "import google.cloud.speech; print('✅ Google Cloud Speech найден')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Google Cloud Speech не найден (опционально)"
    echo "    Для установки выполните: pip install google-cloud-speech"
fi

echo
echo "========================================"
echo "Выберите приложение для запуска:"
echo "========================================"
echo "1. Основное GUI приложение (main.py)"
echo "2. Распознавание речи (run_speech_recognition.py)"
echo "3. Системный трей (run_tray_app.py)"
echo "4. Установка зависимостей (install_dependencies.py)"
echo "5. Выход"
echo
read -p "Введите номер (1-5): " choice

case $choice in
    1)
        echo "🚀 Запуск основного приложения..."
        python3 main.py
        ;;
    2)
        echo "🚀 Запуск распознавания речи..."
        python3 run_speech_recognition.py
        ;;
    3)
        echo "🚀 Запуск системного трея..."
        python3 run_tray_app.py
        ;;
    4)
        echo "🚀 Установка зависимостей..."
        python3 install_dependencies.py
        read -p "Нажмите Enter для продолжения..."
        ;;
    5)
        echo "👋 До свидания!"
        exit 0
        ;;
    *)
        echo "❌ Неверный выбор!"
        read -p "Нажмите Enter для выхода..."
        exit 1
        ;;
esac

if [ $? -ne 0 ]; then
    echo
    echo "❌ Ошибка запуска приложения!"
    echo "Проверьте логи выше для диагностики."
    read -p "Нажмите Enter для выхода..."
fi

echo
echo "📝 Приложение завершено."
read -p "Нажмите Enter для выхода..."