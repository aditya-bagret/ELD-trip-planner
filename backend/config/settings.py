import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_list(name):
    return [v.strip() for v in os.getenv(name, "").split(",") if v.strip()]


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-insecure-key")
DEBUG = os.getenv("DEBUG", "False") == "True"
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS") or ["localhost", "127.0.0.1"]
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS")
ORS_API_KEY = os.getenv("ORS_API_KEY", "")

INSTALLED_APPS = ["corsheaders", "trips"]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {}

USE_TZ = False
