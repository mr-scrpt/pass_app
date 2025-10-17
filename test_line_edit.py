import sys

from PySide6.QtWidgets import QApplication, QLineEdit, QMainWindow, QVBoxLayout, QWidget
from qt_material import apply_stylesheet

from ui_theme import extra


class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QLineEdit Cursor Test")
        self.resize(400, 300)

        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        self.setCentralWidget(main_widget)

        main_layout.addWidget(QLineEdit("Test Input 1"))
        main_layout.addWidget(QLineEdit("Test Input 2"))
        main_layout.addWidget(QLineEdit("Test Input 3"))


def main():
    app = QApplication(sys.argv)
    apply_stylesheet(app, theme="dark_blue.xml", extra=extra)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
