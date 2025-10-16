import sys
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
    QDialog
)
from qt_material import apply_stylesheet

from backend_utils import get_list_from_backend, get_secret_from_backend, save_secret_to_backend
from ui_theme import CATPPUCCIN_COLORS, extra
from components.confirmation_dialog import ConfirmationDialog
from components.hotkey_help import HotkeyHelpWidget
from components.secret_detail_view import SecretDetailWidget
from components.secret_create_view import SecretCreateWidget
from components.secret_list_item import SecretListItem
from components.password_generator_dialog import PasswordGeneratorDialog
from components.status_bar import StatusBarWidget
from hotkey_manager import HotkeyManager
from utils import generate_password

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.all_secrets = []
        self.namespace_colors = {}
        self.current_selected_item = None
        self.setWindowTitle("Pass Suite")
        self.resize(800, 600)

        self.hotkey_manager = HotkeyManager()

        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setCentralWidget(main_widget)

        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

        self.status_bar = StatusBarWidget()
        main_layout.addWidget(self.status_bar)

        self.nav_help_widget = HotkeyHelpWidget()
        self.action_help_widget = HotkeyHelpWidget()
        main_layout.addWidget(self.nav_help_widget)
        main_layout.addWidget(self.action_help_widget)

        # --- Search View ---
        self.search_view = QWidget()
        search_layout = QVBoxLayout(self.search_view)
        
        # Add create button to search view
        search_header = QWidget()
        search_header_layout = QHBoxLayout(search_header)
        search_header_layout.setContentsMargins(0, 0, 0, 0)
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search secrets...")
        search_header_layout.addWidget(self.search_bar, stretch=1)
        
        import qtawesome as qta
        self.create_button = QPushButton()
        self.create_button.setIcon(qta.icon('fa5s.plus', color='#a6e3a1'))
        self.create_button.setToolTip("Create new secret (Ctrl+N)")
        self.create_button.setFixedSize(40, 40)
        self.create_button.clicked.connect(self._show_create_view)
        search_header_layout.addWidget(self.create_button)
        
        search_layout.addWidget(search_header)
        
        self.results_list = QListWidget()
        self.results_list.setStyleSheet("QListWidget::item { border: none; padding: 0px; } QListWidget::item:selected { background-color: rgba(137, 180, 250, 0.2); border-left: 3px solid #89b4fa; } QListWidget::item:hover { background-color: rgba(137, 180, 250, 0.1); }")
        search_layout.addWidget(self.results_list)
        self.stack.addWidget(self.search_view)

        # --- Details View ---
        self.details_widget = SecretDetailWidget(
            back_callback=self._show_search_view,
            save_callback=self._save_secret,
            show_status_callback=self.status_bar.show_status
        )
        self.details_widget.state_changed.connect(self.update_help_text)
        self.stack.addWidget(self.details_widget)
        
        # --- Create View ---
        self.create_widget = SecretCreateWidget(
            back_callback=self._show_search_view_from_create,
            save_callback=self._save_secret,
            show_status_callback=self.status_bar.show_status
        )
        self.create_widget.state_changed.connect(self.update_help_text)
        self.stack.addWidget(self.create_widget)

        # --- Initial Load & Connections ---
        self.load_data_and_populate()
        self.search_bar.textChanged.connect(self._on_search_changed)
        self.results_list.itemActivated.connect(self._on_item_activated)
        self.results_list.currentItemChanged.connect(self._on_selection_changed)
        
        self.installEventFilter(self)
        self._register_hotkeys()
        self._show_search_view()

    def _register_hotkeys(self):
        self.hotkey_manager.register('ctrl+g', self.handle_simple_generate, priority=20)
        self.hotkey_manager.register('ctrl+shift+g', self.handle_advanced_generate, priority=20)
        self.hotkey_manager.register('esc', self.handle_esc, priority=10)
        self.hotkey_manager.register('ctrl+s', self.handle_save, priority=10)
        self.hotkey_manager.register('ctrl+n', self.handle_add_field, priority=8)
        self.hotkey_manager.register('down', self.handle_search_nav, priority=5)
        self.hotkey_manager.register('up', self.handle_search_nav, priority=5)
        self.hotkey_manager.register('return', self.handle_search_activate, priority=5)
        self.hotkey_manager.register('enter', self.handle_search_activate, priority=5)

    def eventFilter(self, source, event):
        if event.type() == QEvent.KeyPress:
            if self.hotkey_manager.handle(event):
                return True
        return super().eventFilter(source, event)

    def update_help_text(self, state):
        help_texts = {
            "search": {
                "nav": "<b>Navigate:</b> ↑/↓",
                "action": "<b>View:</b> Enter &nbsp;&nbsp; <b>Create New:</b> Ctrl+N &nbsp;&nbsp; <b>Generate Pass:</b> Ctrl+G / Ctrl+Shift+G"
            },
            "normal": {
                "nav": "<b>Navigate:</b> ↑/↓, Tab &nbsp;&nbsp; <b>Back:</b> Esc",
                "action": "<b>Copy:</b> Enter &nbsp;<b>Edit:</b> Ctrl+E &nbsp;<b>Deep Edit:</b> Ctrl+Shift+E &nbsp;<b>New Field:</b> Ctrl+N &nbsp;<b>Save:</b> Ctrl+S"
            },
            "edit": {
                "nav": "",
                "action": "<b>Cancel Edit:</b> Esc"
            },
            "deep_edit": {
                "nav": "<b>Navigate:</b> Tab",
                "action": "<b>Confirm:</b> Enter &nbsp;&nbsp; <b>Delete:</b> Ctrl+D &nbsp;&nbsp; <b>Cancel:</b> Esc"
            },
            "add_new": {
                "nav": "<b>Navigate:</b> Tab",
                "action": "<b>Confirm:</b> Enter &nbsp;&nbsp; <b>Cancel:</b> Esc"
            },
            "create": {
                "nav": "<b>Navigate:</b> Tab &nbsp;&nbsp; <b>Back:</b> Esc",
                "action": "<b>Add Field:</b> Click + Button &nbsp;&nbsp; <b>Save:</b> Ctrl+S"
            }
        }
        texts = help_texts.get(state, {"nav": "", "action": ""})
        self.nav_help_widget.setText(texts['nav'])
        self.action_help_widget.setText(texts['action'])

    def handle_simple_generate(self, event):
        password = generate_password()
        QApplication.clipboard().setText(password)
        self.status_bar.show_status("Password generated and copied to clipboard.")
        return True

    def handle_advanced_generate(self, event):
        dialog = PasswordGeneratorDialog(self, show_status_callback=self.status_bar.show_status)
        dialog.exec()
        return True

    def handle_esc(self, event):
        return False

    def handle_save(self, event):
        return False

    def handle_add_field(self, event):
        if self.stack.currentWidget() == self.search_view:
            self._show_create_view()
            return True
        elif self.stack.currentWidget() == self.details_widget:
            self.details_widget.add_new_field_row()
            return True
        return False

    def handle_search_nav(self, event):
        if self.stack.currentWidget() == self.search_view and self.search_bar.hasFocus():
            self.results_list.setFocus()
            QApplication.postEvent(self.results_list, QKeyEvent(event))
            return True
        return False

    def handle_search_activate(self, event):
        if self.stack.currentWidget() == self.search_view and self.results_list.hasFocus():
            if self.results_list.currentItem():
                self._on_item_activated(self.results_list.currentItem())
                return True
        return False

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

        self.update_help_text("search")
        self.stack.setCurrentIndex(0)
        self.search_bar.setFocus()
        self.search_bar.selectAll()

    def _show_details_view(self):
        self.update_help_text("normal")
        self.stack.setCurrentIndex(1)
        if self.details_widget.field_rows:
            self.details_widget._focus_field(0)
    
    def _show_create_view(self):
        self.update_help_text("create")
        self.stack.setCurrentIndex(2)
        self.create_widget.namespace_input.setFocus()
    
    def _show_search_view_from_create(self):
        self.load_data_and_populate()
        self._show_search_view()

def main():
    app = QApplication(sys.argv)
    apply_stylesheet(app, theme='dark_blue.xml', extra=extra)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()