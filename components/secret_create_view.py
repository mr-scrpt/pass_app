from PySide6.QtCore import Qt, Signal, QTimer
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
    QSizePolicy,
)
import qtawesome as qta

from ui_theme import extra
from components.confirmation_dialog import ConfirmationDialog
from ui_components import StyledLineEdit


class SecretCreateWidget(QWidget):
    state_changed = Signal(str)  # Emits the name of the new state

    def __init__(self, back_callback, save_callback, show_status_callback):
        super().__init__()
        self.back_callback = back_callback
        self.save_callback = save_callback
        self.show_status = show_status_callback
        self.field_rows = []
        self.is_dirty = False
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header with back button, title and save button
        header_widget = QWidget()
        header_widget.setStyleSheet(f"background-color: {extra['secondaryColor']}; padding: 12px;")
        header_layout = QHBoxLayout(header_widget)
        
        self.back_button = QPushButton()
        self.back_button.setIcon(qta.icon('fa5s.arrow-left', color=extra['primaryColor']))
        self.back_button.setToolTip("Back to list (Esc)")
        self.back_button.setFixedSize(40, 40)
        self.back_button.clicked.connect(self._handle_back)
        header_layout.addWidget(self.back_button)
        
        self.title_label = QLabel("Create New Secret")
        self.title_label.setStyleSheet(f"color: {extra['primaryColor']}; font-size: 16pt; font-weight: bold;")
        self.title_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.title_label, stretch=1)
        
        self.save_button = QPushButton()
        self.save_button.setIcon(qta.icon('fa5s.save', color='#a6e3a1'))
        self.save_button.setToolTip("Save new secret (Ctrl+S)")
        self.save_button.setFixedSize(40, 40)
        self.save_button.clicked.connect(self._prompt_to_save)
        header_layout.addWidget(self.save_button)
        
        self.main_layout.addWidget(header_widget)
        
        # Scroll area for the form
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        
        self.form_container = QWidget()
        self.form_layout = QVBoxLayout(self.form_container)
        self.form_layout.setSpacing(20)
        self.form_layout.setContentsMargins(20, 20, 20, 20)
        
        # Namespace and Resource name inputs
        resource_info_widget = QWidget()
        resource_info_layout = QHBoxLayout(resource_info_widget)
        resource_info_layout.setSpacing(10)
        
        self.namespace_input = QLineEdit()
        self.namespace_input.setPlaceholderText("Namespace")
        self.namespace_input.setStyleSheet("QLineEdit { font-size: 16px; padding: 10px; border: 2px solid transparent; background-color: rgba(255, 255, 255, 0.1); } QLineEdit:focus { border: 2px solid #89b4fa; }")
        self.namespace_input.textChanged.connect(self._check_for_changes)
        
        self.resource_input = QLineEdit()
        self.resource_input.setPlaceholderText("Resource Name")
        self.resource_input.setStyleSheet("QLineEdit { font-size: 16px; padding: 10px; border: 2px solid transparent; background-color: rgba(255, 255, 255, 0.1); } QLineEdit:focus { border: 2px solid #89b4fa; }")
        self.resource_input.textChanged.connect(self._check_for_changes)
        
        resource_info_layout.addWidget(self.namespace_input)
        resource_info_layout.addWidget(self.resource_input)
        
        self.form_layout.addWidget(resource_info_widget)
        
        # Separator
        separator = QWidget()
        separator.setFixedHeight(2)
        separator.setStyleSheet(f"background-color: {extra['primaryColor']};")
        self.form_layout.addWidget(separator)
        
        # Fields form container
        self.fields_form_layout = QFormLayout()
        self.fields_form_layout.setSpacing(10)
        self.fields_form_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        self.form_layout.addLayout(self.fields_form_layout)
        
        scroll_area.setWidget(self.form_container)
        self.main_layout.addWidget(scroll_area)
        
        # Initialize with default secret field
        self._initialize_default_field()
        self._add_add_new_field_button()
        
        self.state_changed.emit("create")

    def _initialize_default_field(self):
        """Add the default 'secret' field that cannot be renamed"""
        self._add_field_row("secret", "", is_secret=True, key_editable=False)

    def _add_field_row(self, key, value, is_secret=False, key_editable=True):
        """Add a field row to the form"""
        row_container = QWidget()
        row_container.setStyleSheet("QWidget { background-color: transparent; border-left: 3px solid transparent; padding-left: 8px; }")
        container_layout = QHBoxLayout(row_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(12)
        
        # Key input
        if key_editable:
            key_input = QLineEdit(key)
            key_input.setPlaceholderText("Field Name")
            key_input.setStyleSheet("QLineEdit { font-size: 16px; padding: 8px; border: 2px solid transparent; background-color: rgba(255, 255, 255, 0.1); } QLineEdit:focus { border: 2px solid #89b4fa; }")
            key_input.setFixedWidth(150)
            key_input.textChanged.connect(self._check_for_changes)
        else:
            key_input = QLineEdit(key)
            key_input.setReadOnly(True)
            key_input.setStyleSheet("QLineEdit { font-size: 16px; padding: 8px; border: 2px solid transparent; background-color: rgba(255, 255, 255, 0.05); color: #a6adc8; } QLineEdit:focus { border: 2px solid #89b4fa; }")
            key_input.setFixedWidth(150)
        
        container_layout.addWidget(key_input)
        
        # Value input
        value_widget = QWidget()
        value_widget.setStyleSheet("border: none;")
        value_layout = QHBoxLayout(value_widget)
        value_layout.setContentsMargins(0, 0, 0, 0)
        value_layout.setSpacing(8)
        
        value_input = QLineEdit(value)
        value_input.setPlaceholderText("Field Value")
        value_input.setStyleSheet("QLineEdit { font-size: 16px; padding: 8px; border: 2px solid transparent; background-color: rgba(255, 255, 255, 0.1); } QLineEdit:focus { border: 2px solid #89b4fa; }")
        if is_secret:
            value_input.setEchoMode(QLineEdit.Password)
        value_input.textChanged.connect(self._check_for_changes)
        value_layout.addWidget(value_input, stretch=1)
        
        # Toggle visibility button
        toggle_button = QPushButton()
        toggle_icon = 'fa5s.eye' if is_secret else 'fa5s.eye-slash'
        toggle_button.setIcon(qta.icon(toggle_icon, color=extra['primaryTextColor']))
        toggle_button.setToolTip("Toggle Visibility (Ctrl+T)")
        toggle_button.setFixedSize(36, 36)
        toggle_button.clicked.connect(lambda: self._toggle_visibility(value_input, toggle_button))
        value_layout.addWidget(toggle_button)
        
        # Delete button (only for non-secret fields)
        if key_editable:
            delete_button = QPushButton()
            delete_button.setIcon(qta.icon('fa5s.trash-alt', color='#f38ba8'))
            delete_button.setToolTip("Delete field")
            delete_button.setFixedSize(36, 36)
            delete_button.clicked.connect(lambda: self._delete_field_row(row_data))
            value_layout.addWidget(delete_button)
        else:
            delete_button = None
        
        container_layout.addWidget(value_widget, stretch=1)
        self.fields_form_layout.addRow(row_container)
        
        row_data = {
            'container': row_container,
            'key_input': key_input,
            'value_input': value_input,
            'toggle_button': toggle_button,
            'delete_button': delete_button,
            'key_editable': key_editable,
            'is_secret': is_secret
        }
        self.field_rows.append(row_data)

    def _add_add_new_field_button(self):
        """Add the 'Add New Field' button"""
        self.add_field_button = QPushButton(" Add New Field")
        self.add_field_button.setIcon(qta.icon('fa5s.plus-circle', color='#89b4fa'))
        self.add_field_button.setStyleSheet("QPushButton { border: none; padding: 10px; } QPushButton:hover { background-color: rgba(137, 180, 250, 0.1); }")
        self.add_field_button.clicked.connect(self._add_new_field)
        self.fields_form_layout.addRow(self.add_field_button)

    def _add_new_field(self):
        """Add a new editable field"""
        # Remove the button temporarily
        self.fields_form_layout.removeRow(self.add_field_button)
        
        # Add new field row
        self._add_field_row("", "", is_secret=False, key_editable=True)
        
        # Re-add the button
        self._add_add_new_field_button()
        
        # Focus on the new field's key input
        self.field_rows[-1]['key_input'].setFocus()
        self._check_for_changes()

    def _delete_field_row(self, row_data):
        """Delete a field row"""
        if row_data in self.field_rows:
            self.field_rows.remove(row_data)
            row_data['container'].deleteLater()
            self._check_for_changes()

    def _toggle_visibility(self, line_edit, button):
        """Toggle password visibility"""
        if line_edit.echoMode() == QLineEdit.Password:
            line_edit.setEchoMode(QLineEdit.Normal)
            button.setIcon(qta.icon('fa5s.eye-slash', color=extra['primaryTextColor']))
        else:
            line_edit.setEchoMode(QLineEdit.Password)
            button.setIcon(qta.icon('fa5s.eye', color=extra['primaryTextColor']))

    def _check_for_changes(self):
        """Check if there are any changes"""
        has_data = bool(self.namespace_input.text().strip() or self.resource_input.text().strip())
        for row in self.field_rows:
            if row['value_input'].text():
                has_data = True
                break
        self.is_dirty = has_data

    def _handle_back(self):
        """Handle back button click"""
        if self.is_dirty:
            dialog = ConfirmationDialog(self)
            dialog.message_label.setText("You have unsaved changes. Discard them?")
            if dialog.exec() != QDialog.Accepted:
                return
        self.back_callback()

    def _prompt_to_save(self):
        """Prompt to save the new secret"""
        namespace = self.namespace_input.text().strip()
        resource = self.resource_input.text().strip()
        
        # Validation
        if not namespace:
            self.show_status("Namespace cannot be empty.", "error")
            self.namespace_input.setFocus()
            return
        
        if not resource:
            self.show_status("Resource name cannot be empty.", "error")
            self.resource_input.setFocus()
            return
        
        # Check if secret field has a value
        secret_value = ""
        for row in self.field_rows:
            if not row['key_editable']:  # This is the secret field
                secret_value = row['value_input'].text()
                break
        
        if not secret_value:
            self.show_status("Secret value cannot be empty.", "error")
            for row in self.field_rows:
                if not row['key_editable']:
                    row['value_input'].setFocus()
                    break
            return
        
        # Validate other fields
        for row in self.field_rows:
            if row['key_editable']:  # Skip the secret field
                key = row['key_input'].text().strip()
                value = row['value_input'].text()
                if key and not value:
                    self.show_status(f"Field '{key}' has no value.", "error")
                    row['value_input'].setFocus()
                    return
                if value and not key:
                    self.show_status("Field name cannot be empty.", "error")
                    row['key_input'].setFocus()
                    return
        
        dialog = ConfirmationDialog(self)
        dialog.message_label.setText(f"Create secret '[{namespace}] {resource}'?")
        if dialog.exec() == QDialog.Accepted:
            self._save_new_secret()

    def _save_new_secret(self):
        """Save the new secret"""
        namespace = self.namespace_input.text().strip()
        resource = self.resource_input.text().strip()
        
        # Build content
        content_lines = []
        
        # First line is always the secret value
        for row in self.field_rows:
            if not row['key_editable']:  # This is the secret field
                content_lines.append(row['value_input'].text())
                break
        
        # Add other fields
        for row in self.field_rows:
            if row['key_editable']:
                key = row['key_input'].text().strip()
                value = row['value_input'].text()
                if key and value:
                    content_lines.append(f"{key}: {value}")
        
        final_content = "\n".join(content_lines)
        
        result = self.save_callback(namespace, resource, final_content)
        if result and result.get("status") == "success":
            self.show_status("Secret created successfully!", "success")
            self.reset_form()
            QTimer.singleShot(1500, self.back_callback)
        else:
            self.show_status(f"Save failed: {result.get('message', 'Unknown error')}", "error")

    def reset_form(self):
        """Reset the form to initial state"""
        self.namespace_input.clear()
        self.resource_input.clear()
        
        # Clear all field rows
        for row in self.field_rows:
            row['container'].deleteLater()
        self.field_rows = []
        
        # Remove the add button
        self.fields_form_layout.removeRow(self.add_field_button)
        
        # Re-initialize
        self._initialize_default_field()
        self._add_add_new_field_button()
        
        self.is_dirty = False
        self.namespace_input.setFocus()
