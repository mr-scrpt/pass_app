import sys
import os
import subprocess
import json

# PySide6 imports must come BEFORE qt_material
from PySide6.QtCore import Qt, QEvent, QSize, QTimer
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QStackedWidget,
    QPushButton,
    QLabel,
    QFormLayout,
    QScrollArea,
)
from qt_material import apply_stylesheet
import qtawesome as qta

# --- Catppuccin Mocha Colors for qt-material ---
extra = {
    'font_family': 'sans-serif',
    'font_size': '14px',
    'line_height': '14px',
    'density_scale': '0',
    'primaryColor': '#89b4fa', # Blue
    'secondaryColor': '#1e1e2e', # Base
    'primaryTextColor': '#cdd6f4', # Text
    'secondaryTextColor': '#a6adc8', # Subtext0
}

# Catppuccin Mocha color palette for namespaces
CATPPUCCIN_COLORS = [
    '#f38ba8',  # Red
    '#fab387',  # Peach
    '#f9e2af',  # Yellow
    '#a6e3a1',  # Green
    '#94e2d5',  # Teal
    '#89dceb',  # Sky
    '#89b4fa',  # Blue
    '#cba6f7',  # Mauve
    '#f5c2e7',  # Pink
    '#eba0ac',  # Maroon
]

# --- Backend Communication ---
def get_list_from_backend():
    try:
        python_executable = os.path.join(os.path.dirname(__file__), '.venv', 'bin', 'python')
        backend_script = os.path.join(os.path.dirname(__file__), 'pass_backend.py')
        cmd = [python_executable, backend_script, "list"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except Exception as e:
        print(f"Error fetching list from backend: {e}", file=sys.stderr)
        return None

def get_secret_from_backend(namespace, resource):
    try:
        python_executable = os.path.join(os.path.dirname(__file__), '.venv', 'bin', 'python')
        backend_script = os.path.join(os.path.dirname(__file__), 'pass_backend.py')
        cmd = [python_executable, backend_script, "show"]
        input_data = json.dumps({"namespace": namespace, "resource": resource})
        result = subprocess.run(cmd, input=input_data, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except Exception as e:
        print(f"Error fetching secret from backend: {e}", file=sys.stderr)
        return None

# --- Custom List Item Widget ---
class SecretListItem(QWidget):
    def __init__(self, namespace, resource, namespace_color, view_callback, edit_callback):
        super().__init__()
        self.view_callback = view_callback
        self.edit_callback = edit_callback
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignVCenter)
        
        # Namespace label with colored bracket
        ns_label = QLabel(f"[{namespace}]")
        ns_label.setStyleSheet(f"color: {namespace_color}; font-size: 16px;")
        ns_label.setAlignment(Qt.AlignVCenter)
        layout.addWidget(ns_label)
        
        # Resource label - bold
        resource_label = QLabel(resource)
        resource_label.setStyleSheet(f"color: {extra['primaryTextColor']}; font-size: 16px; font-weight: bold;")
        resource_label.setWordWrap(False)
        resource_label.setAlignment(Qt.AlignVCenter)
        layout.addWidget(resource_label, stretch=1)
        
        # Action buttons container (initially hidden)
        self.buttons_widget = QWidget()
        self.buttons_widget.setVisible(False)
        buttons_layout = QHBoxLayout(self.buttons_widget)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(4)
        
        # View button
        view_btn = QPushButton()
        view_btn.setIcon(qta.icon('fa5s.eye', color=extra['primaryTextColor']))
        view_btn.setToolTip("View (Enter)")
        view_btn.setFixedSize(32, 32)
        view_btn.clicked.connect(self.view_callback)
        buttons_layout.addWidget(view_btn)
        
        # Edit button
        edit_btn = QPushButton()
        edit_btn.setIcon(qta.icon('fa5s.edit', color=extra['primaryTextColor']))
        edit_btn.setToolTip("Edit (Ctrl+E)")
        edit_btn.setFixedSize(32, 32)
        edit_btn.clicked.connect(self.edit_callback)
        buttons_layout.addWidget(edit_btn)
        
        layout.addWidget(self.buttons_widget)
        
        self.setMinimumHeight(44)
    
    def set_selected(self, selected):
        """Show/hide buttons based on selection state"""
        self.buttons_widget.setVisible(selected)
    
    def sizeHint(self):
        return QSize(self.width(), 44)

# --- Edit Form Widget ---
class SecretEditWidget(QWidget):
    def __init__(self, back_callback, save_callback):
        super().__init__()
        self.back_callback = back_callback
        self.save_callback = save_callback
        self.field_rows = []  # List of (key_edit, value_edit, delete_button, row_widget)
        self.namespace = ""
        self.resource = ""
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header_widget = QWidget()
        header_widget.setStyleSheet(f"background-color: {extra['secondaryColor']}; padding: 12px;")
        header_layout = QHBoxLayout(header_widget)
        
        self.back_button = QPushButton()
        self.back_button.setIcon(qta.icon('fa5s.arrow-left', color=extra['primaryColor']))
        self.back_button.setToolTip("Back (Esc)")
        self.back_button.setFixedSize(40, 40)
        self.back_button.clicked.connect(back_callback)
        header_layout.addWidget(self.back_button)
        
        self.title_label = QLabel("")
        self.title_label.setStyleSheet(f"color: {extra['primaryColor']}; font-size: 16pt; font-weight: bold;")
        self.title_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.title_label, stretch=1)
        
        # Action buttons
        self.add_field_button = QPushButton()
        self.add_field_button.setIcon(qta.icon('fa5s.plus', color='#a6e3a1'))
        self.add_field_button.setToolTip("Add Field (Ctrl+N)")
        self.add_field_button.setFixedSize(40, 40)
        self.add_field_button.clicked.connect(self._add_new_field)
        header_layout.addWidget(self.add_field_button)
        
        self.save_button = QPushButton()
        self.save_button.setIcon(qta.icon('fa5s.save', color='#a6e3a1'))
        self.save_button.setToolTip("Save (Ctrl+S)")
        self.save_button.setFixedSize(40, 40)
        self.save_button.clicked.connect(self._save_changes)
        header_layout.addWidget(self.save_button)
        
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #a6e3a1; font-size: 13px;")
        self.status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.status_label.setFixedWidth(100)
        header_layout.addWidget(self.status_label)
        
        self.main_layout.addWidget(header_widget)
        
        # Scrollable form area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        
        self.form_container = QWidget()
        self.form_layout = QFormLayout(self.form_container)
        self.form_layout.setSpacing(20)
        self.form_layout.setContentsMargins(20, 20, 20, 20)
        self.form_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        
        scroll_area.setWidget(self.form_container)
        self.main_layout.addWidget(scroll_area)

    def populate_data(self, secret_details, secret_name, namespace, resource):
        self.title_label.setText(f"Edit: {secret_name}")
        self.namespace = namespace
        self.resource = resource
        
        # Clear existing fields
        while self.form_layout.count():
            self.form_layout.removeRow(0)
        
        self.field_rows = []
        
        if not secret_details:
            return
        
        # Add secret field first
        secret_value = secret_details.pop("secret", "")
        if secret_value:
            self._add_field_row("secret", secret_value, is_secret=True)
        
        # Add other fields
        for key, value in sorted(secret_details.items()):
            self._add_field_row(key, value)

    def _add_field_row(self, key="", value="", is_secret=False):
        # Key input
        key_edit = QLineEdit(key)
        key_edit.setPlaceholderText("Field name...")
        key_edit.setReadOnly(is_secret)
        key_edit.setStyleSheet(f"""
            QLineEdit {{
                font-size: 16px;
                font-weight: bold;
                padding: 8px;
                border: 2px solid transparent;
                background-color: {'rgba(255, 255, 255, 0.05)' if not is_secret else 'rgba(137, 180, 250, 0.1)'};
                color: {extra['primaryColor']};
            }}
            QLineEdit:focus {{
                border: 2px solid #89b4fa;
            }}
        """)
        key_edit.setFixedWidth(200)
        key_edit.installEventFilter(self)
        
        # --- Value widget (container for line edit and delete button) ---
        value_widget = QWidget()
        value_layout = QHBoxLayout(value_widget)
        value_layout.setContentsMargins(0, 0, 0, 0)
        value_layout.setSpacing(8)

        value_edit = QLineEdit(value)
        value_edit.setPlaceholderText("Value...")
        value_edit.setStyleSheet("""
            QLineEdit {
                font-size: 16px;
                padding: 8px;
                border: 2px solid transparent;
                background-color: rgba(255, 255, 255, 0.05);
            }
            QLineEdit:focus {
                border: 2px solid #89b4fa;
            }
        """)
        value_edit.installEventFilter(self)
        value_layout.addWidget(value_edit, stretch=1)
        
        delete_btn = None
        if not is_secret:
            delete_btn = QPushButton()
            delete_btn.setIcon(qta.icon('fa5s.trash', color='#f38ba8'))
            delete_btn.setToolTip("Delete field")
            delete_btn.setFixedSize(36, 36)
            # Use a lambda to pass the row's widget to the delete function
            delete_btn.clicked.connect(lambda: self._delete_field(key_edit))
            value_layout.addWidget(delete_btn)
        
        # Add the row to the form layout
        self.form_layout.addRow(key_edit, value_widget)
        
        # Store references to the widgets for this row
        self.field_rows.append((key_edit, value_edit, delete_btn, key_edit))

    def _add_new_field(self):
        self._add_field_row("", "")
        if self.field_rows:
            self.field_rows[-1][0].setFocus()
        self._show_status("Field added")

    def _delete_field(self, key_edit_to_delete):
        # Find and remove the field
        for i, (key_edit, _, _, _) in enumerate(self.field_rows):
            if key_edit == key_edit_to_delete:
                self.form_layout.removeRow(i)
                self.field_rows.pop(i)
                self._show_status("Field deleted")
                break

    def _save_changes(self):
        # Collect all field data
        data = {}
        for key_edit, value_edit, _, _ in self.field_rows:
            key = key_edit.text().strip()
            value = value_edit.text().strip()
            if key:  # Only save non-empty keys
                data[key] = value
        
        # Call save callback
        self.save_callback(self.namespace, self.resource, data)
        self._show_status("✓ Saved!")

    def _show_status(self, message):
        self.status_label.setText(message)
        QTimer.singleShot(2000, lambda: self.status_label.setText(""))

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            key = event.key()
            modifiers = event.modifiers()
            
            if key == Qt.Key_Escape:
                self.back_button.click()
                return True
            elif modifiers == Qt.ControlModifier:
                if key == Qt.Key_S:
                    self._save_changes()
                    return True
                elif key == Qt.Key_N:
                    self._add_new_field()
                    return True
        
        return super().eventFilter(obj, event)


