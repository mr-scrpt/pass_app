from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QWidget,
    QLineEdit
)
from PySide6.QtGui import QKeyEvent

from ui_theme import extra
from fa_keyboard_icons import get_fa_keyboard_icon

class HotkeyCheatsheetDialog(QDialog):
    """Full hotkey reference dialog"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Hotkey Reference")
        self.setModal(True)
        self.setMinimumSize(680, 600)  # Reduced by 15% (800 * 0.85 = 680)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Keyboard Shortcuts Reference")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #89b4fa;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Search box
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        search_label.setStyleSheet("font-size: 14px;")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type to filter shortcuts...")
        self.search_input.textChanged.connect(self._filter_shortcuts)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # Scrollable content
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(f"QScrollArea {{ border: 1px solid {extra['primaryColor']}; background-color: transparent; }}")
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(20)
        
        # Build hotkey sections
        self._build_hotkey_sections()
        
        self.scroll.setWidget(self.content_widget)
        layout.addWidget(self.scroll)
        
        # Close button (similar to other dialogs)
        close_button = QPushButton("  Close")
        close_button.setIcon(get_fa_keyboard_icon('escape', color='#f38ba8', size=96))
        close_button.setIconSize(QSize(32, 32))
        close_button.setMinimumHeight(50)
        close_button.setStyleSheet("""
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
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
        
        self.setStyleSheet(f"QDialog {{ background-color: {extra['secondaryColor']}; }}")
    
    def _build_hotkey_sections(self):
        """Build all hotkey sections"""
        sections = [
            {
                "title": "Search View",
                "items": [
                    ("Up/Down", "Navigate through secrets list"),
                    ("Enter", "View selected secret"),
                    ("Ctrl+N", "Create new secret"),
                    ("Ctrl+R", "Sync with remote repository"),
                    ("Ctrl+G", "Generate password (simple)"),
                    ("Ctrl+Shift+G", "Generate password (advanced)")
                ]
            },
            {
                "title": "Detail View - Normal Mode",
                "items": [
                    ("Up/Down", "Navigate between fields"),
                    ("Tab", "Next field"),
                    ("Shift+Tab", "Previous field"),
                    ("Esc", "Back to search"),
                    ("Enter", "Copy field value to clipboard"),
                    ("Ctrl+C", "Copy to clipboard"),
                    ("Ctrl+E", "Edit field value"),
                    ("Ctrl+Shift+E", "Deep edit (edit key and value)"),
                    ("Ctrl+T", "Toggle password visibility"),
                    ("Ctrl+N", "Add new field"),
                    ("Ctrl+D", "Delete field"),
                    ("Ctrl+S", "Save changes")
                ]
            },
            {
                "title": "Detail View - Edit Mode",
                "items": [
                    ("Enter", "Confirm edit"),
                    ("Esc", "Cancel edit"),
                    ("Tab", "Native input navigation")
                ]
            },
            {
                "title": "Detail View - Deep Edit Mode",
                "items": [
                    ("Tab", "Switch between key/value inputs"),
                    ("Shift+Tab", "Switch backward"),
                    ("Enter", "Confirm changes"),
                    ("Ctrl+D", "Delete field"),
                    ("Esc", "Cancel deep edit")
                ]
            },
            {
                "title": "Detail View - Add New Field",
                "items": [
                    ("Tab", "Switch between key/value"),
                    ("Shift+Tab", "Switch backward"),
                    ("Enter", "Confirm field"),
                    ("Esc", "Cancel / delete empty field"),
                    ("Ctrl+N", "Add another field")
                ]
            },
            {
                "title": "Create View - Navigation Mode",
                "items": [
                    ("Up/Down", "Navigate between sections"),
                    ("Tab", "Next field"),
                    ("Shift+Tab", "Previous field"),
                    ("Esc", "Back to search (with confirmation)"),
                    ("Enter", "Activate section"),
                    ("Ctrl+E", "Edit field"),
                    ("Ctrl+T", "Add new tag/namespace"),
                    ("Ctrl+N", "Add new field"),
                    ("Ctrl+S", "Save resource"),
                    ("Ctrl+G", "Generate password")
                ]
            },
            {
                "title": "Create View - Tags Interaction Mode",
                "items": [
                    ("Up/Down", "Navigate tags (alternative)"),
                    ("Tab", "Next tag"),
                    ("Shift+Tab", "Previous tag"),
                    ("Left/Right", "Navigate tags"),
                    ("Esc", "Exit tags mode"),
                    ("Enter", "Select/deselect tag"),
                    ("Space", "Toggle tag selection"),
                    ("Ctrl+T", "Add new namespace")
                ]
            },
            {
                "title": "Create View - Editing Mode",
                "items": [
                    ("Tab", "Navigate within input"),
                    ("Enter", "Confirm edit"),
                    ("Esc", "Cancel edit"),
                    ("Ctrl+G", "Generate password (if password field)")
                ]
            },
            {
                "title": "Create View - New Field Mode",
                "items": [
                    ("Tab", "Switch between key/value"),
                    ("Shift+Tab", "Switch backward"),
                    ("Enter", "Confirm field"),
                    ("Esc", "Delete empty field"),
                    ("Ctrl+N", "Add another field")
                ]
            },
            {
                "title": "Password Generator Dialog",
                "items": [
                    ("Up/Down", "Navigate fields"),
                    ("Left/Right", "Adjust password length"),
                    ("Space", "Toggle option (Mixed Case/Symbols)"),
                    ("Enter", "Copy password and close"),
                    ("Ctrl+C", "Copy password"),
                    ("Esc", "Cancel")
                ]
            },
            {
                "title": "Confirmation Dialog",
                "items": [
                    ("Enter", "Confirm action"),
                    ("Ctrl+S", "Save (if available)"),
                    ("Esc", "Cancel")
                ]
            },
            {
                "title": "Global Shortcuts",
                "items": [
                    ("F1", "Show this help dialog"),
                    ("Ctrl+H", "Show this help dialog (alternative)")
                ]
            }
        ]
        
        for section_data in sections:
            self._add_section(section_data["title"], section_data["items"])
    
    def _add_section(self, title, items):
        """Add a hotkey section"""
        # Section title
        section_title = QLabel(title)
        section_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #89b4fa; margin-top: 10px;")
        self.content_layout.addWidget(section_title)
        
        # Section items
        for hotkey, description in items:
            item_widget = QWidget()
            item_layout = QHBoxLayout(item_widget)
            item_layout.setContentsMargins(20, 5, 10, 5)
            item_layout.setSpacing(15)
            
            # Hotkey label (light background with dark text)
            hotkey_label = QLabel(hotkey)
            hotkey_label.setStyleSheet("""
                background-color: #89b4fa;
                color: #1e1e2e;
                padding: 5px 10px;
                border-radius: 4px;
                font-family: monospace;
                font-size: 13px;
                font-weight: bold;
            """)
            hotkey_label.setMinimumWidth(150)
            item_layout.addWidget(hotkey_label)
            
            # Description label (bright text for dark background)
            desc_label = QLabel(description)
            desc_label.setStyleSheet("color: #cdd6f4; font-size: 13px;")
            item_layout.addWidget(desc_label, stretch=1)
            
            self.content_layout.addWidget(item_widget)
            # Store references for filtering
            item_widget.hotkey_text = hotkey.lower()
            item_widget.desc_text = description.lower()
    
    def _filter_shortcuts(self, text):
        """Filter shortcuts based on search text"""
        filter_text = text.lower()
        
        for i in range(self.content_layout.count()):
            widget = self.content_layout.itemAt(i).widget()
            if widget and hasattr(widget, 'hotkey_text'):
                # Show if matches hotkey or description
                visible = (filter_text in widget.hotkey_text or 
                          filter_text in widget.desc_text or 
                          not filter_text)
                widget.setVisible(visible)
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle key events"""
        key = event.key()
        
        # Escape - close dialog
        if key == Qt.Key_Escape:
            self.accept()
            event.accept()
            return
        
        # Up/Down - scroll content (if search not focused)
        if key in (Qt.Key_Up, Qt.Key_Down):
            if not self.search_input.hasFocus():
                scrollbar = self.scroll.verticalScrollBar()
                step = 50  # Scroll step in pixels
                if key == Qt.Key_Up:
                    scrollbar.setValue(scrollbar.value() - step)
                else:
                    scrollbar.setValue(scrollbar.value() + step)
                event.accept()
                return
        
        super().keyPressEvent(event)
