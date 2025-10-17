import qtawesome as qta
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from backend_utils import get_secret_from_backend
from components.confirmation_dialog import ConfirmationDialog
from ui_components import StyledLineEdit
from ui_theme import extra


class SecretDetailWidget(QWidget):
    state_changed = Signal(str)  # Emits the name of the new state

    def __init__(self, back_callback, save_callback, show_status_callback, exec_dialog_callback):
        super().__init__()
        self.back_callback = back_callback
        self.save_callback = save_callback
        self.exec_dialog_callback = exec_dialog_callback
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
        self.back_button.setIcon(qta.icon("fa5s.arrow-left", color=extra["primaryColor"]))
        self.back_button.setToolTip("Back to list (Esc)")
        self.back_button.setFixedSize(40, 40)
        self.back_button.clicked.connect(self._handle_back)
        header_layout.addWidget(self.back_button)

        self.title_label = QLabel("")
        self.title_label.setStyleSheet(f"color: {extra['primaryColor']}; font-size: 16pt; font-weight: bold;")
        self.title_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.title_label, stretch=1)

        self.save_button = QPushButton()
        self.save_button.setIcon(qta.icon("fa5s.save", color="#a6e3a1"))
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
            row["widget"].deleteLater()
        self.new_rows = []

        while self.form_layout.count():
            self.form_layout.removeRow(0)

        self.field_rows = []

        if not secret_data:
            self.form_layout.addRow(QLabel("Could not load secret details."))
            return

        for item in secret_data:
            key, value = item
            is_password = key == "secret"
            self._add_form_row(key, value, is_password=is_password)

        self._add_add_new_field_button()

        if self.field_rows:
            QTimer.singleShot(0, lambda: self._focus_field(0))

    def _add_form_row(self, key, value, is_password=False):
        row_container = QWidget()
        row_container.setStyleSheet(
            "QWidget { background-color: transparent; border-left: 3px solid transparent; padding-left: 8px; }"
        )
        container_layout = QHBoxLayout(row_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(12)

        label_stack = QStackedWidget()
        label_stack.setFixedWidth(150)
        label_stack.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        label = QLabel(f"{key}:")
        label.setStyleSheet(f"color: {extra['primaryColor']}; font-size: 16px; font-weight: bold; border: none;")
        label.setAlignment(Qt.AlignVCenter | Qt.AlignRight)

        key_le = StyledLineEdit(key)
        key_le.setStyleSheet(
            "QLineEdit { font-size: 16px; padding: 8px; border: 2px solid transparent; background-color: rgba(255, 255, 255, 0.1); } QLineEdit:focus { border: 2px solid #89b4fa; }"
        )
        key_le.textChanged.connect(self._check_for_changes)
        key_le.navigation.connect(self._handle_navigation)
        # Track editing state changes for deep edit mode
        key_le.editing_changed = lambda is_editing, c=row_container: self._on_editing_state_changed(c, is_editing)

        label_stack.addWidget(label)
        label_stack.addWidget(key_le)
        container_layout.addWidget(label_stack)

        value_widget = QWidget()
        value_widget.setStyleSheet("border: none;")
        value_layout = QHBoxLayout(value_widget)
        value_layout.setContentsMargins(0, 0, 0, 0)
        value_layout.setSpacing(8)

        line_edit = StyledLineEdit(value)
        line_edit.set_editing(False)
        line_edit.setStyleSheet(
            "QLineEdit { font-size: 16px; padding: 8px; border: 2px solid transparent; background-color: rgba(255, 255, 255, 0.05); } QLineEdit:focus { border: 2px solid #89b4fa; } QLineEdit:!read-only { background-color: rgba(255, 255, 255, 0.1); }"
        )
        if is_password:
            line_edit.setEchoMode(QLineEdit.Password)

        line_edit.navigation.connect(self._handle_navigation)
        line_edit.setFocusPolicy(Qt.StrongFocus)
        line_edit.focusInEvent = lambda e, c=row_container: self._on_field_focus_in(e, c)
        line_edit.focusOutEvent = lambda e, c=row_container: self._on_field_focus_out(e, c)
        line_edit.textChanged.connect(self._check_for_changes)
        # Track editing state changes
        line_edit.editing_changed = lambda is_editing, c=row_container: self._on_editing_state_changed(c, is_editing)
        value_layout.addWidget(line_edit, stretch=1)

        toggle_button = QPushButton()
        toggle_icon = "fa5s.eye" if is_password else "fa5s.eye-slash"
        toggle_button.setIcon(qta.icon(toggle_icon, color=extra["primaryTextColor"]))
        toggle_button.setToolTip("Toggle Visibility (Ctrl+T)")
        toggle_button.setFixedSize(36, 36)
        toggle_button.clicked.connect(lambda: self._toggle_visibility(line_edit, toggle_button))
        value_layout.addWidget(toggle_button)

        edit_button = QPushButton()
        edit_button.setIcon(qta.icon("fa5s.pencil-alt", color=extra["primaryTextColor"]))
        edit_button.setToolTip("Edit field (Ctrl+E)")
        edit_button.setFixedSize(36, 36)
        edit_button.clicked.connect(lambda: self._enable_editing(line_edit))
        value_layout.addWidget(edit_button)

        copy_button = QPushButton()
        copy_button.setIcon(qta.icon("fa5s.copy", color=extra["primaryTextColor"]))
        copy_button.setToolTip("Copy to Clipboard (Enter or Ctrl+C)")
        copy_button.setFixedSize(36, 36)
        copy_button.clicked.connect(lambda: self._copy_to_clipboard(line_edit.text()))
        value_layout.addWidget(copy_button)

        container_layout.addWidget(value_widget, stretch=1)
        self.form_layout.addRow(row_container)
        self.field_rows.append(
            {
                "le": line_edit,
                "orig_val": value,
                "container": row_container,
                "toggle_btn": toggle_button,
                "label": label,
                "key_le": key_le,
                "label_stack": label_stack,
                "orig_key": key,
                "value_layout": value_layout,
                "is_deep_editing": False,
                "delete_button": None,
                "deleted": False,
            }
        )

    def _add_add_new_field_button(self):
        self.add_field_button = QPushButton(" Add New Field")
        self.add_field_button.setIcon(qta.icon("fa5s.plus-circle", color="#89b4fa"))
        self.add_field_button.setStyleSheet(
            "QPushButton { border: none; padding: 10px; } QPushButton:hover { background-color: rgba(137, 180, 250, 0.1); }"
        )
        self.add_field_button.clicked.connect(self.add_new_field_row)
        self.form_layout.addRow(self.add_field_button)

    def add_new_field_row(self):
        """Add a new field row with validation"""
        # Check if there's already a partially or completely empty field
        for row_data in self.new_rows:
            key = row_data["key_le"].text().strip()
            value = row_data["val_le"].text().strip()

            # Both empty - focus on key
            if not key and not value:
                row_data["key_le"].setFocus()
                row_data["key_le"].set_editing(True)
                return

            # Only key filled - focus on value and highlight red
            if key and not value:
                self._highlight_field_error(row_data, "value")
                row_data["val_le"].setFocus()
                row_data["val_le"].set_editing(True)
                self.show_status(f"Field '{key}' is missing a value.", "error")
                return

            # Only value filled - focus on key and highlight red
            if not key and value:
                self._highlight_field_error(row_data, "key")
                row_data["key_le"].setFocus()
                row_data["key_le"].set_editing(True)
                self.show_status("Field is missing a name.", "error")
                return

        # No empty or partially filled fields found, add new one
        key_edit = StyledLineEdit()
        key_edit.setPlaceholderText("Field Name")
        key_edit.setStyleSheet(
            "QLineEdit { font-size: 16px; padding: 8px; border: 2px solid #f9e2af; background-color: rgba(255, 255, 255, 0.1); color: #f9e2af; } QLineEdit:focus { border: 2px solid #f9e2af; }"
        )
        key_edit.textChanged.connect(self._check_for_changes)
        key_edit.navigation.connect(self._handle_navigation)
        key_edit.set_editing(True)

        value_edit = StyledLineEdit()
        value_edit.setPlaceholderText("Field Value")
        value_edit.setStyleSheet(
            "QLineEdit { font-size: 16px; padding: 8px; border: 2px solid #f9e2af; background-color: rgba(255, 255, 255, 0.1); color: #f9e2af; } QLineEdit:focus { border: 2px solid #f9e2af; }"
        )
        value_edit.textChanged.connect(self._check_for_changes)
        value_edit.navigation.connect(self._handle_navigation)
        value_edit.set_editing(True)

        remove_button = QPushButton()
        remove_button.setIcon(qta.icon("fa5s.trash-alt", color="#f38ba8"))
        remove_button.setToolTip("Remove this field")
        remove_button.setFixedSize(36, 36)

        # Container with border for highlighting
        new_row_container = QWidget()
        new_row_container.setStyleSheet(
            "QWidget { background-color: transparent; border-left: 3px solid #f9e2af; padding-left: 8px; }"
        )
        new_row_layout = QHBoxLayout(new_row_container)
        new_row_layout.setContentsMargins(0, 0, 0, 0)
        new_row_layout.setSpacing(8)

        new_row_widget = QWidget()
        layout = QHBoxLayout(new_row_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(key_edit)
        layout.addWidget(value_edit)
        layout.addWidget(remove_button)

        new_row_layout.addWidget(new_row_widget)

        row_data = {"widget": new_row_widget, "key_le": key_edit, "val_le": value_edit, "container": new_row_container}
        remove_button.clicked.connect(lambda: self._remove_new_field_row(row_data))

        # Track editing state changes
        key_edit.editing_changed = lambda is_editing, c=new_row_container: self._on_editing_state_changed(c, is_editing)
        value_edit.editing_changed = lambda is_editing, c=new_row_container: self._on_editing_state_changed(
            c, is_editing
        )

        # Handle Esc on empty field
        def on_key_escape():
            k = row_data["key_le"].text().strip()
            v = row_data["val_le"].text().strip()
            if not k and not v:
                self._remove_new_field_row(row_data)

        def on_value_escape():
            k = row_data["key_le"].text().strip()
            v = row_data["val_le"].text().strip()
            if not k and not v:
                self._remove_new_field_row(row_data)

        key_edit.on_escape_empty = on_key_escape
        value_edit.on_escape_empty = on_value_escape

        self.form_layout.insertRow(self.form_layout.rowCount() - 1, new_row_container)
        self.new_rows.append(row_data)
        self._check_for_changes()
        key_edit.setFocus()
        self.state_changed.emit("add_new")

    def _remove_new_field_row(self, row_data):
        if row_data in self.new_rows:
            # Get index before removing
            row_index = self.new_rows.index(row_data)
            self.new_rows.remove(row_data)

            # Delete container (which contains the widget)
            if "container" in row_data:
                row_data["container"].deleteLater()
            else:
                row_data["widget"].deleteLater()

            self._check_for_changes()
            self.state_changed.emit("normal")

            # Restore focus after deletion
            if self.new_rows:
                # Focus on previous or same index
                target_index = min(row_index, len(self.new_rows) - 1)
                QTimer.singleShot(10, lambda: self.new_rows[target_index]["key_le"].setFocus())
            elif self.field_rows:
                # Focus on last existing field
                QTimer.singleShot(10, lambda: self._focus_field(len(self.field_rows) - 1))

    def _highlight_field_error(self, row_data, field_type):
        """Highlight a field with red border to indicate error"""
        if field_type == "key":
            row_data["key_le"].setStyleSheet(
                "QLineEdit { font-size: 16px; padding: 8px; border: 2px solid #f38ba8; background-color: rgba(255, 255, 255, 0.1); } QLineEdit:focus { border: 2px solid #f38ba8; }"
            )
            # Reset after 3 seconds
            QTimer.singleShot(3000, lambda: self._reset_field_style(row_data, "key"))
        elif field_type == "value":
            row_data["val_le"].setStyleSheet(
                "QLineEdit { font-size: 16px; padding: 8px; border: 2px solid #f38ba8; background-color: rgba(255, 255, 255, 0.1); } QLineEdit:focus { border: 2px solid #f38ba8; }"
            )
            # Reset after 3 seconds
            QTimer.singleShot(3000, lambda: self._reset_field_style(row_data, "value"))

    def _reset_field_style(self, row_data, field_type):
        """Reset field style to normal"""
        normal_style = "QLineEdit { font-size: 16px; padding: 8px; border: 2px solid transparent; background-color: rgba(255, 255, 255, 0.1); } QLineEdit:focus { border: 2px solid #89b4fa; }"
        if field_type == "key" and row_data in self.new_rows:
            row_data["key_le"].setStyleSheet(normal_style)
        elif field_type == "value" and row_data in self.new_rows:
            row_data["val_le"].setStyleSheet(normal_style)

    def _confirm_and_convert_field(self, row_data):
        key = row_data["key_le"].text().strip()
        value = row_data["val_le"].text()

        if not key:
            self._highlight_field_error(row_data, "key")
            self.show_status("Field name cannot be empty.", "error")
            row_data["key_le"].setFocus()
            row_data["key_le"].set_editing(True)
            return False
        if not value:
            self._highlight_field_error(row_data, "value")
            self.show_status("Field value cannot be empty.", "error")
            row_data["val_le"].setFocus()
            row_data["val_le"].set_editing(True)
            return False

        dialog = ConfirmationDialog(self)
        dialog.message_label.setText(f"Add field '{key}' to the secret?")
        if self.exec_dialog_callback(dialog) != QDialog.Accepted:
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
        if not (0 <= index < len(self.field_rows)) or index == 0 or self.field_rows[index]["is_deep_editing"]:
            return
        row = self.field_rows[index]
        row["is_deep_editing"] = True

        row["key_le"].set_editing(True)
        row["le"].set_editing(True)

        row["label_stack"].setCurrentWidget(row["key_le"])

        delete_button = QPushButton()
        delete_button.setIcon(qta.icon("fa5s.minus-circle", color="#f38ba8"))
        delete_button.setToolTip("Delete field (Ctrl+D)")
        delete_button.setFixedSize(36, 36)
        delete_button.clicked.connect(lambda: self._prompt_for_delete(index))
        row["value_layout"].addWidget(delete_button)
        row["delete_button"] = delete_button

        row["key_le"].setFocus()
        self._set_dirty(True)
        self.state_changed.emit("deep_edit")

    def _exit_deep_edit_mode(self, index, reset_values):
        if not (0 <= index < len(self.field_rows)):
            return
        row = self.field_rows[index]

        if reset_values:
            row["key_le"].setText(row["orig_key"])
            row["le"].setText(row["orig_val"])

        row["label"].setText(f"{row['key_le'].text()}:")
        row["label_stack"].setCurrentWidget(row["label"])
        row["key_le"].set_editing(False)
        row["le"].set_editing(False)

        if row["delete_button"]:
            row["delete_button"].deleteLater()
            row["delete_button"] = None

        row["is_deep_editing"] = False
        self._check_for_changes()
        self.state_changed.emit("normal")
        QTimer.singleShot(0, lambda: self._focus_field(index))

    def _confirm_and_apply_deep_edit(self, index):
        if not (0 <= index < len(self.field_rows)):
            return
        row = self.field_rows[index]
        new_key = row["key_le"].text().strip()
        new_value = row["le"].text()
        if not new_key:
            self.show_status("Field name cannot be empty.", "error")
            return
        if new_key == row["orig_key"] and new_value == row["orig_val"]:
            self._exit_deep_edit_mode(index, reset_values=False)
            return
        dialog = ConfirmationDialog(self)
        dialog.message_label.setText("Apply changes to this field?")
        if self.exec_dialog_callback(dialog) == QDialog.Accepted:
            row["orig_key"] = new_key
            row["orig_val"] = new_value
            self._exit_deep_edit_mode(index, reset_values=False)
            self._set_dirty(True)
        else:
            self._exit_deep_edit_mode(index, reset_values=True)

    def _handle_esc_in_deep_edit(self, index):
        row = self.field_rows[index]
        has_changes = (row["key_le"].text() != row["orig_key"]) or (row["le"].text() != row["orig_val"])
        if not has_changes:
            self._exit_deep_edit_mode(index, reset_values=False)
            return

        dialog = ConfirmationDialog(self)
        dialog.message_label.setText("Discard changes to this field?")
        if self.exec_dialog_callback(dialog) == QDialog.Accepted:
            self._exit_deep_edit_mode(index, reset_values=True)

    def _handle_esc_in_new_field(self, row_data):
        key_text = row_data["key_le"].text()
        val_text = row_data["val_le"].text()
        if not key_text and not val_text:
            self._remove_new_field_row(row_data)
            self._focus_field(len(self.field_rows) - 1)
            return

        dialog = ConfirmationDialog(
            self,
            text="You have an unconfirmed new field.",
            confirm_text="Save Field",
            cancel_text="Cancel",
            third_button_text="Discard",
        )
        result = self.exec_dialog_callback(dialog)

        if result == QDialog.Accepted:
            self._confirm_and_convert_field(row_data)
        elif result == dialog.third_button_role:
            self._remove_new_field_row(row_data)

    def _prompt_for_delete(self, index):
        if not (0 <= index < len(self.field_rows)):
            return
        row = self.field_rows[index]
        if not row.get("is_deep_editing", False):
            return
        dialog = ConfirmationDialog(self)
        dialog.message_label.setText("Permanently delete this field?")
        if self.exec_dialog_callback(dialog) == QDialog.Accepted:
            self._delete_row(index)

    def _delete_row(self, index):
        if not (0 <= index < len(self.field_rows)):
            return
        row = self.field_rows[index]
        row["deleted"] = True
        row["container"].hide()
        self._set_dirty(True)

    def _set_dirty(self, dirty):
        self.is_dirty = dirty
        self.save_button.setEnabled(dirty)

    def _handle_back(self):
        """Handle back button click"""
        if self.is_dirty:
            dialog = ConfirmationDialog(
                self,
                text="You have unsaved changes.",
                confirm_text="Discard",
                cancel_text="Cancel",
                third_button_text="Save",
            )
            result = self.exec_dialog_callback(dialog)
            if result == QDialog.Rejected:  # Cancel
                return
            elif result == dialog.third_button_role:  # Save
                self._prompt_to_save()
                return
            # Otherwise (Accepted) - discard and go back
        self.back_callback()

    def _check_for_changes(self):
        for row in self.field_rows:
            if row.get("deleted", False):
                self._set_dirty(True)
                return
            if row["orig_key"] != row["key_le"].text() or row["orig_val"] != row["le"].text():
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
            # Check for partially filled fields
            for row_data in self.new_rows:
                key = row_data["key_le"].text().strip()
                value = row_data["val_le"].text().strip()

                if not key and not value:
                    # Both empty - focus on key
                    self.show_status("You have an empty field. Fill it or remove it.", "error")
                    row_data["key_le"].setFocus()
                    row_data["key_le"].set_editing(True)
                    return
                elif key and not value:
                    # Only key filled
                    self._highlight_field_error(row_data, "value")
                    self.show_status(f"Field '{key}' is missing a value.", "error")
                    row_data["val_le"].setFocus()
                    row_data["val_le"].set_editing(True)
                    return
                elif not key and value:
                    # Only value filled
                    self._highlight_field_error(row_data, "key")
                    self.show_status("Field is missing a name.", "error")
                    row_data["key_le"].setFocus()
                    row_data["key_le"].set_editing(True)
                    return

            # All fields filled, ask to confirm
            self.show_status("You have unconfirmed fields. Press Enter to confirm them first.", "info")
            # Focus on first new field
            if self.new_rows:
                self.new_rows[0]["key_le"].setFocus()
            return
        dialog = ConfirmationDialog(self)
        if self.exec_dialog_callback(dialog) == QDialog.Accepted:
            self._save_changes()

    def _save_changes(self):
        content_lines = []
        password = ""
        for row in self.field_rows:
            if row.get("deleted", False):
                continue
            key = row["orig_key"]
            if key == "secret":
                password = row["orig_val"]
                break
        content_lines.append(password)

        for row in self.field_rows:
            if row.get("deleted", False):
                continue
            key = row["orig_key"]
            if key == "secret":
                continue
            value = row["orig_val"]
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
        line_edit.set_editing(True)
        line_edit.setFocus()
        self.state_changed.emit("edit")
        self.show_status("Editing enabled", "info")

        # Set callback to emit state change when editing ends
        def on_editing_changed(is_editing):
            if not is_editing:
                self.state_changed.emit("normal")

        line_edit.editing_changed = on_editing_changed

    def _cancel_editing(self, line_edit):
        for row in self.field_rows:
            if row["le"] == line_edit:
                line_edit.setText(row["orig_val"])
                break
        line_edit.set_editing(False)
        self.show_status("Edit cancelled", "info")
        self._check_for_changes()
        self.state_changed.emit("normal")

    def _on_field_focus_in(self, event, container):
        container.setStyleSheet(
            "QWidget { background-color: transparent; border-left: 3px solid #89b4fa; padding-left: 8px; }"
        )

    def _on_field_focus_out(self, event, container):
        container.setStyleSheet(
            "QWidget { background-color: transparent; border-left: 3px solid transparent; padding-left: 8px; }"
        )
        line_edit = container.findChild(StyledLineEdit)
        if line_edit and line_edit._is_editing:
            is_deep_editing = False
            for row in self.field_rows:
                if row["le"] is line_edit and row["is_deep_editing"]:
                    is_deep_editing = True
                    break
            if is_deep_editing:
                return
            focus_dest = QApplication.focusWidget()
            if focus_dest and focus_dest.parent() == line_edit.parent():
                pass
            else:
                line_edit.set_editing(False)
                self.show_status("")

    def _on_editing_state_changed(self, container, is_editing):
        """Change border color and field styles based on editing state"""
        # Find the row data for this container
        row_data = None
        for row in self.field_rows:
            if row["container"] == container:
                row_data = row
                break

        if is_editing:
            # Yellow border for editing mode
            container.setStyleSheet(
                "QWidget { background-color: transparent; border-left: 3px solid #f9e2af; padding-left: 8px; }"
            )
            # Apply yellow styling to label and inputs
            if row_data:
                # Yellow color for label text
                row_data["label"].setStyleSheet(
                    "color: #f9e2af; font-size: 16px; font-weight: bold; border: none;"
                )
                # Yellow border and text for key input (in deep edit mode)
                row_data["key_le"].setStyleSheet(
                    "QLineEdit { font-size: 16px; padding: 8px; border: 2px solid #f9e2af; background-color: rgba(255, 255, 255, 0.1); color: #f9e2af; } QLineEdit:focus { border: 2px solid #f9e2af; }"
                )
                # Yellow border and text for value input
                row_data["le"].setStyleSheet(
                    "QLineEdit { font-size: 16px; padding: 8px; border: 2px solid #f9e2af; background-color: rgba(255, 255, 255, 0.05); color: #f9e2af; } QLineEdit:focus { border: 2px solid #f9e2af; } QLineEdit:!read-only { background-color: rgba(255, 255, 255, 0.1); }"
                )
        else:
            # Blue border for navigation mode
            container.setStyleSheet(
                "QWidget { background-color: transparent; border-left: 3px solid #89b4fa; padding-left: 8px; }"
            )
            # Restore normal styling
            if row_data:
                # Blue color for label text
                row_data["label"].setStyleSheet(
                    f"color: {extra['primaryColor']}; font-size: 16px; font-weight: bold; border: none;"
                )
                # Normal border and text for key input
                row_data["key_le"].setStyleSheet(
                    "QLineEdit { font-size: 16px; padding: 8px; border: 2px solid transparent; background-color: rgba(255, 255, 255, 0.1); } QLineEdit:focus { border: 2px solid #89b4fa; }"
                )
                # Normal border and text for value input
                row_data["le"].setStyleSheet(
                    "QLineEdit { font-size: 16px; padding: 8px; border: 2px solid transparent; background-color: rgba(255, 255, 255, 0.05); } QLineEdit:focus { border: 2px solid #89b4fa; } QLineEdit:!read-only { background-color: rgba(255, 255, 255, 0.1); }"
                )

    def _toggle_visibility(self, line_edit, button):
        if line_edit.echoMode() == QLineEdit.Password:
            line_edit.setEchoMode(QLineEdit.Normal)
            button.setIcon(qta.icon("fa5s.eye-slash", color=extra["primaryTextColor"]))
        else:
            line_edit.setEchoMode(QLineEdit.Password)
            button.setIcon(qta.icon("fa5s.eye", color=extra["primaryTextColor"]))

    def _copy_to_clipboard(self, text):
        self.show_status("Copied!", "success")
        QApplication.clipboard().setText(text)

    def _focus_field(self, index):
        if 0 <= index < len(self.field_rows):
            self.current_field_index = index
            line_edit = self.field_rows[index]["le"]
            line_edit.setFocus()

    def _handle_navigation(self, event):
        key = event.key()
        modifiers = event.modifiers()

        # Check if in new rows
        focused_widget = self.focusWidget()
        is_new_row = False
        for row_data in self.new_rows:
            if focused_widget is row_data["key_le"] or focused_widget is row_data["val_le"]:
                is_new_row = True
                break

        # Handle navigation in new rows (if not in editing mode)
        if is_new_row:
            if key == Qt.Key_Escape:
                self.back_button.click()
                return

            # Handle Ctrl hotkeys in new rows
            if modifiers == Qt.ControlModifier:
                if key == Qt.Key_S:
                    self._prompt_to_save()
                    return
                elif key == Qt.Key_N:
                    self.add_new_field_row()
                    return

            # Don't process other navigation for new rows
            return

        focused_row_index = -1
        for i, row in enumerate(self.field_rows):
            if self.focusWidget() is row["le"] or self.focusWidget() is row["key_le"]:
                focused_row_index = i
                break

        if focused_row_index != -1:
            self.current_field_index = focused_row_index
            row_data = self.field_rows[focused_row_index]

            if key == Qt.Key_Escape:
                self.back_button.click()
                return

            if key in (Qt.Key_Return, Qt.Key_Enter):
                self._enable_editing(row_data["le"])
                return

            if key == Qt.Key_Down or (key == Qt.Key_Tab and modifiers == Qt.NoModifier):
                self._focus_field((self.current_field_index + 1) % len(self.field_rows))
                return
            if key == Qt.Key_Up or (key == Qt.Key_Tab and modifiers == Qt.ShiftModifier):
                self._focus_field((self.current_field_index - 1) % len(self.field_rows))
                return

            if modifiers == Qt.ControlModifier:
                if key == Qt.Key_S:
                    self._prompt_to_save()
                elif key == Qt.Key_C:
                    self._copy_to_clipboard(row_data["le"].text())
                elif key == Qt.Key_E:
                    self._enter_deep_edit_mode(self.current_field_index)
                elif key == Qt.Key_T:
                    self._toggle_visibility(row_data["le"], row_data["toggle_btn"])
                elif key == Qt.Key_D:
                    self._prompt_for_delete(self.current_field_index)
                elif key == Qt.Key_N:
                    self.add_new_field_row()
                return
