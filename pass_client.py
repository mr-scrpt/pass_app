import sys
import os
import subprocess
import json

# PySide6 imports must come BEFORE qt-material
from PySide6.QtCore import Qt, QEvent, QSize, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import QKeyEvent, QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
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
def get_backend_command(command_name):
    python_executable = os.path.join(os.path.dirname(__file__), '.venv', 'bin', 'python')
    backend_script = os.path.join(os.path.dirname(__file__), 'pass_backend.py')
    return [python_executable, backend_script, command_name]

def get_list_from_backend():
    try:
        cmd = get_backend_command("list")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except Exception as e:
        print(f"Error fetching list from backend: {e}", file=sys.stderr)
        return None

def get_secret_from_backend(namespace, resource):
    try:
        cmd = get_backend_command("show")
        input_data = json.dumps({"namespace": namespace, "resource": resource})
        result = subprocess.run(cmd, input=input_data, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except Exception as e:
        print(f"Error fetching secret from backend: {e}", file=sys.stderr)
        return None

def save_secret_to_backend(namespace, resource, content):
    try:
        cmd = get_backend_command("create") # 'create' uses 'pass insert' which handles updates
        input_data = json.dumps({"namespace": namespace, "resource": resource, "content": content})
        result = subprocess.run(cmd, input=input_data, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except Exception as e:
        print(f"Error saving secret to backend: {e}", file=sys.stderr)
        return {"status": "error", "message": str(e)}

# --- Custom Widgets ---

class Toast(QWidget):
    def __init__(self, parent, message):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        layout = QVBoxLayout(self)
        self.label = QLabel(message, self)
        self.label.setStyleSheet(
            f"""QLabel {{ 
                color: {extra['primaryTextColor']};
                background-color: #313244;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 10px 15px;
                font-size: 14px;
            }}"""
        )
        layout.addWidget(self.label)

        self.animation = QPropertyAnimation(self, b"windowOpacity", self)
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)

        self.show()

    def showEvent(self, event):
        super().showEvent(event)
        parent_rect = self.parent().geometry()
        self.move(
            parent_rect.x() + (parent_rect.width() - self.width()) // 2,
            parent_rect.y() + parent_rect.height() - self.height() - 30
        )
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.start()
        QTimer.singleShot(2000, self.hide_toast)

    def hide_toast(self):
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.finished.connect(self.close)
        self.animation.start()

    @staticmethod
    def show_toast(parent, message):
        Toast(parent, message)

class ConfirmationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Confirm Save")
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        self.message_label = QLabel("Are you sure you want to save the changes?")
        self.message_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.message_label)

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        confirm_button = QPushButton("Confirm")
        confirm_button.setDefault(True)
        confirm_button.setStyleSheet(f"background-color: {extra['primaryColor']}; color: {extra['secondaryColor']};")
        confirm_button.clicked.connect(self.accept)
        button_layout.addWidget(confirm_button)

        layout.addLayout(button_layout)

        self.setStyleSheet(f"background-color: {extra['secondaryColor']};")

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)

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

