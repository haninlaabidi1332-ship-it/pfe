"""
Base settings for SUPERVISION OLT project.
"""
import os
from pathlib import Path
from datetime import timedelta
from celery.schedules import crontab
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

SECRET_KEY = env("SECRET_KEY", default="django-insecure-hob-u(oh$bfu9z8jb09a@x)sb4otmthv%9jsk49j+9ha#$*qa#")
DEBUG = env("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# Application definition
DJANGO_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    'import_export',
    'django_extensions',
    'channels',
    'django_celery_beat',
    'django_celery_results',
    'drf_spectacular',
]

LOCAL_APPS = [
    'apps.core',
    'apps.users',
    'apps.olt_inventory',
    'apps.olt_monitoring',
    'apps.olt_analytics',
    'apps.olt_alerts',
    'apps.olt_dashboard',
    'apps.olt_api',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.middleware.RequestLoggingMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "config.wsgi.application"

# Database
DATABASES = {
    "default": {
        "ENGINE": env("DB_ENGINE", default="django.db.backends.postgresql"),
        "NAME": env("DB_NAME", default="olt_supervision_db"),
        "USER": env("DB_USER", default="olt_supervision_admin"),
        "PASSWORD": env("DB_PASSWORD", default="123456"),
        "HOST": env("DB_HOST", default="localhost"),
        "PORT": env("DB_PORT", default="5432"),
    },
}

# Custom user model
AUTH_USER_MODEL = 'users.User'

# Authentication backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'apps.users.authentication.EmailAuthBackend',
]

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ─── REST Framework ───────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.StandardPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
        "user": "1000/hour",
        "login": "10/minute",
    },
    "EXCEPTION_HANDLER": "apps.core.exceptions.custom_exception_handler",
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.NamespaceVersioning",
    "ALLOWED_VERSIONS": ['v1'],
    "DEFAULT_VERSION": 'v1',
}

# ─── JWT ──────────────────────────────────────────────────────────────────────
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env.int("ACCESS_TOKEN_LIFETIME_MINUTES", default=60)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env.int("REFRESH_TOKEN_LIFETIME_DAYS", default=7)),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'TOKEN_OBTAIN_SERIALIZER': 'apps.users.serializers.CustomTokenObtainSerializer',
}

# ─── CORS ─────────────────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[
    "http://localhost:3000",
    "http://127.0.0.1:3000",
])
CORS_ALLOW_CREDENTIALS = True

# ============================================================================
# CHANNELS CONFIGURATION (WebSocket)
# ============================================================================
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {"hosts": [('127.0.0.1', 6379)]},
    },
}
if DEBUG:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    }

# ============================================================================
# EMAIL CONFIGURATION
# ============================================================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@oltsupervision.com")

# ============================================================================
# SMS / SLACK / TEAMS (optionnel)
# ============================================================================
TWILIO_ACCOUNT_SID = env("TWILIO_ACCOUNT_SID", default="")
TWILIO_AUTH_TOKEN = env("TWILIO_AUTH_TOKEN", default="")
TWILIO_PHONE_NUMBER = env("TWILIO_PHONE_NUMBER", default="")
SLACK_BOT_TOKEN = env("SLACK_BOT_TOKEN", default="")
SLACK_SIGNING_SECRET = env("SLACK_SIGNING_SECRET", default="")
TEAMS_WEBHOOK_URL = env("TEAMS_WEBHOOK_URL", default="")
TELEGRAM_BOT_TOKEN = env("TELEGRAM_BOT_TOKEN", default="")
TELEGRAM_CHAT_ID = env("TELEGRAM_CHAT_ID", default="")

# ============================================================================
# CELERY CONFIGURATION
# ============================================================================
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_TASK_SOFT_TIME_LIMIT = 20 * 60

CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_BEAT_SCHEDULE = {
    'collect-snmp-metrics-every-30s': {
        'task': 'apps.olt_monitoring.tasks.collect_all_metrics',
        'schedule': 30.0,
    },
    'check-anomalies-every-minute': {
        'task': 'apps.olt_analytics.tasks.analyze_olt_metrics',
        'schedule': 60.0,
    },
}

