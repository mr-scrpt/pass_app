from PySide6.QtCore import Qt, Signal, QTimer, QRect, QSize, QPoint
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QTextEdit,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QFormLayout,
    QFrame,
    QLayout,
    QDialog,
)
from PySide6.QtGui import QColor
import qtawesome as qta

from ui_theme import extra
from components.confirmation_dialog import ConfirmationDialog
from ui_components import StyledLineEdit


class FlowLayout(QLayout):
    """Flow layout that wraps items to multiple rows"""
    def __init__(self, parent=None, margin=0, spacing=-1):
        super().__init__(parent)
        self._item_list = []
        self._h_spacing = spacing
        self._v_spacing = spacing
        self.setContentsMargins(margin, margin, margin, margin)

    def addItem(self, item):
        self._item_list.append(item)

    def horizontalSpacing(self):
        if self._h_spacing >= 0:
            return self._h_spacing
        return self.smartSpacing(QSizePolicy.PushButton, Qt.Horizontal)

    def verticalSpacing(self):
        if self._v_spacing >= 0:
            return self._v_spacing
        return self.smartSpacing(QSizePolicy.PushButton, Qt.Vertical)

    def count(self):
        return len(self._item_list)

    def itemAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientations(Qt.Orientation(0))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self._do_layout(QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._item_list:
            size = size.expandedTo(item.minimumSize())
        margin = self.contentsMargins()
        size += QSize(margin.left() + margin.right(), margin.top() + margin.bottom())
        return size

    def _do_layout(self, rect, test_only):
        x = rect.x()
        y = rect.y()
        line_height = 0
        spacing_x = self.horizontalSpacing()
        spacing_y = self.verticalSpacing()

        for item in self._item_list:
            widget = item.widget()
            space_x = spacing_x + widget.style().layoutSpacing(
                QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Horizontal
            )
            space_y = spacing_y + widget.style().layoutSpacing(
                QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Vertical
            )
            next_x = x + item.sizeHint().width() + space_x
            if next_x - space_x > rect.right() and line_height > 0:
                x = rect.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        return y + line_height - rect.y()

    def smartSpacing(self, pm, orientation):
        parent = self.parent()
        if not parent:
            return -1
        if parent.isWidgetType():
            return parent.style().pixelMetric(pm, None, parent)
        return parent.spacing()


class SecretCreateWidget(QWidget):
    state_changed = Signal(str)  # Emits the name of the new state

    def __init__(self, back_callback, save_callback, show_status_callback, namespace_colors=None, namespaces=None, namespace_resources=None):
        super().__init__()
        self.back_callback = back_callback
        self.save_callback = save_callback
        self.show_status = show_status_callback
        self.field_rows = []
        self.is_dirty = False
        self.namespace_colors = namespace_colors or {}
        self.namespaces = namespaces or []
        self.namespace_resources = namespace_resources or {}  # {namespace: [resource1, resource2, ...]}
        self.selected_namespace = None
        self.namespace_buttons = []
        self.current_focus_index = 0  # Track current focused element (0 = tags, 1 = resource_input, 2+ = field_rows)
        self.current_tag_index = 0  # Track current focused tag
        
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
        self.form_layout.setSpacing(5)  # Reduce spacing between sections
        self.form_layout.setContentsMargins(20, 10, 20, 20)
        
        # Namespace section: left (tags with scroll) + right (NEW button)
        # Wrapper for border highlight
        tags_section_wrapper = QWidget()
        tags_section_wrapper.setMaximumHeight(150)  # Limit wrapper height
        tags_section_wrapper.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        tags_wrapper_layout = QHBoxLayout(tags_section_wrapper)
        tags_wrapper_layout.setContentsMargins(0, 0, 0, 0)
        tags_wrapper_layout.setSpacing(0)
        
        self.namespace_main_container = QWidget()
        self.namespace_main_container.setStyleSheet("QWidget { background-color: transparent; }")
        self.namespace_main_container.setFocusPolicy(Qt.StrongFocus)
        self.namespace_main_container.keyPressEvent = self._handle_tags_keypress
        
        # Border indicator for highlight
        self.tags_border_indicator = QWidget()
        self.tags_border_indicator.setFixedWidth(3)
        self.tags_border_indicator.setStyleSheet("background-color: transparent;")
        tags_wrapper_layout.addWidget(self.tags_border_indicator)
        
        # Container for tags
        tags_content_container = QWidget()
        tags_content_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        tags_content_layout = QHBoxLayout(tags_content_container)
        tags_content_layout.setContentsMargins(8, 0, 0, 0)
        tags_content_layout.setSpacing(0)
        namespace_main_layout = QHBoxLayout()
        namespace_main_layout.setSpacing(10)
        namespace_main_layout.setContentsMargins(0, 0, 0, 0)
        tags_content_layout.addLayout(namespace_main_layout)
        
        # Left section: tags with FlowLayout and scroll
        self.tags_container = QWidget()
        self.tags_layout = FlowLayout(self.tags_container, spacing=6)
        self.tags_layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll area for tags (up to 3 rows)
        tags_scroll = QScrollArea()
        tags_scroll.setWidgetResizable(True)
        tags_scroll.setFrameShape(QScrollArea.NoFrame)
        tags_scroll.setMinimumHeight(30)  # Minimum height for at least one row
        tags_scroll.setMaximumHeight(150)  # Maximum height for 3 rows
        tags_scroll.setWidget(self.tags_container)
        tags_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        tags_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        namespace_main_layout.addWidget(tags_scroll, stretch=1)  # Takes all available width
        
        # Right section: NEW button container
        new_button_container = QWidget()
        new_button_container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        new_button_layout = QVBoxLayout(new_button_container)
        new_button_layout.setContentsMargins(0, 0, 0, 0)
        new_button_layout.setSpacing(0)
        new_button_layout.setAlignment(Qt.AlignTop)
        
        self.new_namespace_button = QPushButton(" New")
        self.new_namespace_button.setIcon(qta.icon('fa5s.plus-circle', color='#a6e3a1'))
        self.new_namespace_button.setStyleSheet(
            "QPushButton { border: none; padding: 4px 8px; color: #a6e3a1; font-size: 11px; font-weight: bold; } "
            "QPushButton:hover { background-color: rgba(166, 227, 161, 0.1); }"
        )
        self.new_namespace_button.clicked.connect(self._add_new_namespace)
        self.new_namespace_button.setCursor(Qt.PointingHandCursor)
        
        new_button_layout.addWidget(self.new_namespace_button)
        namespace_main_layout.addWidget(new_button_container)  # Fixed width on the right
        
        self.namespace_main_container.setLayout(tags_content_layout)
        tags_wrapper_layout.addWidget(self.namespace_main_container, stretch=1)
        
        self.form_layout.addWidget(tags_section_wrapper)
        
        # Resource name input (compact) with container for border highlight
        self.resource_input_container = QWidget()
        self.resource_input_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.resource_input_container.setStyleSheet("QWidget { background-color: transparent; border-left: 3px solid transparent; padding-left: 8px; margin-top: 0px; margin-bottom: 0px; }")
        resource_input_layout = QHBoxLayout(self.resource_input_container)
        resource_input_layout.setContentsMargins(0, 0, 0, 0)
        resource_input_layout.setSpacing(0)
        
        self.resource_input = StyledLineEdit()
        self.resource_input.setPlaceholderText("Resource Name")
        self.resource_input.setStyleSheet("QLineEdit { font-size: 15px; padding: 8px; border: 2px solid transparent; background-color: rgba(255, 255, 255, 0.1); } QLineEdit:focus { border: 2px solid #89b4fa; }")
        self.resource_input.textChanged.connect(self._check_for_changes)
        self.resource_input.navigation.connect(self._handle_navigation)
        self.resource_input.focusInEvent = lambda e: self._on_resource_focus_in(e)
        self.resource_input.focusOutEvent = lambda e: self._on_resource_focus_out(e)
        resource_input_layout.addWidget(self.resource_input)
        
        self.form_layout.addWidget(self.resource_input_container)
        
        # Separator (thinner)
        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: {extra['primaryColor']}; opacity: 0.3;")
        self.form_layout.addWidget(separator)
        
        # Fields form container
        self.fields_form_layout = QFormLayout()
        self.fields_form_layout.setSpacing(5)  # Reduce spacing like on detail page
        self.fields_form_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        self.fields_form_layout.setContentsMargins(0, 0, 0, 0)
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
    
    def _add_namespace_tag(self, namespace, color):
        """Add a single namespace tag button"""
        tag_button = QPushButton(namespace)
        tag_button.setCheckable(True)
        tag_button.setFixedHeight(24)  # Fixed height for compact look
        tag_button.setFocusPolicy(Qt.StrongFocus)  # Make focusable
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
            f"}} "
            f"QPushButton:focus {{ "
            f"  border: 2px solid #89b4fa; "
            f"}}"
        )
        tag_button.clicked.connect(lambda: self._select_namespace(namespace, tag_button))
        tag_button.setCursor(Qt.PointingHandCursor)
        # Add to flow layout
        self.tags_layout.addWidget(tag_button)
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
        row_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_container.setStyleSheet("QWidget { background-color: transparent; border-left: 3px solid transparent; padding-left: 8px; }")
        container_layout = QHBoxLayout(row_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(12)
        row_container.setProperty('row_container', True)  # Mark as navigable
        
        # Key input
        if key_editable:
            key_input = StyledLineEdit(key)
            key_input.setPlaceholderText("Field Name")
            key_input.setStyleSheet("QLineEdit { font-size: 16px; padding: 8px; border: 2px solid transparent; background-color: rgba(255, 255, 255, 0.1); } QLineEdit:focus { border: 2px solid #89b4fa; }")
            key_input.setFixedWidth(150)
            key_input.textChanged.connect(self._check_for_changes)
            key_input.navigation.connect(self._handle_navigation)
            key_input.focusInEvent = lambda e, c=row_container: self._on_field_focus_in(e, c)
            key_input.focusOutEvent = lambda e, c=row_container: self._on_field_focus_out(e, c)
        else:
            key_input = StyledLineEdit(key)
            key_input.set_editing(False)
            key_input.setStyleSheet("QLineEdit { font-size: 16px; padding: 8px; border: 2px solid transparent; background-color: rgba(255, 255, 255, 0.05); color: #a6adc8; } QLineEdit:focus { border: 2px solid #89b4fa; }")
            key_input.setFixedWidth(150)
            key_input.navigation.connect(self._handle_navigation)
            key_input.focusInEvent = lambda e, c=row_container: self._on_field_focus_in(e, c)
            key_input.focusOutEvent = lambda e, c=row_container: self._on_field_focus_out(e, c)
        
        container_layout.addWidget(key_input)
        
        # Value input
        value_widget = QWidget()
        value_widget.setStyleSheet("border: none;")
        value_layout = QHBoxLayout(value_widget)
        value_layout.setContentsMargins(0, 0, 0, 0)
        value_layout.setSpacing(8)
        
        value_input = StyledLineEdit(value)
        value_input.setPlaceholderText("Field Value")
        value_input.setStyleSheet("QLineEdit { font-size: 16px; padding: 8px; border: 2px solid transparent; background-color: rgba(255, 255, 255, 0.1); } QLineEdit:focus { border: 2px solid #89b4fa; }")
        if is_secret:
            value_input.setEchoMode(QLineEdit.Password)
        value_input.textChanged.connect(self._check_for_changes)
        value_input.navigation.connect(self._handle_navigation)
        value_input.focusInEvent = lambda e, c=row_container: self._on_field_focus_in(e, c)
        value_input.focusOutEvent = lambda e, c=row_container: self._on_field_focus_out(e, c)
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
            dialog = ConfirmationDialog(
                self,
                text="You have unsaved changes.",
                confirm_text="Discard",
                cancel_text="Cancel",
                third_button_text="Save"
            )
            result = dialog.exec()
            if result == QDialog.Rejected:  # Cancel
                return
            elif result == dialog.third_button_role:  # Save
                self._prompt_to_save()
                return
            # Otherwise (Accepted) - discard and go back
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
        
        # Check if resource already exists in this namespace
        if namespace in self.namespace_resources:
            if resource in self.namespace_resources[namespace]:
                self.show_status(f"Resource '{resource}' already exists in namespace '{namespace}'.", "error")
                self.resource_input.setFocus()
                self.resource_input.selectAll()
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
    
    def update_namespaces(self, namespaces, namespace_colors, namespace_resources=None):
        """Update the list of namespaces and their resources"""
        self.namespaces = namespaces
        self.namespace_colors = namespace_colors
        if namespace_resources is not None:
            self.namespace_resources = namespace_resources
        self._populate_namespace_tags()
    
    def _on_tags_focus_in(self):
        """Highlight tags section on focus"""
        self.tags_border_indicator.setStyleSheet("background-color: #89b4fa;")
        self.current_focus_index = 0
    
    def _on_tags_focus_out(self):
        """Remove highlight from tags section"""
        self.tags_border_indicator.setStyleSheet("background-color: transparent;")
    
    def _on_resource_focus_in(self, event):
        """Highlight resource input on focus"""
        self.resource_input_container.setStyleSheet("QWidget { background-color: transparent; border-left: 3px solid #89b4fa; padding-left: 8px; margin-top: 0px; margin-bottom: 0px; }")
        self.current_focus_index = 1
    
    def _on_resource_focus_out(self, event):
        """Remove highlight from resource input"""
        self.resource_input_container.setStyleSheet("QWidget { background-color: transparent; border-left: 3px solid transparent; padding-left: 8px; margin-top: 0px; margin-bottom: 0px; }")
    
    def _on_field_focus_in(self, event, container):
        """Highlight field row on focus"""
        container.setStyleSheet("QWidget { background-color: transparent; border-left: 3px solid #89b4fa; padding-left: 8px; }")
        # Update current focus index
        for i, row in enumerate(self.field_rows):
            if row['container'] == container:
                self.current_focus_index = i + 2  # +2 because 0 is tags, 1 is resource_input
                break
    
    def _on_field_focus_out(self, event, container):
        """Remove highlight from field row"""
        container.setStyleSheet("QWidget { background-color: transparent; border-left: 3px solid transparent; padding-left: 8px; }")
    
    def _focus_element(self, index):
        """Focus on element by index (0 = tags, 1 = resource_input, 2+ = field_rows)"""
        if index == 0:
            self.namespace_main_container.setFocus()
            self._on_tags_focus_in()
        elif index == 1:
            self.resource_input.setFocus()
        elif index >= 2:
            row = self.field_rows[index - 2]
            row['value_input'].setFocus()
    
    def _handle_navigation(self, event):
        """Handle keyboard navigation"""
        key = event.key()
        modifiers = event.modifiers()
        
        # Navigation mode:
        # Esc - go back (with confirmation if dirty)
        if key == Qt.Key_Escape:
            self._handle_back()
            return
        
        # Enter - enable editing mode
        focused = self.focusWidget()
        if key in (Qt.Key_Return, Qt.Key_Enter) and modifiers == Qt.NoModifier:
            if isinstance(focused, StyledLineEdit):
                focused.set_editing(True)
                return
        
        # Tab navigation within field (between key and value)
        if key == Qt.Key_Tab and modifiers == Qt.NoModifier:
            if self.current_focus_index >= 2:  # We're in a field row
                row_index = self.current_focus_index - 2
                if row_index < len(self.field_rows):
                    row = self.field_rows[row_index]
                    focused = self.focusWidget()
                    if focused == row['key_input']:
                        row['value_input'].setFocus()
                        return
                    elif focused == row['value_input']:
                        # Move to next element
                        total_elements = 2 + len(self.field_rows)
                        next_index = (self.current_focus_index + 1) % total_elements
                        self._focus_element(next_index)
                        return
            # Default: move to next element
            total_elements = 2 + len(self.field_rows)
            next_index = (self.current_focus_index + 1) % total_elements
            self._focus_element(next_index)
            return
        
        # Navigation with arrows
        if key == Qt.Key_Down:
            total_elements = 2 + len(self.field_rows)  # tags + resource_input + field_rows
            next_index = (self.current_focus_index + 1) % total_elements
            self._focus_element(next_index)
            return
        
        if key == Qt.Key_Up:
            total_elements = 2 + len(self.field_rows)
            next_index = (self.current_focus_index - 1) % total_elements
            self._focus_element(next_index)
            return
        
        # Hotkeys with Ctrl
        if modifiers == Qt.ControlModifier:
            if key == Qt.Key_N:
                # Add new field
                self._add_new_field()
                return
            elif key == Qt.Key_T:
                # Add new namespace tag
                self._add_new_namespace()
                return
            elif key == Qt.Key_S:
                # Save
                self._prompt_to_save()
                return
    
    def _handle_tags_keypress(self, event):
        """Handle keypresses in tags section"""
        key = event.key()
        modifiers = event.modifiers()
        
        # Esc - go back (with confirmation if dirty)
        if key == Qt.Key_Escape:
            self._handle_back()
            event.accept()
            return
        
        checkable_buttons = [btn for btn in self.namespace_buttons if btn.isCheckable()]
        
        if not checkable_buttons:
            return
        
        # Tab - navigate between tags
        if key == Qt.Key_Tab and modifiers == Qt.NoModifier:
            self.current_tag_index = (self.current_tag_index + 1) % len(checkable_buttons)
            checkable_buttons[self.current_tag_index].setFocus()
            event.accept()
            return
        
        # Space or Enter - select tag
        if key in (Qt.Key_Space, Qt.Key_Return, Qt.Key_Enter):
            if self.current_tag_index < len(checkable_buttons):
                btn = checkable_buttons[self.current_tag_index]
                btn.click()
            event.accept()
            return
        
        # Arrow Down/Up - exit tags section
        if key == Qt.Key_Down:
            self._on_tags_focus_out()
            self._focus_element(1)  # Move to resource_input
            event.accept()
            return
        
        if key == Qt.Key_Up:
            self._on_tags_focus_out()
            total_elements = 2 + len(self.field_rows)
            self._focus_element(total_elements - 1)  # Move to last field
            event.accept()
            return
