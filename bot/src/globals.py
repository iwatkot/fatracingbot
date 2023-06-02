import os
import sys
import logging

from pytz import timezone
from datetime import datetime, timedelta
from dotenv import load_dotenv

from googleapiclient.discovery import build
from google.oauth2 import service_account

CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))
WORKSPACE_PATH = os.path.dirname(CURRENT_PATH)

LOG_FORMATTER = "%(name)s | %(asctime)s | %(levelname)s | %(message)s"
LOG_DIR = os.path.join(WORKSPACE_PATH, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

GH_DIR = os.path.join(WORKSPACE_PATH, "tracks_repo")
os.makedirs(GH_DIR, exist_ok=True)

TRACKS_DIR = os.path.join(WORKSPACE_PATH, "tracks")
os.makedirs(TRACKS_DIR, exist_ok=True)

MAP_DIR = os.path.join(WORKSPACE_PATH, "map")
os.makedirs(MAP_DIR, exist_ok=True)
MAP_PATH = os.path.join(MAP_DIR, "map.html")

# Chat IDs with volunteers and staff.
TEAM_CHAT_ID = "-937192524"


async def get_time_shift():
    moscow_timezone = timezone("Europe/Moscow")
    utc_time = datetime.utcnow()

    hour_shift = int(moscow_timezone.utcoffset(utc_time) / timedelta(hours=1))

    logger.info(f"Time shift between UTC and Moscow time is {hour_shift} hours.")

    return hour_shift


# Difference between time on host in comparsion to local time.
HOUR_SHIFT = None

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
            self.start_time = None
            self.finishers = []

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
