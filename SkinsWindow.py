import os
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QWidget,
)
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPixmap
from paths import assets_dir


class SkinsWindow(QDialog):
    def __init__(self, parent=None, db=None, player_name=None):
        super().__init__(parent)
        self.db = db
        self.player_name = player_name

        self.setWindowTitle("Skins Shop")
        self.setFixedSize(390, 430)
        
        self.title = QLabel(f"Player: {self.player_name} | Coins: 0", self)
        self.title.setGeometry(10, 10, 350, 25)

        self.table = QTableWidget(self)
        self.table.setGeometry(10, 40, 370, 320)
        self.table.setColumnCount(5) # Key, Skin, Price, Owned, Active
        self.table.setHorizontalHeaderLabels(["Key", "Skin", "Price", "Owned", "Active"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers) # no editing
        self.table.setSelectionBehavior(QTableWidget.SelectRows) # select whole row
        self.table.setSelectionMode(QTableWidget.SingleSelection) # single row only

        self.table.setColumnHidden(0, True) # Column 0 is hidden and keeps the real skin key

        self.buy_btn = QPushButton("Buy Selected", self)
        self.buy_btn.setGeometry(30, 370, 100, 45)
        self.buy_btn.clicked.connect(self.buy_selected)

        self.set_btn = QPushButton("Set Active", self)
        self.set_btn.setGeometry(145, 370, 100, 45)
        self.set_btn.clicked.connect(self.set_active)

        self.close_btn = QPushButton("Close", self)
        self.close_btn.setGeometry(260, 370, 100, 45)
        self.close_btn.clicked.connect(self.close)

        self.refresh() # load skins into table

    def skin_sheet_path(self, skin_key): # return path to skin's sprite sheet
        assets = assets_dir()
        if skin_key == "default":
            return os.path.join(assets, "doodle_sheet.png")
        return os.path.join(assets, f"{skin_key}_doodle_sheet.png")

    def skin_display_name(self, skin_key):
        names = {
            "default": "Doodle",
            "carrot": "Carrot",
            "blue_bird": "Blue Bird",
            "bunny": "Bunny",
            "ninja": "Ninja",
            "chicken": "Chicken",
        }
        return names.get(skin_key, skin_key)

    def skin_preview_pixmap(self, skin_key): # return preview pixmap for skin to show in shop
        path = self.skin_sheet_path(skin_key)
        pm = QPixmap(path)
        if pm.isNull():
            return QPixmap()

        # Crop right-facing doodle from sprite sheet
        if pm.width() >= 696 and pm.height() >= 314:
            pm = pm.copy(QRect(348, 0, 348, 314))

        return pm.scaledToHeight(60, Qt.SmoothTransformation) # scale to height 60 to fit cell
    
    def make_skin_cell(self, skin_key): # create widget for skin preview + name
        w = QWidget()
        w.setFixedSize(160, 92)

        img = QLabel(w)
        img.setGeometry(0, 4, 160, 60)
        img.setAlignment(Qt.AlignCenter)

        pm = self.skin_preview_pixmap(skin_key)
        if not pm.isNull():
            img.setPixmap(pm)
        else:
            img.setText("No Image")

        name = QLabel(self.skin_display_name(skin_key), w)
        name.setGeometry(6, 64, 112, 24)
        name.setAlignment(Qt.AlignCenter)
        name.setWordWrap(True)

        return w

    def refresh(self): # reload skins into table
        if not self.db or not self.player_name:
            return
        # make sure DB contains every doodle sheet that exists in assets
        try:
            self.db.sync_skins_from_assets(
                default_price=50,
                price_overrides={
                    "carrot": 20,
                    "blue_bird": 30,
                    "bunny": 35,
                    "ninja": 40
                }
            )
        except Exception:
            pass

        player = self.db.get_player(self.player_name) # fetch player details
        coins = player[1] if player else 0  # player's coins
        active_skin = player[2] if player else "default" # selected skin

        self.title.setText(f"Player: {self.player_name} | Coins: {coins}")
        skins = self.db.get_shop_skins() # fetch available skins

        self.table.setRowCount(len(skins)) # set number of rows

        for r, (skin_key, price) in enumerate(skins):
            owned = self.db.player_owns_skin(self.player_name, skin_key) or (skin_key == "default") # check ownership
            is_active = (skin_key == active_skin) # check if active

            self.table.setItem(r, 0, QTableWidgetItem(str(skin_key))) # hidden key col

            # visible preview + name
            self.table.setCellWidget(r, 1, self.make_skin_cell(skin_key))
            self.table.setRowHeight(r, 104)

            self.table.setItem(r, 2, QTableWidgetItem(str(price))) # price col
            self.table.setItem(r, 3, QTableWidgetItem("Yes" if owned else "No")) # owned col
            self.table.setItem(r, 4, QTableWidgetItem("Yes" if is_active else "No")) # active col

        # center align price, owned, active columns
        for r in range(self.table.rowCount()):
            for c in (2, 3, 4):
                item = self.table.item(r, c)
                if item:
                    item.setTextAlignment(Qt.AlignCenter)

        self.table.setColumnWidth(1, 150) # Skin
        self.table.setColumnWidth(2, 60) # Price
        self.table.setColumnWidth(3, 60) # Owned
        self.table.setColumnWidth(4, 60) # Active

    def selected_skin_key(self): # return skin key of selected row
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)  # hidden key column
        return item.text() if item else None

    def buy_selected(self): # buy selected skin
        skin = self.selected_skin_key() # get selected skin key
        if not skin:
            QMessageBox.warning(self, "Select", "Please select a skin.")
            return

        ok, msg = self.db.buy_skin(self.player_name, skin) # attempt purchase
        QMessageBox.information(self, "Buy", "Purchased!" if ok else msg)
        self.refresh() # refresh table

    def set_active(self): # set selected skin as active
        skin = self.selected_skin_key() # get selected skin key
        if not skin:
            QMessageBox.warning(self, "Select", "Please select a skin.")
            return

        owned = self.db.player_owns_skin(self.player_name, skin) or (skin == "default") # check ownership
        if not owned:
            QMessageBox.warning(self, "Not owned", "You must buy this skin first.")
            return

        self.db.set_selected_skin(self.player_name, skin) # set as active
        QMessageBox.information(self, "Active", f"Selected skin: {skin}")
        self.refresh() # refresh table