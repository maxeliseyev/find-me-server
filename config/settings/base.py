"""Базовые настройки. Переопределяются в local/production/test."""

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="insecure-dev-key-change-me")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=[])

# --- Приложения ---

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
]

LOCAL_APPS = [
    "apps.core",
    "apps.accounts",
    "apps.pets",
    "apps.reports",
    "apps.sightings",
    "apps.geo",
    "apps.moderation",
    "apps.chat",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# --- База данных ---
# PostgreSQL 16 + PostGIS, все координаты — geography(Point, 4326).

DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default="postgis://findme:findme@localhost:5432/findme",
    ),
}
DATABASES["default"]["ENGINE"] = "django.contrib.gis.db.backends.postgis"
DATABASES["default"]["CONN_MAX_AGE"] = env.int("DATABASE_CONN_MAX_AGE", default=60)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"

# GeoDjango на macOS не всегда находит библиотеки сам.
GDAL_LIBRARY_PATH = env("GDAL_LIBRARY_PATH", default=None)
GEOS_LIBRARY_PATH = env("GEOS_LIBRARY_PATH", default=None)

# --- Кэш и очередь ---

REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    },
}

CELERY_BROKER_URL = env("CELERY_BROKER_URL", default=REDIS_URL)
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default=REDIS_URL)
CELERY_TASK_ALWAYS_EAGER = False
CELERY_TASK_TIME_LIMIT = 300
CELERY_TASK_SOFT_TIME_LIMIT = 240

# --- Статика и медиа ---

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# S3-совместимое хранилище для фото; в dev — локальная файловая система.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

# --- Локаль ---

LANGUAGE_CODE = "ru-ru"
TIME_ZONE = env("DJANGO_TIME_ZONE", default="Europe/Moscow")
USE_I18N = True
USE_TZ = True

# --- API ---

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_RATES": {
        # Отметку ставят без регистрации — рейтлимит здесь единственная защита.
        "anon_sighting": "10/hour",
        "user_sighting": "60/hour",
    },
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Find Me API",
    "DESCRIPTION": "Сервис поиска потерянных животных",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])

# --- Доменные настройки (см. спеку) ---

# Раздел 9: точка пропажи — обычно подъезд владельца, публично показываем смещённой.
PUBLIC_LOCATION_BLUR_M = env.int("PUBLIC_LOCATION_BLUR_M", default=250)

# Раздел 6.2: период полураспада веса отметки, часы.
SIGHTING_HALF_LIFE_HOURS = {"cat": 12, "dog": 36, "bird": 12, "other": 24}

# Раздел 8: защита от выгорания подписчиков.
NOTIFICATIONS_DAILY_CAP = env.int("NOTIFICATIONS_DAILY_CAP", default=15)
NOTIFICATIONS_QUIET_HOURS = (22, 9)
NOTIFICATIONS_DEDUP_WINDOW_MIN = 30

TELEGRAM_BOT_TOKEN = env("TELEGRAM_BOT_TOKEN", default="")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"simple": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"}},
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
    },
    "root": {"handlers": ["console"], "level": env("DJANGO_LOG_LEVEL", default="INFO")},
}
