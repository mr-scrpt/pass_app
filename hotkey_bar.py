from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from ui_theme import extra


class HotkeyBar(QWidget):
    """A reusable widget for displaying a bar of hotkey hints."""

    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background-color: {extra['secondaryColor']}; padding: 8px; border-top: 1px solid #45475a;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 5, 15, 5)

        self.label = QLabel("")
        self.label.setStyleSheet(f"color: {extra['primaryTextColor']}; font-size: 12px;")
        self.label.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.label)

    def update_hotkeys(self, hotkey_map):
        """Updates the displayed hotkeys from a dictionary."""
        parts = []
        for key, desc in hotkey_map.items():
            parts.append(f"<b>{key}:</b> {desc}")

        hotkey_text = "&nbsp;&nbsp;".join(parts)
        self.label.setText(hotkey_text)
