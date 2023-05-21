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


DEV_ENV_FILE = os.path.join(WORKSPACE_PATH, "dev.env")
PROD_ENV_FILE = os.path.join(WORKSPACE_PATH, "prod.env")


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
            self.admins = os.getenv("ADMINS").split(",")

    class DataBase:
        def __init__(self):
            self.host = os.getenv("HOST")
            self.port = int(os.getenv("PORT"))
            self.username = os.getenv("USERNAME")
            self.password = os.getenv("PASSWORD")
            self.db = os.getenv("DB")

    def __init__(self):
        # Reads .env files and saved the app mode, must be run first.
        self.dev_mode = is_dev_mode()

        self.Bot = self.Bot()
        self.DataBase = self.DataBase()

        self.user_data = {}


logger = Logger(__name__)
AppState = State()