# --- Details Form Widget ---
class SecretDetailWidget(QWidget):
    def __init__(self, back_callback):
        super().__init__()
        # List of (line_edit, toggle_button, edit_button, value, container)
        self.field_rows = []
        self.current_field_index = 0
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header with back button, title and status
        header_widget = QWidget()
        header_widget.setStyleSheet(f"background-color: {extra['secondaryColor']}; padding: 12px;")
        header_layout = QHBoxLayout(header_widget)
        
        self.back_button = QPushButton()
        self.back_button.setIcon(qta.icon('fa5s.arrow-left', color=extra['primaryColor']))
        self.back_button.setToolTip("Back to list (Esc)")
        self.back_button.setFixedSize(40, 40)
        self.back_button.clicked.connect(back_callback)
        header_layout.addWidget(self.back_button)
        
        self.title_label = QLabel("")
        self.title_label.setStyleSheet(f"color: {extra['primaryColor']}; font-size: 16pt; font-weight: bold;")
        self.title_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.title_label, stretch=1)
        
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #a6e3a1; font-size: 13px;")
        self.status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.status_label.setFixedWidth(100)
        header_layout.addWidget(self.status_label)
        
        self.main_layout.addWidget(header_widget)
        
        # Scrollable form area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        
        self.form_container = QWidget()
        self.form_layout = QFormLayout(self.form_container)
        self.form_layout.setSpacing(20)
        self.form_layout.setContentsMargins(20, 20, 20, 20)
        self.form_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        
        scroll_area.setWidget(self.form_container)
        self.main_layout.addWidget(scroll_area)

    def populate_data(self, secret_details, secret_name):
        self.title_label.setText(secret_name)
        
        # Clear existing fields
        while self.form_layout.count():
            self.form_layout.removeRow(0)
        
        self.field_rows = []
        
        if not secret_details:
            self.form_layout.addRow(QLabel("Could not load secret details."))
            return
        
        # Add secret field first
        secret_value = secret_details.pop("secret", "")
        if secret_value:
            self._add_form_row("Secret", secret_value, is_password=True)
        
        # Add other fields
        for key, value in sorted(secret_details.items()):
            self._add_form_row(key, value)
        
        # Focus first field
        if self.field_rows:
            self._focus_field(0)

    def _add_form_row(self, key, value, is_password=False):
        # Container for the entire row (for border styling)
        row_container = QWidget()
        row_container.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border-left: 3px solid transparent;
                padding-left: 8px;
            }
        """)
        container_layout = QHBoxLayout(row_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(12)
        
        # Label with fixed width for alignment
        label = QLabel(f"{key}:")
        label.setStyleSheet(f"color: {extra['primaryColor']}; font-size: 16px; font-weight: bold; border: none;")
        label.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        label.setFixedWidth(150)
        container_layout.addWidget(label)
        
        # Value row with controls
        value_widget = QWidget()
        value_widget.setStyleSheet("border: none;")
        value_layout = QHBoxLayout(value_widget)
        value_layout.setContentsMargins(0, 0, 0, 0)
        value_layout.setSpacing(8)
        
        line_edit = QLineEdit(value)
        line_edit.setReadOnly(True)
        line_edit.setStyleSheet("""
            QLineEdit {
                font-size: 16px;
                padding: 8px;
                border: 2px solid transparent;
                background-color: rgba(255, 255, 255, 0.05);
            }
            QLineEdit:focus {
                border: 2px solid #89b4fa;
                background-color: rgba(255, 255, 255, 0.05);
            }
            QLineEdit:!read-only {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        if is_password:
            line_edit.setEchoMode(QLineEdit.Password)
        
        # Install event filter and connect focus events
        line_edit.installEventFilter(self)
        line_edit.setFocusPolicy(Qt.StrongFocus)
        line_edit.focusInEvent = lambda e, container=row_container: self._on_field_focus_in(e, container)
        line_edit.focusOutEvent = lambda e, container=row_container: self._on_field_focus_out(e, container)
        value_layout.addWidget(line_edit, stretch=1)
        
        # Toggle button with icon only
        toggle_button = QPushButton()
        if is_password:
            toggle_button.setIcon(qta.icon('fa5s.eye', color=extra['primaryTextColor']))
        else:
            toggle_button.setIcon(qta.icon('fa5s.eye-slash', color=extra['primaryTextColor']))
        toggle_button.setToolTip("Toggle Visibility (Ctrl+T)")
        toggle_button.setFixedSize(36, 36)
        toggle_button.clicked.connect(lambda: self._toggle_visibility(line_edit, toggle_button))
        value_layout.addWidget(toggle_button)
        
        # Edit button
        edit_button = QPushButton()
        edit_button.setIcon(qta.icon('fa5s.pencil-alt', color=extra['primaryTextColor']))
        edit_button.setToolTip("Edit field (Ctrl+E)")
        edit_button.setFixedSize(36, 36)
        edit_button.clicked.connect(lambda: self._enable_editing(line_edit))
        value_layout.addWidget(edit_button)

        # Copy button with icon only
        copy_button = QPushButton()
        copy_button.setIcon(qta.icon('fa5s.copy', color=extra['primaryTextColor']))
        copy_button.setToolTip("Copy to Clipboard (Enter or Ctrl+C)")
        copy_button.setFixedSize(36, 36)
        copy_button.clicked.connect(lambda: self._copy_to_clipboard(line_edit.text()))
        value_layout.addWidget(copy_button)
        
        container_layout.addWidget(value_widget, stretch=1)
        
        self.form_layout.addRow(row_container)
        
        # Store reference for keyboard navigation
        self.field_rows.append((line_edit, toggle_button, edit_button, value, row_container))

    def _enable_editing(self, line_edit):
        line_edit.setReadOnly(False)
        line_edit.setFocus()
        self._show_status("Editing enabled")

    def _cancel_editing(self, line_edit):
        # Find original value
        for le, _, _, original_value, _ in self.field_rows:
            if le == line_edit:
                line_edit.setText(original_value)
                break
        line_edit.setReadOnly(True)
        self._show_status("Edit cancelled")

    def _on_field_focus_in(self, event, container):
        """Highlight the row when field gets focus"""
        container.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border-left: 3px solid #89b4fa;
                padding-left: 8px;
            }
        """)
        QLineEdit.focusInEvent(container.findChild(QLineEdit), event)

    def _on_field_focus_out(self, event, container):
        """Remove highlight when field loses focus"""
        container.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border-left: 3px solid transparent;
                padding-left: 8px;
            }
        """)
        # Make the field read-only again when it loses focus
        line_edit = container.findChild(QLineEdit)
        if line_edit and not line_edit.isReadOnly():
            # Don't make it read-only if focus is moving to a button in the same row
            focus_dest = QApplication.focusWidget()
            if focus_dest and focus_dest.parent() == line_edit.parent():
                pass # Focus is still within the value_widget
            else:
                line_edit.setReadOnly(True)
                self._show_status("") # Clear status
        
        QLineEdit.focusOutEvent(line_edit, event)

    def _toggle_visibility(self, line_edit, button):
        if line_edit.echoMode() == QLineEdit.Password:
            line_edit.setEchoMode(QLineEdit.Normal)
            button.setIcon(qta.icon('fa5s.eye-slash', color=extra['primaryTextColor']))
        else:
            line_edit.setEchoMode(QLineEdit.Password)
            button.setIcon(qta.icon('fa5s.eye', color=extra['primaryTextColor']))

    def _copy_to_clipboard(self, text):
        QApplication.clipboard().setText(text)
        self.status_label.setText("✓ Copied!")
        QTimer.singleShot(2000, lambda: self.status_label.setText(""))

    def _focus_field(self, index):
        if 0 <= index < len(self.field_rows):
            self.current_field_index = index
            line_edit, _, _, _, _ = self.field_rows[index]
            line_edit.setFocus()
            line_edit.selectAll()

    def _show_status(self, message):
        self.status_label.setText(message)
        QTimer.singleShot(2000, lambda: self.status_label.setText(""))

    def eventFilter(self, obj, event):
        """Intercept key events from line edits"""
        if event.type() == QEvent.KeyPress:
            key = event.key()
            modifiers = event.modifiers()
            
            # --- Global Escape Key Handler ---
            if key == Qt.Key_Escape:
                focused_widget = QApplication.focusWidget()
                if isinstance(focused_widget, QLineEdit) and not focused_widget.isReadOnly():
                    # If a field is being edited, cancel the edit
                    self._cancel_editing(focused_widget)
                    return True
                else:
                    # Otherwise, go back
                    self.back_button.click()
                    return True

            # Check if event is from one of our line edits
            is_our_field = any(obj == line_edit for line_edit, _, _, _, _ in self.field_rows)
            if not is_our_field:
                return super().eventFilter(obj, event)
            
            # --- Field-specific key handlers ---
            current_le = obj
            
            # Find current field index
            for i, (line_edit, _, _, _, _) in enumerate(self.field_rows):
                if obj == line_edit:
                    self.current_field_index = i
                    break
            
            # Handle navigation and action keys
            if key in (Qt.Key_Return, Qt.Key_Enter):
                self._copy_to_clipboard(current_le.text())
                return True
            elif key == Qt.Key_Down or (key == Qt.Key_Tab and modifiers == Qt.NoModifier):
                next_index = (self.current_field_index + 1) % len(self.field_rows)
                self._focus_field(next_index)
                return True
            elif key == Qt.Key_Up or (key == Qt.Key_Tab and modifiers == Qt.ShiftModifier):
                prev_index = (self.current_field_index - 1) % len(self.field_rows)
                self._focus_field(prev_index)
                return True
            elif modifiers == Qt.ControlModifier:
                if key == Qt.Key_C:
                    self._copy_to_clipboard(current_le.text())
                    return True
                elif key == Qt.Key_E:
                    self._enable_editing(current_le)
                    return True
                elif key == Qt.Key_T:
                    _, toggle_button, _, _, _ = self.field_rows[self.current_field_index]
                    self._toggle_visibility(current_le, toggle_button)
                    return True
        
        return super().eventFilter(obj, event)

