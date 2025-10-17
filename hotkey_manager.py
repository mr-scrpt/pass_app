from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence


class HotkeyManager:
    def __init__(self):
        self.handlers = {}

    def register(self, key_combo, handler, priority=0):
        if key_combo not in self.handlers:
            self.handlers[key_combo] = []
        self.handlers[key_combo].append((priority, handler))
        self.handlers[key_combo].sort(key=lambda x: x[0], reverse=True)

    def unregister(self, key_combo, handler):
        if key_combo in self.handlers:
            self.handlers[key_combo] = [(p, h) for p, h in self.handlers[key_combo] if h != handler]

    def handle(self, event):
        key = event.key()
        modifiers = event.modifiers()

        key_combo = ""
        if modifiers & Qt.ControlModifier:
            key_combo += "ctrl+"
        if modifiers & Qt.ShiftModifier:
            key_combo += "shift+"
        if modifiers & Qt.AltModifier:
            key_combo += "alt+"
        key_combo += QKeySequence(key).toString().lower()

        if key_combo in self.handlers:
            for priority, handler in self.handlers[key_combo]:
                if handler(event):
                    return True
        return False
