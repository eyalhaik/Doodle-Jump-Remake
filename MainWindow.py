from PySide6.QtWidgets import QMainWindow, QLabel, QLineEdit, QPushButton, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

import os
import pygame
import json

from Database import Database
from GameWindow import Game
from SettingsWindow import SettingsWindow, DEFAULT_SETTINGS, menu_music_volume
from ScoresWindow import ScoresWindow
from SkinsWindow import SkinsWindow
from HistoryWindow import HistoryWindow
from AboutWindow import AboutWindow
from paths import asset_path, sound_path, settings_path


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Doodle Jump Remake")
        self.setFixedSize(440, 420)

        self.db = Database()
        self.db.seed_skins() # seed shop skins if empty

        self.settings = self.load_settings()  # load settings from file

        self.current_player_name = None
        self.game = Game(main_window=self, db=self.db, settings=self.settings)  # create game instance

        self.bg = QLabel(self)
        self.bg.setGeometry(0, 0, 440, 420)
        # Load background image
        pm = QPixmap(asset_path("start_background.png"))
        if pm.isNull():
            pm = QPixmap(asset_path("background.png"))

        # scale to fit window
        self.bg.setPixmap(pm.scaled(self.width(), self.height(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation))

        # Player name input
        self.name_edit = QLineEdit(self)
        self.name_edit.setGeometry(110, 110, 220, 40)
        self.name_edit.setPlaceholderText("")
        self.name_edit.setAlignment(Qt.AlignCenter)
        self.name_edit.setStyleSheet(
            "background: transparent;"
            "border: none;"
            "font-size: 26px;"
        )
        self.name_edit.returnPressed.connect(self.ensure_player_from_input)

        # Invisible Buttons
        self.play_btn = self.make_invisible_button(120, 60, 210, 40) # Play
        self.play_btn.clicked.connect(self.start_game)

        self.skins_btn = self.make_invisible_button(70, 170, 300, 40) # Skins Shop
        self.skins_btn.clicked.connect(self.open_skins)

        self.scores_btn = self.make_invisible_button(110, 220, 220, 40) # High scores
        self.scores_btn.clicked.connect(self.open_scores)

        self.settings_btn = self.make_invisible_button(120, 270, 200, 40) # Settings
        self.settings_btn.clicked.connect(self.open_settings)

        self.history_btn = self.make_invisible_button(120, 320, 200, 40) # History
        self.history_btn.clicked.connect(self.open_history)

        self.about_btn = self.make_invisible_button(0, 380, 140, 40) # About
        self.about_btn.clicked.connect(self.open_about)

        self.exit_btn = self.make_invisible_button(300, 380, 140, 40) # Exit
        self.exit_btn.clicked.connect(self.close)

        # Start menu music
        self.menu_music()

        # Make sure background label stays behind everything
        self.bg.lower()
        
    def load_settings(self):
        defaults = DEFAULT_SETTINGS.copy() # start with default settings

        path = settings_path()

        if not os.path.exists(path):
            return defaults

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    defaults.update(data)
        except Exception:
            pass

        return defaults
    
    def save_settings(self):
        path = settings_path()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False) # save current settings to file even if it contains non-ASCII characters
        except Exception:
            pass

    def make_invisible_button(self, x, y, w, h):
        btn = QPushButton("", self)
        btn.setGeometry(x, y, w, h)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(
            "QPushButton { background: transparent; border: none; }"
            "QPushButton:hover { background: rgba(0, 0, 0, 18); border-radius: 18px; }"
            "QPushButton:pressed { background: rgba(0, 0, 0, 35); border-radius: 18px; }"
        )
        return btn

    def menu_music(self):  # start background music on main menu
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()

            path = sound_path("start_music.mp3")
            if not os.path.exists(path):
                return

            pygame.mixer.music.load(path)
            menu_music_volume(self.settings)  # apply volume settings
            pygame.mixer.music.play(-1)
            
        except Exception:
            pass

    def stop_menu_music(self):  # stop menu background music
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
        except Exception:
            pass

    def ensure_player_from_input(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing Name", "Please enter a player name.")
            return False

        self.db.ensure_player(name)  # creates player if not exists
        self.current_player_name = name  # set current player

        return True

    def require_player(self):  # ensure a player is selected
        typed = self.name_edit.text().strip()
        if self.current_player_name and typed == self.current_player_name:
            return True
        return self.ensure_player_from_input()

    def start_game(self):
        if not self.require_player():
            return

        self.stop_menu_music()  # stop menu music while the game runs
        self.game.set_player(self.current_player_name)  # set player in game

        self.hide()  # hide main window
        self.game.run()  # start game loop
        self.menu_music()  # resume menu music
        self.game.apply_settings(self.settings)  # apply updated settings to the game
        self.show()  # show main window again after game ends

    def open_settings(self):
        dlg = SettingsWindow(self, current_settings=self.settings, on_settings_changed=self.on_setting_changed_live) # open settings dialog
        if dlg.exec():
            self.save_settings()
            self.game.apply_settings(self.settings)  # update game parameters
            menu_music_volume(self.settings) # apply volume settings
    
    def on_setting_changed_live(self, settings: dict):
        self.settings = settings # update current settings
        self.game.apply_settings(self.settings) # apply settings to game immediately
        menu_music_volume(self.settings) # apply volume settings to menu music

    def open_scores(self):
        dlg = ScoresWindow(self, db=self.db)
        dlg.exec()

    def open_skins(self):
        if not self.require_player(): # ensure player selected
            return
        dlg = SkinsWindow(self, db=self.db, player_name=self.current_player_name)  # open skins shop
        dlg.exec()

    def open_history(self):
        if not self.require_player(): # ensure player selected
            return
        dlg = HistoryWindow(self, db=self.db, player_name=self.current_player_name)  # open history window
        dlg.exec()

    def open_about(self):
        dlg = AboutWindow(self)
        dlg.exec()

    def closeEvent(self, event):
        try:
            self.db.close()  # close database connection
        except Exception:
            pass
        event.accept()  # accept close event