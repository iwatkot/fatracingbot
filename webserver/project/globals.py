import logging
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LOG_FORMATTER = "%(name)s | %(asctime)s | %(levelname)s | %(message)s"
LOG_DIR = os.path.join(WORKSPACE_DIR, "logs")
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


logger = Logger(__name__)

DEV_KEY = os.path.join(WORKSPACE_DIR, "dev.env")
PROD_KEY = os.path.join(WORKSPACE_DIR, "prod.env")

if os.path.exists(DEV_KEY):
    os.environ["APP_MODE"] = "dev"
    logger.info(f"Dev file found: {DEV_KEY}, app mode set to dev.")
    load_dotenv(DEV_KEY)
elif os.path.exists(PROD_KEY):
    os.environ["APP_MODE"] = "prod"
    logger.info(f"Prod file found: {PROD_KEY}, app mode set to prod.")
    load_dotenv(PROD_KEY)
else:
    logger.error("Can't find neither dev.env nor prod.env, exiting.")
    raise FileNotFoundError(
        "At least one of the env files (dev or prod) must be present."
    )