# ─── API Docs ─────────────────────────────────────────────────────────────────
SPECTACULAR_SETTINGS = {
    "TITLE": "OLT Supervision API",
    "DESCRIPTION": "API de supervision d'équipements OLT (SNMP, BFD, anomalies, alertes)",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SWAGGER_UI_SETTINGS": {
        "persistAuthorization": True,
    },
}

# ─── Jazzmin Admin Theme ──────────────────────────────────────────────────────
# Vous pouvez conserver ou supprimer la ligne d'import selon que vous utilisez jazzmin_settings
# from .jazzmin_settings import *

# ─── File Uploads ─────────────────────────────────────────────────────────────
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
FILE_UPLOAD_PERMISSIONS = 0o644

# ─── Security Headers ─────────────────────────────────────────────────────────
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = not DEBUG
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG

# ─── Rate Limiting ────────────────────────────────────────────────────────────
LOGIN_RATE_LIMIT = env("LOGIN_RATE_LIMIT", default="10/m")

# ─── Test Runner ──────────────────────────────────────────────────────────────
TEST_RUNNER = 'django.test.runner.DiscoverRunner'
TEST_NON_SERIALIZED_APPS = ['django.contrib.contenttypes', 'django.contrib.auth']

# ─── Session Configuration ────────────────────────────────────────────────────
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 86400
SESSION_SAVE_EVERY_REQUEST = True

# ─── CSRF Trusted Origins ─────────────────────────────────────────────────────
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[
    "http://localhost:3000",
    "http://127.0.0.1:3000",
])

# ─── Internal IPs ─────────────────────────────────────────────────────────────
INTERNAL_IPS = env.list("INTERNAL_IPS", default=["127.0.0.1", "localhost"])

# ─── Frontend / Backend URLs ──────────────────────────────────────────────────
FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:3000")
BACKEND_URL = env("BACKEND_URL", default="http://localhost:8000")

# ─── Site Information ─────────────────────────────────────────────────────────
SITE_NAME = "OLT Supervision Platform"
SITE_DESCRIPTION = "Plateforme de supervision d'équipements OLT"
CONTACT_EMAIL = env("CONTACT_EMAIL", default="admin@oltsupervision.com")
SUPPORT_EMAIL = env("SUPPORT_EMAIL", default="support@oltsupervision.com")

# ─── SNMP Defaults ───────────────────────────────────────────────────────────
SNMP_DEFAULT_COMMUNITY = env("SNMP_DEFAULT_COMMUNITY", default="public")
SNMP_DEFAULT_PORT = env.int("SNMP_DEFAULT_PORT", default=161)
SNMP_TIMEOUT = env.float("SNMP_TIMEOUT", default=5.0)
SNMP_RETRIES = env.int("SNMP_RETRIES", default=2)

# ─── Alert Thresholds ─────────────────────────────────────────────────────────
ALERT_CPU_THRESHOLD = env.float("ALERT_CPU_THRESHOLD", default=85.0)
ALERT_TEMPERATURE_THRESHOLD = env.float("ALERT_TEMPERATURE_THRESHOLD", default=75.0)
ALERT_PACKET_LOSS_THRESHOLD = env.float("ALERT_PACKET_LOSS_THRESHOLD", default=1.0)
ALERT_RX_POWER_THRESHOLD = env.float("ALERT_RX_POWER_THRESHOLD", default=-25.0)

# ─── ML Analytics (optionnel) ─────────────────────────────────────────────────
ML_MODELS_PATH = BASE_DIR / "data" / "ml_models"
ML_AUTO_RETRAIN = env.bool("ML_AUTO_RETRAIN", default=False)
ML_RETRAIN_FREQUENCY_HOURS = env.int("ML_RETRAIN_FREQUENCY_HOURS", default=24)

# ─── Logging ──────────────────────────────────────────────────────────────────
LOG_LEVEL = env("LOG_LEVEL", default="INFO")
LOG_FILE = BASE_DIR / "logs" / "olt_supervision.log"

AUTH_USER_MODEL = 'users.User'