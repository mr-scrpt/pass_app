from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel

class StatusBarWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(15, 2, 15, 2)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)

        self.main_layout.addStretch()
        self.main_layout.addWidget(self.status_label)
        self.main_layout.addStretch()

    def show_status(self, message, toast_type="success"):
        if not message:
            self.status_label.setText("")
            return

        color_map = {
            "success": "#a6e3a1", # Green
            "error": "#f38ba8",   # Red
            "info": "#89b4fa"      # Blue
        }
        color = color_map.get(toast_type, "#cdd6f4") # Default to primary text color

        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: bold;")
        QTimer.singleShot(3000, lambda: self.status_label.setText(""))
