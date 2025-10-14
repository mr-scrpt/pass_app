from PySide6.QtCore import Qt, QEvent, QSize, QTimer, QPoint
from PySide6.QtGui import QKeyEvent, QColor
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QFormLayout,
    QScrollArea,
    QDialog
)
import qtawesome as qta

from ui_theme import extra
from components.confirmation_dialog import ConfirmationDialog
from backend_utils import get_secret_from_backend

class SecretDetailWidget(QWidget):
    def __init__(self, back_callback, save_callback):
        super().__init__()
        self.back_callback = back_callback
        self.save_callback = save_callback
        self.field_rows = []
        self.new_rows = []
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
        self.save_button.setEnabled(False)
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

        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(15, 2, 15, 2)
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        status_layout.addStretch(1)
        status_layout.addWidget(self.status_label)
        status_layout.addStretch(1)
        self.main_layout.addLayout(status_layout)

    def populate_data(self, secret_data, secret_name, namespace, resource):
        self.title_label.setText(secret_name)
        self.namespace = namespace
        self.resource = resource
        self._set_dirty(False)

        for row in self.new_rows:
            row['widget'].deleteLater()
        self.new_rows = []

        while self.form_layout.count():
            self.form_layout.removeRow(0)
        
        self.field_rows = []
        
        if not secret_data:
            self.form_layout.addRow(QLabel("Could not load secret details."))
            return
        
        # Now expects a list of [key, value] pairs
        for item in secret_data:
            key, value = item
            is_password = (key == "secret")
            self._add_form_row(key, value, is_password=is_password)
        
        self._add_add_new_field_button()

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

    def _add_add_new_field_button(self):
        self.add_field_button = QPushButton(" Add New Field")
        self.add_field_button.setIcon(qta.icon('fa5s.plus-circle', color='#89b4fa'))
        self.add_field_button.setStyleSheet("QPushButton { border: none; padding: 10px; } QPushButton:hover { background-color: rgba(137, 180, 250, 0.1); }")
        self.add_field_button.clicked.connect(self.add_new_field_row)
        self.form_layout.addRow(self.add_field_button)

    def add_new_field_row(self):
        key_edit = QLineEdit()
        key_edit.setPlaceholderText("Field Name")
        key_edit.setStyleSheet("QLineEdit { font-size: 16px; padding: 8px; border: 2px solid transparent; background-color: rgba(255, 255, 255, 0.1); } QLineEdit:focus { border: 2px solid #89b4fa; }")
        key_edit.textChanged.connect(self._check_for_changes)

        value_edit = QLineEdit()
        value_edit.setPlaceholderText("Field Value")
        value_edit.setStyleSheet("QLineEdit { font-size: 16px; padding: 8px; border: 2px solid transparent; background-color: rgba(255, 255, 255, 0.1); } QLineEdit:focus { border: 2px solid #89b4fa; }")
        value_edit.textChanged.connect(self._check_for_changes)

        remove_button = QPushButton()
        remove_button.setIcon(qta.icon('fa5s.trash-alt', color='#f38ba8'))
        remove_button.setToolTip("Remove this field")
        remove_button.setFixedSize(36, 36)

        new_row_widget = QWidget()
        layout = QHBoxLayout(new_row_widget)
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(key_edit)
        layout.addWidget(value_edit)
        layout.addWidget(remove_button)

        row_data = {'widget': new_row_widget, 'key_le': key_edit, 'val_le': value_edit}
        remove_button.clicked.connect(lambda: self._remove_new_field_row(row_data))
        
        key_edit.installEventFilter(self)
        value_edit.installEventFilter(self)

        self.form_layout.insertRow(self.form_layout.rowCount() - 1, new_row_widget)
        self.new_rows.append(row_data)
        self._check_for_changes()
        key_edit.setFocus()

    def _remove_new_field_row(self, row_data):
        if row_data in self.new_rows:
            self.new_rows.remove(row_data)
            row_data['widget'].deleteLater()
            self._check_for_changes()

    def _confirm_and_convert_field(self, row_data):
        key = row_data['key_le'].text().strip()
        value = row_data['val_le'].text()

        if not key or not value:
            self._show_status("Field name and value cannot be empty.", "error")
            return

        dialog = ConfirmationDialog(self)
        dialog.message_label.setText(f"Add field '{key}' to the secret?")
        if dialog.exec() != QDialog.Accepted:
            return

        self._remove_new_field_row(row_data)
        self.form_layout.removeRow(self.add_field_button)
        self._add_form_row(key, value)
        self._add_add_new_field_button()
        self._set_dirty(True)
        self._focus_field(len(self.field_rows) - 1)

    def _set_dirty(self, dirty):
        self.is_dirty = dirty
        self.save_button.setEnabled(dirty)

    def _check_for_changes(self):
        for row in self.field_rows:
            if row['le'].text() != row['orig_val']:
                self._set_dirty(True)
                return

        if self.new_rows:
            self._set_dirty(True)
            return

        self._set_dirty(False)

    def _prompt_to_save(self):
        if not self.is_dirty:
            return
        
        if self.new_rows:
            self._show_status("You have unconfirmed fields. Press Enter to confirm them first.", "info")
            return

        dialog = ConfirmationDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self._save_changes()

    def _save_changes(self):
        content_lines = []
        password = ""
        # Ensure password is first
        for row in self.field_rows:
            if row['label'].text() == "secret:":
                password = row['le'].text()
                break
        content_lines.append(password)

        # Add other fields in their visual order
        for row in self.field_rows:
            key = row['label'].text().strip(':')
            if key == "secret":
                continue
            value = row['le'].text()
            content_lines.append(f"{key}: {value}")
        
        final_content = "\n".join(content_lines)
        
        result = self.save_callback(self.namespace, self.resource, final_content)
        if result and result.get("status") == "success":
            self._show_status("Saved!", "success")
            new_details = get_secret_from_backend(self.namespace, self.resource)
            self.populate_data(new_details, self.title_label.text(), self.namespace, self.resource)
        else:
            self._show_status(f"Save failed: {result.get('message', 'Unknown error')}", "error")

    def _enable_editing(self, line_edit):
        line_edit.setReadOnly(False)
        line_edit.setFocus()
        self._show_status("Editing enabled", "info")

    def _cancel_editing(self, line_edit):
        for row in self.field_rows:
            if row['le'] == line_edit:
                line_edit.setText(row['orig_val'])
                break
        line_edit.setReadOnly(True)
        self._show_status("Edit cancelled", "info")
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
        self._show_status("Copied!", "success")
        QApplication.clipboard().setText(text)

    def _focus_field(self, index):
        if 0 <= index < len(self.field_rows):
            self.current_field_index = index
            line_edit = self.field_rows[index]['le']
            line_edit.setFocus()
            line_edit.selectAll()

    def _show_status(self, message, toast_type="success"):
        if not message:
            self.status_label.setText("")
            return

        color = extra['primaryTextColor']
        if toast_type == "success":
            color = "#a6e3a1"
        elif toast_type == "error":
            color = "#f38ba8"
        elif toast_type == "info":
            color = "#89b4fa"

        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: bold;")
        QTimer.singleShot(3000, lambda: self.status_label.setText(""))

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            key = event.key()
            modifiers = event.modifiers()

            for row_data in self.new_rows:
                if obj is row_data['key_le'] or obj is row_data['val_le']:
                    if key in (Qt.Key_Return, Qt.Key_Enter):
                        self._confirm_and_convert_field(row_data)
                        return True
                    return super().eventFilter(obj, event)

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