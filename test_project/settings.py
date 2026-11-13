# -*- coding: utf-8 -*-
# Bare ``settings.py`` for running tests for url_filter
import os

from sqlalchemy import create_engine


DEBUG = True
INTERNAL_IPS = ["127.0.0.1"]

if os.environ.get("USE_POSTGRES") == "True":
    SQLALCHEMY_ENGINE = create_engine(
        "postgresql://postgres:test@localhost:5432", echo=True
    )
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": "postgres",
            "USER": "postgres",
            "PASSWORD": "test",
            "HOST": "127.0.0.1",
            "PORT": "5432",
        }
    }
else:
    SQLALCHEMY_ENGINE = create_engine("sqlite:///url_filter.sqlite", echo=True)
    DATABASES = {
        "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": "url_filter.sqlite"}
    }

INSTALLED_APPS = (
    "test_project.generic",
    "test_project.many_to_many",
    "test_project.many_to_one",
    "test_project.one_to_one",
    "url_filter",
    "django_extensions",
    "rest_framework",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
)

STATIC_URL = "/static/"
SECRET_KEY = "foo"

MIDDLEWARE = [
    "test_project.middleware.SQLAlchemySessionMiddleware",
]

TEMPLATES = [
    {"BACKEND": "django.template.backends.django.DjangoTemplates", "APP_DIRS": True}
]

ROOT_URLCONF = "test_project.urls"

REST_FRAMEWORK = {
    "DEFAULT_FILTER_BACKENDS": ["url_filter.integrations.drf.DjangoFilterBackend"]
}

