from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
import qtawesome as qta

from ui_theme import extra

class SecretListItem(QWidget):
    def __init__(self, namespace, resource, namespace_color, view_callback):
        super().__init__()
        self.view_callback = view_callback
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignVCenter)
        
        ns_label = QLabel(f"[{namespace}]")
        ns_label.setStyleSheet(f"color: {namespace_color}; font-size: 16px;")
        ns_label.setAlignment(Qt.AlignVCenter)
        layout.addWidget(ns_label)
        
        resource_label = QLabel(resource)
        resource_label.setStyleSheet(f"color: {extra['primaryTextColor']}; font-size: 16px; font-weight: bold;")
        resource_label.setWordWrap(False)
        resource_label.setAlignment(Qt.AlignVCenter)
        layout.addWidget(resource_label, stretch=1)
        
        self.buttons_widget = QWidget()
        self.buttons_widget.setVisible(False)
        buttons_layout = QHBoxLayout(self.buttons_widget)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(4)
        
        view_btn = QPushButton()
        view_btn.setIcon(qta.icon('fa5s.eye', color=extra['primaryTextColor']))
        view_btn.setToolTip("View (Enter)")
        view_btn.setFixedSize(32, 32)
        view_btn.clicked.connect(self.view_callback)
        buttons_layout.addWidget(view_btn)
        
        layout.addWidget(self.buttons_widget)
        
        self.setMinimumHeight(44)
    
    def set_selected(self, selected):
        self.buttons_widget.setVisible(selected)
    
    def sizeHint(self):
        return QSize(self.width(), 44)
