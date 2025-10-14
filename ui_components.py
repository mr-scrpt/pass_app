from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel

from ui_theme import extra

class HotkeyHelpWidget(QWidget):
    def __init__(self, text=""):
        super().__init__()
        self.setStyleSheet(f"background-color: {extra['primaryColor']}; padding: 8px;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 5, 15, 5)
        self.label = QLabel(text)
        self.label.setStyleSheet(f"color: {extra['secondaryColor']}; font-size: 12px; font-weight: bold;")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addStretch(1)
        layout.addWidget(self.label)
        layout.addStretch(1)

    def setText(self, text):
        self.label.setText(text)
