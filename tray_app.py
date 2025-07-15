import sys
import os
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Signal, Slot
import logging
from voice_control.voice_annotation_widget import VoiceAnnotationWidget
from settings_modules.hotkey_manager import HotkeyManager
from settings_modules.hotkey_settings_dialog import HotkeySettingsDialog
from settings_modules.settings_manager import SettingsManager
from window_binder.binder_manager import BinderManager

logger = logging.getLogger(__name__)

class TrayApplication(QApplication):
    # Сигнал для потокобезопасного вызова виджета
    hotkey_pressed = Signal(bool)

    def __init__(self, argv):
        super().__init__(argv)
        logger.info("========================================")
        logger.info("      TrayApplication Initializing      ")
        logger.info("========================================")
        self.setQuitOnLastWindowClosed(False)

        logger.info("TrayApplication.__init__: Initializing SettingsManager")
        self.settings_manager = SettingsManager()
        logger.info("TrayApplication.__init__: SettingsManager initialized")

        logger.info("TrayApplication.__init__: Initializing BinderManager")
        self.binder_manager = BinderManager(self)
        logger.info("TrayApplication.__init__: BinderManager initialized")

        self.widget = VoiceAnnotationWidget(settings_manager=self.settings_manager)
        self.widget.view.text_changed_signal.connect(self.binder_manager.on_recognition_finished)
        self.binder_manager.widget_manager.stop_recognition_signal.connect(self.widget._finalize_annotation)
        logger.info("TrayApplication.__init__: Connected recognition_finished to binder_manager")

        self.create_tray_icon()

    def create_tray_icon(self):
        logger.info("Creating tray icon")
        self.tray_icon = QSystemTrayIcon(self)
        icon_path = os.path.abspath("assets/icons/voice_annotation_action.svg")
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
            logger.info(f"Tray icon set from {icon_path}")
        else:
            logger.error(f"Icon file not found at {icon_path}")

        self.tray_menu = self.create_tray_menu()
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()
        logger.info("Tray icon created and shown")

    def create_tray_menu(self):
        menu = QMenu()
        launch_action = QAction("Запустить виджет", self)
        launch_action.triggered.connect(lambda: self.launch_widget(start_recording=False))
        menu.addAction(launch_action)

        hotkey_settings_action = QAction("Настроить горячие клавиши", self)
        hotkey_settings_action.triggered.connect(self.open_hotkey_settings)
        menu.addAction(hotkey_settings_action)

        recognition_settings_action = QAction("Настройки распознавания", self)
        recognition_settings_action.triggered.connect(self.open_recognition_settings)
        menu.addAction(recognition_settings_action)

        binder_settings_action = QAction("Настроить привязки", self)
        binder_settings_action.triggered.connect(self.open_binder_settings)
        menu.addAction(binder_settings_action)
        
        manage_bindings_action = QAction("Управление привязками", self)
        manage_bindings_action.triggered.connect(self.open_binding_management)
        menu.addAction(manage_bindings_action)

        menu.addSeparator()

        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.quit)
        menu.addAction(exit_action)
        return menu

        # Подключаем сигнал к слоту
        self.hotkey_manager = HotkeyManager()
        self.hotkey_manager.register_hotkey('launch_widget', 'ctrl+shift+space', self.on_hotkey_pressed)

        self.hotkey_pressed.connect(self.launch_widget)




    def open_binder_settings(self):
        self.binder_manager.show_settings()
    
    def open_binding_management(self):
        """Открыть диалог управления привязками"""
        self.binder_manager.show_management_dialog()

    def on_hotkey_pressed(self):
        """Обработчик нажатия горячей клавиши."""
        logger.info("Горячая клавиша нажата!")
        self.hotkey_pressed.emit(True)

    def open_hotkey_settings(self):
        dialog = HotkeySettingsDialog(self.hotkey_manager)
        dialog.exec()

    def open_recognition_settings(self):
        """Открывает окно настроек распознавания речи."""
        if self.widget is None:
            # Если виджет еще не создан, создаем его для доступа к настройкам
            self.widget = VoiceAnnotationWidget(settings_manager=self.settings_manager)
            # Мы не будем показывать основной виджет, только диалог настроек

        # Получаем диалог настроек из виджета
        settings_dialog = self.widget.open_settings_dialog()

        # Подключаемся к сигналу закрытия диалога
        if settings_dialog:
            settings_dialog.finished.connect(self.on_settings_dialog_finished)

    def on_settings_dialog_finished(self):
        """Слот, который вызывается после закрытия диалога настроек."""
        logger.info("Диалог настроек закрыт, перезагружаем распознаватель в виджете...")
        if self.widget:
            self.widget.reload_recognizer()

    @Slot(bool)
    def launch_widget(self, start_recording=False):
        logger.info(f"launch_widget called with start_recording={start_recording}")
        """Запускает и отображает VoiceAnnotationWidget (вызывается в основном потоке)."""
        if self.widget is None:
            self.widget = VoiceAnnotationWidget(settings_manager=self.settings_manager)
            

        
        if not self.widget.isVisible():
            if start_recording:
                self.widget.start_recording_and_show()
            else:
                self.widget.show()
        else:
            # Если виджет уже видим, просто активируем его
            self.widget.activateWindow()