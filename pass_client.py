import sys
from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QStackedWidget,
    QDialog
)
from qt_material import apply_stylesheet

from backend_utils import get_list_from_backend, get_secret_from_backend, save_secret_to_backend
from ui_theme import CATPPUCCIN_COLORS, extra
from components.confirmation_dialog import ConfirmationDialog
from components.hotkey_help import HotkeyHelpWidget
from components.secret_detail_view import SecretDetailWidget
from components.secret_list_item import SecretListItem
from hotkey_manager import HotkeyManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.all_secrets = []
        self.namespace_colors = {}
        self.current_selected_item = None
        self.setWindowTitle("Pass Suite")
        self.resize(600, 450)

        self.hotkey_manager = HotkeyManager()

        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setCentralWidget(main_widget)

        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

        self.help_widget = HotkeyHelpWidget()
        main_layout.addWidget(self.help_widget)

        # --- Search View ---
        self.search_view = QWidget()
        search_layout = QVBoxLayout(self.search_view)
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search secrets...")
        search_layout.addWidget(self.search_bar)
        self.results_list = QListWidget()
        self.results_list.setStyleSheet("QListWidget::item { border: none; padding: 0px; } QListWidget::item:selected { background-color: rgba(137, 180, 250, 0.2); border-left: 3px solid #89b4fa; } QListWidget::item:hover { background-color: rgba(137, 180, 250, 0.1); }")
        search_layout.addWidget(self.results_list)
        self.stack.addWidget(self.search_view)

        # --- Details View ---
        self.details_widget = SecretDetailWidget(
            back_callback=self._show_search_view,
            save_callback=self._save_secret
        )
        self.stack.addWidget(self.details_widget)

        # --- Initial Load & Connections ---
        self.load_data_and_populate()
        self.search_bar.textChanged.connect(self._on_search_changed)
        self.results_list.itemActivated.connect(self._on_item_activated)
        self.results_list.currentItemChanged.connect(self._on_selection_changed)
        
        self.installEventFilter(self)
        self._register_hotkeys()
        self._show_search_view()

    def _register_hotkeys(self):
        # Global hotkeys (high priority)
        self.hotkey_manager.register('esc', self.handle_esc, priority=10)
        self.hotkey_manager.register('ctrl+s', self.handle_save, priority=10)

        # Search view hotkeys (low priority)
        self.hotkey_manager.register('down', self.handle_search_nav, priority=5)
        self.hotkey_manager.register('up', self.handle_search_nav, priority=5)
        self.hotkey_manager.register('return', self.handle_search_activate, priority=5)
        self.hotkey_manager.register('enter', self.handle_search_activate, priority=5)

        self.hotkey_manager.register('ctrl+n', self.handle_add_field, priority=8)

    def eventFilter(self, source, event):
        if event.type() == QEvent.KeyPress:
            if self.hotkey_manager.handle(event):
                return True
        return super().eventFilter(source, event)

    # --- Hotkey Handlers ---
    def handle_esc(self, event):
        if self.stack.currentWidget() == self.details_widget:
            self.details_widget.back_button.click()
            return True
        return False

    def handle_save(self, event):
        if self.stack.currentWidget() == self.details_widget:
            self.details_widget._prompt_to_save()
            return True
        return False

    def handle_search_nav(self, event):
        if self.stack.currentWidget() == self.search_view and self.search_bar.hasFocus():
            self.results_list.setFocus()
            QApplication.postEvent(self.results_list, QKeyEvent(event))
            return True
        return False

    def handle_search_activate(self, event):
        if self.stack.currentWidget() == self.search_view and self.results_list.currentItem():
            self._on_item_activated(self.results_list.currentItem())
            return True
        return False

    def handle_add_field(self, event):
        if self.stack.currentWidget() == self.details_widget:
            self.details_widget.add_new_field_row()
            return True
        return False

    # --- Data & UI Logic ---
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
                return

        self.help_widget.setText("<b>Navigate:</b> ↑/↓ &nbsp;&nbsp; <b>View Secret:</b> Enter")
        self.stack.setCurrentIndex(0)
        self.search_bar.setFocus()
        self.search_bar.selectAll()

    def _show_details_view(self):
        self.help_widget.setText("<b>Navigate:</b> ↑/↓, Tab &nbsp;&nbsp; <b>Copy:</b> Enter, Ctrl+C &nbsp;&nbsp; <b>Edit:</b> Ctrl+E &nbsp;&nbsp; <b>Save:</b> Ctrl+S &nbsp;&nbsp; <b>Back:</b> Esc")
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
