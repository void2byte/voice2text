"""
Модуль с виджетом настроек файлов и форматирования.
"""

import logging
import datetime
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QCheckBox, QGroupBox, QLineEdit, QRadioButton,
    QButtonGroup, QSlider, QPushButton
)

logger = logging.getLogger(__name__)

class FileSettingsTab(QWidget):
    """Вкладка настроек файлов"""
    
    settings_changed = Signal(dict)
    
    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self._init_ui()
        self._load_settings()
    
    def _init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Группа настроек имени файла
        self.naming_group = QGroupBox(self.tr("Именование файлов"))
        naming_layout = QVBoxLayout()
        self.naming_group.setLayout(naming_layout)
        
        # Добавление временной метки
        self.add_timestamp = QCheckBox(self.tr("Добавлять временную метку к имени файла"))
        naming_layout.addWidget(self.add_timestamp)
        
        # Формат временной метки
        timestamp_layout = QHBoxLayout()
        self.timestamp_label = QLabel(self.tr("Формат временной метки:"))
        self.timestamp_format = QLineEdit()
        self.timestamp_preview = QLabel()
        
        timestamp_layout.addWidget(self.timestamp_label)
        timestamp_layout.addWidget(self.timestamp_format)
        naming_layout.addLayout(timestamp_layout)
        
        # Предпросмотр временной метки
        preview_layout = QHBoxLayout()
        self.preview_label = QLabel(self.tr("Пример:"))
        preview_layout.addWidget(self.preview_label)
        preview_layout.addWidget(self.timestamp_preview)
        naming_layout.addLayout(preview_layout)
        
        # Создание подпапок по дате
        self.create_subdirs = QCheckBox(self.tr("Создавать подпапки по дате"))
        naming_layout.addWidget(self.create_subdirs)
        
        layout.addWidget(self.naming_group)
        
        # Группа настроек формата файла
        self.format_group_widget = QGroupBox(self.tr("Формат изображения"))
        format_layout = QVBoxLayout()
        self.format_group_widget.setLayout(format_layout)
        
        # Выбор формата
        self.format_group = QButtonGroup(self)
        self.png_format = QRadioButton(self.tr("PNG (без потерь)"))
        self.jpg_format = QRadioButton(self.tr("JPEG (с сжатием)"))
        
        format_layout.addWidget(self.png_format)
        format_layout.addWidget(self.jpg_format)
        
        self.format_group.addButton(self.png_format)
        self.format_group.addButton(self.jpg_format)
        
        # Настройки JPEG
        jpeg_layout = QHBoxLayout()
        self.jpeg_label = QLabel(self.tr("Качество JPEG:"))
        self.jpeg_quality = QSlider(Qt.Orientation.Horizontal)
        self.jpeg_quality.setRange(0, 100)
        self.jpeg_quality.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.jpeg_quality.setTickInterval(10)
        
        self.quality_label = QLabel("90%")
        self.jpeg_quality.valueChanged.connect(
            lambda v: self.quality_label.setText(f"{v}%")
        )
        
        jpeg_layout.addWidget(self.jpeg_label)
        jpeg_layout.addWidget(self.jpeg_quality)
        jpeg_layout.addWidget(self.quality_label)
        
        format_layout.addLayout(jpeg_layout)
        
        layout.addWidget(self.format_group_widget)
        layout.addStretch()
        
        # Подключение сигналов
        self.add_timestamp.toggled.connect(self._on_settings_changed)
        self.timestamp_format.textChanged.connect(self._update_timestamp_preview)
        self.timestamp_format.textChanged.connect(self._on_settings_changed)
        self.create_subdirs.toggled.connect(self._on_settings_changed)
        self.png_format.toggled.connect(self._on_settings_changed)
        self.jpg_format.toggled.connect(self._on_settings_changed)
        self.jpeg_quality.valueChanged.connect(self._on_settings_changed)
        
        self.retranslate_ui()
    
    def _load_settings(self):
        """Загрузка настроек"""
        # Настройки временной метки
        self.add_timestamp.setChecked(
            self.settings_manager.get_setting("files/add_timestamp", True)
        )
        self.timestamp_format.setText(
            self.settings_manager.get_setting("files/timestamp_format", "%Y%m%d_%H%M%S")
        )
        self._update_timestamp_preview()
        
        # Подпапки по дате
        self.create_subdirs.setChecked(
            self.settings_manager.get_setting("files/create_subdirs_by_date", False)
        )
        
        # Формат изображения
        image_format = self.settings_manager.get_setting("files/image_format", "png")
        if image_format == "jpg":
            self.jpg_format.setChecked(True)
        else:
            self.png_format.setChecked(True)
        
        # Качество JPEG
        self.jpeg_quality.setValue(
            self.settings_manager.get_setting("files/jpg_quality", 90)
        )
        
        # Активация/деактивация слайдера качества в зависимости от формата
        self.jpeg_quality.setEnabled(image_format == "jpg")
    
    def _update_timestamp_preview(self):
        """Обновление предпросмотра временной метки"""
        try:
            timestamp = datetime.datetime.now().strftime(self.timestamp_format.text())
            self.timestamp_preview.setText(f"screenshot_{timestamp}.png")
            self.timestamp_preview.setStyleSheet("")
        except ValueError as e:
            self.timestamp_preview.setText(self.tr("Неверный формат!"))
            self.timestamp_preview.setStyleSheet("color: red;")
    
    def _on_settings_changed(self):
        """Обработчик изменения настроек"""
        # Активация/деактивация слайдера качества
        self.jpeg_quality.setEnabled(self.jpg_format.isChecked())
        
        settings = {
            "files": {
                "add_timestamp": self.add_timestamp.isChecked(),
                "timestamp_format": self.timestamp_format.text(),
                "create_subdirs_by_date": self.create_subdirs.isChecked(),
                "image_format": "jpg" if self.jpg_format.isChecked() else "png",
                "jpg_quality": self.jpeg_quality.value()
            }
        }
    
    def retranslate_ui(self):
        """Обновляет переводы интерфейса"""
        # Обновляем тексты групп
        self.naming_group.setTitle(self.tr("Именование файлов"))
        self.format_group_widget.setTitle(self.tr("Формат изображения"))
        
        # Обновляем чекбоксы
        self.add_timestamp.setText(self.tr("Добавлять временную метку к имени файла"))
        self.create_subdirs.setText(self.tr("Создавать подпапки по дате"))
        
        # Обновляем метки
        self.timestamp_label.setText(self.tr("Формат временной метки:"))
        self.preview_label.setText(self.tr("Пример:"))
        self.jpeg_label.setText(self.tr("Качество JPEG:"))
        
        # Обновляем радиокнопки
        self.png_format.setText(self.tr("PNG (без потерь)"))
        self.jpg_format.setText(self.tr("JPEG (с сжатием)"))
        
        # Обновляем предпросмотр временной метки
        self._update_timestamp_preview()
        self.settings_changed.emit(settings)
    
    def get_settings(self) -> dict:
        """Получение текущих настроек вкладки"""
        return {
            "files": {
                "add_timestamp": self.add_timestamp.isChecked(),
                "timestamp_format": self.timestamp_format.text(),
                "create_subdirs_by_date": self.create_subdirs.isChecked(),
                "image_format": "jpg" if self.jpg_format.isChecked() else "png",
                "jpg_quality": self.jpeg_quality.value()
            }
        }
