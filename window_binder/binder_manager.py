import os
import logging
import pyautogui
import pyperclip
import pygetwindow as gw
from PySide6.QtCore import QObject
from typing import Optional
from window_commander.core.window_manager import WindowManager
from PySide6.QtWidgets import QApplication, QMessageBox, QDialog
from window_binder.dialogs.enhanced_settings_dialog import EnhancedSettingsDialog
from window_binder.storage.binding_storage import BindingStorage
from window_binder.managers.widget_manager import WidgetManager
from window_binder.models.binding_model import WindowBinding, WindowIdentifier, SelectedWindowData, IdentificationMethod
from window_binder.utils.window_identifier import window_identification_service

BINDINGS_FILE = os.path.join("settings", "bindings.json")

class BinderManager(QObject):
    """Главный менеджер для координации работы с привязками окон"""
    
    def __init__(self, tray_app, parent=None):
        super().__init__(parent)
        self.tray_app = tray_app
        self.logger = logging.getLogger(__name__)
        self.window_manager = WindowManager(self.logger)
        
        # Инициализируем компоненты
        self.storage = BindingStorage(BINDINGS_FILE)
        self.widget_manager = WidgetManager()
        self.bindings = {}
        self.specific_binding_target = None
        
        # Настраиваем callbacks для widget_manager
        self.widget_manager.set_callbacks(
            start_recognition_callback=self.start_recognition,
            stop_recognition_callback=self.stop_recognition, # Добавляем новый callback
            binder_moved_callback=self.on_binder_moved,
            delete_requested_callback=self.on_delete_requested
        )
        self.widget_manager.stop_recognition_signal.connect(self.stop_recognition)
        
        # Загружаем существующие привязки
        self.load_bindings()



    def stop_recognition(self, binding_id):
        """Остановить распознавание для конкретной привязки."""
        self.logger.info(f"Stopping recognition for specific binding: {binding_id}")
        # Здесь должна быть логика остановки, например, вызов метода в tray_app или voice_widget
        if self.tray_app.widget and self.tray_app.widget.is_recording:
            self.tray_app.widget.stop_recording()

    def start_recognition(self, binding_id):
        """Начать распознавание для конкретной привязки."""
        self.logger.info(f"Starting recognition for specific binding: {binding_id}")
        binding = self.bindings.get(binding_id)
        if not binding:
            self.logger.error(f"Binding ID {binding_id} not found.")
            return
        
        self.specific_binding_target = binding
        self.tray_app.launch_widget(start_recording=True)

    def on_recognition_finished(self, text):
        self.logger.info(f"builder_manadger on_recognition_finished text: {text}")
        if not text:
            self.logger.warning("Recognition finished with empty text, skipping paste.")
            return

        # Случай 1: Распознавание было вызвано для конкретной привязки
        if self.specific_binding_target:
            binding = self.specific_binding_target
            x, y = binding.x, binding.y
            app_name = binding.window_identifier.title
            self.logger.info(f"Pasting to specific binder target at ({x}, {y}) for app '{app_name}'")

            target_window = window_identification_service.find_window(binding.window_identifier)

            if target_window:
                hwnd = target_window._hWnd
                self.window_manager.set_window_info({'hwnd': hwnd})
                self.logger.info(f"Attempting to click at ({x}, {y}) in window {app_name}")
                # Сначала кликаем по координатам
                if self.window_manager.click_at_position(x, y, with_focus=True):
                    self.logger.info(f"Click successful. Pasting text.")
                    # Затем вставляем текст, фокус уже должен быть установлен
                    self.window_manager.send_text(text, with_focus=False)
                    self.logger.info(f"Text pasted successfully to specific target after click.")
                else:
                    self.logger.error(f"Failed to click at position for window {app_name}")
            else:
                self.logger.error(f"Could not find window for app: {app_name}")
            self.specific_binding_target = None  # Сбрасываем цель
            return

        # Случай 2: Распознавание было вызвано глобально (горячая клавиша)
        active_window = gw.getActiveWindow()
        if not active_window:
            self.logger.warning("No active window found to paste text.")
            return

        hwnd = active_window._hWnd
        self.window_manager.set_window_info({'hwnd': hwnd})
        self.window_manager.send_text(text, with_focus=True)
        self.logger.info(f"Text paste to active window: {text}")

    def on_binder_moved(self, binding_id, pos_x, pos_y):
        """Обработчик перемещения виджета привязки"""
        self.logger.info(f"BinderManager: [WIDGET_MOVED] Widget moved - ID: {binding_id}, New absolute position: ({pos_x}, {pos_y})")
        
        if binding_id not in self.bindings:
            self.logger.error(f"BinderManager: [MOVE_ERROR] Binding {binding_id} not found")
            return
        
        try:
            binding = self.bindings[binding_id]
            app_name = binding.window_identifier.title
            self.logger.debug(f"BinderManager: [MOVE_CALC] Calculating relative position for app '{app_name}'")

            win = window_identification_service.find_window(binding.window_identifier)

            if not win:
                self.logger.warning(f"BinderManager: [MOVE_ERROR] Window '{app_name}' not found for position update")
                return
            relative_x = pos_x - win.left
            relative_y = pos_y - win.top
            
            self.logger.info(f"BinderManager: [POSITION_CALC] Position calculation - Window: ({win.left}, {win.top}), Widget absolute: ({pos_x}, {pos_y}), Relative: ({relative_x}, {relative_y})")
            
            # Обновляем позицию через storage
            if self.storage.update_binding_position(self.bindings, binding_id, relative_x, relative_y):
                self.save_bindings()
                self.logger.info(f"BinderManager: [MOVE_SUCCESS] Successfully updated and saved relative position ({relative_x}, {relative_y}) for binding {binding_id}")
            
        except Exception as e:
            self.logger.error(f"BinderManager: [MOVE_ERROR] Error updating binder position for {binding_id}: {e}")
    
    def on_delete_requested(self, binding_id: str):
        """Обработчик запроса на удаление привязки из контекстного меню виджета"""
        from PySide6.QtWidgets import QMessageBox
        
        try:
            # Получаем информацию о привязке для подтверждения
            binding = self.get_binding_by_id(binding_id)
            if not binding:
                self.logger.warning(f"BinderManager: Binding {binding_id} not found for deletion")
                return
                
            app_name = binding.window_identifier.title
            
            # Запрашиваем подтверждение
            reply = QMessageBox.question(
                None,
                "Подтверждение удаления",
                f"Вы уверены, что хотите удалить привязку для '{app_name}'?\n\n"
                f"Это действие нельзя отменить.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                success = self.remove_binding(binding_id)
                if success:
                    self.logger.info(f"BinderManager: Binding {binding_id} successfully deleted via context menu")
                    QMessageBox.information(None, "Успех", f"Привязка для '{app_name}' удалена")
                else:
                    QMessageBox.warning(None, "Ошибка", "Не удалось удалить привязку")
                    
        except Exception as e:
            self.logger.error(f"BinderManager: Error handling delete request for {binding_id}: {e}")
            QMessageBox.critical(None, "Ошибка", f"Произошла ошибка при удалении: {e}")

    def add_binding(self, new_binding: WindowBinding):
        """Добавить новую привязку, используя WindowBinding."""
        self.logger.info(f"BinderManager: [ADD_BINDING] Adding new binding with data: {new_binding}")

        # Добавляем привязку через storage, который теперь принимает WindowBinding
        binding_id = self.storage.add_binding(self.bindings, new_binding)
        if binding_id:
            self.logger.info(f"BinderManager: [BINDING_CREATED] Successfully created binding with ID: {binding_id}")
            self.save_bindings()
            self.create_binder_for_binding(binding_id, self.bindings[binding_id])
            return binding_id
        else:
            self.logger.error("BinderManager: [BINDING_FAILED] Failed to create binding.")
            return None

    def save_bindings(self):
        """Сохранить привязки"""
        self.logger.info(f"BinderManager: [SAVE_BINDINGS] Saving {len(self.bindings)} bindings to storage")
        self.storage.save_bindings(self.bindings)
        self.logger.info("BinderManager: [SAVE_BINDINGS] Bindings saved successfully")

    def load_bindings(self):
        """Загрузить привязки из файла"""
        self.logger.info("BinderManager: [LOAD_BINDINGS] Loading bindings from storage")
        self.bindings = self.storage.load_bindings()
        self.logger.info(f"BinderManager: [LOAD_BINDINGS] Loaded {len(self.bindings)} bindings from storage")
        
        # Логируем детали каждой загруженной привязки
        for binding_id, binding_data in self.bindings.items():
            app_name = binding_data.window_identifier.title
            x, y = binding_data.x, binding_data.y
            pos_x, pos_y = binding_data.pos_x, binding_data.pos_y
            self.logger.debug(f"BinderManager: [LOADED_BINDING] ID: {binding_id}, App: '{app_name}', Window: ({x}, {y}), Position: ({pos_x}, {pos_y})")
        
        # Создаем виджеты для всех загруженных привязок
        for binding_id, binding_data in self.bindings.items():
            self.create_binder_for_binding(binding_id, binding_data)

    def create_binder_for_binding(self, binding_id, binding_data: WindowBinding):
        """Создать виджет для существующей привязки."""
        # Данные теперь берутся напрямую из объекта WindowBinding
        app_name = binding_data.window_identifier.title
        x = binding_data.x
        y = binding_data.y
        pos_x = binding_data.pos_x
        pos_y = binding_data.pos_y

        self.logger.info(f"BinderManager: [LOAD_BINDING] Loading binding {binding_id} - App: '{app_name}', Data: x={x}, y={y}, pos_x={pos_x}, pos_y={pos_y}")
        self.logger.debug(f"BinderManager: [BINDING_FULL_DATA] Full binding data for {binding_id}: {binding_data.to_dict()}")

        # Используем расширенную идентификацию для поиска окна
        window = window_identification_service.find_window(binding_data.window_identifier)
        if window:
            self.logger.info(f"BinderManager: Found window using enhanced identification: {window.title}")
            # Обновляем app_name, если заголовок окна изменился
            if window.title != app_name:
                self.logger.info(f"BinderManager: Updating app_name from '{app_name}' to '{window.title}'")
                app_name = window.title
                # Обновляем данные в самом объекте привязки и сохраняем
                binding_data.window_identifier.title = app_name
                self.save_bindings()
        else:
            self.logger.warning(f"BinderManager: Window identification failed for binding {binding_id}, widget may not appear correctly.")

        # Создаем SelectedWindowData для передачи в widget_manager
        # Используем идентификатор из объекта binding_data
        data = SelectedWindowData(
            identifier=binding_data.window_identifier,
            x=x,
            y=y,
            pos_x=pos_x,
            pos_y=pos_y
        )

        widget = self.widget_manager.create_binder(binding_id, data)
        if not widget:
            self.logger.warning(f"BinderManager: Failed to create widget for binding {binding_id} ('{app_name}')")
    
    def test_window_identification(self, binding_id: str) -> bool:
        """Тестировать идентификацию окна для привязки"""
        if binding_id not in self.bindings:
            return False
        
        binding_data = self.bindings[binding_id]
        enhanced_binding_data = binding_data.get('_enhanced_binding')
        
        if enhanced_binding_data:
            try:
                # Восстанавливаем объект WindowBinding из словаря
                from window_binder.models.binding_model import WindowBinding
                enhanced_binding = WindowBinding.from_dict(enhanced_binding_data)
                window = window_identification_service.find_window(enhanced_binding.window_identifier)
                return window is not None
            except Exception as e:
                self.logger.error(f"BinderManager: Error testing identification: {e}")
        
        # Fallback к стандартной идентификации
        app_name = binding_data['app_name']
        windows = gw.getWindowsWithTitle(app_name)
        return len(windows) > 0
    def show_settings(self, existing_binding_id: str = None):
        """Показать диалог настроек для создания новой привязки или редактирования существующей"""
        self.logger.info(f"BinderManager: Opening settings dialog (editing: {existing_binding_id is not None})")
        
        # Подготавливаем данные для редактирования
        existing_binding = None
        if existing_binding_id and existing_binding_id in self.bindings:
            binding = self.bindings[existing_binding_id]
            # Проверяем, есть ли расширенные данные
            if '_enhanced_binding' in binding:
                # Восстанавливаем объект WindowBinding из словаря
                from window_binder.models.binding_model import WindowBinding
                existing_binding = WindowBinding.from_dict(binding['_enhanced_binding'])
        
        dialog = EnhancedSettingsDialog(existing_binding=existing_binding)
        
        # Подключаем обработчик результата
        dialog.result_ready.connect(self._handle_settings_result)
        self.logger.info("BinderManager: Connected result_ready signal to _handle_settings_result")
        
        result = dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            self.logger.info("BinderManager: Settings dialog accepted")
        else:
            self.logger.info("BinderManager: Settings dialog cancelled")
    
    def show_management_dialog(self):
        """Показать диалог управления привязками"""
        from window_binder.binding_management_dialog import BindingManagementDialog
        
        self.logger.info("BinderManager: Opening binding management dialog")
        
        dialog = BindingManagementDialog(self)
        dialog.exec()
        
        self.logger.info("BinderManager: Binding management dialog closed")
    
    def _handle_settings_result(self, binding: WindowBinding):
        """Обработать результат из диалога настроек (принимает WindowBinding)"""
        self.logger.info(f"BinderManager: [SIGNAL_RECEIVED] Received result_ready signal with WindowBinding: {binding.id}")
        self.logger.debug(f"BinderManager: [RESULT_DATA] Received binding data: {binding.to_dict()}")

        try:
            is_update = binding.id and binding.id in self.bindings

            if is_update:
                # Обновляем существующую привязку
                self.logger.info(f"BinderManager: [UPDATE_BINDING] Updating existing binding - ID: {binding.id}")
                
                # update_binding принимает **kwargs, поэтому мы распаковываем словарь
                if self.update_binding(binding.id, **binding.to_dict()):
                    # Обновляем позицию виджета
                    self.widget_manager.update_widget_position(binding.id, binding.pos_x, binding.pos_y)
                    self.logger.info(f"BinderManager: Successfully updated binding {binding.id}")
                else:
                    self.logger.error(f"BinderManager: Failed to update binding {binding.id}")
            else:
                # Добавляем новую привязку
                self.logger.info("BinderManager: [ADD_NEW_BINDING] Adding new binding from WindowBinding object")
                
                new_binding_id = self.add_binding(binding)
                if new_binding_id:
                    self.logger.info(f"BinderManager: Successfully created binding {new_binding_id}")
                else:
                    self.logger.error(f"BinderManager: Failed to create binding for '{binding.window_identifier.title}'")

        except Exception as e:
            self.logger.error(f"BinderManager: Error processing settings result: {e}")
            QMessageBox.warning(None, "Ошибка", f"Произошла ошибка при обработке настроек: {e}")
    
    def _save_enhanced_binding(self, binding_id: str, enhanced_binding: WindowBinding):
        """Сохранить расширенные данные привязки"""
        try:
            # Обновляем основную привязку с дополнительными данными
            if binding_id in self.bindings:
                # Преобразуем WindowBinding в словарь для JSON-сериализации
                self.bindings[binding_id]['_enhanced_binding'] = enhanced_binding.to_dict()
                self.save_bindings()
                
            self.logger.info(f"BinderManager: Saved enhanced binding data for {binding_id}")
        except Exception as e:
            self.logger.error(f"BinderManager: Error saving enhanced binding: {e}")

    def hide_all_binders(self):
        """Скрыть все виджеты привязок"""
        self.widget_manager.hide_all_widgets()

    def show_all_binders(self):
        """Показать все виджеты привязок"""
        self.widget_manager.show_all_widgets()
    
    def remove_binding(self, binding_id: str) -> bool:
        """Удалить привязку"""
        # Удаляем виджет
        widget_removed = self.widget_manager.remove_widget(binding_id)
        
        # Удаляем данные привязки
        binding_removed = self.storage.remove_binding(self.bindings, binding_id)
        
        if binding_removed:
            self.save_bindings()
            self.logger.info(f"Successfully removed binding {binding_id}")
            return True
        else:
            self.logger.error(f"Failed to remove binding {binding_id}")
            return False
    
    def update_binding(self, binding_id: str, **kwargs) -> bool:
        """Обновить данные привязки"""
        self.logger.info(f"BinderManager: [UPDATE_BINDING] Updating binding {binding_id} with data: {kwargs}")
        if self.storage.update_binding(self.bindings, binding_id, **kwargs):
            self.logger.info(f"BinderManager: [UPDATE_BINDING] Successfully updated binding {binding_id}")
            self.save_bindings()
            return True
        self.logger.error(f"BinderManager: [UPDATE_BINDING] Failed to update binding {binding_id}")
        return False
    
    def get_binding_by_id(self, binding_id: str) -> Optional[WindowBinding]:
        """Получить объект WindowBinding по его ID."""
        return self.bindings.get(binding_id)
    
    def get_all_bindings(self) -> list[WindowBinding]:
        """Получить все привязки в виде списка объектов WindowBinding."""
        self.logger.info(f"BinderManager: [GET_ALL_BINDINGS] Returning {len(self.bindings)} bindings as a list of objects")

        # Логируем детали каждой привязки, используя атрибуты объекта
        for binding_id, binding_data in self.bindings.items():
            # self.bindings теперь содержит объекты WindowBinding, доступ к данным через атрибуты
            app_name = binding_data.window_identifier.title
            x, y = binding_data.x, binding_data.y
            pos_x, pos_y = binding_data.pos_x, binding_data.pos_y
            self.logger.debug(f"BinderManager: [BINDING_INFO] ID: {binding_id}, App: '{app_name}', Window: ({x}, {y}), Position: ({pos_x}, {pos_y})")

        return list(self.bindings.values())
    
    def cleanup(self):
        """Очистить все ресурсы"""
        self.widget_manager.cleanup()
        self.logger.info("BinderManager cleanup completed")