import sys
import os
import subprocess
import json

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QTextEdit,
)

# --- Backend Communication ---

def get_list_from_backend():
    """Calls the backend script to get the list of secrets."""
    try:
        python_executable = os.path.join(os.path.dirname(__file__), '.venv', 'bin', 'python')
        backend_script = os.path.join(os.path.dirname(__file__), 'pass_backend.py')
        cmd = [python_executable, backend_script, "list"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except Exception as e:
        # In a real app, this should show a proper error dialog
        print(f"Error fetching list from backend: {e}", file=sys.stderr)
        if isinstance(e, subprocess.CalledProcessError):
            print(f"Backend stderr:\n{e.stderr}", file=sys.stderr)
        return None

def get_secret_from_backend(namespace, resource):
    """Calls the backend to get the details of a single secret."""
    try:
        python_executable = os.path.join(os.path.dirname(__file__), '.venv', 'bin', 'python')
        backend_script = os.path.join(os.path.dirname(__file__), 'pass_backend.py')
        cmd = [python_executable, backend_script, "show"]
        input_data = json.dumps({"namespace": namespace, "resource": resource})
        result = subprocess.run(cmd, input=input_data, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error fetching secret from backend: {e}")
        return None

# --- Main Window ---

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pass Suite")
        self.resize(800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Namespaces"])
        splitter.addWidget(self.tree)

        self.details_view = QTextEdit()
        self.details_view.setReadOnly(True)
        self.details_view.setFontFamily("monospace")
        splitter.addWidget(self.details_view)

        splitter.setSizes([250, 550])

        self.populate_tree()
        self.tree.currentItemChanged.connect(self.on_item_selected)

    def populate_tree(self):
        """Fetches data and populates the tree widget, storing data on each item."""
        self.tree.clear()
        data = get_list_from_backend()
        # If data is None, it indicates a backend error. An empty list is valid.
        if data is None:
            error_item = QTreeWidgetItem(self.tree)
            error_item.setText(0, "Error loading data")
            return

        for ns_item in data:
            namespace_name = ns_item.get("namespace", "Unknown")
            namespace_node = QTreeWidgetItem(self.tree)
            namespace_node.setText(0, namespace_name)

            for resource_name in ns_item.get("resources", []):
                resource_node = QTreeWidgetItem(namespace_node)
                resource_node.setText(0, resource_name)
                # Store the necessary data on the item itself
                resource_data = {"namespace": namespace_name, "resource": resource_name}
                resource_node.setData(0, Qt.UserRole, resource_data)
        
        self.tree.expandAll()

    def on_item_selected(self, current_item, previous_item):
        """Handler for when the selected item in the tree changes."""
        self.details_view.clear()
        if not current_item:
            return

        # Retrieve the data we stored on the item
        item_data = current_item.data(0, Qt.UserRole)

        # item_data will be None for top-level namespace nodes
        if item_data:
            namespace = item_data["namespace"]
            resource = item_data["resource"]
            
            secret_details = get_secret_from_backend(namespace, resource)
            
            if secret_details:
                # Format the output string
                secret = secret_details.pop("secret", "[No secret found]")
                formatted_text = f"{secret}\n\n---\n"
                for key, value in secret_details.items():
                    formatted_text += f"{key}: {value}\n"
                self.details_view.setText(formatted_text)
            else:
                self.details_view.setText(f"Could not load secret: {namespace}/{resource}")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()