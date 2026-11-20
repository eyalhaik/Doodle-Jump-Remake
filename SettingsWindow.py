import pygame

from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QSlider, QComboBox
from PySide6.QtCore import Qt


DEFAULT_SETTINGS = {
    "music_volume": 70,
    "sfx_volume": 70,
    "window_size": [700, 500],
    "muted": False
}


def menu_music_volume(settings: dict): # apply music volume based on settings
    try:
        if not pygame.mixer.get_init(): # initialize mixer if not already done
            pygame.mixer.init()

        muted = bool(settings.get("muted", False)) # get muted state from settings
        music_percent = int(settings.get("music_volume", 70)) # get music volume percentage from settings

        if muted:
            pygame.mixer.music.set_volume(0.0)
        else:
            vol = max(0.0, min(1.0, music_percent / 100.0)) # clamp volume between 0.0 and 1.0
            pygame.mixer.music.set_volume(vol)
    except Exception:
        pass

class SettingsWindow(QDialog):
    def __init__(self, parent=None, current_settings=None, on_settings_changed=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setFixedSize(420, 260)

        self.settings = (current_settings or DEFAULT_SETTINGS).copy() # load current settings or default settings 
        self.on_settings_changed = on_settings_changed
        # Music Volume
        QLabel("Music Volume:", self).setGeometry(20, 30, 130, 25)
        self.music_slider = QSlider(Qt.Horizontal, self)
        self.music_slider.setGeometry(160, 30, 230, 25)
        self.music_slider.setRange(0, 10)
        self.music_slider.setSingleStep(1)
        self.music_slider.setTickPosition(QSlider.TicksBelow)
        self.music_slider.setTickInterval(1)

        mv = int(self.settings.get("music_volume", 70)) # get current music volume from settings
        self.music_slider.setValue(max(0, min(10, int(round(mv / 10))))) # set slider value (0-10)
        # SFX Volume
        QLabel("SFX Volume:", self).setGeometry(20, 70, 130, 25)
        self.sfx_slider = QSlider(Qt.Horizontal, self)
        self.sfx_slider.setGeometry(160, 70, 230, 25)
        self.sfx_slider.setRange(0, 10)
        self.sfx_slider.setSingleStep(1)
        self.sfx_slider.setTickPosition(QSlider.TicksBelow)
        self.sfx_slider.setTickInterval(1)

        sv = int(self.settings.get("sfx_volume", 70))
        self.sfx_slider.setValue(max(0, min(10, int(round(sv / 10)))))
        # Window Size
        QLabel("Window Size:", self).setGeometry(20, 110, 130, 25)
        self.size_combo = QComboBox(self)
        self.size_combo.setGeometry(160, 110, 230, 25)
        self.size_combo.addItems(["560x400", "700x500", "840x600"])

        w, h = self.settings.get("window_size", [700, 500]) # get current window size from settings
        current = f"{w}x{h}"
        idx = self.size_combo.findText(current) # find index of current size
        if idx != -1: # if found, set combo box to it
            self.size_combo.setCurrentIndex(idx) # set combo box to current size
        # Mute Button
        self.mute_btn = QPushButton(self)
        self.mute_btn.setGeometry(160, 200, 110, 35)
        self.mute_btn.clicked.connect(self.on_toggle_mute)
        self.mute_button_text()
        # Close Button
        self.close_btn = QPushButton("Close", self)
        self.close_btn.setGeometry(280, 200, 110, 35)
        self.close_btn.clicked.connect(self.accept)
        # Auto-save
        self.music_slider.valueChanged.connect(self.auto_save)
        self.sfx_slider.valueChanged.connect(self.auto_save)
        self.size_combo.currentIndexChanged.connect(self.auto_save)

        menu_music_volume(self.settings)

    def mute_button_text(self): # update mute button text based on settings
        muted = bool(self.settings.get("muted", False))
        self.mute_btn.setText("Unmute" if muted else "Mute")

    def read_ui_into_settings(self): # read current UI values into settings dict
        try:
            w_str, h_str = self.size_combo.currentText().split("x")
            self.settings["window_size"] = [int(w_str), int(h_str)]
        except Exception:
            self.settings["window_size"] = [700, 500] # default size on error

        self.settings["music_volume"] = int(self.music_slider.value()) * 10
        self.settings["sfx_volume"] = int(self.sfx_slider.value()) * 10

    def auto_save(self, *args): # auto-save settings on change
        self.read_ui_into_settings()
        menu_music_volume(self.settings)

        if callable(self.on_settings_changed): # notify callback if set
            self.on_settings_changed(self.settings)

    def on_toggle_mute(self): # toggle mute setting
        muted = not bool(self.settings.get("muted", False))
        self.settings["muted"] = muted

        self.music_slider.setEnabled(not muted)
        self.sfx_slider.setEnabled(not muted)

        self.mute_button_text()

        self.read_ui_into_settings() # read current UI values into settings dict

        menu_music_volume(self.settings) # apply music volume

        if callable(self.on_settings_changed):
            self.on_settings_changed(self.settings)

    def get_settings(self): # return current settings dict
        self.read_ui_into_settings()
        return self.settings