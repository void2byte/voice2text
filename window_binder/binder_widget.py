import os
from PySide6.QtWidgets import QPushButton, QMenu
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QIcon

from voice_control.voice_annotation_view import VoiceAnnotationView

class BinderWidget(QPushButton):
    start_recognition = Signal(str)
    stop_recognition = Signal(str)
    moved = Signal(str, int, int)
    delete_requested = Signal(str)  # Новый сигнал для запроса удаления

    def __init__(self, binding_id, parent=None):
        super().__init__(parent)
        self.binding_id = binding_id
        self.is_recording = False
        self.dragging = False
        self.offset = None

        # Загрузка иконок
        self.start_icon = QIcon(os.path.abspath("assets/icons/record_start.svg"))
        self.stop_icon = QIcon(os.path.abspath("assets/icons/record_stop.svg"))

        self.setIcon(self.start_icon)
        self.setText("") # Убираем текст
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(30, 30)
        self.clicked.connect(self.on_click)
        
        # Включаем контекстное меню
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        

    def on_recording_finished(self):
        self.stop_recognition.emit(self.binding_id)
        self.setIcon(self.start_icon)
        self.is_recording = False

    def on_click(self):
        if self.is_recording:
            self.stop_recognition.emit(self.binding_id)
            self.setIcon(self.start_icon)
        else:
            self.start_recognition.emit(self.binding_id)
            self.setIcon(self.stop_icon)
        self.is_recording = not self.is_recording

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.offset = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(self.mapToParent(event.pos() - self.offset))
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            self.moved.emit(self.binding_id, self.pos().x(), self.pos().y())
        super().mouseReleaseEvent(event)
    
    def show_context_menu(self, position):
        """Показать контекстное меню"""
        context_menu = QMenu(self)
        
        # Действие для удаления
        delete_action = QAction("Удалить привязку", self)
        delete_action.triggered.connect(lambda: self.delete_requested.emit(self.binding_id))
        context_menu.addAction(delete_action)
        
        # Показываем меню в глобальных координатах
        context_menu.exec(self.mapToGlobal(position))