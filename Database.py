import sqlite3
import os
from paths import assets_dir, db_path
from datetime import datetime


class Database:
    def __init__(self):
        self.connection = sqlite3.connect(db_path()) # connect to database file (creates if it doesn't exist)
        self.connection.execute("PRAGMA foreign_keys = ON") # enable foreign key constraints
        self.create_tables() # create tables if they don't exist

    def create_tables(self):
        cursor = self.connection.cursor() # create a cursor object

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Players (
            name TEXT PRIMARY KEY,
            coins INTEGER NOT NULL DEFAULT 0,
            selected_skin TEXT NOT NULL DEFAULT 'default'
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT NOT NULL,
            score INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (player_name) REFERENCES Players(name) ON DELETE CASCADE
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ShopSkins (
            skin_name TEXT PRIMARY KEY,
            price INTEGER NOT NULL
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS PlayerSkins (
            player_name TEXT NOT NULL,
            skin_name TEXT NOT NULL,
            PRIMARY KEY (player_name, skin_name),
            FOREIGN KEY (player_name) REFERENCES Players(name) ON DELETE CASCADE,
            FOREIGN KEY (skin_name) REFERENCES ShopSkins(skin_name) ON DELETE CASCADE
        )
        """)

        self.connection.commit() # commit changes to database

    def discover_skin_names_from_assets(self): # discover available skin names from assets
        assets = assets_dir()
        if not os.path.isdir(assets):
            return []

        suffix = "_doodle_sheet.png" # skin sprite sheet suffix
        names = []
        for fn in os.listdir(assets): # iterate over files in assets directory
            if not fn.lower().endswith(suffix): # check for skin sprite sheet files
                continue
            name = fn[:-len(suffix)] # extract skin name from filename
            if not name or name == "default":
                continue
            names.append(name)

        return sorted(set(names)) # return unique sorted skin names

    def sync_skins_from_assets(self, default_price=50, price_overrides=None): # sync skins from assets to database
        if price_overrides is None:
            price_overrides = {} # allow custom prices for specific skins

        cursor = self.connection.cursor()

        cursor.execute(
            "INSERT OR IGNORE INTO ShopSkins (skin_name, price) VALUES (?, ?)",
            ("default", 0)
        )

        for name in self.discover_skin_names_from_assets(): # iterate over discovered skin names
            price = int(price_overrides.get(name, default_price)) # get price for skin
            cursor.execute(
                """
                INSERT INTO ShopSkins (skin_name, price)
                VALUES (?, ?)
                ON CONFLICT(skin_name) DO UPDATE SET price=excluded.price
                """,
                (name, price)
            )

        self.connection.commit()

    def ensure_player(self, name): # ensure player exists in database
        cursor = self.connection.cursor()
        cursor.execute("INSERT OR IGNORE INTO Players (name, coins, selected_skin) VALUES (?, 0, 'default')", (name,))
        cursor.execute("INSERT OR IGNORE INTO PlayerSkins (player_name, skin_name) VALUES (?, 'default')", (name,))
        self.connection.commit()

    def get_player(self, name): # fetch player details
        cursor = self.connection.cursor()
        cursor.execute("SELECT name, coins, selected_skin FROM Players WHERE name = ?", (name,))
        return cursor.fetchone()

    def add_coins(self, name, amount): # add coins to player
        cursor = self.connection.cursor()
        cursor.execute("UPDATE Players SET coins = max(0, coins + ?) WHERE name = ?", (int(amount), name))
        self.connection.commit()

    def set_selected_skin(self, name, skin_name): # set player's selected skin
        cursor = self.connection.cursor()
        cursor.execute("UPDATE Players SET selected_skin = ? WHERE name = ?", (skin_name, name))
        self.connection.commit()

    def add_score(self, player_name, score): # add a new score for player
        cursor = self.connection.cursor()
        cursor.execute(
            "INSERT INTO Scores (player_name, score, created_at) VALUES (?, ?, ?)",
            (player_name, int(score), datetime.now().isoformat(timespec="seconds"))
        )
        self.connection.commit()

    def get_top_scores(self, limit=10): # fetch top scores across all players
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT player_name, score FROM Scores ORDER BY score DESC LIMIT ?",
            (int(limit),)
        )
        return cursor.fetchall()

    def get_player_scores(self, player_name): # fetch all scores for a specific player
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT score, created_at FROM Scores WHERE player_name = ? ORDER BY created_at ASC",
            (player_name,)
        )
        return cursor.fetchall()

    def seed_skins(self): # seed shop skins from assets (if not already present)
        self.sync_skins_from_assets()

    def get_shop_skins(self): # fetch available shop skins
        cursor = self.connection.cursor()
        cursor.execute("SELECT skin_name, price FROM ShopSkins ORDER BY price ASC")
        return cursor.fetchall()

    def player_owns_skin(self, player_name, skin_name): # check if player owns a specific skin
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT 1 FROM PlayerSkins WHERE player_name = ? AND skin_name = ?",
            (player_name, skin_name)
        )
        return cursor.fetchone() is not None

    def buy_skin(self, player_name, skin_name, price=None):  # process skin purchase for player
        cursor = self.connection.cursor()

        # make sure player exists
        self.ensure_player(player_name)

        # already owned?
        if self.player_owns_skin(player_name, skin_name):
            return False, "You already own this skin."

        # get price from shop if not provided
        if price is None:
            cursor.execute("SELECT price FROM ShopSkins WHERE skin_name = ?", (skin_name,))
            row = cursor.fetchone()
            if not row:
                return False, "Skin is not available in the shop."
            price = int(row[0])
        else:
            price = int(price)

        # check coins
        cursor.execute("SELECT coins FROM Players WHERE name = ?", (player_name,))
        row = cursor.fetchone()
        coins = int(row[0]) if row else 0 # player's current coins

        if coins < price:
            return False, f"Not enough coins ({coins}/{price})."

        # purchase
        cursor.execute(
            "UPDATE Players SET coins = max(0, coins - ?) WHERE name = ?",
            (price, player_name)
        )
        cursor.execute(
            "INSERT OR IGNORE INTO PlayerSkins (player_name, skin_name) VALUES (?, ?)",
            (player_name, skin_name)
        )
        self.connection.commit()
        return True, f"Purchased {skin_name} for {price} coins."

    def close(self): # close database connection
        self.connection.close()