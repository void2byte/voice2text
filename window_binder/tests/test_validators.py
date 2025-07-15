"""Тесты для модуля валидации"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Добавляем путь к модулю
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from validators import BindingValidator
from config import config


class TestBindingValidator(unittest.TestCase):
    """Тесты для класса BindingValidator"""
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        self.validator = BindingValidator()
    
    def test_validate_app_name_valid(self):
        """Тест валидации корректного названия приложения"""
        valid, error = self.validator.validate_app_name("Notepad")
        self.assertTrue(valid)
        self.assertEqual(error, "")
    
    def test_validate_app_name_empty(self):
        """Тест валидации пустого названия приложения"""
        valid, error = self.validator.validate_app_name("")
        self.assertFalse(valid)
        self.assertIn("пустым", error)
    
    def test_validate_app_name_whitespace(self):
        """Тест валидации названия из пробелов"""
        valid, error = self.validator.validate_app_name("   ")
        self.assertFalse(valid)
        self.assertIn("пустым", error)
    
    def test_validate_app_name_too_short(self):
        """Тест валидации слишком короткого названия"""
        valid, error = self.validator.validate_app_name("A")
        self.assertFalse(valid)
        self.assertIn("минимум", error)
    
    def test_validate_app_name_too_long(self):
        """Тест валидации слишком длинного названия"""
        long_name = "A" * (config.validation.max_app_name_length + 1)
        valid, error = self.validator.validate_app_name(long_name)
        self.assertFalse(valid)
        self.assertIn("превышать", error)
    
    def test_validate_coordinates_valid(self):
        """Тест валидации корректных координат"""
        valid, error, x, y = self.validator.validate_coordinates("100", "200")
        self.assertTrue(valid)
        self.assertEqual(error, "")
        self.assertEqual(x, 100)
        self.assertEqual(y, 200)
    
    def test_validate_coordinates_invalid_format(self):
        """Тест валидации некорректного формата координат"""
        valid, error, x, y = self.validator.validate_coordinates("abc", "200")
        self.assertFalse(valid)
        self.assertIn("числами", error)
        self.assertIsNone(x)
        self.assertIsNone(y)
    
    def test_validate_coordinates_negative(self):
        """Тест валидации отрицательных координат"""
        valid, error, x, y = self.validator.validate_coordinates("-10", "200")
        self.assertFalse(valid)
        self.assertIn("положительными", error)
    
    def test_validate_coordinates_too_large(self):
        """Тест валидации слишком больших координат"""
        large_coord = str(config.validation.max_coordinate_value + 1)
        valid, error, x, y = self.validator.validate_coordinates(large_coord, "200")
        self.assertFalse(valid)
        self.assertIn("превышать", error)
    
    @patch('pyautogui.size')
    def test_validate_coordinates_screen_bounds(self, mock_size):
        """Тест валидации координат относительно границ экрана"""
        mock_size.return_value = (1920, 1080)
        
        # Включаем проверку границ экрана
        original_value = config.validation.validate_screen_bounds
        config.validation.validate_screen_bounds = True
        
        try:
            # Координаты в пределах экрана
            valid, error, x, y = self.validator.validate_coordinates("100", "100")
            self.assertTrue(valid)
            
            # Координаты за пределами экрана
            valid, error, x, y = self.validator.validate_coordinates("2000", "100")
            self.assertFalse(valid)
            self.assertIn("пределы экрана", error)
        finally:
            config.validation.validate_screen_bounds = original_value
    
    def test_validate_position_valid(self):
        """Тест валидации корректной позиции"""
        valid, error, pos_x, pos_y = self.validator.validate_position("50", "-30")
        self.assertTrue(valid)
        self.assertEqual(error, "")
        self.assertEqual(pos_x, 50)
        self.assertEqual(pos_y, -30)
    
    def test_validate_position_invalid_format(self):
        """Тест валидации некорректного формата позиции"""
        valid, error, pos_x, pos_y = self.validator.validate_position("abc", "50")
        self.assertFalse(valid)
        self.assertIn("числом", error)
    
    def test_validate_position_too_large(self):
        """Тест валидации слишком большой позиции"""
        large_pos = str(config.validation.max_position_offset + 1)
        valid, error, pos_x, pos_y = self.validator.validate_position(large_pos, "50")
        self.assertFalse(valid)
        self.assertIn("превышать", error)
    
    @patch('pygetwindow.getWindowsWithTitle')
    def test_validate_window_exists_found(self, mock_get_windows):
        """Тест проверки существования окна - окно найдено"""
        mock_window = MagicMock()
        mock_window.width = 800
        mock_window.height = 600
        mock_get_windows.return_value = [mock_window]
        
        valid, error = self.validator.validate_window_exists("Notepad")
        self.assertTrue(valid)
        self.assertEqual(error, "")
    
    @patch('pygetwindow.getWindowsWithTitle')
    def test_validate_window_exists_not_found(self, mock_get_windows):
        """Тест проверки существования окна - окно не найдено"""
        mock_get_windows.return_value = []
        
        valid, error = self.validator.validate_window_exists("NonExistentApp")
        self.assertFalse(valid)
        self.assertIn("не найдено", error)
    
    @patch('pygetwindow.getWindowsWithTitle')
    def test_validate_window_exists_minimized(self, mock_get_windows):
        """Тест проверки существования окна - окно свернуто"""
        mock_window = MagicMock()
        mock_window.width = 0
        mock_window.height = 0
        mock_get_windows.return_value = [mock_window]
        
        valid, error = self.validator.validate_window_exists("MinimizedApp")
        self.assertFalse(valid)
        self.assertIn("свернуто", error)
    
    def test_validate_window_exists_disabled(self):
        """Тест проверки существования окна - проверка отключена"""
        original_value = config.validation.validate_window_existence
        config.validation.validate_window_existence = False
        
        try:
            valid, error = self.validator.validate_window_exists("AnyApp")
            self.assertTrue(valid)
            self.assertEqual(error, "")
        finally:
            config.validation.validate_window_existence = original_value
    
    @patch('pygetwindow.getWindowsWithTitle')
    def test_validate_binding_data_complete_valid(self, mock_get_windows):
        """Тест полной валидации корректных данных привязки"""
        mock_window = MagicMock()
        mock_window.width = 800
        mock_window.height = 600
        mock_get_windows.return_value = [mock_window]
        
        valid, error, data = self.validator.validate_binding_data(
            "Notepad", "100", "200", "50", "30"
        )
        
        self.assertTrue(valid)
        self.assertEqual(error, "")
        self.assertEqual(data['app_name'], "Notepad")
        self.assertEqual(data['x'], 100)
        self.assertEqual(data['y'], 200)
        self.assertEqual(data['pos_x'], 50)
        self.assertEqual(data['pos_y'], 30)
    
    def test_validate_binding_data_invalid_app_name(self):
        """Тест полной валидации с некорректным названием приложения"""
        valid, error, data = self.validator.validate_binding_data(
            "", "100", "200", "50", "30"
        )
        
        self.assertFalse(valid)
        self.assertIn("пустым", error)
        self.assertEqual(data, {})
    
    def test_validate_binding_data_invalid_coordinates(self):
        """Тест полной валидации с некорректными координатами"""
        valid, error, data = self.validator.validate_binding_data(
            "Notepad", "abc", "200", "50", "30"
        )
        
        self.assertFalse(valid)
        self.assertIn("числами", error)
        self.assertEqual(data, {})

    def test_is_valid_coordinate_valid(self):
        """Тест валидной координаты"""
        self.assertTrue(self.validator.is_valid_coordinate(100, 200))

    def test_is_valid_coordinate_invalid(self):
        """Тест невалидной координаты"""
        self.assertFalse(self.validator.is_valid_coordinate(-10, 200))

    def test_is_valid_position_offset_valid(self):
        """Тест валидного смещения позиции"""
        self.assertTrue(self.validator.is_valid_position_offset(50, -30))

    def test_is_valid_position_offset_invalid(self):
        """Тест невалидного смещения позиции"""
        self.assertFalse(self.validator.is_valid_position_offset(1001, 50))

    def test_sanitize_app_name(self):
        """Тест очистки названия приложения"""
        self.assertEqual(self.validator.sanitize_app_name(" App Name "), "App Name")

    @patch('pyautogui.size')
    def test_get_screen_size(self, mock_size):
        """Тест получения размера экрана"""
        mock_size.return_value = (1920, 1080)
        self.assertEqual(BindingValidator.get_screen_size(), (1920, 1080))

if __name__ == '__main__':
    unittest.main()