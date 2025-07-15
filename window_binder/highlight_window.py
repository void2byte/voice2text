from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt

class HighlightWindow(QLabel):
    """Виджет для отображения рамки подсветки вокруг окна."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("border: 2px solid red;")

    def highlight(self, rect):
        """Показать и разместить рамку по заданным координатам."""
        self.setGeometry(rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1])
        self.show()

    def hide_highlight(self):
        """Скрыть рамку."""
        self.hide()