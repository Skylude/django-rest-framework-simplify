import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_ENCRYPTION_KEY = "05oTj3MftZL8lyn0"
EMAIL_TEMPLATES_BASE_PATH = BASE_DIR + "/tests/templates/"
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "sql.drfsimp",
    },
    "readreplica": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "sql.drfsimp_rr",
    },
}


SECRET_KEY = "fake-key"
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "rest_framework_simplify",
    "tests.apps.TestAppConfig",
]
ROOT_URLCONF = "tests.urls"
