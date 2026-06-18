import os
from pathlib import Path

from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-secret-key")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "False") == "True"

ALLOWED_HOSTS = ["nomadsarea.com", "www.nomadsarea.com", "161.97.68.234", "localhost", "127.0.0.1"]


# Application definition

INSTALLED_APPS = [
    'jazzmin',
    "modeltranslation",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "nomads_area_app",
    "rest_framework",
    "django_filters",
    "drf_spectacular",
    "corsheaders",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "nomads_area_app.middleware.APILanguageMiddleware",
    "nomads_area.middleware.URLLanguageMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "nomads_area.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "nomads_area.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "NomadsArea2026"),
        "USER": os.getenv("DB_USER", "postgres"),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": int(os.getenv("DB_PORT", 5432)),
        "CONN_MAX_AGE": 60,
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "ru"

TIME_ZONE = "Asia/Bishkek"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = "/media/"


LANGUAGES = (
    ("ru", "Russian"),
    ("en", "English"),
    ("es", "Spanish"),
    ("fr", "French"),
    ("de", "German"),
)

MODELTRANSLATION_DEFAULT_LANGUAGE = "ru"

MODELTRANSLATION_LANGUAGES = ("ru", "en", "es", "fr", "de")


# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CACHE_URL = os.getenv("CACHE_URL", "redis://127.0.0.1:6379/1")
CACHE_BACKEND = os.getenv(
    "CACHE_BACKEND",
    "django.core.cache.backends.redis.RedisCache",
)
CACHES = {
    "default": {
        "BACKEND": CACHE_BACKEND,
        "LOCATION": CACHE_URL,
        "KEY_PREFIX": os.getenv("CACHE_KEY_PREFIX", "nomads-area"),
        "TIMEOUT": int(os.getenv("CACHE_DEFAULT_TIMEOUT", "300")),
    }
}
if CACHE_BACKEND == "django.core.cache.backends.redis.RedisCache":
    CACHES["default"]["OPTIONS"] = {
        "socket_connect_timeout": 2,
        "socket_timeout": 2,
    }

API_CACHE_TIMEOUT = int(os.getenv("API_CACHE_TIMEOUT", "60"))
API_CACHE_KEY_PREFIX = os.getenv("API_CACHE_KEY_PREFIX", "public-api-v1")


REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": os.getenv("DRF_ANON_THROTTLE_RATE", "300/minute"),
        "forms": os.getenv("DRF_FORMS_THROTTLE_RATE", "5/minute"),
    },
}


SPECTACULAR_SETTINGS = {
    "TITLE": "Nomads Area API",
    "DESCRIPTION": "Tourism DRF Backend - туры по Центральной Азии",
    "VERSION": "1.0.0",
    "ENUM_NAME_OVERRIDES": {
        "BookingStatusEnum": "nomads_area_app.models.Booking.STATUS_CHOICES",
        "PaymentStatusEnum": "nomads_area_app.models.Payment.STATUS_CHOICES",
        "ContactRequestStatusEnum": "nomads_area_app.models.ContactRequest.STATUS_CHOICES",
        "TransportRequestStatusEnum": "nomads_area_app.models.TransportRequest.STATUS_CHOICES",
    },
}

API_DOCS_ENABLED = os.getenv("API_DOCS_ENABLED", "True" if DEBUG else "False") == "True"


CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
    if origin.strip()
]

CORS_ALLOW_ALL_ORIGINS = os.getenv("CORS_ALLOW_ALL_ORIGINS", "False") == "True"
CORS_ALLOW_CREDENTIALS = True


TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True") == "True"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", os.getenv("EMAIL_HOST_USER", ""))
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", os.getenv("EMAIL_HOST_USER", ""))


FINIKPAY_API_KEY = os.getenv("FINIKPAY_API_KEY", "")
FINIKPAY_SECRET_KEY = os.getenv("FINIKPAY_SECRET_KEY", "")
FINIKPAY_BASE_URL = os.getenv("FINIKPAY_BASE_URL", "")
FINIKPAY_WEBHOOK_SECRET = os.getenv("FINIKPAY_WEBHOOK_SECRET", "")
FINIKPAY_RETURN_URL = os.getenv("FINIKPAY_RETURN_URL", "")
FINIKPAY_CANCEL_URL = os.getenv("FINIKPAY_CANCEL_URL", "")


CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 120


TRIPADVISOR_API_KEY = os.getenv("TRIPADVISOR_API_KEY", "")

TRIPADVISOR_URL = os.getenv("TRIPADVISOR_URL", "https://www.tripadvisor.com/")
TRIPADVISOR_LOCATION_ID = os.getenv("TRIPADVISOR_LOCATION_ID", "")


JAZZMIN_SETTINGS = {
    "site_title": "Nomads Area Admin",
    "site_header": "Nomads Area",
    "site_brand": "Nomads Area",
    "welcome_sign": "Добро пожаловать в админку Nomads Area",
    "copyright": "Nomads Area",
    "search_model": ["nomads_area_app.Tour", "nomads_area_app.Booking"],
    "show_sidebar": True,
    "navigation_expanded": True,
    "icons": {
        "nomads_area_app.Tour": "fas fa-map-marked-alt",
        "nomads_area_app.Booking": "fas fa-calendar-check",
        "nomads_area_app.QuizLead": "fas fa-clipboard-list",
        "nomads_area_app.ContactMessage": "fas fa-envelope",
        "nomads_area_app.Country": "fas fa-globe-asia",
        "nomads_area_app.City": "fas fa-city",
        "auth.User": "fas fa-user",
        "auth.Group": "fas fa-users",
    },
}








JAZZMIN_UI_TWEAKS = {
    "theme": "darkly",
    "dark_mode_theme": "darkly",
    "navbar": "navbar-dark navbar-dark",
    "sidebar": "sidebar-dark-primary",
    "accent": "accent-primary",
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    },
}
