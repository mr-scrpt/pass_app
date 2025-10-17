from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from fa_keyboard_icons import get_fa_keyboard_icon
from utils import generate_password


class PasswordGeneratorDialog(QDialog):
    @staticmethod
    def get_hotkey_info():
        """Return hotkey help text for this dialog"""
        return {
            "category_nav": "Navigation",
            "nav": "Up/Down - Navigate fields  |  Left/Right - Adjust length  |  Space - Toggle option",
            "category_action": "Actions",
            "action": "Enter - Copy & close  |  Ctrl+C - Copy  |  Esc - Cancel",
        }

    def __init__(self, parent=None, show_status_callback=None):
        super().__init__(parent)
        self.setWindowTitle("Password Generator")
        self.setMinimumWidth(400)
        self.show_status_callback = show_status_callback

        # --- Widgets ---
        self.password_display = QLineEdit()
        self.password_display.setReadOnly(True)
        self.password_display.setStyleSheet("font-size: 16px;")
        self.password_display.setFixedHeight(32)  # Set fixed height

        self.length_spinbox = QSpinBox()
        self.length_spinbox.setRange(4, 28)
        self.length_spinbox.setValue(14)
        self.length_spinbox.setMaximumWidth(60)
        self.length_spinbox.setFixedHeight(32)  # Match password display height
        self.length_spinbox.setFocusPolicy(Qt.NoFocus)  # Prevent focus on spinbox
        self.length_spinbox.setButtonSymbols(QSpinBox.NoButtons)  # Remove up/down arrows
        self.length_spinbox.setStyleSheet("font-size: 16px;")  # Match password display font size

        self.mixed_case_checkbox = QCheckBox("Include Mixed Case (A-Z)")
        self.mixed_case_checkbox.setChecked(True)

        self.symbols_checkbox = QCheckBox("Include Symbols (!@#$)")
        self.symbols_checkbox.setChecked(True)

        # Cancel button with ESC icon (red)
        self.cancel_button = QPushButton("  Cancel")
        self.cancel_button.setIcon(get_fa_keyboard_icon("escape", color="#f38ba8", size=96))
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

        # Copy button with Enter icon (green)
        self.copy_button = QPushButton("  Copy & Close")
        self.copy_button.setIcon(get_fa_keyboard_icon("enter", color="#a6e3a1", size=96))
        self.copy_button.setIconSize(QSize(32, 32))
        self.copy_button.setMinimumHeight(50)
        self.copy_button.setStyleSheet("""
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
        """)

        # --- Navigation fields (without spinbox) ---
        self.focusable_fields = [
            self.password_display,
            self.mixed_case_checkbox,
            self.symbols_checkbox,
            self.cancel_button,
            self.copy_button,
        ]
        self.current_focus_index = 0

        # --- Layout ---
        main_layout = QVBoxLayout(self)

        # Password display and length on same line
        password_layout = QHBoxLayout()
        password_layout.addWidget(self.password_display)
        password_layout.addWidget(self.length_spinbox)
        main_layout.addLayout(password_layout)

        main_layout.addWidget(self.mixed_case_checkbox)
        main_layout.addWidget(self.symbols_checkbox)
        main_layout.addStretch()

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.copy_button)
        main_layout.addLayout(button_layout)

        # --- Connections & Initial State ---
        self.length_spinbox.valueChanged.connect(self._regenerate_password)
        self.mixed_case_checkbox.stateChanged.connect(self._regenerate_password)
        self.symbols_checkbox.stateChanged.connect(self._regenerate_password)
        self.cancel_button.clicked.connect(self.reject)
        self.copy_button.clicked.connect(self.copy_and_close)

        # Install event filter on all focusable widgets to intercept arrow keys
        for widget in self.focusable_fields:
            widget.installEventFilter(self)

        self._regenerate_password()
        self._update_focus()

    def _regenerate_password(self):
        password = generate_password(
            length=self.length_spinbox.value(),
            use_mixed_case=self.mixed_case_checkbox.isChecked(),
            use_symbols=self.symbols_checkbox.isChecked(),
        )
        self.password_display.setText(password)

    def _update_focus(self):
        """Update focus to current field and select text if applicable"""
        current_widget = self.focusable_fields[self.current_focus_index]
        current_widget.setFocus()

        # Select all text in password display
        if current_widget == self.password_display:
            self.password_display.selectAll()

    def _navigate_up(self):
        """Navigate to previous field"""
        self.current_focus_index = (self.current_focus_index - 1) % len(self.focusable_fields)
        self._update_focus()

    def _navigate_down(self):
        """Navigate to next field"""
        self.current_focus_index = (self.current_focus_index + 1) % len(self.focusable_fields)
        self._update_focus()

    def _adjust_length(self, delta):
        """Adjust password length by delta"""
        new_value = self.length_spinbox.value() + delta
        if self.length_spinbox.minimum() <= new_value <= self.length_spinbox.maximum():
            self.length_spinbox.setValue(new_value)

    def _toggle_current_checkbox(self):
        """Toggle checkbox if current focused field is a checkbox"""
        current_widget = self.focusable_fields[self.current_focus_index]
        if isinstance(current_widget, QCheckBox):
            current_widget.setChecked(not current_widget.isChecked())

    def copy_to_clipboard(self):
        QApplication.clipboard().setText(self.password_display.text())
        if self.show_status_callback:
            self.show_status_callback("Password copied to clipboard!", "success")

    def copy_and_close(self):
        self.copy_to_clipboard()
        self.accept()

    def eventFilter(self, obj, event):
        """Filter events to intercept arrow keys and special keys before widgets handle them"""
        from PySide6.QtCore import QEvent

        if event.type() == QEvent.KeyPress:
            key = event.key()

            # Handle arrow keys for navigation and length adjustment
            if key in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right):
                if key == Qt.Key_Up:
                    self._navigate_up()
                elif key == Qt.Key_Down:
                    self._navigate_down()
                elif key == Qt.Key_Left:
                    self._adjust_length(-1)
                elif key == Qt.Key_Right:
                    self._adjust_length(1)
                return True  # Event handled, don't propagate

            # Handle Enter - always copy and close
            elif key in (Qt.Key_Return, Qt.Key_Enter):
                self.copy_and_close()
                return True

            # Handle Space - toggle checkboxes only
            elif key == Qt.Key_Space:
                if isinstance(obj, QCheckBox):
                    self._toggle_current_checkbox()
                    return True

            # Handle Ctrl+C
            elif event.modifiers() == Qt.ControlModifier and key == Qt.Key_C:
                self.copy_to_clipboard()
                return True

            # Handle Escape
            elif key == Qt.Key_Escape:
                self.reject()
                return True

        return super().eventFilter(obj, event)

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()

        if key == Qt.Key_Escape:
            self.reject()
            event.accept()
        elif key == Qt.Key_Up:
            self._navigate_up()
            event.accept()
        elif key == Qt.Key_Down:
            self._navigate_down()
            event.accept()
        elif key == Qt.Key_Left:
            self._adjust_length(-1)
            event.accept()
        elif key == Qt.Key_Right:
            self._adjust_length(1)
            event.accept()
        elif key in (Qt.Key_Return, Qt.Key_Enter):
            # Enter always copies and closes
            self.copy_and_close()
            event.accept()
        elif key == Qt.Key_Space:
            # Space only toggles checkboxes
            current_widget = self.focusable_fields[self.current_focus_index]
            if isinstance(current_widget, QCheckBox):
                self._toggle_current_checkbox()
                event.accept()
            else:
                super().keyPressEvent(event)
        elif event.modifiers() == Qt.ControlModifier and key == Qt.Key_C:
            self.copy_to_clipboard()
            event.accept()
        else:
            super().keyPressEvent(event)
