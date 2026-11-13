from core.config import BASE_DIR, config

SECRET_KEY = config.SECRET_KEY
DEBUG = config.DEBUG
ALLOWED_HOSTS = config.allowed_hosts_list

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "apps.accounts",
    "apps.catalog",
    "apps.recipes",
    "apps.orders",
]

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

ROOT_URLCONF = "core.urls"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config.POSTGRES_DB,
        "USER": config.POSTGRES_USER,
        "PASSWORD": config.POSTGRES_PASSWORD,
        "HOST": config.POSTGRES_HOST,
        "PORT": config.POSTGRES_PORT,
    }
}

CORS_ALLOWED_ORIGINS = config.cors_origins_list

LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

#AUTH_USER_MODEL = "accounts.User"