import sys
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QScrollArea, QGroupBox
)
from PySide6.QtGui import QFont
import qtawesome as qta
from qt_material import apply_stylesheet

from ui_theme import extra
from fa_keyboard_icons import get_fa_keyboard_icon

class IconTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Keyboard Icons Preview")
        self.resize(900, 700)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        title = QLabel("Keyboard Icons Preview")
        title.setStyleSheet("font-size: 24px; font-weight: bold; padding: 20px;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # Our custom transformed keyboard icons
        custom_group = self._create_custom_icon_group("Custom Keyboard Icons (Transformed)", [
            ('enter', 'Enter (flipped + rotated 90°)', '#a6e3a1'),
            ('escape', 'Escape', '#f38ba8'),
            ('backspace', 'Backspace', '#fab387'),
            ('delete', 'Delete', '#f9e2af'),
            ('up', 'Up Arrow', '#89dceb'),
            ('down', 'Down Arrow', '#89b4fa'),
            ('left', 'Left Arrow', '#cba6f7'),
            ('right', 'Right Arrow', '#94e2d5'),
        ])
        scroll_layout.addWidget(custom_group)
        
        # Font Awesome Icons (already available via qtawesome)
        fa_group = self._create_icon_group("Font Awesome Icons (Original)", [
            ("fa5s.keyboard", "Keyboard"),
            ("fa5s.arrow-left", "Arrow Left"),
            ("fa5s.arrow-right", "Arrow Right"),
            ("fa5s.arrow-up", "Arrow Up"),
            ("fa5s.arrow-down", "Arrow Down"),
            ("fa5s.times", "Times/Close"),
            ("fa5s.check", "Check"),
            ("fa5s.undo", "Undo"),
            ("fa5s.sign-out-alt", "Sign Out"),
            ("fa5s.level-up-alt", "Enter/Return"),
            ("fa5s.backspace", "Backspace"),
            ("fa5s.trash", "Delete"),
            ("fa5s.plus", "Plus"),
            ("fa5s.minus", "Minus"),
        ])
        scroll_layout.addWidget(fa_group)
        
        # Unicode Symbols
        unicode_group = self._create_unicode_group("Unicode Symbols", [
            ("↵", "Enter/Return"),
            ("⏎", "Return"),
            ("⌫", "Backspace"),
            ("⌦", "Delete"),
            ("⎋", "Escape"),
            ("⇧", "Shift"),
            ("⌃", "Control"),
            ("⎇", "Alt"),
            ("⌘", "Command"),
            ("⇥", "Tab"),
            ("⇪", "Caps Lock"),
            ("↑", "Up Arrow"),
            ("↓", "Down Arrow"),
            ("←", "Left Arrow"),
            ("→", "Right Arrow"),
        ])
        scroll_layout.addWidget(unicode_group)
        
        # Material Design Icons (if we want to download)
        info_label = QLabel("""
<h3>Recommended Icon Sets to Download:</h3>
<ul>
<li><b>Material Design Icons (MDI)</b> - https://materialdesignicons.com/
   <br>Icons: keyboard-return, keyboard-esc, keyboard-backspace, etc.</li>
<li><b>Lucide Icons</b> - https://lucide.dev/
   <br>Clean, modern SVG icons</li>
<li><b>Phosphor Icons</b> - https://phosphoricons.com/
   <br>Excellent keyboard icon collection</li>
</ul>
        """)
        info_label.setWordWrap(True)
        info_label.setStyleSheet(f"background-color: rgba(137, 180, 250, 0.1); padding: 15px; border-radius: 8px; color: {extra['primaryTextColor']};")
        scroll_layout.addWidget(info_label)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
        
    def _create_icon_group(self, title, icons):
        group = QGroupBox(title)
        group.setStyleSheet(f"""
            QGroupBox {{
                font-size: 18px;
                font-weight: bold;
                border: 2px solid {extra['primaryColor']};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
            }}
            QGroupBox::title {{
                color: {extra['primaryColor']};
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        
        layout = QVBoxLayout()
        
        for icon_name, label_text in icons:
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(10, 5, 10, 5)
            
            try:
                # Small size
                btn_small = QPushButton()
                btn_small.setIcon(qta.icon(icon_name, color=extra['primaryColor']))
                btn_small.setIconSize(btn_small.sizeHint())
                btn_small.setFixedSize(40, 40)
                row_layout.addWidget(btn_small)
                
                # Medium size
                btn_medium = QPushButton()
                btn_medium.setIcon(qta.icon(icon_name, color='#a6e3a1'))
                from PySide6.QtCore import QSize
                btn_medium.setIconSize(QSize(32, 32))
                btn_medium.setFixedSize(50, 50)
                row_layout.addWidget(btn_medium)
                
                # Large size
                btn_large = QPushButton()
                btn_large.setIcon(qta.icon(icon_name, color='#f38ba8'))
                btn_large.setIconSize(QSize(48, 48))
                btn_large.setFixedSize(70, 70)
                row_layout.addWidget(btn_large)
                
                label = QLabel(f"{label_text} ({icon_name})")
                label.setStyleSheet(f"color: {extra['primaryTextColor']}; padding-left: 15px;")
                row_layout.addWidget(label, stretch=1)
                
            except Exception as e:
                label = QLabel(f"{label_text} ({icon_name}) - Error: {str(e)}")
                label.setStyleSheet("color: #f38ba8;")
                row_layout.addWidget(label, stretch=1)
            
            layout.addWidget(row)
        
        group.setLayout(layout)
        return group
    
    def _create_custom_icon_group(self, title, icons):
        """Create group showing our custom transformed keyboard icons"""
        group = QGroupBox(title)
        group.setStyleSheet(f"""
            QGroupBox {{
                font-size: 18px;
                font-weight: bold;
                border: 2px solid #a6e3a1;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: rgba(166, 227, 161, 0.05);
            }}
            QGroupBox::title {{
                color: #a6e3a1;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        
        layout = QVBoxLayout()
        
        for key_name, label_text, color in icons:
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(10, 5, 10, 5)
            
            try:
                # Small size (24x24)
                btn_small = QPushButton()
                btn_small.setIcon(get_fa_keyboard_icon(key_name, color, size=64))
                btn_small.setIconSize(QSize(24, 24))
                btn_small.setFixedSize(40, 40)
                btn_small.setStyleSheet(f"border: 2px solid {color}; border-radius: 6px;")
                row_layout.addWidget(btn_small)
                
                # Medium size (32x32)
                btn_medium = QPushButton()
                btn_medium.setIcon(get_fa_keyboard_icon(key_name, color, size=96))
                btn_medium.setIconSize(QSize(32, 32))
                btn_medium.setFixedSize(50, 50)
                btn_medium.setStyleSheet(f"border: 2px solid {color}; border-radius: 6px; background-color: rgba{tuple(int(color[i:i+2], 16) for i in (1, 3, 5)) + (0.15,)};")
                row_layout.addWidget(btn_medium)
                
                # Large size (48x48)
                btn_large = QPushButton()
                btn_large.setIcon(get_fa_keyboard_icon(key_name, color, size=128))
                btn_large.setIconSize(QSize(48, 48))
                btn_large.setFixedSize(70, 70)
                btn_large.setStyleSheet(f"border: 3px solid {color}; border-radius: 8px; background-color: rgba{tuple(int(color[i:i+2], 16) for i in (1, 3, 5)) + (0.2,)};")
                row_layout.addWidget(btn_large)
                
                label = QLabel(f"<b>{label_text}</b> ({key_name})")
                label.setStyleSheet(f"color: {extra['primaryTextColor']}; padding-left: 15px; font-size: 14px;")
                row_layout.addWidget(label, stretch=1)
                
            except Exception as e:
                label = QLabel(f"{label_text} ({key_name}) - Error: {str(e)}")
                label.setStyleSheet("color: #f38ba8;")
                row_layout.addWidget(label, stretch=1)
            
            layout.addWidget(row)
        
        group.setLayout(layout)
        return group
    
    def _create_unicode_group(self, title, symbols):
        group = QGroupBox(title)
        group.setStyleSheet(f"""
            QGroupBox {{
                font-size: 18px;
                font-weight: bold;
                border: 2px solid {extra['primaryColor']};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
            }}
            QGroupBox::title {{
                color: {extra['primaryColor']};
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        
        layout = QVBoxLayout()
        
        for symbol, label_text in symbols:
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(10, 5, 10, 5)
            
            # Small size
            lbl_small = QLabel(symbol)
            lbl_small.setFont(QFont("Arial", 16))
            lbl_small.setAlignment(Qt.AlignCenter)
            lbl_small.setStyleSheet(f"color: {extra['primaryColor']}; background-color: rgba(137, 180, 250, 0.15); border: 2px solid {extra['primaryColor']}; border-radius: 6px;")
            lbl_small.setFixedSize(40, 40)
            row_layout.addWidget(lbl_small)
            
            # Medium size
            lbl_medium = QLabel(symbol)
            lbl_medium.setFont(QFont("Arial", 24))
            lbl_medium.setAlignment(Qt.AlignCenter)
            lbl_medium.setStyleSheet("color: #a6e3a1; background-color: rgba(166, 227, 161, 0.15); border: 2px solid #a6e3a1; border-radius: 6px;")
            lbl_medium.setFixedSize(50, 50)
            row_layout.addWidget(lbl_medium)
            
            # Large size
            lbl_large = QLabel(symbol)
            lbl_large.setFont(QFont("Arial", 32))
            lbl_large.setAlignment(Qt.AlignCenter)
            lbl_large.setStyleSheet("color: #f38ba8; background-color: rgba(243, 139, 168, 0.15); border: 2px solid #f38ba8; border-radius: 6px;")
            lbl_large.setFixedSize(70, 70)
            row_layout.addWidget(lbl_large)
            
            label = QLabel(f"{label_text} (Unicode: {symbol})")
            label.setStyleSheet(f"color: {extra['primaryTextColor']}; padding-left: 15px;")
            row_layout.addWidget(label, stretch=1)
            
            layout.addWidget(row)
        
        group.setLayout(layout)
        return group

def main():
    app = QApplication(sys.argv)
    apply_stylesheet(app, theme='dark_blue.xml', extra=extra)
    window = IconTestWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

