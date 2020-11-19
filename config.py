import os
import platform

HOST_OS = platform.system()

ROOT_DIR = os.getcwd()

if HOST_OS == 'Darwin':
    # For Apple
    DB_PATH = os.path.join(ROOT_DIR, "database/saved.db")
    SAVED_DIR = os.path.join(ROOT_DIR, "database/images/")
elif HOST_OS == 'Windows':
    # For Windows
    DB_PATH = os.path.join(ROOT_DIR, "database\\saved.db")
    SAVED_DIR = os.path.join(ROOT_DIR, "database\\images\\")
