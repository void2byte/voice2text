import xml.etree.ElementTree as ET
import os
import re

def insert_translations_from_file(ts_file_path, translated_file_path):
    """
    Вставляет переведенные строки из текстового файла в .ts файл, перезаписывая его.

    Args:
        ts_file_path (str): Путь к .ts файлу для обновления.
        translated_file_path (str): Путь к файлу с переводами.
    """
    try:
        # Загрузка переводов из файла
        with open(translated_file_path, 'r', encoding='utf-8') as f:
            translations = f.readlines()
        
        # Парсинг переводов
        parsed_translations = {}
        for line in translations:
            match = re.match(r"(\d+):\s*(.*)", line)
            if match:
                index = int(match.group(1))
                text = match.group(2).strip().replace('\\n', '\n')
                parsed_translations[index] = text

        # Обновление .ts файла
        tree = ET.parse(ts_file_path)
        root = tree.getroot()
        
        untranslated_messages = []
        for message in root.findall('.//message'):
            translation = message.find('translation')
            if translation is None or translation.get('type') == 'unfinished' or not translation.text:
                untranslated_messages.append(message)

        if not parsed_translations:
            print("Файл с переводами пуст или имеет неверный формат.")
            return

        for i, message in enumerate(untranslated_messages):
            line_number = i + 1
            if line_number in parsed_translations:
                translation_text = parsed_translations[line_number]
                translation_element = message.find('translation')
                if translation_element is not None:
                    translation_element.text = translation_text
                    if 'type' in translation_element.attrib:
                        del translation_element.attrib['type'] # Удаляем атрибут 'type', так как перевод готов
                else:
                    # Если тега translation нет, создаем его
                    translation_element = ET.SubElement(message, 'translation')
                    translation_element.text = translation_text

        # Сохранение изменений
        tree.write(ts_file_path, encoding='utf-8', xml_declaration=True)
        print(f"Переводы успешно вставлены. Файл {ts_file_path} обновлен.")

    except FileNotFoundError as e:
        print(f"Файл не найден: {e.filename}")
    except ET.ParseError as e:
        print(f"Ошибка парсинга XML: {e}")
    except Exception as e:
        print(f"Произошла ошибка: {e}")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, '..', '..', '..'))

    # Пути к файлам
    ts_file_to_update = os.path.join(project_root, 'i18n', 'en_US_auto.ts')
    translated_txt_file = os.path.join(script_dir, 'translated.txt')

    # Перед запуском этого скрипта, убедитесь, что файл 'translated.txt' создан
    # и содержит переводы в формате 'номер: текст'.
    if not os.path.exists(translated_txt_file):
        print(f"Файл с переводами не найден: {translated_txt_file}")
        print("Пожалуйста, создайте его и добавьте переводы.")
    else:
        insert_translations_from_file(ts_file_to_update, translated_txt_file)