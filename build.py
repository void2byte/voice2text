import PyInstaller.__main__
import os
import shutil

# Очистка предыдущих сборок
print("Очистка предыдущих сборок...")
if os.path.exists('dist'):
    shutil.rmtree('dist')
if os.path.exists('build'):
    shutil.rmtree('build')
if os.path.exists('Voice2Text.spec'):
    os.remove('Voice2Text.spec')
print("Очистка завершена.")

# Путь к модели vosk
model_path = 'model'

# Проверяем, существует ли папка с моделью
if not os.path.isdir(model_path):
    print(f"Ошибка: Папка с моделью не найдена по пути '{model_path}'")
    print("Пожалуйста, убедитесь, что папка 'model' существует в корне проекта.")
    exit(1)

pyinstaller_args = [
    'main.py',
    '--name=Voice2Text',
    '--onedir',
    '--windowed',
    '--noconfirm',
    '--distpath=release',
    '--workpath=build',
    '--hidden-import=vosk',
    f'--add-data={model_path};model', # Синтаксис для PyInstaller: 'source;destination'
    '--add-data=venv\\Lib\\site-packages\\vosk;vosk'
]

print(f"Запуск PyInstaller с аргументами: {' '.join(pyinstaller_args)}")

try:
    PyInstaller.__main__.run(pyinstaller_args)
    print("\nСборка успешно завершена!")
except Exception as e:
    print(f"\nПроизошла ошибка во время сборки: {e}")