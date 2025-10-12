
import sys
import os
import subprocess
import json

from PySide6.QtCore import Qt, QEvent
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
)

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

# --- Details Form Widget ---

class SecretDetailWidget(QWidget):
    def __init__(self, back_callback):
        super().__init__()
        self.main_layout = QVBoxLayout(self)
        
        self.back_button = QPushButton("<- Back")
        self.back_button.clicked.connect(back_callback)
        self.main_layout.addWidget(self.back_button)

        self.form_widget = QWidget()
        self.form_layout = QFormLayout(self.form_widget)
        self.form_layout.setRowWrapPolicy(QFormLayout.WrapAllRows)
        self.main_layout.addWidget(self.form_widget)

        self.main_layout.addStretch()

    def populate_data(self, secret_details):
        while self.form_layout.count():
            child = self.form_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not secret_details:
            self.form_layout.addRow(QLabel("Could not load secret details."))
            return

        secret_value = secret_details.pop("secret", "")
        self._add_form_row("Secret", secret_value, is_password=True)

        for key, value in sorted(secret_details.items()):
            self._add_form_row(key, value)

    def _add_form_row(self, key, value, is_password=False):
        label = QLabel(f"{key}:")
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        line_edit = QLineEdit(value)
        line_edit.setReadOnly(True)
        if is_password:
            line_edit.setEchoMode(QLineEdit.Password)
        row_layout.addWidget(line_edit)
        toggle_button = QPushButton("👁")
        toggle_button.setFixedWidth(40)
        toggle_button.clicked.connect(lambda: self._toggle_visibility(line_edit, toggle_button))
        row_layout.addWidget(toggle_button)
        copy_button = QPushButton("Copy")
        copy_button.setFixedWidth(60)
        copy_button.clicked.connect(lambda: self._copy_to_clipboard(value))
        row_layout.addWidget(copy_button)
        self.form_layout.addRow(label, row_widget)

    def _toggle_visibility(self, line_edit, button):
        if line_edit.echoMode() == QLineEdit.Password:
            line_edit.setEchoMode(QLineEdit.Normal)
            button.setText("X")
        else:
            line_edit.setEchoMode(QLineEdit.Password)
            button.setText("👁")

    def _copy_to_clipboard(self, text):
        QApplication.clipboard().setText(text)

# --- Main Window ---

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.all_secrets = []
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
        search_layout.addWidget(self.results_list)
        self.stack.addWidget(search_view_widget)

        self.details_widget = SecretDetailWidget(back_callback=self._show_search_view)
        self.stack.addWidget(self.details_widget)

        self.load_data_and_populate()
        self.search_bar.textChanged.connect(self._on_search_changed)
        self.results_list.itemActivated.connect(self._on_item_activated)
        self.search_bar.installEventFilter(self)

    def eventFilter(self, source, event):
        if source == self.search_bar and event.type() == QEvent.KeyPress:
            key = event.key()
            if key == Qt.Key_Down:
                if self.results_list.count() > 0:
                    current = self.results_list.currentRow()
                    current = min(current + 1, self.results_list.count() - 1)
                    self.results_list.setCurrentRow(current)
                return True
            elif key == Qt.Key_Up:
                if self.results_list.count() > 0:
                    current = self.results_list.currentRow()
                    current = max(current - 1, 0)
                    self.results_list.setCurrentRow(current)
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
        for ns_item in backend_data:
            namespace = ns_item.get("namespace", "Unknown")
            for resource_name in ns_item.get("resources", []):
                display_text = f"[{namespace}]: {resource_name}"
                item_data = {"namespace": namespace, "resource": resource_name}
                self.all_secrets.append((display_text, item_data))
        self.all_secrets.sort()
        self._populate_list(self.all_secrets)

    def _populate_list(self, secrets_to_display):
        self.results_list.clear()
        for secret_display, secret_data in secrets_to_display:
            item = QListWidgetItem(secret_display)
            item.setData(Qt.UserRole, secret_data)
            self.results_list.addItem(item)
        if self.results_list.count() > 0:
            self.results_list.setCurrentRow(0)

    def _on_search_changed(self, text):
        if not text:
            filtered_secrets = self.all_secrets
        else:
            filtered_secrets = [s_tuple for s_tuple in self.all_secrets if text.lower() in s_tuple[0].lower()]
        self._populate_list(filtered_secrets)

    def _on_item_activated(self, item):
        item_data = item.data(Qt.UserRole)
        if not item_data:
            return
        secret_details = get_secret_from_backend(item_data["namespace"], item_data["resource"])
        self.details_widget.populate_data(secret_details)
        self._show_details_view()

    def _show_search_view(self):
        self.stack.setCurrentIndex(0)
        self.search_bar.setFocus()
        self.search_bar.selectAll()

    def _show_details_view(self):
        self.stack.setCurrentIndex(1)
        self.details_widget.back_button.setFocus()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
