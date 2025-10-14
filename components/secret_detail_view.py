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

class SecretDetailWidget(QWidget):
    def __init__(self, back_callback, save_callback):
        super().__init__()
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

        # --- Status Bar ---
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(15, 2, 15, 2)
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        status_layout.addStretch(1)
        status_layout.addWidget(self.status_label)
        status_layout.addStretch(1)
        self.main_layout.addLayout(status_layout)

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
            self._show_status("Saved!", "success")
            for row in self.field_rows:
                row['orig_val'] = row['le'].text()
            self._set_dirty(False)
        else:
            self._show_status("Save failed!", "error")

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

        color = extra['primaryTextColor'] # Default color
        if toast_type == "success":
            color = "#a6e3a1" # Green
        elif toast_type == "error":
            color = "#f38ba8" # Red
        elif toast_type == "info":
            color = "#89b4fa" # Blue

        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: bold;")
        QTimer.singleShot(3000, lambda: self.status_label.setText(""))

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