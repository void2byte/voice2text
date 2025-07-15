import subprocess
import os

project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
lupdate_path = os.path.join(project_dir, 'venv', 'Lib', 'site-packages', 'PySide6', 'lupdate.exe')
# Use relative paths since we are setting cwd
import pathspec

def get_gitignore_spec(path):
    patterns = []
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            patterns = f.read().splitlines()
    patterns.extend(['venv/', '.idea/', '.vscode/', '__pycache__/', 'i18n/tools/'])
    return pathspec.PathSpec.from_lines('gitwildmatch', patterns)

gitignore_path = os.path.join(project_dir, '.gitignore')
spec = get_gitignore_spec(gitignore_path)

sources = []
for root, dirs, files in os.walk(project_dir, topdown=True):
    excluded_dirs = []
    for d in dirs:
        full_path = os.path.join(root, d)
        relative_path = os.path.relpath(full_path, project_dir).replace('\\', '/')
        if spec.match_file(relative_path):
            excluded_dirs.append(d)
    for d in excluded_dirs:
        dirs.remove(d)

    for file in files:
        if file.endswith('.py'):
            full_path = os.path.join(root, file)
            relative_path = os.path.relpath(full_path, project_dir).replace('\\', '/')
            if not spec.match_file(relative_path):
                sources.append(relative_path)
ts_files = [
    os.path.relpath(os.path.join(project_dir, 'i18n', 'ru_RU_auto.ts'), project_dir),
    os.path.relpath(os.path.join(project_dir, 'i18n', 'en_US_auto.ts'), project_dir)
]

lupdate_dir = os.path.dirname(lupdate_path)
env = os.environ.copy()
env['PATH'] = f"{lupdate_dir};{env['PATH']}"

for ts_file in ts_files:
    command = [
        'lupdate.exe',
        *sources,
        '-ts',
        ts_file,
        '-no-obsolete'
    ]

    print(f"Running command: {' '.join(command)}")

    try:
        # Using encoding that can handle Russian characters from shell
        result = subprocess.run(command, capture_output=True, text=True, encoding='cp866', errors='replace', check=True, cwd=project_dir, env=env)
        print(f"lupdate ran successfully for {os.path.basename(ts_file)}.")
        print("stdout:")
        print(result.stdout)
        print("stderr:")
        print(result.stderr)
    except FileNotFoundError:
        print(f"Error: lupdate.exe not found at {lupdate_path}")
    except subprocess.CalledProcessError as e:
        print(f"lupdate failed for {os.path.basename(ts_file)} with exit code {e.returncode}")
        print("stdout:")
        print(e.stdout)
        print("stderr:")
        print(e.stderr)
    except Exception as e:
        print(f"An unexpected error occurred with {os.path.basename(ts_file)}: {e}")