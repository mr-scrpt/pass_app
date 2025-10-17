from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QSizePolicy

from ui_theme import extra

class HotkeyHelpWidget(QWidget):
    def __init__(self, category="", text=""):
        super().__init__()
        self.setStyleSheet(f"background-color: {extra['primaryColor']}; padding: 8px 20px; border-top: 1px solid rgba(30, 30, 46, 0.3);")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 6, 15, 6)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        
        # Category label (Navigation / Actions)
        self.category_label = QLabel(category)
        self.category_label.setMinimumWidth(80)
        self.category_label.setMaximumWidth(100)
        self.category_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.category_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
        if category:
            # Dark colors for light background
            category_color = "#1e3a8a" if "Navigation" in category else "#166534"
            self.category_label.setStyleSheet(f"color: {category_color}; font-size: 13px; font-weight: bold;")
        else:
            self.category_label.setStyleSheet(f"color: #1e1e2e; font-size: 13px; font-weight: bold;")
        layout.addWidget(self.category_label)
        
        # Content label
        self.content_label = QLabel(text)
        self.content_label.setStyleSheet(f"color: #1e1e2e; font-size: 12px;")
        self.content_label.setWordWrap(True)
        self.content_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.content_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        layout.addWidget(self.content_label, stretch=1)

    def setText(self, text):
        """Set content text (for backward compatibility)"""
        self.content_label.setText(text)
    
    def setCategory(self, category):
        """Set category label"""
        self.category_label.setText(category)
        if category:
            # Dark colors for light background
            category_color = "#1e3a8a" if "Navigation" in category else "#166534"
            self.category_label.setStyleSheet(f"color: {category_color}; font-size: 13px; font-weight: bold;")
    
    def update_content(self, category, text):
        """Update both category and content"""
        self.setCategory(category)
        self.setText(text)
