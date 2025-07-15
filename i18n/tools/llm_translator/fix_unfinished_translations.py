import xml.etree.ElementTree as ET
import sys

def fix_unfinished_translations(file_path):
    """
    Removes the 'type="unfinished"' attribute from <translation> tags
    that contain text.

    Args:
        file_path (str): The path to the .ts file.
    """
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        changed_count = 0
        # Find all 'translation' tags
        for translation_tag in root.findall('.//translation'):
            # Check if the tag has type="unfinished" and has text content
            if translation_tag.get('type') == 'unfinished' and translation_tag.text and translation_tag.text.strip():
                del translation_tag.attrib['type']
                changed_count += 1

        if changed_count > 0:
            # Write the changes back to the file
            tree.write(file_path, encoding='utf-8', xml_declaration=True)
            print(f"Successfully fixed {changed_count} unfinished translations in {file_path}")
        else:
            print(f"No unfinished translations with content found in {file_path}")

    except ET.ParseError as e:
        print(f"Error parsing XML file: {e}")
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        ts_file = sys.argv[1]
        fix_unfinished_translations(ts_file)
    else:
        print("Usage: python fix_unfinished_translations.py <path_to_ts_file>")