import xml.etree.ElementTree as ET
import os

def extract_strings_for_translation(ts_file_path, output_file_path):
    """
    Извлекает непереведенные строки из .ts файла и сохраняет их в текстовый файл.

    Args:
        ts_file_path (str): Путь к входному .ts файлу.
        output_file_path (str): Путь к выходному файлу для перевода.
    """
    try:
        tree = ET.parse(ts_file_path)
        root = tree.getroot()
        
        strings_to_translate = []
        for message in root.findall('.//message'):
            source = message.find('source')
            translation = message.find('translation')
            
            if source is not None and source.text is not None:
                # Проверяем, нужно ли переводить строку
                if translation is None or translation.get('type') == 'unfinished' or not translation.text:
                    strings_to_translate.append(source.text.strip())

        with open(output_file_path, 'w', encoding='utf-8') as f:
            for i, text in enumerate(strings_to_translate):
                f.write(f"{i + 1}: {text.replace('\n', '\\n')}\n")
        
        print(f"Найдено и записано {len(strings_to_translate)} строк для перевода в {output_file_path}")

    except ET.ParseError as e:
        print(f"Ошибка парсинга XML: {e}")
    except FileNotFoundError:
        print(f"Файл не найден: {ts_file_path}")
    except Exception as e:
        print(f"Произошла ошибка: {e}")

if __name__ == "__main__":
    # Определение путей относительно расположения скрипта
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, '..', '..', '..'))
    
    # Путь к исходному .ts файлу
    input_ts_file = os.path.join(project_root, 'i18n', 'en_US_auto.ts')
    
    # Путь к выходному файлу
    output_txt_file = os.path.join(script_dir, 'for_translation.txt')
    
    extract_strings_for_translation(input_ts_file, output_txt_file)