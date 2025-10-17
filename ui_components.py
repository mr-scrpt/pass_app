from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QWidget

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


class StyledLineEdit(QLineEdit):
    navigation = Signal(QKeyEvent)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_editing = False
        self.editing_changed = None  # Callback for editing state changes
        self.on_escape_empty = None  # Callback for Esc on empty field

    def set_editing(self, is_editing):
        self._is_editing = is_editing
        self.setReadOnly(not is_editing)
        # Notify about editing state change
        if self.editing_changed:
            self.editing_changed(is_editing)

    def keyPressEvent(self, event):
        if self._is_editing:
            # Esc - exit editing mode (and maybe delete if empty)
            if event.key() == Qt.Key_Escape:
                # Check if empty and call callback
                if not self.text().strip() and self.on_escape_empty:
                    self.on_escape_empty()
                self.set_editing(False)
                event.accept()
                return
            # Enter - exit editing mode
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                self.set_editing(False)
                event.accept()
                return
            # Normal text editing
            super().keyPressEvent(event)
        else:
            self.navigation.emit(event)