# --- Main Window ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.all_secrets = []
        self.namespace_colors = {}
        self.current_selected_item = None
        self.setWindowTitle("Pass Suite")
        self.resize(600, 400)
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        search_view_widget = QWidget()
        search_layout = QVBoxLayout(search_view_widget)
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search secrets...")
        search_layout.addWidget(self.search_bar)
        self.results_list = QListWidget()
        
        # Style the list widget for better selection appearance
        self.results_list.setStyleSheet("""
            QListWidget::item {
                border: none;
                padding: 0px;
            }
            QListWidget::item:selected {
                background-color: rgba(137, 180, 250, 0.2);
                border-left: 3px solid #89b4fa;
            }
            QListWidget::item:hover {
                background-color: rgba(137, 180, 250, 0.1);
            }
        """)
        
        search_layout.addWidget(self.results_list)
        self.stack.addWidget(search_view_widget)

        self.details_widget = SecretDetailWidget(back_callback=self._show_search_view)
        self.stack.addWidget(self.details_widget)
        
        self.edit_widget = SecretEditWidget(
            back_callback=self._show_search_view,
            save_callback=self._save_secret
        )
        self.stack.addWidget(self.edit_widget)

        self.load_data_and_populate()
        self.search_bar.textChanged.connect(self._on_search_changed)
        self.results_list.itemActivated.connect(lambda item: self._on_item_activated(item, edit=False))
        self.results_list.currentItemChanged.connect(self._on_selection_changed)
        self.search_bar.installEventFilter(self)

    def eventFilter(self, source, event):
        if source == self.search_bar and event.type() == QEvent.KeyPress:
            key = event.key()
            modifiers = event.modifiers()
            if key in (Qt.Key_Down, Qt.Key_Up):
                self.results_list.setFocus()
                QApplication.sendEvent(self.results_list, event)
                return True
            elif key in (Qt.Key_Return, Qt.Key_Enter):
                if self.results_list.currentItem():
                    self._on_item_activated(self.results_list.currentItem(), edit=False)
                return True
            elif modifiers == Qt.ControlModifier and key == Qt.Key_E:
                if self.results_list.currentItem():
                    self._on_item_activated(self.results_list.currentItem(), edit=True)
                return True
        return super().eventFilter(source, event)

    def load_data_and_populate(self):
        backend_data = get_list_from_backend()
        if backend_data is None:
            self.results_list.addItem("Error: Could not load secrets.")
            return
        self.all_secrets = []
        namespaces_seen = []
        
        for ns_item in backend_data:
            namespace = ns_item.get("namespace", "Unknown")
            
            # Assign color to namespace if not yet assigned
            if namespace not in self.namespace_colors:
                if namespace not in namespaces_seen:
                    namespaces_seen.append(namespace)
                color_index = namespaces_seen.index(namespace) % len(CATPPUCCIN_COLORS)
                self.namespace_colors[namespace] = CATPPUCCIN_COLORS[color_index]
            
            for resource_name in ns_item.get("resources", []):
                plain_text = f"[{namespace}]: {resource_name}"
                item_data = {"namespace": namespace, "resource": resource_name}
                self.all_secrets.append((plain_text, item_data))
        
        self.all_secrets.sort()
        self._populate_list(self.all_secrets)

    def _populate_list(self, secrets_to_display):
        self.results_list.clear()
        for plain_text, secret_data in secrets_to_display:
            item = QListWidgetItem()
            item.setData(Qt.UserRole, secret_data)
            
            # Create custom widget with assigned color
            ns_color = self.namespace_colors.get(
                secret_data["namespace"], 
                extra['secondaryTextColor']
            )
            
            # Store item reference for callbacks
            list_item_widget = SecretListItem(
                secret_data["namespace"], 
                secret_data["resource"], 
                ns_color,
                view_callback=lambda checked=False, i=item: self._view_secret_from_item(i),
                edit_callback=lambda checked=False, i=item: self._edit_secret_from_item(i)
            )
            
            # CRITICAL: Set item size hint to match widget's size hint
            item.setSizeHint(list_item_widget.sizeHint())
            
            self.results_list.addItem(item)
            self.results_list.setItemWidget(item, list_item_widget)

    def _on_selection_changed(self, current, previous):
        """Update button visibility when selection changes"""
        # Hide buttons on previous item
        if previous:
            prev_widget = self.results_list.itemWidget(previous)
            if isinstance(prev_widget, SecretListItem):
                prev_widget.set_selected(False)
        
        # Show buttons on current item
        if current:
            curr_widget = self.results_list.itemWidget(current)
            if isinstance(curr_widget, SecretListItem):
                curr_widget.set_selected(True)
        
        self.current_selected_item = current

    def _on_search_changed(self, text):
        if not text:
            filtered_secrets = self.all_secrets
        else:
            filtered_secrets = [s_tuple for s_tuple in self.all_secrets if text.lower() in s_tuple[0].lower()]
        self._populate_list(filtered_secrets)

    def _on_item_activated(self, item: QListWidgetItem, edit=False):
        item_data = item.data(Qt.UserRole)
        if not item_data:
            return
        
        if edit:
            self._edit_secret(item_data)
        else:
            self._view_secret(item_data)

    def _view_secret_from_item(self, item):
        """View secret from item reference (for button callbacks)"""
        item_data = item.data(Qt.UserRole)
        if item_data:
            self._view_secret(item_data)

    def _edit_secret_from_item(self, item):
        """Edit secret from item reference (for button callbacks)"""
        item_data = item.data(Qt.UserRole)
        if item_data:
            self._edit_secret(item_data)

    def _view_secret(self, item_data):
        secret_details = get_secret_from_backend(item_data["namespace"], item_data["resource"])
        self.details_widget.populate_data(
            secret_details, 
            f"[{item_data['namespace']}] {item_data['resource']}"
        )
        self._show_details_view()

    def _edit_secret(self, item_data):
        secret_details = get_secret_from_backend(item_data["namespace"], item_data["resource"])
        self.edit_widget.populate_data(
            secret_details,
            f"[{item_data['namespace']}] {item_data['resource']}",
            item_data["namespace"],
            item_data["resource"]
        )
        self._show_edit_view()

    def _save_secret(self, namespace, resource, data):
        """Save the edited secret to backend"""
        # TODO: Implement backend save
        print(f"Saving {namespace}/{resource}: {data}")
        # Here you would call a backend function to save the data

    def _show_search_view(self):
        self.stack.setCurrentIndex(0)
        self.search_bar.setFocus()
        self.search_bar.selectAll()

    def _show_details_view(self):
        self.stack.setCurrentIndex(1)
        if self.details_widget.field_rows:
            self.details_widget._focus_field(0)

    def _show_edit_view(self):
        self.stack.setCurrentIndex(2)
        if self.edit_widget.field_rows:
            self.edit_widget.field_rows[0][1].setFocus()  # Focus value field

def main():
    app = QApplication(sys.argv)
    apply_stylesheet(app, theme='dark_blue.xml', extra=extra)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
