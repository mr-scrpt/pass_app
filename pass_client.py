
import sys
import os
import subprocess
import json

# PySide6 imports must come BEFORE qt_material
from PySide6.QtCore import Qt, QEvent
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
)
from qt_material import apply_stylesheet

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
        self.setFocusPolicy(Qt.StrongFocus)
        self.main_layout = QVBoxLayout(self)
        self.back_button = QPushButton("Back")
        self.back_button.setToolTip("Back to list (Esc)")
        self.back_button.clicked.connect(back_callback)
        self.main_layout.addWidget(self.back_button, alignment=Qt.AlignLeft)

        self.title_label = QLabel("")
        self.title_label.setStyleSheet(f"color: {extra['primaryColor']}; font-size: 16pt; font-weight: bold; padding: 10px 0;")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.title_label)

        self.form_widget = QWidget()
        self.form_layout = QFormLayout(self.form_widget)
        self.form_layout.setRowWrapPolicy(QFormLayout.WrapAllRows)
        self.main_layout.addWidget(self.form_widget)
        self.main_layout.addStretch()

    def populate_data(self, secret_details, secret_name):
        self.title_label.setText(secret_name)
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
        row_layout = QHBoxLayout()
        line_edit = QLineEdit(value)
        line_edit.setReadOnly(True)
        if is_password:
            line_edit.setEchoMode(QLineEdit.Password)
        row_layout.addWidget(line_edit)
        toggle_button = QPushButton("Show")
        toggle_button.setToolTip("Toggle Visibility")
        toggle_button.clicked.connect(lambda: self._toggle_visibility(line_edit, toggle_button))
        row_layout.addWidget(toggle_button)
        copy_button = QPushButton("Copy")
        copy_button.setToolTip("Copy to Clipboard")
        copy_button.clicked.connect(lambda: self._copy_to_clipboard(value))
        row_layout.addWidget(copy_button)
        self.form_layout.addRow(label, row_layout)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Escape:
            self.back_button.click()
        else:
            super().keyPressEvent(event)

    def _toggle_visibility(self, line_edit, button):
        if line_edit.echoMode() == QLineEdit.Password:
            line_edit.setEchoMode(QLineEdit.Normal)
            button.setText("Hide")
        else:
            line_edit.setEchoMode(QLineEdit.Password)
            button.setText("Show")

    def _copy_to_clipboard(self, text):
        QApplication.clipboard().setText(text)

# --- Main Window ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.all_secrets = []
        self.namespace_colors = {}
        self.color_index = 0
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
        for ns_item in backend_data:
            namespace = ns_item.get("namespace", "Unknown")
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
            # Forcibly set a minimum height for the item to prevent clipping
            item.setSizeHint(QSize(0, 44))
            self.results_list.addItem(item)

            ns_color = self.namespace_colors.get(secret_data["namespace"], extra['secondaryTextColor'])
            list_item_widget = SecretListItem(secret_data["namespace"], secret_data["resource"], ns_color)
            self.results_list.setItemWidget(item, list_item_widget)

    def _on_search_changed(self, text):
        if not text:
            filtered_secrets = self.all_secrets
        else:
            filtered_secrets = [s_tuple for s_tuple in self.all_secrets if text.lower() in s_tuple[0].lower()]
        self._populate_list(filtered_secrets)

    def _on_item_activated(self, item: QListWidgetItem):
        item_data = item.data(Qt.UserRole)
        if not item_data:
            return
        secret_details = get_secret_from_backend(item_data["namespace"], item_data["resource"])
        self.details_widget.populate_data(secret_details, item.text())
        self._show_details_view()

    def _show_search_view(self):
        self.stack.setCurrentIndex(0)
        self.search_bar.setFocus()
        self.search_bar.selectAll()

    def _show_details_view(self):
        self.stack.setCurrentIndex(1)
        self.details_widget.setFocus()

def main():
    app = QApplication(sys.argv)
    apply_stylesheet(app, theme='dark_blue.xml', extra=extra)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
