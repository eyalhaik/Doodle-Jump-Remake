import os


def root_dir(): # return root project directory
    return os.path.dirname(os.path.abspath(__file__)) # get directory of current file (paths.py) and return it as root directory

def data_dir(): # return path to data directory
    return os.path.join(root_dir(), "data") # construct path to data directory by joining root directory with "data"

def assets_dir(): # return path to assets directory
    return os.path.join(data_dir(), "assets") # construct path to assets directory by joining data directory with "assets"

def fonts_dir(): # return path to fonts directory
    return os.path.join(data_dir(), "fonts")

def sounds_dir(): # return path to sounds directory
    return os.path.join(data_dir(), "sounds")

def settings_path(): # return path to settings.json file
    os.makedirs(data_dir(), exist_ok=True)
    return os.path.join(data_dir(), "settings.json")

def db_path(): # return path to SQLite database file
    return os.path.join(root_dir(), "doodle.db")

def asset_path(filename): # return path to asset file
    return os.path.join(assets_dir(), filename) # construct path to asset file by joining assets directory with filename

def font_path(filename): # return path to font file
    return os.path.join(fonts_dir(), filename)

def sound_path(filename): # return path to sound file
    return os.path.join(sounds_dir(), filename)