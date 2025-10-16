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
    QFrame,
)
from PySide6.QtGui import QColor
import qtawesome as qta

from ui_theme import extra
from components.confirmation_dialog import ConfirmationDialog
from ui_components import StyledLineEdit


class SecretCreateWidget(QWidget):
    state_changed = Signal(str)  # Emits the name of the new state

    def __init__(self, back_callback, save_callback, show_status_callback, namespace_colors=None, namespaces=None):
        super().__init__()
        self.back_callback = back_callback
        self.save_callback = save_callback
        self.show_status = show_status_callback
        self.field_rows = []
        self.is_dirty = False
        self.namespace_colors = namespace_colors or {}
        self.namespaces = namespaces or []
        self.selected_namespace = None
        self.namespace_buttons = []
        
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
        self.form_layout.setSpacing(15)
        self.form_layout.setContentsMargins(20, 10, 20, 20)
        
        # Namespace cloud tags (compact, no label)
        self.tags_container = QWidget()
        self.tags_layout = QHBoxLayout(self.tags_container)
        self.tags_layout.setSpacing(6)
        self.tags_layout.setContentsMargins(0, 0, 0, 0)
        # No alignment set - will use spacer to push NEW button to right
        
        # Scroll area for tags
        tags_scroll = QScrollArea()
        tags_scroll.setWidgetResizable(True)
        tags_scroll.setFrameShape(QScrollArea.NoFrame)
        tags_scroll.setMaximumHeight(50)
        tags_scroll.setWidget(self.tags_container)
        tags_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        tags_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.form_layout.addWidget(tags_scroll)
        
        # Resource name input (compact)
        self.resource_input = QLineEdit()
        self.resource_input.setPlaceholderText("Resource Name")
        self.resource_input.setStyleSheet("QLineEdit { font-size: 15px; padding: 8px; border: 2px solid transparent; background-color: rgba(255, 255, 255, 0.1); } QLineEdit:focus { border: 2px solid #89b4fa; }")
        self.resource_input.textChanged.connect(self._check_for_changes)
        
        self.form_layout.addWidget(self.resource_input)
        
        # Separator (thinner)
        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: {extra['primaryColor']}; opacity: 0.3;")
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
        self._populate_namespace_tags()
        
        self.state_changed.emit("create")

    def _populate_namespace_tags(self):
        """Populate the namespace tags cloud"""
        # Clear existing buttons
        for button in self.namespace_buttons:
            button.deleteLater()
        self.namespace_buttons.clear()
        
        # Add existing namespace tags
        for ns in self.namespaces:
            self._add_namespace_tag(ns, self.namespace_colors.get(ns, extra['primaryColor']))
        
        # Add the "new namespace" button (minimal style like ADD NEW FIELD)
        add_ns_button = QPushButton(" New")
        add_ns_button.setIcon(qta.icon('fa5s.plus-circle', color='#a6e3a1'))
        add_ns_button.setStyleSheet(
            "QPushButton { border: none; padding: 4px 8px; color: #a6e3a1; font-size: 11px; font-weight: bold; } "
            "QPushButton:hover { background-color: rgba(166, 227, 161, 0.1); }"
        )
        add_ns_button.clicked.connect(self._add_new_namespace)
        add_ns_button.setCursor(Qt.PointingHandCursor)
        
        # Add stretch before the NEW button to push it to the right
        self.tags_layout.addStretch()
        self.tags_layout.addWidget(add_ns_button)
        self.namespace_buttons.append(add_ns_button)
    
    def _add_namespace_tag(self, namespace, color):
        """Add a single namespace tag button"""
        tag_button = QPushButton(namespace)
        tag_button.setCheckable(True)
        tag_button.setFixedHeight(24)  # Fixed height for compact look
        tag_button.setStyleSheet(
            f"QPushButton {{ "
            f"  padding: 2px 8px; "
            f"  border: 1px solid {color}; "
            f"  border-radius: 12px; "
            f"  background-color: rgba({self._hex_to_rgb(color)}, 0.2); "
            f"  color: {color}; "
            f"  font-size: 11px; "
            f"  font-weight: bold; "
            f"  min-height: 0px; "
            f"  max-height: 24px; "
            f"}} "
            f"QPushButton:hover {{ "
            f"  background-color: rgba({self._hex_to_rgb(color)}, 0.3); "
            f"}} "
            f"QPushButton:checked {{ "
            f"  background-color: {color}; "
            f"  color: {extra['secondaryColor']}; "
            f"}}"
        )
        tag_button.clicked.connect(lambda: self._select_namespace(namespace, tag_button))
        tag_button.setCursor(Qt.PointingHandCursor)
        # Insert before the stretch spacer (which is always second-to-last)
        insert_pos = self.tags_layout.count() - 2 if self.tags_layout.count() > 1 else 0
        self.tags_layout.insertWidget(insert_pos, tag_button)
        self.namespace_buttons.append(tag_button)
    
    def _hex_to_rgb(self, hex_color):
        """Convert hex color to RGB string for rgba()"""
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return f"{r}, {g}, {b}"
    
    def _select_namespace(self, namespace, button):
        """Select a namespace from the cloud"""
        # Uncheck all other buttons
        for btn in self.namespace_buttons:
            if btn != button and btn.isCheckable():
                btn.setChecked(False)
        
        self.selected_namespace = namespace
        self._check_for_changes()
    
    def _add_new_namespace(self):
        """Add a new namespace"""
        from PySide6.QtWidgets import QInputDialog
        
        text, ok = QInputDialog.getText(self, "New Namespace", "Enter namespace name:")
        if ok and text.strip():
            namespace = text.strip()
            if namespace in self.namespaces:
                self.show_status(f"Namespace '{namespace}' already exists.", "info")
                # Select the existing one
                for btn in self.namespace_buttons:
                    if btn.isCheckable() and btn.text() == namespace:
                        btn.setChecked(True)
                        self._select_namespace(namespace, btn)
                        break
            else:
                # Add to the list
                self.namespaces.append(namespace)
                
                # Assign a color from the palette
                from ui_theme import CATPPUCCIN_COLORS
                color_index = len(self.namespace_colors) % len(CATPPUCCIN_COLORS)
                color = CATPPUCCIN_COLORS[color_index]
                self.namespace_colors[namespace] = color
                
                # Repopulate tags
                self._populate_namespace_tags()
                
                # Select the new namespace
                for btn in self.namespace_buttons:
                    if btn.isCheckable() and btn.text() == namespace:
                        btn.setChecked(True)
                        self._select_namespace(namespace, btn)
                        break
                
                self.show_status(f"Namespace '{namespace}' created.", "success")

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
        has_data = bool(self.selected_namespace or self.resource_input.text().strip())
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
        namespace = self.selected_namespace
        resource = self.resource_input.text().strip()
        
        # Validation
        if not namespace:
            self.show_status("Please select a namespace.", "error")
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
        namespace = self.selected_namespace
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
        self.selected_namespace = None
        self.resource_input.clear()
        
        # Uncheck all namespace buttons
        for btn in self.namespace_buttons:
            if btn.isCheckable():
                btn.setChecked(False)
        
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
        self.resource_input.setFocus()
    
    def update_namespaces(self, namespaces, namespace_colors):
        """Update the list of namespaces"""
        self.namespaces = namespaces
        self.namespace_colors = namespace_colors
        self._populate_namespace_tags()
