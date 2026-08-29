from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "nakama-streak-dev-secret-key-2026"
DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "tracker",
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

ROOT_URLCONF = "nakama.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # str() required for Python 3.7 on Windows — WindowsPath not iterable in older Django
        "DIRS": [str(BASE_DIR / "templates")],
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

WSGI_APPLICATION = "nakama.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        # str() required for Python 3.7 on Windows — fixes "WindowsPath not iterable" crash
        "NAME": str(BASE_DIR / "db.sqlite3"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
# str() for Python 3.7 Windows compat
STATICFILES_DIRS = [str(BASE_DIR / "static")]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/tracker/"
LOGOUT_REDIRECT_URL = "/"

# ── Email (password reset, etc.) ───────────────────────────────────────────
# Sends real mail via Gmail SMTP using an App Password (2FA-protected accounts
# can't use the normal account password for SMTP — an "App Password" is a
# 16-character code generated specifically for an app, here named "Mailed").
#
# To use a different Gmail account, generate your own App Password at
# https://myaccount.google.com/apppasswords and swap the two values below.
# In production, pull these from environment variables instead of hardcoding.
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_HOST_USER = "sontrachithkumar@gmail.com"
EMAIL_HOST_PASSWORD = "qwgrpndpwhhvgvci"  # Gmail App Password (app name: Mailed), spaces removed
DEFAULT_FROM_EMAIL = "Nakama Streak ⚓ <sontrachithkumar@gmail.com>"
SERVER_EMAIL = DEFAULT_FROM_EMAIL
EMAIL_TIMEOUT = 15

# Where password reset redirects after completion
PASSWORD_RESET_TIMEOUT = 86400  # link valid 24 hours
