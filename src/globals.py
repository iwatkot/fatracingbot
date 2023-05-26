import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))
WORKSPACE_PATH = os.path.dirname(CURRENT_PATH)

LOG_FORMATTER = "%(name)s | %(asctime)s | %(levelname)s | %(message)s"
LOG_DIR = os.path.join(WORKSPACE_PATH, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Path to the static folder, maps should be placed here.
STATIC_DIR = os.path.join(WORKSPACE_PATH, "src", "static")
os.makedirs(STATIC_DIR, exist_ok=True)

TRACKS_DIR = os.path.join(WORKSPACE_PATH, "tracks")
os.makedirs(TRACKS_DIR, exist_ok=True)

JSON_DIR = os.path.join(WORKSPACE_PATH, "json")
os.makedirs(JSON_DIR, exist_ok=True)
JSON_RACE_INFO = os.path.join(JSON_DIR, "race_info.json")

GH_DIR = os.path.join(WORKSPACE_PATH, "gh")
os.makedirs(GH_DIR, exist_ok=True)
REPO_URL = "https://github.com/iwatkot/fatracks.git"

# Chat IDs with volunteers and staff.
TEAM_CHAT_ID = "-937192524"

# Difference between time on host in comparsion to local time.
HOUR_SHIFT = datetime.utcnow().hour - datetime.now().hour + 3

# How often the map should be updated.
MAP_TICKRATE = "*/1 * * * *"

# Paths to the env files.
# * Important: if the dev.env file exists, the app will run in dev mode.
DEV_ENV_FILE = os.path.join(WORKSPACE_PATH, "dev.env")
PROD_ENV_FILE = os.path.join(WORKSPACE_PATH, "prod.env")


class Logger(logging.getLoggerClass()):
    """Handles logging to the file and stroudt with timestamps."""

    def __init__(self, name: str):
        super().__init__(name)
        self.setLevel(logging.DEBUG)
        self.stdout_handler = logging.StreamHandler(sys.stdout)
        self.file_handler = logging.FileHandler(
            filename=self.log_file(), mode="a", encoding="utf-8"
        )
        self.fmt = LOG_FORMATTER
        self.stdout_handler.setFormatter(logging.Formatter(LOG_FORMATTER))
        self.file_handler.setFormatter(logging.Formatter(LOG_FORMATTER))
        self.addHandler(self.stdout_handler)
        self.addHandler(self.file_handler)

    def log_file(self):
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(LOG_DIR, f"{today}.txt")
        return log_file


def is_dev_mode():
    if os.path.exists(DEV_ENV_FILE):
        logger.debug(f"File {DEV_ENV_FILE} exists, the app will run in dev mode.")
        load_dotenv(DEV_ENV_FILE)
        return True
    elif os.path.exists(PROD_ENV_FILE):
        logger.debug(f"File {PROD_ENV_FILE} exists, the app will run in prod mode.")
        load_dotenv(PROD_ENV_FILE)
        return False
    else:
        raise FileNotFoundError("No dev.env or prod.env file found.")


class State:
    class Bot:
        def __init__(self):
            self.token = os.getenv("TOKEN")
            self.admins = [int(admin) for admin in os.getenv("ADMINS").split(",")]

    class DataBase:
        def __init__(self):
            self.host = os.getenv("HOST")
            self.port = int(os.getenv("PORT"))
            self.username = os.getenv("USERNAME")
            self.password = os.getenv("PASSWORD")
            self.db = os.getenv("DB")

    class Race:
        def __init__(self):
            self.info = None
            self.ongoing = False
            self.location_data = {}
            self.leaderboard = []

    def __init__(self):
        # Reads .env files and saved the app mode, must be run first.
        self.dev_mode = is_dev_mode()

        self.Bot = self.Bot()
        self.DataBase = self.DataBase()
        self.Race = self.Race()

        self.user_data = {}
        self.user_edit_field = None


logger = Logger(__name__)
AppState = State()

# Credentials for payments message.
SBP_PHONE = os.getenv("SBP_PHONE")
SBP_BANKS = os.getenv("SBP_BANKS")
SBP_CRED = os.getenv("SBP_CRED")
