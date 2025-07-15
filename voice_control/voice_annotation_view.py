import logging
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QProgressBar, QApplication, QSizePolicy
from PySide6.QtCore import Signal, Qt, QPropertyAnimation, QSize, QTimer
from PySide6.QtGui import QIcon

# Предполагается, что icons_rc.py будет сгенерирован в указанной директории
# и Screph_new (или родительская директория) находится в PYTHONPATH
from assets import icons_rc

logger = logging.getLogger(__name__)

class VoiceAnnotationView(QWidget):
    text_set = Signal(str)
    record_button_pressed = Signal()
    settings_button_clicked = Signal()
    done_button_clicked = Signal()
    close_button_clicked = Signal()
    text_changed_signal = Signal(str) # Сигнал об изменении текста

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self._init_ui()

    def retranslate_ui(self):
        self.settings_button.setToolTip(self.tr("Открыть настройки распознавания"))
        self.done_button.setToolTip(self.tr("Завершить аннотацию (Enter)"))
        self.text_edit.setPlaceholderText(self.tr("Здесь появится распознанный текст..."))
        
    def _init_ui(self):
        # Основной макет
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(5)
        
        # Верхняя часть с кнопкой и индикатором звука
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(5)
        
        # Кнопка записи с иконкой
        self.record_button = QPushButton()
        self.record_button.setCheckable(True)
        self.record_button.setFixedSize(20, 20) # Размер кнопки
        # Устанавливаем IconSize отдельно от setFixedSize, если иконка должна быть меньше кнопки
        self.record_button.setIconSize(QSize(14, 14)) # Размер самой иконки
        self.record_button.pressed.connect(self.record_button_pressed)

        # Анимация пульсации для кнопки
        self.pulse_animation = QPropertyAnimation(self.record_button, b"styleSheet")
        self.pulse_animation.setDuration(800)  # Длительность анимации в мс
        self.pulse_animation.setLoopCount(-1)  # Бесконечное повторение

        self._update_record_button_style(False) # Начальное состояние - не запись

        # Индикатор уровня звука (тонкая шкала)
        self.sound_level = QProgressBar()
        self.sound_level.setFixedHeight(3)  # Устанавливаем толщину 3 пикселя
        self.sound_level.setTextVisible(False)
        self.sound_level.setStyleSheet("""
            QProgressBar {
                background-color: rgba(200, 200, 200, 50);
                border: none;
                border-radius: 1px;
            }
            QProgressBar::chunk {
                background-color: rgba(0, 160, 230, 150);
                border-radius: 1px;
            }
        """)
        
        top_layout.addWidget(self.record_button)
        top_layout.addWidget(self.sound_level, 1)  # Индикатор занимает все оставшееся пространство
        
        # Кнопка Настройки
        self.settings_button = QPushButton()
        self.settings_button.setFixedSize(20, 20)
        self.settings_button.setIcon(QIcon(":/icons/settings_va.svg"))
        self.settings_button.setIconSize(QSize(14, 14))
        self.settings_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(220, 220, 220, 200); /* Светло-серый полупрозрачный */
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover { background-color: rgba(200, 200, 200, 220); /* Чуть темнее при наведении */ }
        """)
        self.settings_button.clicked.connect(self.settings_button_clicked)
        top_layout.addWidget(self.settings_button)

        # Кнопка Готово
        self.done_button = QPushButton()
        self.done_button.setFixedSize(20, 20)
        self.done_button.setIcon(QIcon(":/icons/action_done.svg"))
        self.done_button.setIconSize(QSize(14, 14))
        self.done_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(220, 220, 220, 200); /* Светло-серый полупрозрачный */
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover { background-color: rgba(200, 200, 200, 220); /* Чуть темнее при наведении */ }
        """)

        # Кнопка Закрыть
        self.close_button = QPushButton()
        self.close_button.setFixedSize(20, 20)
        self.close_button.setIcon(QIcon(":/icons/close_va.svg"))
        self.close_button.setIconSize(QSize(14, 14))
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(220, 220, 220, 200); /* Светло-серый полупрозрачный */
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover { background-color: rgba(200, 200, 200, 220); /* Чуть темнее при наведении */ }
        """)
        self.done_button.clicked.connect(self.done_button_clicked.emit)
        top_layout.addWidget(self.done_button)

        self.close_button.clicked.connect(self.close_button_clicked.emit)
        top_layout.addWidget(self.close_button)

        # Текстовое поле для отображения и редактирования распознанного текста
        self.text_edit = QTextEdit()
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: rgba(255, 255, 255, 200);
                border: 1px solid rgba(200, 200, 200, 100);
                border-radius: 4px;
                padding: 4px;
            }
        """)
        self.text_edit.setVisible(False)  # Изначально скрываем текстовое поле
        self.text_edit.textChanged.connect(self._on_text_changed)

        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.text_edit, 1)
        self.setLayout(main_layout)

        self.setMinimumHeight(40) # Начальная высота
        self.resize(300, 40) # Начальный размер

        self.retranslate_ui()

    def _on_text_changed(self):
        self.text_changed_signal.emit(self.text_edit.toPlainText())
        self.logger.debug(f"voise_annotation_view: Текст в View изменен: {self.text_edit.toPlainText()}")

    def get_current_text(self) -> str:
        return self.text_edit.toPlainText()

    def set_current_text(self, text: str):
        # Предотвращаем рекурсивный вызов, если текст тот же
        if self.text_edit.toPlainText() != text:
            self.text_edit.setText(text)
            self.text_set.emit(text)

    def set_placeholder_text(self, text: str):
        self.text_edit.setPlaceholderText(text)

    def show_text_edit(self, show: bool):
        self.text_edit.setVisible(show)
        if show:
            self.text_edit.setMinimumHeight(60)  # Минимальная высота для текстового поля
            self.setMinimumHeight(100) # Общая минимальная высота View
            # Разрешаем виджету расширяться по вертикали
            self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.MinimumExpanding)
        else:
            self.text_edit.setMinimumHeight(0)
            self.setMinimumHeight(40)    # Компактный размер
            # Возвращаем политику размеров по умолчанию или фиксированную
            self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        
        # Обновляем геометрию самого View и его родителя через QTimer
        QTimer.singleShot(0, self._adjust_size_and_parent)

    def _adjust_size_and_parent(self):
        """Корректирует размер текущего виджета и его родителя."""
        self.adjustSize()
        parent = self.parentWidget()
        if parent:
            parent.adjustSize()

    def retranslate_ui(self):
        """Обновляет переводы интерфейса."""
        # В данном виджете нет текстовых элементов для перевода,
        # но метод нужен для соответствия паттерну
        pass

    def reset_ui(self):
        """Сбрасывает элементы интерфейса View к их начальному состоянию."""
        logger.debug(self.tr("Resetting VoiceAnnotationView UI."))
        self.show_text_edit(False)  # Скрываем текстовое поле и возвращаем компактный размер
        self.text_edit.clear()      # Очищаем текстовое поле
        self._update_record_button_style(is_recording=False) # Возвращаем кнопку в состояние "не запись"
        #self.status_label.setText("")    # Очищаем метку статуса
        # Можно добавить сброс иконок или других элементов, если они меняются

    def _update_record_button_style(self, is_recording: bool):
        if is_recording:
            self.record_button.setChecked(True)
            # Используем QIcon для состояния записи
            self.record_button.setIcon(QIcon(":/icons/record_stop.svg"))
            record_icon_style = """
                QPushButton {
                    /* background-color: #ff4444; */
                    border-radius: 10px;
                    border: none;
                    /* image: url(:/icons/record_stop.svg); --- Управляется через setIcon */
                }
                QPushButton:hover {
                    /* background-color: #ff6666; */
                }
            """
            self.record_button.setStyleSheet(record_icon_style)
            
            pulse_start_style = """
                QPushButton {
                    /* background-color: #ff4444; */
                    border-radius: 10px;
                    border: none;
                    /* image: url(:/icons/record_stop.svg); */
                }
            """
            pulse_end_style = """
                QPushButton {
                    /* background-color: #990000; */ /* Затемненный для пульсации */
                    border-radius: 10px;
                    border: none;
                    /* image: url(:/icons/record_stop.svg); */
                }
            """
            self.pulse_animation.setStartValue(pulse_start_style)
            self.pulse_animation.setEndValue(pulse_end_style)
            self.pulse_animation.start()
        else:
            self.record_button.setChecked(False)
            # Используем QIcon для состояния НЕ записи
            self.record_button.setIcon(QIcon(":/icons/record_start.svg"))
            self.pulse_animation.stop() # Останавливаем анимацию
            initial_record_icon_style = """
                QPushButton {
                    background-color: rgba(220, 220, 220, 200); /* Светло-серый полупрозрачный */
                    border-radius: 10px;
                    border: none;
                    /* image: url(:/icons/record_start.svg); --- Управляется через setIcon */
                }
                QPushButton:hover {
                    background-color: rgba(200, 200, 200, 220); /* Чуть темнее при наведении */
                }
            """
            self.record_button.setStyleSheet(initial_record_icon_style)

    def set_sound_level(self, level: int):
        self.sound_level.setValue(level)

    def get_text_edit_widget(self):
        return self.text_edit

    def clear_text_edit(self):
        """Очищает текстовое поле."""
        self.text_edit.clear()

# Пример использования, если нужно запустить только View
if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    view = VoiceAnnotationView()
    view.show()
    sys.exit(app.exec())
