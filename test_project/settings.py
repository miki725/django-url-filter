# Bare ``settings.py`` for running tests for url_filter
from sqlalchemy import create_engine


DEBUG = True

SQLALCHEMY_ENGINE = create_engine('sqlite:///url_filter.sqlite', echo=True)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'url_filter.sqlite'
    }
}

INSTALLED_APPS = (
    'test_project.many_to_many',
    'test_project.many_to_one',
    'test_project.one_to_one',

    'url_filter',

    'django_extensions',
    'rest_framework',

    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
)

STATIC_URL = '/static/'
SECRET_KEY = 'foo'

MIDDLEWARE_CLASSES = [
    'test_project.middleware.SQLAlchemySessionMiddleware',
]

ROOT_URLCONF = 'test_project.urls'

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': [
        'url_filter.integrations.drf.DjangoFilterBackend',
    ],
}
