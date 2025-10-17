import qtawesome as qta
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from components.hotkey_help import HotkeyHelpWidget
from fa_keyboard_icons import get_fa_keyboard_icon
from ui_theme import extra


class ConfirmationDialog(QDialog):
    def __init__(
        self, parent=None, text="Are you sure?", confirm_text="Confirm", cancel_text="Cancel", third_button_text=None
    ):
        super().__init__(parent)
        self.setWindowTitle("Confirm Action")
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        self.message_label = QLabel(text)
        self.message_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.message_label)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        # Cancel button with red icon and red text
        self.cancel_button = QPushButton(f"  {cancel_text}")
        self.cancel_button.setIcon(get_fa_keyboard_icon("escape", color="#f38ba8", size=96))  # Red
        self.cancel_button.setIconSize(QSize(32, 32))
        self.cancel_button.setMinimumHeight(50)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(243, 139, 168, 0.15);
                color: #f38ba8;
                border: 2px solid #f38ba8;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(243, 139, 168, 0.25);
                border-color: #f5a3b8;
                color: #f5a3b8;
            }
            QPushButton:pressed {
                background-color: rgba(243, 139, 168, 0.35);
            }
        """)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        if third_button_text:
            # Save button with yellow icon and yellow text
            self.third_button = QPushButton(f"  {third_button_text}")
            self.third_button.setIcon(qta.icon("fa5s.save", color="#f9e2af"))  # Yellow
            self.third_button.setIconSize(QSize(24, 24))
            self.third_button.setMinimumHeight(50)
            self.third_button.setStyleSheet("""
                QPushButton {
                    background-color: rgba(249, 226, 175, 0.15);
                    color: #f9e2af;
                    border: 2px solid #f9e2af;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: rgba(249, 226, 175, 0.25);
                    border-color: #fae8bf;
                    color: #fae8bf;
                }
                QPushButton:pressed {
                    background-color: rgba(249, 226, 175, 0.35);
                }
            """)
            self.third_button.clicked.connect(self.on_third_button_clicked)
            button_layout.addWidget(self.third_button)
            self.third_button_role = 2  # A custom role

        # Confirm button with green icon and green text
        self.confirm_button = QPushButton(f"  {confirm_text}")
        self.confirm_button.setIcon(get_fa_keyboard_icon("enter", color="#a6e3a1", size=96))  # Green
        self.confirm_button.setIconSize(QSize(32, 32))
        self.confirm_button.setMinimumHeight(50)
        self.confirm_button.setDefault(True)
        self.confirm_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(166, 227, 161, 0.15);
                color: #a6e3a1;
                border: 2px solid #a6e3a1;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(166, 227, 161, 0.25);
                border-color: #b6e8b1;
                color: #b6e8b1;
            }
            QPushButton:pressed {
                background-color: rgba(166, 227, 161, 0.35);
            }
            QPushButton:default {
                border-width: 3px;
            }
        """)
        self.confirm_button.clicked.connect(self.accept)
        button_layout.addWidget(self.confirm_button)

        layout.addLayout(button_layout)

        # --- Hotkey Help Widget ---
        if third_button_text:
            # With third button (Save)
            self.help_widget = HotkeyHelpWidget(
                category="Actions", text="Enter - Confirm  |  Ctrl+S - Save  |  Esc - Cancel"
            )
        else:
            # Standard confirmation
            self.help_widget = HotkeyHelpWidget(category="Actions", text="Enter - Confirm  |  Esc - Cancel")
        layout.addWidget(self.help_widget)

        self.setStyleSheet(f"background-color: {extra['secondaryColor']};")

    def on_third_button_clicked(self):
        self.done(self.third_button_role)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Escape:
            self.reject()
        elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_S:
            # Ctrl+S - trigger save button (third button)
            if hasattr(self, "third_button"):
                self.third_button.click()
        else:
            super().keyPressEvent(event)
