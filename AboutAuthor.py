from PySide6.QtWidgets import QDialog, QLabel, QPushButton
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtCore import Qt

from paths import asset_path


class AboutAuthor(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("About The Author")
        self.setFixedSize(420, 280)
        self.setStyleSheet("background-color: #f4f4f4;")

        # כותרת
        self.title_label = QLabel("Information About the Author", self)
        self.title_label.setGeometry(20, 10, 380, 30)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(QFont("Patrick Hand", 16, QFont.Bold))

        # פרטי כותב
        self.info_label = QLabel(self)
        self.info_label.setGeometry(160, 60, 230, 120)
        self.info_label.setText(
            "Author: Eyal Haik\n"
            "Course: Practical Programming\n"
            "Instructor: Dr. Tal Alon\n"
            "Year: 2025/26"
        )
        self.info_label.setFont(QFont("Patrick Hand", 12))
        self.info_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        # תמונה
        self.image_label = QLabel(self)
        self.image_label.setGeometry(20, 60, 100, 110)
        pix = QPixmap(asset_path("me.jpg"))
        if not pix.isNull():
            self.image_label.setPixmap(
                pix.scaled(100, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
            self.image_label.setStyleSheet("border: 1px solid #999;")
        else:
            self.image_label.setText("No image")
            self.image_label.setAlignment(Qt.AlignCenter)
            self.image_label.setStyleSheet("border: 1px solid #999;")

        # לינק לפרופיל לינקדאין
        self.link_label = QLabel(self)
        self.link_label.setGeometry(20, 230, 260, 20)
        self.link_label.setText(
            '<a href="https://www.linkedin.com/in/eyal-haik-89445b368?utm_source=share_via&utm_content=profile&utm_medium=member_ios">LinkedIn Profile</a>'
        )
        self.link_label.setOpenExternalLinks(True)
        self.link_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.link_label.setFont(QFont("Patrick Hand", 11, QFont.Bold))

        # כפתור סגירה
        self.close_button = QPushButton("Close", self)
        self.close_button.setGeometry(320, 225, 70, 28)
        self.close_button.clicked.connect(self.close)