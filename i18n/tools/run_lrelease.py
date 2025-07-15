import subprocess
import os

project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
lrelease_path = os.path.join(project_dir, 'venv', 'Lib', 'site-packages', 'PySide6', 'lrelease.exe')

i18n_dir = os.path.join(project_dir, 'i18n')
ts_files = [
    os.path.join(i18n_dir, 'ru_RU_auto.ts'),
    os.path.join(i18n_dir, 'en_US_auto.ts')
]

if not os.path.exists(lrelease_path):
    print(f"Error: lrelease.exe not found at {lrelease_path}")
    exit(1)

lrelease_dir = os.path.dirname(lrelease_path)
env = os.environ.copy()
env['PATH'] = f"{lrelease_dir};{env['PATH']}"

for ts_file in ts_files:
    if not os.path.exists(ts_file):
        print(f"Warning: Skipping non-existent file {ts_file}")
        continue

    # Use relative paths for ts_file as cwd is set
    relative_ts_file = os.path.relpath(ts_file, project_dir)

    command = [
        'lrelease.exe',
        relative_ts_file,
        '-qm',
        relative_ts_file.replace('.ts', '.qm')
    ]

    print(f"Running command: {' '.join(command)}")

    try:
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace', check=True, cwd=project_dir, env=env)
        print(f"Successfully compiled {os.path.basename(ts_file)}")
        if result.stdout:
            print("stdout:")
            print(result.stdout)
        if result.stderr:
            print("stderr:")
            print(result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"lrelease failed for {os.path.basename(ts_file)} with exit code {e.returncode}")
        print("stdout:")
        print(e.stdout)
        print("stderr:")
        print(e.stderr)
    except Exception as e:
        print(f"An unexpected error occurred with {os.path.basename(ts_file)}: {e}")