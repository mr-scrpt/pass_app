from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QCheckBox,
    QSpinBox
)
from PySide6.QtGui import QKeyEvent

from utils import generate_password

class PasswordGeneratorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Password Generator")
        self.setMinimumWidth(400)

        # --- Widgets ---
        self.password_display = QLineEdit()
        self.password_display.setReadOnly(True)
        self.password_display.setStyleSheet("font-size: 16px;")

        self.length_label = QLabel("Length:")
        self.length_spinbox = QSpinBox()
        self.length_spinbox.setRange(4, 28)
        self.length_spinbox.setValue(14)

        self.mixed_case_checkbox = QCheckBox("Include Mixed Case (A-Z)")
        self.mixed_case_checkbox.setChecked(True)

        self.symbols_checkbox = QCheckBox("Include Symbols (!@#$)")
        self.symbols_checkbox.setChecked(True)

        self.copy_button = QPushButton("Copy & Close")
        self.status_label = QLabel("")

        # --- Layout ---
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.password_display)

        options_layout = QHBoxLayout()
        options_layout.addWidget(self.length_label)
        options_layout.addWidget(self.length_spinbox)
        options_layout.addStretch()
        main_layout.addLayout(options_layout)

        main_layout.addWidget(self.mixed_case_checkbox)
        main_layout.addWidget(self.symbols_checkbox)
        main_layout.addStretch()
        main_layout.addWidget(self.status_label)
        main_layout.addWidget(self.copy_button)

        # --- Connections & Initial State ---
        self.length_spinbox.valueChanged.connect(self._regenerate_password)
        self.mixed_case_checkbox.stateChanged.connect(self._regenerate_password)
        self.symbols_checkbox.stateChanged.connect(self._regenerate_password)
        self.copy_button.clicked.connect(self.copy_and_close)

        self._regenerate_password()
        self.password_display.setFocus()
        self.password_display.selectAll()

    def _regenerate_password(self):
        password = generate_password(
            length=self.length_spinbox.value(),
            use_mixed_case=self.mixed_case_checkbox.isChecked(),
            use_symbols=self.symbols_checkbox.isChecked()
        )
        self.password_display.setText(password)

    def copy_to_clipboard(self):
        QApplication.clipboard().setText(self.password_display.text())
        self.status_label.setText("Copied!")
        QTimer.singleShot(2000, lambda: self.status_label.setText(""))

    def copy_and_close(self):
        self.copy_to_clipboard()
        self.accept()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Escape:
            self.reject()
        elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_C:
            self.copy_to_clipboard()
        else:
            super().keyPressEvent(event)