class SecretDetailWidget(QWidget):
    def __init__(self, main_window, back_callback, save_callback):
        super().__init__()
        self.main_window = main_window
        self.back_callback = back_callback
        self.save_callback = save_callback
        self.field_rows = []
        self.current_field_index = 0
        self.is_dirty = False
        self.namespace = ""
        self.resource = ""
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        header_widget = QWidget()
        header_widget.setStyleSheet(f"background-color: {extra['secondaryColor']}; padding: 12px;")
        header_layout = QHBoxLayout(header_widget)
        
        self.back_button = QPushButton()
        self.back_button.setIcon(qta.icon('fa5s.arrow-left', color=extra['primaryColor']))
        self.back_button.setToolTip("Back to list (Esc)")
        self.back_button.setFixedSize(40, 40)
        self.back_button.clicked.connect(self.back_callback)
        header_layout.addWidget(self.back_button)
        
        self.title_label = QLabel("")
        self.title_label.setStyleSheet(f"color: {extra['primaryColor']}; font-size: 16pt; font-weight: bold;")
        self.title_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.title_label, stretch=1)
        
        self.save_button = QPushButton()
        self.save_button.setIcon(qta.icon('fa5s.save', color='#a6e3a1'))
        self.save_button.setToolTip("Save changes (Ctrl+S)")
        self.save_button.setFixedSize(40, 40)
        self.save_button.setEnabled(False) # Initially disabled
        self.save_button.clicked.connect(self._prompt_to_save)
        header_layout.addWidget(self.save_button)
        
        self.main_layout.addWidget(header_widget)
        
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

        help_footer = QWidget()
        help_footer.setStyleSheet(f"background-color: {extra['secondaryColor']}; border-top: 1px solid #45475a; padding: 4px;")
        help_layout = QHBoxLayout(help_footer)
        help_layout.setContentsMargins(15, 5, 15, 5)

        hotkey_text = (
            "<b>Navigate:</b> ↑/↓, Tab &nbsp;&nbsp; "
            "<b>Copy:</b> Enter, Ctrl+C &nbsp;&nbsp; "
            "<b>Edit:</b> Ctrl+E &nbsp;&nbsp; "
            "<b>Toggle View:</b> Ctrl+T &nbsp;&nbsp; "
            "<b>Save:</b> Ctrl+S &nbsp;&nbsp; "
            "<b>Cancel/Back:</b> Esc"
        )
        help_label = QLabel(hotkey_text)
        help_label.setStyleSheet(f"color: {extra['secondaryTextColor']}; font-size: 12px;")
        help_layout.addWidget(help_label, alignment=Qt.AlignCenter)
        self.main_layout.addWidget(help_footer)

    def populate_data(self, secret_details, secret_name, namespace, resource):
        self.title_label.setText(secret_name)
        self.namespace = namespace
        self.resource = resource
        self._set_dirty(False)

        while self.form_layout.count():
            self.form_layout.removeRow(0)
        
        self.field_rows = []
        
        if not secret_details:
            self.form_layout.addRow(QLabel("Could not load secret details."))
            return
        
        secret_value = secret_details.pop("secret", "")
        self._add_form_row("secret", secret_value, is_password=True)
        
        for key, value in sorted(secret_details.items()):
            self._add_form_row(key, value, is_password=False)
        
        if self.field_rows:
            self._focus_field(0)

    def _add_form_row(self, key, value, is_password=False):
        row_container = QWidget()
        row_container.setStyleSheet("QWidget { background-color: transparent; border-left: 3px solid transparent; padding-left: 8px; }")
        container_layout = QHBoxLayout(row_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(12)
        
        label = QLabel(f"{key}:")
        label.setStyleSheet(f"color: {extra['primaryColor']}; font-size: 16px; font-weight: bold; border: none;")
        label.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        label.setFixedWidth(150)
        container_layout.addWidget(label)
        
        value_widget = QWidget()
        value_widget.setStyleSheet("border: none;")
        value_layout = QHBoxLayout(value_widget)
        value_layout.setContentsMargins(0, 0, 0, 0)
        value_layout.setSpacing(8)
        
        line_edit = QLineEdit(value)
        line_edit.setReadOnly(True)
        line_edit.setStyleSheet("QLineEdit { font-size: 16px; padding: 8px; border: 2px solid transparent; background-color: rgba(255, 255, 255, 0.05); } QLineEdit:focus { border: 2px solid #89b4fa; } QLineEdit:!read-only { background-color: rgba(255, 255, 255, 0.1); }")
        if is_password:
            line_edit.setEchoMode(QLineEdit.Password)
        
        line_edit.installEventFilter(self)
        line_edit.setFocusPolicy(Qt.StrongFocus)
        line_edit.focusInEvent = lambda e, c=row_container: self._on_field_focus_in(e, c)
        line_edit.focusOutEvent = lambda e, c=row_container: self._on_field_focus_out(e, c)
        line_edit.textEdited.connect(self._check_for_changes)
        value_layout.addWidget(line_edit, stretch=1)
        
        toggle_button = QPushButton()
        toggle_icon = 'fa5s.eye' if is_password else 'fa5s.eye-slash'
        toggle_button.setIcon(qta.icon(toggle_icon, color=extra['primaryTextColor']))
        toggle_button.setToolTip("Toggle Visibility (Ctrl+T)")
        toggle_button.setFixedSize(36, 36)
        toggle_button.clicked.connect(lambda: self._toggle_visibility(line_edit, toggle_button))
        value_layout.addWidget(toggle_button)
        
        edit_button = QPushButton()
        edit_button.setIcon(qta.icon('fa5s.pencil-alt', color=extra['primaryTextColor']))
        edit_button.setToolTip("Edit field (Ctrl+E)")
        edit_button.setFixedSize(36, 36)
        edit_button.clicked.connect(lambda: self._enable_editing(line_edit))
        value_layout.addWidget(edit_button)

        copy_button = QPushButton()
        copy_button.setIcon(qta.icon('fa5s.copy', color=extra['primaryTextColor']))
        copy_button.setToolTip("Copy to Clipboard (Enter or Ctrl+C)")
        copy_button.setFixedSize(36, 36)
        copy_button.clicked.connect(lambda: self._copy_to_clipboard(line_edit.text()))
        value_layout.addWidget(copy_button)
        
        container_layout.addWidget(value_widget, stretch=1)
        self.form_layout.addRow(row_container)
        self.field_rows.append({'le': line_edit, 'orig_val': value, 'container': row_container, 'toggle_btn': toggle_button, 'label': label})

    def _set_dirty(self, dirty):
        self.is_dirty = dirty
        self.save_button.setEnabled(dirty)

    def _check_for_changes(self):
        is_different = False
        for row in self.field_rows:
            if row['le'].text() != row['orig_val']:
                is_different = True
                break
        self._set_dirty(is_different)

    def _prompt_to_save(self):
        if not self.is_dirty:
            return
        
        dialog = ConfirmationDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self._save_changes()

    def _save_changes(self):
        new_data = {}
        for row in self.field_rows:
            key = row['label'].text().strip(':')
            value = row['le'].text()
            new_data[key] = value
        
        secret = new_data.pop('secret', '')
        content_lines = [secret]
        for key, value in new_data.items():
            content_lines.append(f"{key}: {value}")
        
        final_content = "\n".join(content_lines)
        
        result = self.save_callback(self.namespace, self.resource, final_content)
        if result and result.get("status") == "success":
            self._show_status("✓ Saved!")
            for row in self.field_rows:
                row['orig_val'] = row['le'].text()
            self._set_dirty(False)
        else:
            self._show_status("Save failed!")

    def _enable_editing(self, line_edit):
        line_edit.setReadOnly(False)
        line_edit.setFocus()
        self._show_status("Editing enabled")

    def _cancel_editing(self, line_edit):
        for row in self.field_rows:
            if row['le'] == line_edit:
                line_edit.setText(row['orig_val'])
                break
        line_edit.setReadOnly(True)
        self._show_status("Edit cancelled")
        self._check_for_changes()

    def _on_field_focus_in(self, event, container):
        container.setStyleSheet("QWidget { background-color: transparent; border-left: 3px solid #89b4fa; padding-left: 8px; }")
        QLineEdit.focusInEvent(container.findChild(QLineEdit), event)

    def _on_field_focus_out(self, event, container):
        container.setStyleSheet("QWidget { background-color: transparent; border-left: 3px solid transparent; padding-left: 8px; }")
        line_edit = container.findChild(QLineEdit)
        if line_edit and not line_edit.isReadOnly():
            focus_dest = QApplication.focusWidget()
            if focus_dest and focus_dest.parent() == line_edit.parent():
                pass
            else:
                line_edit.setReadOnly(True)
                self._show_status("")
        QLineEdit.focusOutEvent(line_edit, event)

    def _toggle_visibility(self, line_edit, button):
        if line_edit.echoMode() == QLineEdit.Password:
            line_edit.setEchoMode(QLineEdit.Normal)
            button.setIcon(qta.icon('fa5s.eye-slash', color=extra['primaryTextColor']))
        else:
            line_edit.setEchoMode(QLineEdit.Password)
            button.setIcon(qta.icon('fa5s.eye', color=extra['primaryTextColor']))

    def _copy_to_clipboard(self, text):
        self._show_status("✓ Copied!")
        QApplication.clipboard().setText(text)

    def _focus_field(self, index):
        if 0 <= index < len(self.field_rows):
            self.current_field_index = index
            line_edit = self.field_rows[index]['le']
            line_edit.setFocus()
            line_edit.selectAll()

    def _show_status(self, message):
        if message:
            Toast.show_toast(self.main_window, message)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            key = event.key()
            modifiers = event.modifiers()
            
            if key == Qt.Key_Escape:
                focused_widget = QApplication.focusWidget()
                if isinstance(focused_widget, QLineEdit) and not focused_widget.isReadOnly():
                    self._cancel_editing(focused_widget)
                    return True
                else:
                    self.back_button.click()
                    return True

            is_our_field = any(obj == row['le'] for row in self.field_rows)
            if not is_our_field:
                return super().eventFilter(obj, event)
            
            current_le = obj
            
            for i, row in enumerate(self.field_rows):
                if obj == row['le']:
                    self.current_field_index = i
                    break
            
            if key in (Qt.Key_Return, Qt.Key_Enter):
                if current_le.isReadOnly():
                    self._copy_to_clipboard(current_le.text())
                else:
                    current_le.clearFocus()
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
                if key == Qt.Key_S:
                    self._prompt_to_save()
                    return True
                elif key == Qt.Key_C:
                    self._copy_to_clipboard(current_le.text())
                    return True
                elif key == Qt.Key_E:
                    self._enable_editing(current_le)
                    return True
                elif key == Qt.Key_T:
                    self._toggle_visibility(current_le, self.field_rows[self.current_field_index]['toggle_btn'])
                    return True
        
        return super().eventFilter(obj, event)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.all_secrets = []
        self.namespace_colors = {}
        self.current_selected_item = None
        self.setWindowTitle("Pass Suite")
        self.resize(600, 450) # Increased height for the help footer
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        search_view_widget = QWidget()
        search_layout = QVBoxLayout(search_view_widget)
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search secrets...")
        search_layout.addWidget(self.search_bar)
        self.results_list = QListWidget()
        
        self.results_list.setStyleSheet("QListWidget::item { border: none; padding: 0px; } QListWidget::item:selected { background-color: rgba(137, 180, 250, 0.2); border-left: 3px solid #89b4fa; } QListWidget::item:hover { background-color: rgba(137, 180, 250, 0.1); }")
        
        search_layout.addWidget(self.results_list)
        self.stack.addWidget(search_view_widget)

        self.details_widget = SecretDetailWidget(
            main_window=self,
            back_callback=self._show_search_view,
            save_callback=self._save_secret
        )
        self.stack.addWidget(self.details_widget)
        
        self.load_data_and_populate()
        self.search_bar.textChanged.connect(self._on_search_changed)
        self.results_list.itemActivated.connect(self._on_item_activated)
        self.results_list.currentItemChanged.connect(self._on_selection_changed)
        self.search_bar.installEventFilter(self)

    def eventFilter(self, source, event):
        if source == self.search_bar and event.type() == QEvent.KeyPress:
            key = event.key()
            if key in (Qt.Key_Down, Qt.Key_Up):
                self.results_list.setFocus()
                QApplication.sendEvent(self.results_list, event)
                return True
            elif key in (Qt.Key_Return, Qt.Key_Enter):
                if self.results_list.currentItem():
                    self._on_item_activated(self.results_list.currentItem())
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
        for _, secret_data in secrets_to_display:
            item = QListWidgetItem()
            item.setData(Qt.UserRole, secret_data)
            
            ns_color = self.namespace_colors.get(secret_data["namespace"], extra['secondaryTextColor'])
            
            list_item_widget = SecretListItem(
                secret_data["namespace"], 
                secret_data["resource"], 
                ns_color,
                view_callback=lambda checked=False, i=item: self._view_secret_from_item(i)
            )
            
            item.setSizeHint(list_item_widget.sizeHint())
            
            self.results_list.addItem(item)
            self.results_list.setItemWidget(item, list_item_widget)

    def _on_selection_changed(self, current, previous):
        if previous:
            prev_widget = self.results_list.itemWidget(previous)
            if isinstance(prev_widget, SecretListItem):
                prev_widget.set_selected(False)
        
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

    def _on_item_activated(self, item: QListWidgetItem):
        item_data = item.data(Qt.UserRole)
        if item_data:
            self._view_secret(item_data)

    def _view_secret_from_item(self, item):
        item_data = item.data(Qt.UserRole)
        if item_data:
            self._view_secret(item_data)

    def _view_secret(self, item_data):
        secret_details = get_secret_from_backend(item_data["namespace"], item_data["resource"])
        self.details_widget.populate_data(
            secret_details, 
            f"[{item_data['namespace']}] {item_data['resource']}",
            item_data['namespace'],
            item_data['resource']
        )
        self._show_details_view()

    def _save_secret(self, namespace, resource, data):
        return save_secret_to_backend(namespace, resource, data)

    def _show_search_view(self):
        if self.details_widget.is_dirty:
            dialog = ConfirmationDialog(self)
            dialog.message_label.setText("You have unsaved changes. Discard them?")
            if dialog.exec() != QDialog.Accepted:
                return # User cancelled, stay on the details page

        self.stack.setCurrentIndex(0)
        self.search_bar.setFocus()
        self.search_bar.selectAll()

    def _show_details_view(self):
        self.stack.setCurrentIndex(1)
        if self.details_widget.field_rows:
            self.details_widget._focus_field(0)

def main():
    app = QApplication(sys.argv)
    apply_stylesheet(app, theme='dark_blue.xml', extra=extra)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()