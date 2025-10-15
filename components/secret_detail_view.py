from PySide6.QtCore import Qt, QEvent, QSize, QTimer, QPoint, Signal
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
    QDialog,
    QStackedWidget,
    QSizePolicy,
    QMessageBox
)
import qtawesome as qta

from ui_theme import extra
from components.confirmation_dialog import ConfirmationDialog
from backend_utils import get_secret_from_backend

class SecretDetailWidget(QWidget):
    state_changed = Signal(str) # Emits the name of the new state

    def __init__(self, back_callback, save_callback, show_status_callback):
        super().__init__()
        self.back_callback = back_callback
        self.save_callback = save_callback
        self.show_status = show_status_callback
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
        self.form_layout.setSpacing(10)
        self.form_layout.setContentsMargins(20, 20, 20, 20)
        self.form_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        
        scroll_area.setWidget(self.form_container)
        self.main_layout.addWidget(scroll_area)

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
        
        for item in secret_data:
            key, value = item
            is_password = (key == "secret")
            self._add_form_row(key, value, is_password=is_password)
        
        self._add_add_new_field_button()

        if self.field_rows:
            QTimer.singleShot(0, lambda: self._focus_field(0))

    def _add_form_row(self, key, value, is_password=False):
        row_container = QWidget()
        row_container.setStyleSheet("QWidget { background-color: transparent; border-left: 3px solid transparent; padding-left: 8px; }")
        container_layout = QHBoxLayout(row_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(12)
        
        label_stack = QStackedWidget()
        label_stack.setFixedWidth(150)
        label_stack.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        label = QLabel(f"{key}:")
        label.setStyleSheet(f"color: {extra['primaryColor']}; font-size: 16px; font-weight: bold; border: none;")
        label.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        key_le = QLineEdit(key)
        key_le.setStyleSheet("QLineEdit { font-size: 16px; padding: 8px; border: 2px solid transparent; background-color: rgba(255, 255, 255, 0.1); } QLineEdit:focus { border: 2px solid #89b4fa; }")
        key_le.textChanged.connect(self._check_for_changes)
        label_stack.addWidget(label)
        label_stack.addWidget(key_le)
        container_layout.addWidget(label_stack)
        
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
        key_le.installEventFilter(self)
        line_edit.setFocusPolicy(Qt.StrongFocus)
        line_edit.focusInEvent = lambda e, c=row_container: self._on_field_focus_in(e, c)
        line_edit.focusOutEvent = lambda e, c=row_container: self._on_field_focus_out(e, c)
        line_edit.textChanged.connect(self._check_for_changes)
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
        self.field_rows.append({
            'le': line_edit, 'orig_val': value, 'container': row_container, 
            'toggle_btn': toggle_button, 'label': label, 'key_le': key_le, 
            'label_stack': label_stack, 'orig_key': key, 'value_layout': value_layout,
            'is_deep_editing': False, 'delete_button': None, 'deleted': False
        })

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
        self.state_changed.emit("add_new")

    def _remove_new_field_row(self, row_data):
        if row_data in self.new_rows:
            self.new_rows.remove(row_data)
            row_data['widget'].deleteLater()
            self._check_for_changes()
            self.state_changed.emit("normal")

    def _confirm_and_convert_field(self, row_data):
        key = row_data['key_le'].text().strip()
        value = row_data['val_le'].text()

        if not key:
            self.show_status("Field name cannot be empty.", "error")
            row_data['key_le'].setFocus()
            return False
        if not value:
            self.show_status("Field value cannot be empty.", "error")
            row_data['val_le'].setFocus()
            return False

        dialog = ConfirmationDialog(self)
        dialog.message_label.setText(f"Add field '{key}' to the secret?")
        if dialog.exec() != QDialog.Accepted:
            return False

        self._remove_new_field_row(row_data)
        self.form_layout.removeRow(self.add_field_button)
        self._add_form_row(key, value)
        self._add_add_new_field_button()
        self._set_dirty(True)
        self.state_changed.emit("normal")
        QTimer.singleShot(0, lambda: self._focus_field(len(self.field_rows) - 1))
        return True

    def _enter_deep_edit_mode(self, index):
        if not (0 <= index < len(self.field_rows)) or index == 0 or self.field_rows[index]['is_deep_editing']:
            return
        row = self.field_rows[index]
        row['is_deep_editing'] = True
        row['key_le'].setText(row['orig_key'])
        row['label_stack'].setCurrentWidget(row['key_le'])
        row['le'].setReadOnly(False)
        delete_button = QPushButton()
        delete_button.setIcon(qta.icon('fa5s.minus-circle', color='#f38ba8'))
        delete_button.setToolTip("Delete field (Ctrl+D)")
        delete_button.setFixedSize(36, 36)
        delete_button.clicked.connect(lambda: self._prompt_for_delete(index))
        row['value_layout'].addWidget(delete_button)
        row['delete_button'] = delete_button
        row['key_le'].setFocus()
        self._set_dirty(True)
        self.state_changed.emit("deep_edit")

    def _exit_deep_edit_mode(self, index, reset_values):
        if not (0 <= index < len(self.field_rows)):
            return
        row = self.field_rows[index]
        if reset_values:
            row['key_le'].setText(row['orig_key'])
            row['le'].setText(row['orig_val'])
        row['label'].setText(f"{row['key_le'].text()}:")
        row['label_stack'].setCurrentWidget(row['label'])
        row['le'].setReadOnly(True)
        if row['delete_button']:
            row['delete_button'].deleteLater()
            row['delete_button'] = None
        row['is_deep_editing'] = False
        self._check_for_changes()
        self.state_changed.emit("normal")
        QTimer.singleShot(0, lambda: self._focus_field(index))

    def _confirm_and_apply_deep_edit(self, index):
        if not (0 <= index < len(self.field_rows)):
            return
        row = self.field_rows[index]
        new_key = row['key_le'].text().strip()
        new_value = row['le'].text()
        if not new_key:
            self.show_status("Field name cannot be empty.", "error")
            return
        if new_key == row['orig_key'] and new_value == row['orig_val']:
            self._exit_deep_edit_mode(index, reset_values=False)
            return
        dialog = ConfirmationDialog(self)
        dialog.message_label.setText("Apply changes to this field?")
        if dialog.exec() == QDialog.Accepted:
            row['orig_key'] = new_key
            row['orig_val'] = new_value
            self._exit_deep_edit_mode(index, reset_values=False)
            self._set_dirty(True)
        else:
            self._exit_deep_edit_mode(index, reset_values=True)

    def _handle_esc_in_deep_edit(self, index):
        row = self.field_rows[index]
        has_changes = (row['key_le'].text() != row['orig_key']) or (row['le'].text() != row['orig_val'])
        if not has_changes:
            self._exit_deep_edit_mode(index, reset_values=False)
            return
        
        dialog = ConfirmationDialog(self)
        dialog.message_label.setText("Discard changes to this field?")
        if dialog.exec() == QDialog.Accepted:
            self._exit_deep_edit_mode(index, reset_values=True)

    def _handle_esc_in_new_field(self, row_data):
        key_text = row_data['key_le'].text()
        val_text = row_data['val_le'].text()
        if not key_text and not val_text:
            self._remove_new_field_row(row_data)
            self._focus_field(len(self.field_rows) -1)
            return

        dialog = ConfirmationDialog(self, 
            text="You have an unconfirmed new field.",
            confirm_text="Save Field",
            cancel_text="Cancel",
            third_button_text="Discard"
        )
        result = dialog.exec()

        if result == QDialog.Accepted:
            self._confirm_and_convert_field(row_data)
        elif result == dialog.third_button_role:
            self._remove_new_field_row(row_data)

    def _prompt_for_delete(self, index):
        if not (0 <= index < len(self.field_rows)):
            return
        row = self.field_rows[index]
        if not row.get('is_deep_editing', False):
            return
        dialog = ConfirmationDialog(self)
        dialog.message_label.setText("Permanently delete this field?")
        if dialog.exec() == QDialog.Accepted:
            self._delete_row(index)

    def _delete_row(self, index):
        if not (0 <= index < len(self.field_rows)):
            return
        row = self.field_rows[index]
        row['deleted'] = True
        row['container'].hide()
        self._set_dirty(True)

    def _set_dirty(self, dirty):
        self.is_dirty = dirty
        self.save_button.setEnabled(dirty)

    def _check_for_changes(self):
        for row in self.field_rows:
            if row.get('deleted', False):
                self._set_dirty(True)
                return
            if row['orig_key'] != row['key_le'].text() or row['orig_val'] != row['le'].text():
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
            self.show_status("You have unconfirmed fields. Press Enter to confirm them first.", "info")
            return
        dialog = ConfirmationDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self._save_changes()

    def _save_changes(self):
        content_lines = []
        password = ""
        for row in self.field_rows:
            if row.get('deleted', False):
                continue
            key = row['orig_key']
            if key == "secret":
                password = row['orig_val']
                break
        content_lines.append(password)

        for row in self.field_rows:
            if row.get('deleted', False):
                continue
            key = row['orig_key']
            if key == "secret":
                continue
            value = row['orig_val']
            content_lines.append(f"{key}: {value}")
        
        final_content = "\n".join(content_lines)
        
        result = self.save_callback(self.namespace, self.resource, final_content)
        if result and result.get("status") == "success":
            self.show_status("Saved!", "success")
            new_details = get_secret_from_backend(self.namespace, self.resource)
            self.populate_data(new_details, self.title_label.text(), self.namespace, self.resource)
        else:
            self.show_status(f"Save failed: {result.get('message', 'Unknown error')}", "error")

    def _enable_editing(self, line_edit):
        self.state_changed.emit("edit")
        line_edit.setReadOnly(False)
        line_edit.setFocus()
        self.show_status("Editing enabled", "info")

    def _cancel_editing(self, line_edit):
        for row in self.field_rows:
            if row['le'] == line_edit:
                line_edit.setText(row['orig_val'])
                break
        line_edit.setReadOnly(True)
        self.show_status("Edit cancelled", "info")
        self._check_for_changes()
        self.state_changed.emit("normal")

    def _on_field_focus_in(self, event, container):
        container.setStyleSheet("QWidget { background-color: transparent; border-left: 3px solid #89b4fa; padding-left: 8px; }")

    def _on_field_focus_out(self, event, container):
        container.setStyleSheet("QWidget { background-color: transparent; border-left: 3px solid transparent; padding-left: 8px; }")
        line_edit = container.findChild(QLineEdit)
        if line_edit and not line_edit.isReadOnly():
            is_deep_editing = False
            for row in self.field_rows:
                if row['le'] is line_edit and row['is_deep_editing']:
                    is_deep_editing = True
                    break
            if is_deep_editing:
                return
            focus_dest = QApplication.focusWidget()
            if focus_dest and focus_dest.parent() == line_edit.parent():
                pass
            else:
                line_edit.setReadOnly(True)
                self.show_status("")

    def _toggle_visibility(self, line_edit, button):
        if line_edit.echoMode() == QLineEdit.Password:
            line_edit.setEchoMode(QLineEdit.Normal)
            button.setIcon(qta.icon('fa5s.eye-slash', color=extra['primaryTextColor']))
        else:
            line_edit.setEchoMode(QLineEdit.Password)
            button.setIcon(qta.icon('fa5s.eye', color=extra['primaryTextColor']))

    def _copy_to_clipboard(self, text):
        self.show_status("Copied!", "success")
        QApplication.clipboard().setText(text)

    def _focus_field(self, index):
        if 0 <= index < len(self.field_rows):
            self.current_field_index = index
            line_edit = self.field_rows[index]['le']
            line_edit.setFocus()

    def eventFilter(self, obj, event):
        if event.type() != QEvent.KeyPress:
            return super().eventFilter(obj, event)

        key = event.key()
        modifiers = event.modifiers()

        # CONTEXT 1: A new, unconfirmed row is focused
        for row_data in self.new_rows:
            if obj is row_data['key_le'] or obj is row_data['val_le']:
                if key == Qt.Key_Escape:
                    self._handle_esc_in_new_field(row_data)
                    return True
                if key in (Qt.Key_Return, Qt.Key_Enter):
                    self._confirm_and_convert_field(row_data)
                    return True
                if key == Qt.Key_Tab:
                    if obj is row_data['key_le']:
                        row_data['val_le'].setFocus()
                    else:
                        row_data['key_le'].setFocus()
                    return True
                if key == Qt.Key_Backtab:
                    if obj is row_data['val_le']:
                        row_data['key_le'].setFocus()
                    else:
                        row_data['val_le'].setFocus()
                    return True
                return super().eventFilter(obj, event) # Allow normal typing

        # CONTEXT 2: An existing field row is focused
        focused_row_index = -1
        for i, row in enumerate(self.field_rows):
            if obj is row['le'] or obj is row['key_le']:
                focused_row_index = i
                break
        
        if focused_row_index != -1:
            self.current_field_index = focused_row_index
            row_data = self.field_rows[focused_row_index]

            # SUB-CONTEXT: Deep Edit Mode
            if row_data['is_deep_editing']:
                if key == Qt.Key_Escape:
                    self._handle_esc_in_deep_edit(focused_row_index)
                    return True
                if key in (Qt.Key_Return, Qt.Key_Enter):
                    self._confirm_and_apply_deep_edit(focused_row_index)
                    return True
                if modifiers == Qt.ControlModifier and key == Qt.Key_D:
                    self._prompt_for_delete(focused_row_index)
                    return True
                if key == Qt.Key_Tab:
                    if obj is row_data['key_le']:
                        row_data['le'].setFocus()
                    else:
                        row_data['key_le'].setFocus()
                    return True
                if key == Qt.Key_Backtab:
                    if obj is row_data['le']:
                        row_data['key_le'].setFocus()
                    else:
                        row_data['le'].setFocus()
                    return True
                # In deep edit, block other navigation hotkeys but allow typing
                return super().eventFilter(obj, event)

            # SUB-CONTEXT: Normal or Value-Edit Mode
            if key == Qt.Key_Escape:
                if not row_data['le'].isReadOnly(): # In normal value-edit mode
                    self._cancel_editing(row_data['le'])
                    return True
                else: # Not editing, so global Esc to go back
                    self.back_button.click()
                    return True

            if key in (Qt.Key_Return, Qt.Key_Enter):
                if row_data['le'].isReadOnly(): 
                    self._copy_to_clipboard(row_data['le'].text())
                else: 
                    row_data['le'].clearFocus()
                return True
            
            if key == Qt.Key_Down or (key == Qt.Key_Tab and modifiers == Qt.NoModifier):
                self._focus_field((self.current_field_index + 1) % len(self.field_rows))
                return True
            if key == Qt.Key_Up or (key == Qt.Key_Tab and modifiers == Qt.ShiftModifier):
                self._focus_field((self.current_field_index - 1) % len(self.field_rows))
                return True

            if modifiers == (Qt.ControlModifier | Qt.ShiftModifier) and key == Qt.Key_E:
                self._enter_deep_edit_mode(self.current_field_index)
                return True
            
            if modifiers == Qt.ControlModifier:
                if key == Qt.Key_S: self._prompt_to_save()
                elif key == Qt.Key_C: self._copy_to_clipboard(row_data['le'].text())
                elif key == Qt.Key_E: self._enable_editing(row_data['le'])
                elif key == Qt.Key_T: self._toggle_visibility(row_data['le'], row_data['toggle_btn'])
                elif key == Qt.Key_D: self._prompt_for_delete(self.current_field_index) # This will now only be called if not in deep edit, which is fine.
                else: return super().eventFilter(obj, event)
                return True

            return super().eventFilter(obj, event)

        # CONTEXT 3: No specific field is focused, but we are on the details page
        if key == Qt.Key_Escape:
            self.back_button.click()
            return True

        return super().eventFilter(obj, event)