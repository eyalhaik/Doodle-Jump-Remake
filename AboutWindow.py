import os
import webbrowser

from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QMessageBox
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices # to open demo video
from paths import data_dir
from AboutAuthor import AboutAuthor


class AboutWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About")
        self.setFixedSize(520, 300)
        # Title
        title = QLabel("Game Rules", self)
        title.setGeometry(10, 10, 500, 25)
        title.setAlignment(Qt.AlignCenter)

        txt = QLabel(
            "Doodle Jump Remake is a simple game:\n"
            "Try to jump as high as possible!\n"
            "Gain points by landing on platforms and avoiding obstacles.\n"
            "Get as many coins as possible to buy new Doodles in the shop!\n"
            "Important controls:\n"
            "P - pauses the game\n"
            "ESC - returns to menu\n"
            "SPACE - restarts on game over",
            self
        )
        txt.setGeometry(20, 50, 480, 140)
        txt.setAlignment(Qt.AlignCenter)
        # Demo video button
        self.video_btn = QPushButton("Play Demo Video", self)
        self.video_btn.setGeometry(20, 215, 160, 35)
        self.video_btn.clicked.connect(self.open_video)
        # About the author
        self.author_btn = QPushButton("About the Author", self)
        self.author_btn.setGeometry(190, 215, 160, 35)
        self.author_btn.clicked.connect(self.show_author_info)
        # Close button
        self.close_btn = QPushButton("Close", self)
        self.close_btn.setGeometry(410, 245, 90, 35)
        self.close_btn.clicked.connect(self.close)

    def open_video(self):
        demo_path = os.path.join(data_dir(), "demo.mp4")
        if not os.path.exists(demo_path):
            QMessageBox.warning(self, "Missing file", "Put demo.mp4 inside the data folder.")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(demo_path))

    def show_author_info(self):
        dlg = AboutAuthor()
        dlg.exec()