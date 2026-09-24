from .base import *  # noqa: F403
from .base import env

DEBUG = False
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")

SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])
X_FRAME_OPTIONS = "DENY"

# Фото — в S3-совместимое хранилище. Исходники — в отдельный приватный бакет:
# правило доступа на бакет проще проверить, чем политику на префикс.
S3_CONNECTION = {
    "endpoint_url": env("S3_ENDPOINT_URL"),
    "access_key": env("S3_ACCESS_KEY"),
    "secret_key": env("S3_SECRET_KEY"),
    "region_name": env("S3_REGION", default="ru-central1"),
    "file_overwrite": False,
}
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            **S3_CONNECTION,
            "bucket_name": env("S3_BUCKET_NAME"),
            "querystring_auth": False,
        },
    },
    "quarantine": {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            **S3_CONNECTION,
            "bucket_name": env("S3_QUARANTINE_BUCKET_NAME"),
            "default_acl": "private",
            "querystring_auth": True,
        },
    },
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"},
}
