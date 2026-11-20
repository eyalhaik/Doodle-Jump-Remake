import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QFontDatabase, QIcon
from MainWindow import MainWindow
from paths import asset_path, font_path


if __name__ == "__main__":
    app = QApplication(sys.argv)
    QFontDatabase.addApplicationFont(font_path("PatrickHand-Regular.ttf"))
    app.setFont(QFont("Patrick Hand", 11))
    app.setWindowIcon(QIcon(asset_path("icon.ico"))) # Set the application icon
    window = MainWindow()
    window.show()
    sys.exit(app.exec())