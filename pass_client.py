import sys
from PySide6.QtCore import Qt, QEvent, QTimer, QThread, Signal
from PySide6.QtGui import QKeyEvent, QMovie
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
    QDialog,
    QLabel
)
from qt_material import apply_stylesheet

from backend_utils import (
    get_list_from_backend, 
    get_secret_from_backend, 
    save_secret_to_backend,
    git_push_to_backend,
    git_pull_from_backend,
    git_status_from_backend
)
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

class GitSyncWorker(QThread):
    """Worker thread for asynchronous git operations."""
    finished = Signal(bool, str, str)  # success, message, operation_type
    
    def __init__(self, operation_type):
        super().__init__()
        self.operation_type = operation_type  # 'sync', 'push', 'pull', 'status'
    
    def run(self):
        try:
            if self.operation_type == 'sync':
                # Pull first
                pull_result = git_pull_from_backend()
                if pull_result.get("status") == "error":
                    self.finished.emit(False, f"Pull failed: {pull_result.get('message', 'Unknown error')}", 'sync')
                    return
                
                # Then push
                push_result = git_push_to_backend()
                if push_result.get("status") == "error":
                    self.finished.emit(False, f"Push failed: {push_result.get('message', 'Unknown error')}", 'sync')
                    return
                
                self.finished.emit(True, "Successfully synced with remote.", 'sync')
            
            elif self.operation_type == 'push':
                result = git_push_to_backend()
                if result.get("status") == "error":
                    self.finished.emit(False, f"Push failed: {result.get('message', 'Unknown error')}", 'push')
                else:
                    self.finished.emit(True, result.get('message', 'Successfully pushed'), 'push')
            
            elif self.operation_type == 'pull':
                result = git_pull_from_backend()
                if result.get("status") == "error":
                    self.finished.emit(False, f"Pull failed: {result.get('message', 'Unknown error')}", 'pull')
                else:
                    self.finished.emit(True, result.get('message', 'Successfully pulled'), 'pull')
            
            elif self.operation_type == 'status':
                status = git_status_from_backend()
                # For status, we just emit success with the status data as message
                import json
                self.finished.emit(True, json.dumps(status), 'status')
        
        except Exception as e:
            self.finished.emit(False, str(e), self.operation_type)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.all_secrets = []
        self.namespace_colors = {}
        self.namespace_resources = {}  # {namespace: [resource1, resource2, ...]}
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
        
        # Sync button with status indicator
        self.sync_button = QPushButton()
        self.sync_button.setIcon(qta.icon('fa5s.sync-alt', color='#89b4fa'))
        self.sync_button.setToolTip("Sync with remote (Ctrl+R)")
        self.sync_button.setFixedSize(40, 40)
        self.sync_button.clicked.connect(self._handle_sync)
        search_header_layout.addWidget(self.sync_button)
        
        # Sync loader (spinner)
        self.sync_loader = QLabel("⟳")
        self.sync_loader.setStyleSheet("color: #89b4fa; font-size: 20px;")
        self.sync_loader.setToolTip("Syncing...")
        self.sync_loader.setFixedWidth(20)
        self.sync_loader.hide()  # Hidden by default
        search_header_layout.addWidget(self.sync_loader)
        
        # Animation timer for loader
        self.loader_timer = QTimer()
        self.loader_timer.timeout.connect(self._animate_loader)
        self.loader_rotation = 0
        
        # Sync status indicator (dot)
        self.sync_status_indicator = QLabel("●")
        self.sync_status_indicator.setStyleSheet("color: #6c7086; font-size: 16px;")  # Gray by default
        self.sync_status_indicator.setToolTip("Sync status")
        self.sync_status_indicator.setFixedWidth(20)
        search_header_layout.addWidget(self.sync_status_indicator)
        
        # Worker thread for git operations
        self.git_worker = None
        
        self.create_button = QPushButton()
        self.create_button.setIcon(qta.icon('fa5s.plus', color='#a6e3a1'))
        self.create_button.setToolTip("Create new secret (Ctrl+N)")
        self.create_button.setFixedSize(40, 40)
        self.create_button.clicked.connect(self._show_create_view)
        search_header_layout.addWidget(self.create_button)
        
        search_layout.addWidget(search_header)
        
        # Initialize sync status check
        self.sync_status_timer = QTimer()
        self.sync_status_timer.timeout.connect(self._check_git_status_async)
        self.sync_status_timer.start(30000)  # Check every 30 seconds
        
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
            show_status_callback=self.status_bar.show_status,
            namespace_colors=self.namespace_colors,
            namespaces=list(self.namespace_colors.keys()),
            namespace_resources=self.namespace_resources
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
        
        # Check git status on startup (async)
        QTimer.singleShot(1000, self._check_git_status_async)

    def _register_hotkeys(self):
        self.hotkey_manager.register('ctrl+g', self.handle_simple_generate, priority=20)
        self.hotkey_manager.register('ctrl+shift+g', self.handle_advanced_generate, priority=20)
        self.hotkey_manager.register('esc', self.handle_esc, priority=10)
        self.hotkey_manager.register('ctrl+s', self.handle_save, priority=10)
        self.hotkey_manager.register('ctrl+r', self.handle_sync, priority=10)
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
                "nav": "<b>Navigate:</b> ↑/↓ &nbsp;&nbsp; <b>Back:</b> Esc",
                "action": "<b>Add Field:</b> Ctrl+N &nbsp;&nbsp; <b>Add Tag:</b> Ctrl+T &nbsp;&nbsp; <b>Save:</b> Ctrl+S"
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
    
    def handle_sync(self, event):
        """Handle Ctrl+R for sync on search view."""
        if self.stack.currentIndex() == 0:  # Search view
            self._handle_sync()
            return True
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
        self.namespace_resources = {}  # Reset namespace resources
        namespaces_seen = []
        
        for ns_item in backend_data:
            namespace = ns_item.get("namespace", "Unknown")
            
            if namespace not in self.namespace_colors:
                if namespace not in namespaces_seen:
                    namespaces_seen.append(namespace)
                color_index = namespaces_seen.index(namespace) % len(CATPPUCCIN_COLORS)
                self.namespace_colors[namespace] = CATPPUCCIN_COLORS[color_index]
            
            # Build namespace_resources dictionary
            resources = ns_item.get("resources", [])
            self.namespace_resources[namespace] = resources
            
            for resource_name in resources:
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
        # Update namespaces and resources before showing
        self.create_widget.update_namespaces(
            list(self.namespace_colors.keys()),
            self.namespace_colors,
            self.namespace_resources
        )
        self.update_help_text("create")
        self.stack.setCurrentIndex(2)
        # Focus on tags section (first element)
        self.create_widget.namespace_main_container.setFocus()
        self.create_widget._on_tags_focus_in()
    
    def _show_search_view_from_create(self):
        self.load_data_and_populate()
        self._show_search_view()
    
    def _handle_sync(self):
        """Handle git synchronization (pull then push) asynchronously."""
        if self.git_worker and self.git_worker.isRunning():
            return  # Already syncing
        
        self.status_bar.show_status("Syncing with remote...", "info")
        self.sync_button.setEnabled(False)
        
        # Show loader and start animation
        self.sync_status_indicator.hide()
        self.sync_loader.show()
        self.loader_timer.start(50)  # Update every 50ms
        
        # Start async sync
        self.git_worker = GitSyncWorker('sync')
        self.git_worker.finished.connect(self._on_sync_finished)
        self.git_worker.start()
    
    def _on_sync_finished(self, success, message, operation_type):
        """Handle completion of git sync operation."""
        # Stop loader animation
        self.loader_timer.stop()
        self.sync_loader.hide()
        self.sync_status_indicator.show()
        self.sync_button.setEnabled(True)
        
        if success:
            # Reload data
            self.load_data_and_populate()
            self.status_bar.show_status(message, "success")
            # Check status to update indicator
            self._check_git_status_async()
        else:
            self.status_bar.show_status(message, "error")
    
    def _animate_loader(self):
        """Animate the sync loader."""
        # Simple rotation animation using unicode arrows
        arrows = ['⟳', '↻', '⟲', '↺']
        self.loader_rotation = (self.loader_rotation + 1) % len(arrows)
        self.sync_loader.setText(arrows[self.loader_rotation])
    
    def _check_git_status(self):
        """Check git status and update indicator (synchronous - for backward compatibility)."""
        status = git_status_from_backend()
        self._update_status_indicator(status)
    
    def _check_git_status_async(self):
        """Check git status asynchronously."""
        if self.git_worker and self.git_worker.isRunning():
            return  # Another operation is running
        
        self.git_worker = GitSyncWorker('status')
        self.git_worker.finished.connect(self._on_status_check_finished)
        self.git_worker.start()
    
    def _on_status_check_finished(self, success, message, operation_type):
        """Handle completion of git status check."""
        if success:
            import json
            status = json.loads(message)
            self._update_status_indicator(status)
    
    def _update_status_indicator(self, status):
        """Update the sync status indicator based on git status."""
        if not status.get("has_remote", False):
            # No remote configured - gray dot
            self.sync_status_indicator.setStyleSheet("color: #6c7086; font-size: 16px;")
            self.sync_status_indicator.setToolTip("No git remote configured")
            return
        
        needs_push = status.get("needs_push", False)
        needs_pull = status.get("needs_pull", False)
        
        if needs_push or needs_pull:
            # Changes to sync - yellow dot
            self.sync_status_indicator.setStyleSheet("color: #f9e2af; font-size: 16px;")
            tooltip = []
            if needs_pull:
                tooltip.append(f"Behind remote by {status.get('behind', 0)} commits")
            if needs_push:
                tooltip.append(f"Ahead of remote by {status.get('ahead', 0)} commits")
            self.sync_status_indicator.setToolTip("\n".join(tooltip))
        else:
            # Everything synced - green dot
            self.sync_status_indicator.setStyleSheet("color: #a6e3a1; font-size: 16px;")
            self.sync_status_indicator.setToolTip("Synced with remote")

def main():
    app = QApplication(sys.argv)
    apply_stylesheet(app, theme='dark_blue.xml', extra=extra)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()