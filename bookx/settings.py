import os
from pathlib import Path
import dj_database_url

# --------------------------------------------------------------------------------------
# Core
# --------------------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-insecure")
DEBUG = True  # in dev

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"  # keep this

# Use the simple storage in DEBUG so admin loads without collectstatic
if DEBUG:
    STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
else:
    # if you use whitenoise in prod, keep this line
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Accept everything in dev; set explicit domains in prod if you want stricter control
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")

# --------------------------------------------------------------------------------------
# Applications
# --------------------------------------------------------------------------------------
INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # 3rd party
    "rest_framework",
    "rest_framework.authtoken",
    "drf_spectacular",
    "corsheaders",

    # Local apps
    "books",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",   # serve static files
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "bookx.urls"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {
        "context_processors": [
            "django.template.context_processors.debug",
            "django.template.context_processors.request",
            "django.contrib.auth.context_processors.auth",
            "django.contrib.messages.context_processors.messages",
        ]
    },
}]

WSGI_APPLICATION = "bookx.wsgi.application"

# --------------------------------------------------------------------------------------
# Database (Railway provides DATABASE_URL)
# Fallback to sqlite locally if env is absent
# --------------------------------------------------------------------------------------
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        ssl_require=False,  # Railway Postgres usually works without forcing SSL; set True if needed
    )
}

AUTH_PASSWORD_VALIDATORS = []  # keep simple for now; add validators in production if needed

# --------------------------------------------------------------------------------------
# I18N
# --------------------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_TZ = True

# --------------------------------------------------------------------------------------
# Static / Media
# - Static via WhiteNoise
# - Media: local by default; auto-switch to S3 when AWS env vars are set
# --------------------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# Optional S3 media (enable by setting AWS_STORAGE_BUCKET_NAME)
if os.getenv("AWS_STORAGE_BUCKET_NAME"):
    INSTALLED_APPS.append("storages")
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME", "eu-central-1")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_S3_SIGNATURE_VERSION = os.getenv("AWS_S3_SIGNATURE_VERSION", "s3v4")
    AWS_QUERYSTRING_AUTH = os.getenv("AWS_QUERYSTRING_AUTH", "False").lower() in {"1", "true", "yes"}
    AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}
    # If using public media without CloudFront:
    # MEDIA_URL = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --------------------------------------------------------------------------------------
# DRF / Auth
# --------------------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PARSER_CLASSES": (
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "BookX API",
    "DESCRIPTION": "Book exchange + AI advisor (v4, hardened)",
    "VERSION": "4.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SWAGGER_UI_SETTINGS": {"persistAuthorization": True},
}

# --------------------------------------------------------------------------------------
# CORS / CSRF
# - CORS for ALL (as requested)
# - CSRF trusted for Railway + optional frontend domain(s)
# --------------------------------------------------------------------------------------
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True  # if you need cookies across origins

# Comma-separated list of extra trusted origins from env, e.g. "https://yourdomain.com,https://www.yourdomain.com"
_extra_csrf = [o.strip() for o in os.getenv("CSRF_EXTRA_TRUSTED", "").split(",") if o.strip()]
CSRF_TRUSTED_ORIGINS = [
    "https://*.up.railway.app",
    "https://railway.app",
    # add your custom domains here or via CSRF_EXTRA_TRUSTED env
    *[o for o in _extra_csrf],
]

# --------------------------------------------------------------------------------------
# Security (good defaults for proxies like Railway)
# --------------------------------------------------------------------------------------
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# --------------------------------------------------------------------------------------
# Logging (simple, useful in Railway logs)
# --------------------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "[{levelname}] {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
    },
    "root": {"handlers": ["console"], "level": os.getenv("LOG_LEVEL", "INFO")},
}

# --------------------------------------------------------------------------------------
# Misc project-specific envs
# --------------------------------------------------------------------------------------
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
