import os
import mongoengine

from dotenv import load_dotenv

import globals as g

logger = g.Logger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

logger.info(f"Django starting with base dir: {BASE_DIR}")

SECRET_KEY = os.getenv("DJANGO_KEY")

if os.getenv("APP_MODE") == "prod":
    DEBUG = False
else:
    DEBUG = True

logger.info(f"Debug is set to: {DEBUG}")

HOST = os.getenv("HOST")
PORT = int(os.getenv("PORT"))
DB = os.getenv("DB")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "fatracing.ru",
    "www.fatracing.ru",
    "iwatkot.online",
]

logger.info(f"Allowed hosts: {ALLOWED_HOSTS}")

INSTALLED_APPS = [
    # * My apps.
    "app",
    # * Third-party apps.
    "bootstrap4",
    "django_bootstrap_icons",
    "mongoengine",
    # * Built-in apps.
    # "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "project.wsgi.application"


con_info = mongoengine.connect(
    host=HOST,
    port=PORT,
    db=DB,
    username=USERNAME,
    password=PASSWORD,
)

logger.info(
    f"Succesfully connected to following Mongo databases: {con_info.list_database_names()}"
)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }
}

LANGUAGE_CODE = "ru-ru"

TIME_ZONE = "Europe/Moscow"
USE_I18N = False
USE_TZ = False

logger.info(f"Lanuage code: {LANGUAGE_CODE}, time zone: {TIME_ZONE}")


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

# DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
