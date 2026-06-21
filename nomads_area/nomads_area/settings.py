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

DEFAULT_ALLOWED_HOSTS = [
    "nomadsarea.com",
    "www.nomadsarea.com",
    "161.97.68.234",
    "localhost",
    "127.0.0.1",
]
ENV_ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("ALLOWED_HOSTS", "").split(",")
    if host.strip()
]
ALLOWED_HOSTS = list(dict.fromkeys(DEFAULT_ALLOWED_HOSTS + ENV_ALLOWED_HOSTS))


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
        "CONN_MAX_AGE": int(os.getenv("DB_CONN_MAX_AGE", "60")),
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

API_CACHE_TIMEOUT = int(os.getenv("API_CACHE_TIMEOUT", "10"))
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
        "ContactRequestStatusEnum": "nomads_area_app.models.ContactRequest.STATUS_CHOICES",
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

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "False") == "True"
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "True" if not DEBUG else "False") == "True"
CSRF_COOKIE_SECURE = os.getenv("CSRF_COOKIE_SECURE", "True" if not DEBUG else "False") == "True"
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv("SECURE_HSTS_INCLUDE_SUBDOMAINS", "False") == "True"
SECURE_HSTS_PRELOAD = os.getenv("SECURE_HSTS_PRELOAD", "False") == "True"
SECURE_REFERRER_POLICY = os.getenv("SECURE_REFERRER_POLICY", "same-origin")


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
    "welcome_sign": "Панель управления Nomads Area",
    "copyright": "Nomads Area",
    "custom_css": "admin/css/jazzmin-light.css",
    "show_sidebar": True,
    "navigation_expanded": True,
    "related_modal_active": True,
    "changeform_format": "horizontal_tabs",
    "hide_models": [
        "nomads_area_app.AttractionImage",
        "nomads_area_app.ItineraryDay",
        "nomads_area_app.QuizAnswerOption",
        "nomads_area_app.TourImage",
        "nomads_area_app.TourPriceTier",
        "nomads_area_app.TourRoutePoint",
    ],
    "topmenu_links": [
        {"name": "Сайт", "url": "https://www.nomadsarea.com", "new_window": True},
    ],
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.User": "fas fa-user",
        "auth.Group": "fas fa-users",
        "nomads_area_app": "fas fa-compass",
        "nomads_area_app.Tour": "fas fa-route",
        "nomads_area_app.TourCategory": "fas fa-layer-group",
        "nomads_area_app.ItineraryDay": "fas fa-calendar-day",
        "nomads_area_app.TourDate": "fas fa-calendar-alt",
        "nomads_area_app.TourPriceTier": "fas fa-tags",
        "nomads_area_app.TourImage": "fas fa-image",
        "nomads_area_app.Attraction": "fas fa-landmark",
        "nomads_area_app.ExtraService": "fas fa-concierge-bell",
        "nomads_area_app.FAQ": "fas fa-circle-question",
        "nomads_area_app.Country": "fas fa-earth-asia",
        "nomads_area_app.City": "fas fa-city",
        "nomads_area_app.Booking": "fas fa-bookmark",
        "nomads_area_app.QuizLead": "fas fa-user-tag",
        "nomads_area_app.TeamMember": "fas fa-users",
        "nomads_area_app.SiteSettings": "fas fa-gear",
    },
}

JAZZMIN_UI_TWEAKS = {
    "theme": "flatly",
    "dark_mode_theme": None,
    "default_theme_mode": "light",
    "navbar": "navbar-white navbar-light",
    "brand_colour": "navbar-dark",
    "accent": "accent-primary",
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_child_indent": True,
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success",
    },
}
