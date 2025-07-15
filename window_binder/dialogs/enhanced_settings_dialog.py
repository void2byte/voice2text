"""Расширенный диалог настроек привязок с дополнительными методами идентификации"""

import os
import logging
from typing import Optional, Dict, Any
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
    QComboBox, QMessageBox, QCheckBox, QGroupBox, QGridLayout, QTabWidget,
    QWidget, QTextEdit, QSpinBox, QFormLayout, QRadioButton, QButtonGroup
)
from PySide6.QtCore import Signal, QEvent
from window_binder.picker_widget import PickerWidget
from window_binder.validators import BindingValidator
from window_binder.models.binding_model import WindowBinding, WindowIdentifier, IdentificationMethod
from window_binder.utils.window_identifier import window_identification_service
from window_binder.config import config


class EnhancedSettingsDialog(QDialog):
    """Расширенный диалог настроек привязок"""
    
    result_ready = Signal(dict)
    
    def __init__(self, parent=None, existing_binding: Optional[WindowBinding] = None):
        super().__init__(parent)
        self.existing_binding = existing_binding
        self.logger = logging.getLogger(__name__)
        
        # Хранение всех признаков выбранного окна
        self.current_window_info = {}
        
        self.setWindowTitle("Расширенные настройки привязки")
        self.setMinimumSize(600, 500)
        
        self.setup_ui()
        self.load_dialog_settings()
        self.load_existing_data()
    
    def setup_ui(self):
        """Настройка интерфейса"""
        layout = QVBoxLayout(self)
        
        # Создаем вкладки
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Вкладка основных настроек
        self.setup_main_tab()
        
        # Вкладка идентификации
        self.setup_identification_tab()
        
        # Вкладка дополнительных настроек
        self.setup_advanced_tab()
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        self.test_button = QPushButton("Тестировать")
        self.test_button.clicked.connect(self.test_identification)
        
        self.save_button = QPushButton("Сохранить")
        self.save_button.clicked.connect(self.on_save_clicked)
        
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self.reject)
        
        buttons_layout.addWidget(self.test_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.save_button)
        
        layout.addLayout(buttons_layout)
        
        # Подключаем сигналы после создания всех элементов
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
    
    def on_detection_mode_changed(self):
        """Обработчик изменения режима обнаружения окон"""
        self.refresh_window_list()
    
    def get_detection_mode(self):
        """Получить текущий режим обнаружения окон"""
        return self.detection_mode_group.checkedId()
    
    def set_detection_mode(self, mode):
        """Установить режим обнаружения окон"""
        button = self.detection_mode_group.button(mode)
        if button:
            button.setChecked(True)
    
    def setup_main_tab(self):
        """Настройка основной вкладки"""
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        
        # Группа выбора окна
        window_group = QGroupBox("Выбор окна")
        window_layout = QVBoxLayout(window_group)
        
        # Picker widget и список окон
        picker_layout = QHBoxLayout()
        self.picker_widget = PickerWidget()
        picker_layout.addWidget(self.picker_widget)
        
        self.window_combo = QComboBox()
        self.window_combo.setEditable(True)
        picker_layout.addWidget(self.window_combo)
        
        self.refresh_button = QPushButton("Обновить")
        self.refresh_button.clicked.connect(self.refresh_window_list)
        picker_layout.addWidget(self.refresh_button)
        
        window_layout.addLayout(picker_layout)
        
        # Переключатель режимов обнаружения окон
        detection_group = QGroupBox("Режим обнаружения окон")
        detection_layout = QVBoxLayout(detection_group)
        
        self.detection_mode_group = QButtonGroup()
        
        self.filtered_mode_radio = QRadioButton("Фильтрованный (только пользовательские окна)")
        self.all_windows_mode_radio = QRadioButton("Все окна (включая системные)")
        self.basic_extended_mode_radio = QRadioButton("Базовый расширенный (+ скрытые окна)")
        self.full_extended_mode_radio = QRadioButton("Полный расширенный (все процессы)")
        
        self.detection_mode_group.addButton(self.filtered_mode_radio, 0)
        self.detection_mode_group.addButton(self.all_windows_mode_radio, 1)
        self.detection_mode_group.addButton(self.basic_extended_mode_radio, 2)
        self.detection_mode_group.addButton(self.full_extended_mode_radio, 3)
        
        # Устанавливаем режим по умолчанию
        self.filtered_mode_radio.setChecked(True)
        
        detection_layout.addWidget(self.filtered_mode_radio)
        detection_layout.addWidget(self.all_windows_mode_radio)
        detection_layout.addWidget(self.basic_extended_mode_radio)
        detection_layout.addWidget(self.full_extended_mode_radio)
        
        # Подключаем сигналы
        self.detection_mode_group.buttonClicked.connect(self.on_detection_mode_changed)
        
        window_layout.addWidget(detection_group)
        
        layout.addWidget(window_group)
        
        # Группа координат
        coords_group = QGroupBox("Координаты клика")
        coords_layout = QFormLayout(coords_group)
        
        self.x_coord_input = QSpinBox()
        self.x_coord_input.setRange(0, 9999)
        coords_layout.addRow("X координата:", self.x_coord_input)
        
        self.y_coord_input = QSpinBox()
        self.y_coord_input.setRange(0, 9999)
        coords_layout.addRow("Y координата:", self.y_coord_input)
        
        layout.addWidget(coords_group)
        
        # Группа позиции виджета
        widget_group = QGroupBox("Позиция виджета")
        widget_layout = QFormLayout(widget_group)
        
        self.pos_x_input = QSpinBox()
        self.pos_x_input.setRange(-500, 500)
        widget_layout.addRow("Смещение X:", self.pos_x_input)
        
        self.pos_y_input = QSpinBox()
        self.pos_y_input.setRange(-500, 500)
        widget_layout.addRow("Смещение Y:", self.pos_y_input)
        
        layout.addWidget(widget_group)
        
        # Подключаем сигналы
        self.picker_widget.window_selected.connect(self.on_window_selected_picker)
        self.window_combo.activated.connect(self.on_window_selected_combo)
        
        self.tab_widget.addTab(main_widget, "Основные")
        
        # Инициализируем список окон
        self.refresh_window_list()
    
    def setup_identification_tab(self):
        """Настройка вкладки идентификации"""
        id_widget = QWidget()
        layout = QVBoxLayout(id_widget)

        # Методы идентификации
        methods_group = QGroupBox("Методы идентификации")
        methods_layout = QVBoxLayout(methods_group)

        self.id_method_checkboxes = {}
        for method in IdentificationMethod:
            if method not in [IdentificationMethod.COMBINED, IdentificationMethod.PROCESS_ID]:
                checkbox = QCheckBox(self._get_method_display_name(method))
                self.id_method_checkboxes[method] = checkbox
                methods_layout.addWidget(checkbox)

        layout.addWidget(methods_group)
        
        # Дополнительные параметры идентификации
        params_group = QGroupBox("Параметры идентификации")
        params_layout = QFormLayout(params_group)
        
        # Информация об окне (только для чтения)
        self.window_info_text = QTextEdit()
        self.window_info_text.setMaximumHeight(100)
        self.window_info_text.setReadOnly(True)
        params_layout.addRow("Информация об окне:", self.window_info_text)
        
        # Путь к исполняемому файлу
        self.executable_path_input = QLineEdit()
        self.executable_path_input.setReadOnly(True)
        params_layout.addRow("Путь к исполняемому файлу:", self.executable_path_input)
        
        # Имя исполняемого файла
        self.executable_name_input = QLineEdit()
        self.executable_name_input.setReadOnly(True)
        params_layout.addRow("Имя исполняемого файла:", self.executable_name_input)
        
        # Класс окна
        self.window_class_input = QLineEdit()
        self.window_class_input.setReadOnly(True)
        params_layout.addRow("Класс окна:", self.window_class_input)
        
        layout.addWidget(params_group)
        
        self.tab_widget.addTab(id_widget, "Идентификация")
    
    def setup_advanced_tab(self):
        """Настройка вкладки дополнительных настроек"""
        advanced_widget = QWidget()
        layout = QVBoxLayout(advanced_widget)
        
        # Общие настройки
        general_group = QGroupBox("Общие настройки")
        general_layout = QFormLayout(general_group)
        
        self.description_input = QLineEdit()
        general_layout.addRow("Описание:", self.description_input)
        
        self.hotkey_input = QLineEdit()
        self.hotkey_input.setPlaceholderText("Например: Ctrl+Shift+R")
        general_layout.addRow("Горячая клавиша:", self.hotkey_input)
        
        self.enabled_checkbox = QCheckBox("Включена")
        self.enabled_checkbox.setChecked(True)
        general_layout.addRow("Состояние:", self.enabled_checkbox)
        
        layout.addWidget(general_group)
        
        # Настройки поиска
        search_group = QGroupBox("Настройки поиска")
        search_layout = QFormLayout(search_group)
        
        self.case_sensitive_checkbox = QCheckBox("Учитывать регистр")
        self.case_sensitive_checkbox.toggled.connect(self.on_settings_changed)
        search_layout.addRow("Чувствительность к регистру:", self.case_sensitive_checkbox)
        
        self.use_regex_checkbox = QCheckBox("Использовать регулярные выражения")
        self.use_regex_checkbox.toggled.connect(self.on_settings_changed)
        search_layout.addRow("Регулярные выражения:", self.use_regex_checkbox)
        
        layout.addWidget(search_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(advanced_widget, "Дополнительно")
    
    def _get_method_display_name(self, method: IdentificationMethod) -> str:
        """Получить отображаемое имя метода"""
        names = {
            IdentificationMethod.TITLE_EXACT: "Точное совпадение заголовка",
            IdentificationMethod.TITLE_PARTIAL: "Частичное совпадение заголовка",
            IdentificationMethod.EXECUTABLE_PATH: "Путь к исполняемому файлу",
            IdentificationMethod.EXECUTABLE_NAME: "Имя исполняемого файла",
            IdentificationMethod.WINDOW_CLASS: "Класс окна",
            IdentificationMethod.PROCESS_ID: "ID процесса (не рекомендуется)",
            IdentificationMethod.COMBINED: "Комбинированный метод"
        }
        return names.get(method, method.value)
    
    def refresh_window_list(self):
        """Обновить список окон"""
        self.logger.info("Обновление списка окон")
        
        current_text = self.window_combo.currentText()
        self.window_combo.clear()
        
        detection_mode = self.get_detection_mode()
        windows_details = window_identification_service.get_all_windows_with_details(detection_mode)
        
        for details in windows_details:
            title = details['title']
            self.window_combo.addItem(title)
        
        # Восстанавливаем предыдущий выбор
        if current_text:
            index = self.window_combo.findText(current_text)
            if index >= 0:
                self.window_combo.setCurrentIndex(index)
            else:
                self.window_combo.addItem(current_text)
                self.window_combo.setCurrentText(current_text)
        
        self.logger.info(f"Добавлено {len(windows_details)} окон в список")
    
    def on_settings_changed(self):
        """Обработчик изменения настроек"""
        if config.dialog.remember_settings:
            # Сохраняем настройки при изменении
            config.dialog.detection_mode = self.get_detection_mode()
            config.dialog.case_sensitive = self.case_sensitive_checkbox.isChecked()
            config.dialog.use_regex = self.use_regex_checkbox.isChecked()
            
            # Сохраняем конфигурацию в файл
            config.save_to_file("settings/window_binder_config.json")
            
            # Обновляем список окон при изменении "Показать все окна"
            if hasattr(self, 'primary_method_combo'):
                method = self.primary_method_combo.currentData()
                if method:
                    self.refresh_window_list_by_method(method)
    
    def on_window_selected_combo(self, index):
        """Обработчик выбора окна из комбо-бокса"""
        self.update_window_info()
    
    def on_tab_changed(self, index):
        """Обработчик переключения вкладок"""
        # Восстанавливаем настройки при переключении на вкладку идентификации
        if index == 1 and config.dialog.remember_settings:  # Вкладка "Идентификация" имеет индекс 1
            self.load_dialog_settings()
    

    
    def on_window_selected_picker(self, *args):
        """Обработчик выбора окна из PickerWidget"""
        self.logger.info(f"Picker Aргументы: {args}")
        if not args or len(args) < 3:
            self.logger.error(f"Получено неверное количество аргументов: {len(args)}")
            return

        identifier, x, y = args[:3]
        
        if not isinstance(identifier, WindowIdentifier):
            self.logger.error(f"Неверный тип идентификатора: {type(identifier)}")
            return

        self.logger.info(f"Окно выбрано: {identifier.title}, координаты: ({x}, {y})")
        self.current_window_info = identifier.to_dict()

        self.window_combo.setCurrentText(identifier.title)
        
        # Обновляем координаты
        self.x_coord_input.setValue(x)
        self.y_coord_input.setValue(y)

        # Обновляем поля идентификации
        self.executable_path_input.setText(identifier.executable_path or '')
        self.executable_name_input.setText(identifier.executable_name or '')
        self.window_class_input.setText(identifier.window_class or '')

        # Обновляем информационное поле
        info_text = f"Заголовок: {identifier.title}\n"
        if identifier.executable_name:
            info_text += f"Исполняемый файл: {identifier.executable_name}\n"
        if identifier.window_class:
            info_text += f"Класс окна: {identifier.window_class}\n"
        
        self.window_info_text.setPlainText(info_text)
        self.logger.info(f"Получена дополнительная информация о окне: {info_text}")

    
    def update_window_info(self):
        """Обновить информацию об окне"""
        window_title = self.window_combo.currentText().strip()
        if not window_title:
            return
        
        details = window_identification_service.get_window_details(window_title)
        if details:
            # Обновляем поля информации
            info_text = f"Заголовок: {details['title']}\n"
            info_text += f"Размер: {details['width']}x{details['height']}\n"
            info_text += f"Позиция: ({details['left']}, {details['top']})"
            
            self.window_info_text.setPlainText(info_text)
            
            # Обновляем поля идентификации
            self.executable_path_input.setText(details.get('executable_path', ''))
            self.executable_name_input.setText(details.get('executable_name', ''))
            self.window_class_input.setText(details.get('window_class', ''))
    
    def test_identification(self):
        """Тестировать идентификацию окна"""
        identifier = self.create_window_identifier()
        if not identifier:
            QMessageBox.warning(self, "Ошибка", "Не удалось создать идентификатор окна")
            return
        
        window = window_identification_service.find_window(identifier)
        if window:
            QMessageBox.information(
                self, "Успех", 
                f"Окно найдено: {window.title}\n"
                f"Размер: {window.width}x{window.height}\n"
                f"Позиция: ({window.left}, {window.top})"
            )
        else:
            QMessageBox.warning(
                self, "Не найдено", 
                "Окно не найдено с текущими настройками идентификации"
            )
    
    def create_window_identifier(self) -> Optional[WindowIdentifier]:
        """Создать идентификатор окна из текущих настроек"""
        if not self.current_window_info:
            return None

        selected_methods = []
        for method, checkbox in self.id_method_checkboxes.items():
            if checkbox.isChecked():
                selected_methods.append(method)

        if not selected_methods:
            # По умолчанию, если ничего не выбрано, используем частичное совпадение заголовка
            selected_methods.append(IdentificationMethod.TITLE_PARTIAL)
            if IdentificationMethod.TITLE_PARTIAL in self.id_method_checkboxes:
                 self.id_method_checkboxes[IdentificationMethod.TITLE_PARTIAL].setChecked(True)

        return WindowIdentifier(
            title=self.current_window_info.get('title'),
            executable_path=self.current_window_info.get('executable_path'),
            executable_name=self.current_window_info.get('executable_name'),
            window_class=self.current_window_info.get('window_class'),
            identification_methods=selected_methods,
            case_sensitive=self.case_sensitive_checkbox.isChecked(),
            use_regex=self.use_regex_checkbox.isChecked()
        )
    
    def create_window_binding(self) -> Optional[WindowBinding]:
        """Создать привязку окна из текущих настроек"""
        identifier = self.create_window_identifier()
        if not identifier:
            return None
        
        binding = WindowBinding(
            window_identifier=identifier,
            x=self.x_coord_input.value(),
            y=self.y_coord_input.value(),
            pos_x=self.pos_x_input.value(),
            pos_y=self.pos_y_input.value(),
            enabled=self.enabled_checkbox.isChecked(),
            description=self.description_input.text().strip() or None,
            hotkey=self.hotkey_input.text().strip() or None
        )
        
        if self.existing_binding:
            binding.id = self.existing_binding.id
            binding.created_at = self.existing_binding.created_at
        
        binding.update_timestamp()
        return binding
    
    def load_existing_data(self):
        """Загрузить данные существующей привязки"""
        if not self.existing_binding:
            return
        
        binding = self.existing_binding
        identifier = binding.window_identifier
        
        # Основные поля
        if identifier.title:
            self.window_combo.addItem(identifier.title)
            self.window_combo.setCurrentText(identifier.title)
        
        self.x_coord_input.setValue(binding.x)
        self.y_coord_input.setValue(binding.y)
        self.pos_x_input.setValue(binding.pos_x)
        self.pos_y_input.setValue(binding.pos_y)
        
        # Идентификация
        for method in identifier.identification_methods:
            if method in self.id_method_checkboxes:
                self.id_method_checkboxes[method].setChecked(True)
        
        # Дополнительные настройки
        if binding.description:
            self.description_input.setText(binding.description)
        if binding.hotkey:
            self.hotkey_input.setText(binding.hotkey)
        
        self.enabled_checkbox.setChecked(binding.enabled)
        self.case_sensitive_checkbox.setChecked(identifier.case_sensitive)
        self.use_regex_checkbox.setChecked(identifier.use_regex)
        
        # Обновляем информацию об окне
        self.update_window_info()
    
    def validate_inputs(self) -> tuple[bool, str, Optional[WindowBinding]]:
        """Валидация введенных данных"""
        # Проверяем основные поля
        if not self.window_combo.currentText().strip():
            return False, "Необходимо выбрать окно", None
        
        # Создаем привязку
        binding = self.create_window_binding()
        if not binding:
            return False, "Не удалось создать привязку", None
        
        # Дополнительная валидация
        validator = BindingValidator()
        
        # Проверяем координаты
        is_valid, error_message, _ = validator.validate_binding_data(
            identifier=binding.window_identifier,
            x=str(binding.x),
            y=str(binding.y),
            pos_x=str(binding.pos_x),
            pos_y=str(binding.pos_y)
        )
        
        if not is_valid:
            return False, error_message, None
        
        return True, "", binding
    
    def on_save_clicked(self):
        """Обработчик сохранения"""
        self.logger.info("Сохранение настроек привязки")
        
        is_valid, error_message, binding = self.validate_inputs()
        
        if not is_valid:
            QMessageBox.warning(self, "Ошибка валидации", error_message)
            return
        
        # Сохраняем данные для передачи
        self.validated_binding = binding
        
        # Преобразуем в формат для BinderManager
        result_data = {
            'app_name': binding.window_identifier.title,
            'x': binding.x,
            'y': binding.y,
            'pos_x': binding.pos_x,
            'pos_y': binding.pos_y
        }
        
        if binding.id:
            result_data['id'] = binding.id
        
        # Сохраняем расширенные данные для внутреннего использования
        result_data['_enhanced_binding'] = binding
        
        self.logger.info(f"EnhancedSettingsDialog: [RESULT_DATA] Sending result - App: '{result_data['app_name']}', Window coords: ({result_data['x']}, {result_data['y']}), Widget position: ({result_data['pos_x']}, {result_data['pos_y']}), ID: {result_data.get('id')}")
        
        # Показываем уведомление
        action = "обновлена" if self.existing_binding else "создана"
        QMessageBox.information(
            self, "Успех", 
            f"Привязка для '{binding.get_display_name()}' успешно {action}"
        )
        
        # Сохраняем настройки диалога
        self.save_dialog_settings()
        
        # Отправляем результат в BinderManager
        self.result_ready.emit(result_data)
        
        self.accept()
    
    def load_dialog_settings(self):
        """Загрузить настройки диалога из конфигурации"""
        if not config.dialog.remember_settings:
            return
        
        try:
            
            # Восстанавливаем режим обнаружения окон
            detection_mode = getattr(config.dialog, 'detection_mode', 0)  # По умолчанию фильтрованный режим
            self.set_detection_mode(detection_mode)
            
            self.case_sensitive_checkbox.setChecked(config.dialog.case_sensitive)
            self.use_regex_checkbox.setChecked(config.dialog.use_regex)
            
            self.logger.info("Настройки диалога загружены из конфигурации")
        except Exception as e:
            self.logger.warning(f"Ошибка загрузки настроек диалога: {e}")
    
    def save_dialog_settings(self):
        """Сохранить настройки диалога в конфигурацию"""
        if not config.dialog.remember_settings:
            return
        
        try:
            
            config.dialog.detection_mode = self.get_detection_mode()
            config.dialog.case_sensitive = self.case_sensitive_checkbox.isChecked()
            config.dialog.use_regex = self.use_regex_checkbox.isChecked()
            
            # Сохраняем в файл
            config.save_to_file("settings/window_binder_config.json")
            
            self.logger.info("Настройки диалога сохранены в конфигурацию")
        except Exception as e:
            self.logger.warning(f"Ошибка сохранения настроек диалога: {e}")
    
    def refresh_window_list_by_method(self, method: IdentificationMethod):
        """Обновить список окон с учетом выбранного метода идентификации"""
        try:
            current_text = self.window_combo.currentText()
            self.window_combo.clear()
            
            detection_mode = self.get_detection_mode()
            windows_details = window_identification_service.get_all_windows_with_details(detection_mode)
            
            # Фильтруем окна в зависимости от метода идентификации
            filtered_windows = []
            for details in windows_details:
                # Проверяем, есть ли необходимые данные для выбранного метода
                if self._window_supports_method(details, method):
                    filtered_windows.append(details)
            
            # Добавляем окна в список
            for details in filtered_windows:
                title = details['title']
                self.window_combo.addItem(title)
            
            # Восстанавливаем предыдущий выбор
            if current_text:
                index = self.window_combo.findText(current_text)
                if index >= 0:
                    self.window_combo.setCurrentIndex(index)
                else:
                    self.window_combo.addItem(current_text)
                    self.window_combo.setCurrentText(current_text)
            
            self.logger.info(f"Список окон обновлен для метода {method.value}: {len(filtered_windows)} окон")
        except Exception as e:
            self.logger.error(f"Ошибка обновления списка окон: {e}")
    
    def _window_supports_method(self, window_details: dict, method: IdentificationMethod) -> bool:
        """Проверить, поддерживает ли окно выбранный метод идентификации"""
        if method in [IdentificationMethod.TITLE_EXACT, IdentificationMethod.TITLE_PARTIAL]:
            return bool(window_details.get('title'))
        elif method == IdentificationMethod.EXECUTABLE_PATH:
            return bool(window_details.get('executable_path'))
        elif method == IdentificationMethod.EXECUTABLE_NAME:
            return bool(window_details.get('executable_name'))
        elif method == IdentificationMethod.WINDOW_CLASS:
            return bool(window_details.get('window_class'))
        elif method == IdentificationMethod.PROCESS_ID:
            return bool(window_details.get('process_id'))
        else:
            return True  # Для комбинированного метода показываем все окна