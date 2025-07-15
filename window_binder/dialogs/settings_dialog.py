"""Диалог настроек привязок с расширенными возможностями идентификации"""

import os
import logging
from typing import Optional, Dict, Any
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
    QComboBox, QMessageBox, QCheckBox, QGroupBox, QFormLayout, QSpinBox
)
from PySide6.QtCore import Signal, QEvent
from window_binder.picker_widget import PickerWidget

from window_binder.validators import BindingValidator
from window_binder.models.binding_model import WindowBinding, WindowIdentifier, IdentificationMethod
from window_binder.utils.window_identifier import window_identification_service


class SettingsDialog(QDialog):
    """Диалог настроек привязок с расширенными возможностями идентификации"""
    
    result_ready = Signal(dict)
    
    def __init__(self, parent=None, existing_data: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        self.existing_data = existing_data
        self.existing_binding = None
        self.logger = logging.getLogger(__name__)
        
        # Преобразуем старые данные в новый формат если необходимо
        if existing_data:
            self.existing_binding = self._convert_legacy_data(existing_data)
        
        self.setWindowTitle("Настройки привязки")
        self.setMinimumSize(500, 400)
        
        self.setup_ui()
        if existing_data:
            self.load_existing_data_from_dict()
        elif self.existing_binding:
            self.load_existing_data()
    
    def _convert_legacy_data(self, data: Dict[str, Any]) -> WindowBinding:
        """Преобразовать старые данные в новый формат"""
        # Создаем идентификатор окна из старых данных
        identifier = WindowIdentifier(
            title=data.get('app_name', ''),
            primary_method=IdentificationMethod.TITLE_PARTIAL,
            fallback_methods=[IdentificationMethod.EXECUTABLE_NAME],
            case_sensitive=False
        )
        
        # Создаем привязку
        binding = WindowBinding(
            window_identifier=identifier,
            x=int(data.get('x', 0)),
            y=int(data.get('y', 0)),
            pos_x=int(data.get('pos_x', 0)),
            pos_y=int(data.get('pos_y', 0))
        )
        
        if 'id' in data:
            binding.id = data['id']
        
        return binding
    
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
    
    def setup_ui(self):
        """Настройка интерфейса"""
        layout = QVBoxLayout(self)
        
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
        
        # Галочка для отображения всех окон
        self.show_all_checkbox = QCheckBox("Показать все окна (включая системные)")
        self.show_all_checkbox.stateChanged.connect(self.refresh_window_list)
        window_layout.addWidget(self.show_all_checkbox)
        
        layout.addWidget(window_group)
        
        # Группа методов идентификации
        id_group = QGroupBox("Методы идентификации")
        id_layout = QFormLayout(id_group)
        
        # Основной метод
        self.primary_method_combo = QComboBox()
        for method in IdentificationMethod:
            if method != IdentificationMethod.PROCESS_ID:  # Исключаем нестабильный метод
                self.primary_method_combo.addItem(self._get_method_display_name(method), method)
        self.primary_method_combo.setCurrentText("Частичное совпадение заголовка")
        id_layout.addRow("Основной метод:", self.primary_method_combo)
        
        # Резервные методы
        self.use_executable_checkbox = QCheckBox("Использовать имя исполняемого файла")
        self.use_executable_checkbox.setChecked(True)
        id_layout.addRow("Резервный метод:", self.use_executable_checkbox)
        
        self.case_sensitive_checkbox = QCheckBox("Учитывать регистр")
        id_layout.addRow("Настройки:", self.case_sensitive_checkbox)
        
        layout.addWidget(id_group)
        
        # Группа координат
        coords_group = QGroupBox("Координаты и позиция")
        coords_layout = QFormLayout(coords_group)
        
        self.x_coord_input = QSpinBox()
        self.x_coord_input.setRange(0, 9999)
        coords_layout.addRow("X координата:", self.x_coord_input)
        
        self.y_coord_input = QSpinBox()
        self.y_coord_input.setRange(0, 9999)
        coords_layout.addRow("Y координата:", self.y_coord_input)
        
        self.pos_x_input = QSpinBox()
        self.pos_x_input.setRange(-500, 500)
        coords_layout.addRow("Смещение X:", self.pos_x_input)
        
        self.pos_y_input = QSpinBox()
        self.pos_y_input.setRange(-500, 500)
        coords_layout.addRow("Смещение Y:", self.pos_y_input)
        
        layout.addWidget(coords_group)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        self.test_button = QPushButton("Тестировать")
        self.test_button.clicked.connect(self.test_identification)
        buttons_layout.addWidget(self.test_button)
        
        self.advanced_button = QPushButton("Расширенные...")
        self.advanced_button.clicked.connect(self.open_advanced_dialog)
        buttons_layout.addWidget(self.advanced_button)
        
        buttons_layout.addStretch()
        
        self.save_button = QPushButton("Сохранить")
        self.save_button.clicked.connect(self.on_save_clicked)
        
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self.reject)
        
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.save_button)
        
        layout.addLayout(buttons_layout)
        
        # Подключаем сигналы
        self.picker_widget.window_selected.connect(self.update_fields)
        self.window_combo.activated.connect(self.on_window_selected)
        
        # Инициализируем список окон
        self.refresh_window_list()
    
    def refresh_window_list(self):
        """Обновить список окон"""
        self.logger.info("Обновление списка окон")
        
        current_text = self.window_combo.currentText()
        self.window_combo.clear()
        
        # Преобразуем старый чекбокс в режим обнаружения
        detection_mode = 1 if self.show_all_checkbox.isChecked() else 0
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
    
    def on_window_selected(self, index):
        """Обработчик выбора окна"""
        pass  # Можно добавить дополнительную логику при необходимости
    
    def update_fields(self, title, x, y):
        """Обновить поля при выборе окна через picker"""
        self.logger.info(f"Обновление полей: {title}, X: {x}, Y: {y}")
        
        if not title or not title.strip():
            return
        
        title = title.strip()
        
        # Обновляем комбобокс
        index = self.window_combo.findText(title)
        if index >= 0:
            self.window_combo.setCurrentIndex(index)
        else:
            self.window_combo.addItem(title)
            self.window_combo.setCurrentText(title)
        
        # Обновляем координаты
        self.x_coord_input.setValue(x)
        self.y_coord_input.setValue(y)
    
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
    
    def open_advanced_dialog(self):
        """Открыть расширенный диалог настроек"""
        from window_binder.dialogs.enhanced_settings_dialog import EnhancedSettingsDialog
        
        # Создаем привязку из текущих данных
        current_binding = self.create_window_binding()
        
        dialog = EnhancedSettingsDialog(self, current_binding)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Обновляем текущие поля из расширенного диалога
            if hasattr(dialog, 'validated_binding'):
                self.existing_binding = dialog.validated_binding
                self.load_existing_data()
    
    def create_window_identifier(self) -> Optional[WindowIdentifier]:
        """Создать идентификатор окна из текущих настроек"""
        window_title = self.window_combo.currentText().strip()
        if not window_title:
            return None
        
        # Получаем основной метод
        primary_method = self.primary_method_combo.currentData()
        
        # Получаем резервные методы
        fallback_methods = []
        if self.use_executable_checkbox.isChecked():
            fallback_methods.append(IdentificationMethod.EXECUTABLE_NAME)
        
        # Получаем дополнительную информацию об окне
        details = window_identification_service.get_window_details(window_title)
        
        return WindowIdentifier(
            title=window_title,
            executable_path=details.get('executable_path', '') if details else '',
            executable_name=details.get('executable_name', '') if details else '',
            window_class=details.get('window_class', '') if details else '',
            primary_method=primary_method,
            fallback_methods=fallback_methods,
            case_sensitive=self.case_sensitive_checkbox.isChecked()
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
            pos_y=self.pos_y_input.value()
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
        
        # Методы идентификации
        primary_index = self.primary_method_combo.findData(identifier.primary_method)
        if primary_index >= 0:
            self.primary_method_combo.setCurrentIndex(primary_index)
        
        # Резервные методы
        if IdentificationMethod.EXECUTABLE_NAME in identifier.fallback_methods:
            self.use_executable_checkbox.setChecked(True)
        
        # Настройки
        self.case_sensitive_checkbox.setChecked(identifier.case_sensitive)
    

    

    
    def create_enhanced_binding(self, app_name: str):
        """Создать расширенную привязку из текущих настроек"""
        try:
            # Определяем основной метод идентификации
            primary_method = self.primary_method_combo.currentData()
            if not primary_method:
                primary_method = IdentificationMethod.TITLE_PARTIAL
            
            # Определяем резервные методы
            fallback_methods = []
            if self.use_executable_checkbox.isChecked():
                fallback_methods.append(IdentificationMethod.EXECUTABLE_NAME)
            
            # Получаем дополнительную информацию об окне
            details = window_identification_service.get_window_details(app_name)
            
            # Создаем идентификатор
            identifier = WindowIdentifier(
                title=app_name,
                executable_path=details.get('executable_path', '') if details else '',
                executable_name=details.get('executable_name', '') if details else '',
                window_class=details.get('window_class', '') if details else '',
                primary_method=primary_method,
                fallback_methods=fallback_methods,
                case_sensitive=self.case_sensitive_checkbox.isChecked()
            )
            
            # Создаем привязку
            binding = WindowBinding(
                window_identifier=identifier,
                x=self.x_coord_input.value(),
                y=self.y_coord_input.value(),
                pos_x=self.pos_x_input.value(),
                pos_y=self.pos_y_input.value()
            )
            
            # Сохраняем ID если редактируем
            if self.existing_data:
                binding.id = self.existing_data.get('id')
            
            return binding
            
        except Exception as e:
            self.logger.error(f"Error creating enhanced binding: {e}")
            return None
    
    def get_identification_method_name(self, method: IdentificationMethod) -> str:
        """Получить читаемое имя метода идентификации"""
        method_names = {
            IdentificationMethod.TITLE_EXACT: "По заголовку (точно)",
            IdentificationMethod.TITLE_PARTIAL: "По заголовку (частично)",
            IdentificationMethod.EXECUTABLE_NAME: "По исполняемому файлу",
            IdentificationMethod.EXECUTABLE_PATH: "По пути к файлу",
            IdentificationMethod.WINDOW_CLASS: "По классу окна"
        }
        return method_names.get(method, "Неизвестный метод")
    
    def load_existing_data_from_dict(self):
        """Загрузить данные для редактирования из словаря"""
        if not self.existing_data:
            return
        
        try:
            # Загружаем основные данные
            self.window_combo.setCurrentText(self.existing_data.get('app_name', ''))
            self.x_coord_input.setValue(self.existing_data.get('x', 0))
            self.y_coord_input.setValue(self.existing_data.get('y', 0))
            self.pos_x_input.setValue(self.existing_data.get('pos_x', 50))
            self.pos_y_input.setValue(self.existing_data.get('pos_y', 50))
            
            # Загружаем расширенные данные если есть
            enhanced_binding = self.existing_data.get('_enhanced_binding')
            if enhanced_binding and isinstance(enhanced_binding, WindowBinding):
                try:
                    identifier = enhanced_binding.window_identifier
                    
                    # Устанавливаем основной метод
                    primary_index = self.primary_method_combo.findData(identifier.primary_method)
                    if primary_index >= 0:
                        self.primary_method_combo.setCurrentIndex(primary_index)
                    
                    # Устанавливаем резервные методы
                    if identifier.fallback_methods:
                        if IdentificationMethod.EXECUTABLE_NAME in identifier.fallback_methods:
                            self.use_executable_checkbox.setChecked(True)
                    
                    # Устанавливаем параметры
                    self.case_sensitive_checkbox.setChecked(identifier.case_sensitive)
                    
                except Exception as e:
                    self.logger.error(f"Error loading enhanced data: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error loading existing data: {e}")
    
    def validate_inputs(self) -> tuple[bool, str, Optional[WindowBinding]]:
        """Валидация введенных данных"""
        try:
            # Проверяем заполненность полей
            if not self.window_combo.currentText().strip():
                return False, "Выберите окно", None
            
            # Создаем расширенную привязку
            app_name = self.window_combo.currentText().strip()
            enhanced_binding = self.create_enhanced_binding(app_name)
            
            if not enhanced_binding:
                return False, "Не удалось создать привязку", None
            
            # Простая валидация координат
            if enhanced_binding.x < 0 or enhanced_binding.y < 0:
                return False, "Координаты не могут быть отрицательными", None
            
            if enhanced_binding.pos_x < 0 or enhanced_binding.pos_y < 0:
                return False, "Позиция виджета не может быть отрицательной", None
            
            return True, "", enhanced_binding
            
        except Exception as e:
            self.logger.error(f"Error validating inputs: {e}")
            return False, f"Ошибка валидации: {e}", None
    
    def on_save_clicked(self):
        """Обработчик сохранения"""
        self.logger.info("Сохранение настроек привязки")
        
        is_valid, error_message, binding = self.validate_inputs()
        
        if not is_valid:
            QMessageBox.warning(self, "Ошибка валидации", error_message)
            return
        
        # Преобразуем в старый формат для совместимости
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
        
        # Показываем уведомление
        action = "обновлена" if self.existing_binding else "создана"
        QMessageBox.information(
            self, "Успех", 
            f"Привязка для '{binding.get_display_name()}' успешно {action}"
        )
        
        # Отправляем результат
        self.result_ready.emit(result_data)
        self.accept()