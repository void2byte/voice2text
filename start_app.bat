@echo off
chcp 65001 >nul
echo ========================================
echo       Voice2Text - Запуск приложения
echo ========================================
echo.

:: Проверка существования виртуального окружения
if not exist "venv\Scripts\activate.bat" (
    echo ❌ Виртуальное окружение не найдено!
    echo Убедитесь, что папка venv скопирована в проект.
    echo.
    pause
    exit /b 1
)

:: Активация виртуального окружения
echo 🔄 Активация виртуального окружения...
call venv\Scripts\activate.bat

if errorlevel 1 (
    echo ❌ Ошибка активации виртуального окружения!
    pause
    exit /b 1
)

echo ✅ Виртуальное окружение активировано
echo.

:: Проверка Python
echo 🔍 Проверка Python...
python --version
if errorlevel 1 (
    echo ❌ Python не найден!
    pause
    exit /b 1
)
echo.

:: Проверка основных зависимостей
echo 🔍 Проверка зависимостей...
python -c "import PySide6; print('✅ PySide6 найден')" 2>nul
if errorlevel 1 (
    echo ⚠️  PySide6 не найден, попытка установки...
    pip install PySide6
)

python -c "import requests; print('✅ requests найден')" 2>nul
if errorlevel 1 (
    echo ⚠️  requests не найден, попытка установки...
    pip install requests
)

:: Проверка Google Cloud Speech (опционально)
python -c "import google.cloud.speech; print('✅ Google Cloud Speech найден')" 2>nul
if errorlevel 1 (
    echo ⚠️  Google Cloud Speech не найден (опционально)
    echo    Для установки выполните: pip install google-cloud-speech
)

echo.
echo ========================================
echo Выберите приложение для запуска:
echo ========================================
echo 1. Основное GUI приложение (main.py)
echo 2. Распознавание речи (run_speech_recognition.py)
echo 3. Системный трей (run_tray_app.py)
echo 4. Установка зависимостей (install_dependencies.py)
echo 5. Выход
echo.
set /p choice=Введите номер (1-5): 

if "%choice%"=="1" (
    echo 🚀 Запуск основного приложения...
    python main.py
) else if "%choice%"=="2" (
    echo 🚀 Запуск распознавания речи...
    python run_speech_recognition.py
) else if "%choice%"=="3" (
    echo 🚀 Запуск системного трея...
    python run_tray_app.py
) else if "%choice%"=="4" (
    echo 🚀 Установка зависимостей...
    python install_dependencies.py
    pause
) else if "%choice%"=="5" (
    echo 👋 До свидания!
    exit /b 0
) else (
    echo ❌ Неверный выбор!
    pause
    goto :eof
)

if errorlevel 1 (
    echo.
    echo ❌ Ошибка запуска приложения!
    echo Проверьте логи выше для диагностики.
    pause
)

echo.
echo 📝 Приложение завершено.
pause