from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, 
    QListWidgetItem, QLabel, QMessageBox, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import logging
from typing import Dict, Optional


class BindingManagementDialog(QDialog):
    """Диалог для управления привязками окон"""
    
    def __init__(self, binder_manager, parent=None):
        super().__init__(parent)
        self.binder_manager = binder_manager
        self.logger = logging.getLogger(__name__)
        
        self.setWindowTitle("Управление привязками")
        self.setModal(True)
        self.resize(500, 400)
        
        self.setup_ui()
        self.load_bindings()
        
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        layout = QVBoxLayout(self)
        
        # Заголовок
        title_label = QLabel("Сохраненные привязки")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Список привязок
        self.bindings_list = QListWidget()
        self.bindings_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        layout.addWidget(self.bindings_list)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        
        self.edit_button = QPushButton("Редактировать")
        self.edit_button.clicked.connect(self.edit_selected_binding)
        self.edit_button.setEnabled(False)
        buttons_layout.addWidget(self.edit_button)
        
        self.delete_button = QPushButton("Удалить")
        self.delete_button.clicked.connect(self.delete_selected_binding)
        self.delete_button.setEnabled(False)
        buttons_layout.addWidget(self.delete_button)
        
        buttons_layout.addStretch()
        
        self.refresh_button = QPushButton("Обновить")
        self.refresh_button.clicked.connect(self.load_bindings)
        buttons_layout.addWidget(self.refresh_button)
        
        layout.addLayout(buttons_layout)
        
        # Кнопки диалога
        dialog_buttons_layout = QHBoxLayout()
        
        self.add_button = QPushButton("Добавить новую")
        self.add_button.clicked.connect(self.add_new_binding)
        dialog_buttons_layout.addWidget(self.add_button)
        
        dialog_buttons_layout.addStretch()
        
        self.close_button = QPushButton("Закрыть")
        self.close_button.clicked.connect(self.accept)
        dialog_buttons_layout.addWidget(self.close_button)
        
        layout.addLayout(dialog_buttons_layout)
        
        # Подключение сигналов
        self.bindings_list.itemSelectionChanged.connect(self.on_selection_changed)
        self.bindings_list.itemDoubleClicked.connect(self.edit_selected_binding)
        
    def load_bindings(self):
        """Загрузить список привязок"""
        self.logger.info("BindingManagementDialog: [LOAD_BINDINGS] Loading bindings list for UI")
        self.bindings_list.clear()
        
        bindings = self.binder_manager.get_all_bindings()
        self.logger.info(f"BindingManagementDialog: [LOAD_BINDINGS] Retrieved {len(bindings)} bindings from manager")
        
        if not bindings:
            self.logger.info("BindingManagementDialog: [LOAD_BINDINGS] No bindings found, showing empty state")
            item = QListWidgetItem("Нет сохраненных привязок")
            item.setFlags(Qt.ItemFlag.NoItemFlags)  # Делаем элемент неактивным
            self.bindings_list.addItem(item)
            return
            
        for binding in bindings:
            app_name = binding.window_identifier.title
            x = binding.x
            y = binding.y
            pos_x = binding.pos_x
            pos_y = binding.pos_y
            
            # Создаем текст для отображения
            display_text = f"{app_name} | Клик: ({x}, {y}) | Позиция: ({pos_x}, {pos_y})"
            
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, binding.id)  # Сохраняем ID привязки
            self.bindings_list.addItem(item)
            
            self.logger.debug(f"BindingManagementDialog: [BINDING_ITEM] Added to UI - ID: {binding.id}, App: '{app_name}', Display: '{display_text}'")
            
        self.logger.info(f"BindingManagementDialog: [LOAD_BINDINGS] Successfully loaded {len(bindings)} bindings to UI")
        
    def on_selection_changed(self):
        """Обработчик изменения выбора в списке"""
        has_selection = bool(self.bindings_list.selectedItems())
        
        # Проверяем, что выбранный элемент не является заглушкой
        if has_selection:
            selected_item = self.bindings_list.selectedItems()[0]
            binding_id = selected_item.data(Qt.ItemDataRole.UserRole)
            has_valid_selection = binding_id is not None
        else:
            has_valid_selection = False
            
        self.edit_button.setEnabled(has_valid_selection)
        self.delete_button.setEnabled(has_valid_selection)
        
    def get_selected_binding_id(self) -> Optional[str]:
        """Получить ID выбранной привязки"""
        selected_items = self.bindings_list.selectedItems()
        if not selected_items:
            return None
            
        return selected_items[0].data(Qt.ItemDataRole.UserRole)
        
    def edit_selected_binding(self):
        """Редактировать выбранную привязку"""
        binding_id = self.get_selected_binding_id()
        if not binding_id:
            return
            
        try:
            # Открываем диалог настроек для редактирования
            self.binder_manager.show_settings(existing_binding_id=binding_id)
            # Обновляем список после возможного редактирования
            self.load_bindings()
        except Exception as e:
            self.logger.error(f"Ошибка при редактировании привязки {binding_id}: {e}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось открыть редактирование привязки: {e}")
            
    def delete_selected_binding(self):
        """Удалить выбранную привязку"""
        binding_id = self.get_selected_binding_id()
        if not binding_id:
            return
            
        # Получаем информацию о привязке для подтверждения
        binding = self.binder_manager.get_binding_by_id(binding_id)
        app_name = binding.window_identifier.title if binding else 'Неизвестно'
        
        # Запрашиваем подтверждение
        reply = QMessageBox.question(
            self, 
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить привязку для '{app_name}'?\n\n"
            f"Это действие нельзя отменить.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                success = self.binder_manager.remove_binding(binding_id)
                if success:
                    self.logger.info(f"Привязка {binding_id} успешно удалена")
                    QMessageBox.information(self, "Успех", f"Привязка для '{app_name}' удалена")
                    self.load_bindings()  # Обновляем список
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось удалить привязку")
            except Exception as e:
                self.logger.error(f"Ошибка при удалении привязки {binding_id}: {e}")
                QMessageBox.critical(self, "Ошибка", f"Произошла ошибка при удалении: {e}")
                
    def add_new_binding(self):
        """Добавить новую привязку"""
        try:
            self.binder_manager.show_settings()
            # Обновляем список после возможного добавления
            self.load_bindings()
        except Exception as e:
            self.logger.error(f"Ошибка при добавлении новой привязки: {e}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось открыть создание привязки: {e}")