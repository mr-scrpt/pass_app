import sys
import os
import subprocess
import json

# PySide6 imports must come BEFORE qt-material
from PySide6.QtCore import Qt, QEvent, QSize, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import QKeyEvent, QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
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
    QScrollArea,
)
from qt_material import apply_stylesheet
import qtawesome as qta

from ui_theme import extra, CATPPUCCIN_COLORS

from backend_utils import get_list_from_backend, get_secret_from_backend, save_secret_to_backend

# --- Custom Widgets ---

from ui_widgets import Toast, ConfirmationDialog, SecretListItem, SecretDetailWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.all_secrets = []
        self.namespace_colors = {}
        self.current_selected_item = None
        self.setWindowTitle("Pass Suite")
        self.resize(600, 450) # Increased height for the help footer
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        search_view_widget = QWidget()
        search_layout = QVBoxLayout(search_view_widget)
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search secrets...")
        search_layout.addWidget(self.search_bar)
        self.results_list = QListWidget()
        
        self.results_list.setStyleSheet("QListWidget::item { border: none; padding: 0px; } QListWidget::item:selected { background-color: rgba(137, 180, 250, 0.2); border-left: 3px solid #89b4fa; } QListWidget::item:hover { background-color: rgba(137, 180, 250, 0.1); }")
        
        search_layout.addWidget(self.results_list)
        self.stack.addWidget(search_view_widget)

        self.details_widget = SecretDetailWidget(
            main_window=self,
            back_callback=self._show_search_view,
            save_callback=self._save_secret
        )
        self.stack.addWidget(self.details_widget)
        
        self.load_data_and_populate()
        self.search_bar.textChanged.connect(self._on_search_changed)
        self.results_list.itemActivated.connect(self._on_item_activated)
        self.results_list.currentItemChanged.connect(self._on_selection_changed)
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
        namespaces_seen = []
        
        for ns_item in backend_data:
            namespace = ns_item.get("namespace", "Unknown")
            
            if namespace not in self.namespace_colors:
                if namespace not in namespaces_seen:
                    namespaces_seen.append(namespace)
                color_index = namespaces_seen.index(namespace) % len(CATPPUCCIN_COLORS)
                self.namespace_colors[namespace] = CATPPUCCIN_COLORS[color_index]
            
            for resource_name in ns_item.get("resources", []):
                plain_text = f"[{namespace}]: {resource_name}"
                item_data = {"namespace": namespace, "resource": resource_name}
                self.all_secrets.append((plain_text, item_data))
        
        self.all_secrets.sort()
        self._populate_list(self.all_secrets)

    def _populate_list(self, secrets_to_display):
        self.results_list.clear()
        for _, secret_data in secrets_to_display:
            item = QListWidgetItem()
            item.setData(Qt.UserRole, secret_data)
            
            ns_color = self.namespace_colors.get(secret_data["namespace"], extra['secondaryTextColor'])
            
            list_item_widget = SecretListItem(
                secret_data["namespace"], 
                secret_data["resource"], 
                ns_color,
                view_callback=lambda checked=False, i=item: self._view_secret_from_item(i)
            )
            
            item.setSizeHint(list_item_widget.sizeHint())
            
            self.results_list.addItem(item)
            self.results_list.setItemWidget(item, list_item_widget)

    def _on_selection_changed(self, current, previous):
        if previous:
            prev_widget = self.results_list.itemWidget(previous)
            if isinstance(prev_widget, SecretListItem):
                prev_widget.set_selected(False)
        
        if current:
            curr_widget = self.results_list.itemWidget(current)
            if isinstance(curr_widget, SecretListItem):
                curr_widget.set_selected(True)
        
        self.current_selected_item = current

    def _on_search_changed(self, text):
        if not text:
            filtered_secrets = self.all_secrets
        else:
            filtered_secrets = [s_tuple for s_tuple in self.all_secrets if text.lower() in s_tuple[0].lower()]
        self._populate_list(filtered_secrets)

    def _on_item_activated(self, item: QListWidgetItem):
        item_data = item.data(Qt.UserRole)
        if item_data:
            self._view_secret(item_data)

    def _view_secret_from_item(self, item):
        item_data = item.data(Qt.UserRole)
        if item_data:
            self._view_secret(item_data)

    def _view_secret(self, item_data):
        secret_details = get_secret_from_backend(item_data["namespace"], item_data["resource"])
        self.details_widget.populate_data(
            secret_details, 
            f"[{item_data['namespace']}] {item_data['resource']}",
            item_data['namespace'],
            item_data['resource']
        )
        self._show_details_view()

    def _save_secret(self, namespace, resource, data):
        return save_secret_to_backend(namespace, resource, data)

    def _show_search_view(self):
        if self.details_widget.is_dirty:
            dialog = ConfirmationDialog(self)
            dialog.message_label.setText("You have unsaved changes. Discard them?")
            if dialog.exec() != QDialog.Accepted:
                return # User cancelled, stay on the details page

        self.stack.setCurrentIndex(0)
        self.search_bar.setFocus()
        self.search_bar.selectAll()

    def _show_details_view(self):
        self.stack.setCurrentIndex(1)
        if self.details_widget.field_rows:
            self.details_widget._focus_field(0)

def main():
    app = QApplication(sys.argv)
    apply_stylesheet(app, theme='dark_blue.xml', extra=extra)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()