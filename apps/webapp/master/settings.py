# -*- coding: utf-8 -*-

import os

MASTER_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "../master/",
    ),
)

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
)

MANAGERS = ADMINS

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "io",
        "USER": "",
        "PASSWORD": "",
        "HOST": "127.0.0.1",
        "PORT": "3306",
        "TEST_MIRROR": "test_default",
    },
    "test_default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "test.db",
    }
}

TIME_ZONE = "Asia/Seoul"
LANGUAGE_CODE = "en-us"
SITE_ID = 1
USE_I18N = True
USE_L10N = True
MEDIA_ROOT = ""
MEDIA_URL = "/_media/"
STATICFILES_ROOT = "/tmp/_static/"
STATICFILES_URL = "/_m/"
ADMIN_MEDIA_PREFIX = "/static/admin/"

STATICFILES_DIRS = (
    "master/templates/media/",
)
STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",

)
SECRET_KEY = "()c!8s@7asblqy7$&(dfmipn92u-zla)s$za@r)$&yzx#o3-jm"
TEMPLATE_LOADERS = (
    #"django_modules.template.loaders.include_media_loader.Loader",
    "django.template.loaders.filesystem.Loader",
    "django.template.loaders.app_directories.Loader",
)
MIDDLEWARE_CLASSES = (
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.transaction.TransactionMiddleware",
    "django.middleware.gzip.GZipMiddleware",

    "master.middlewares.CheckAuthenticated",
    "master.middlewares.ExceptionHandler",
)
ROOT_URLCONF = "master.urls"
TEMPLATE_DIRS = (
    "master/templates",
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.contrib.messages.context_processors.messages",
    "django.core.context_processors.request",

    "django_modules.context_processors.read_settings",
    "master.context_processors.projects",
    "master.context_processors.profile_labels",
)
INSTALLED_APPS = (
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    #"django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "django.contrib.admin",

    "django_modules.common_app",

    "IO.common",
    "IO.developer",
    "IO.project",
    "IO.version_control",
    "IO.dialog",
)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "mail_admins": {
            "level": "ERROR",
            "class": "django.utils.log.AdminEmailHandler"
        }
    },
    "loggers": {
        "django.request":{
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": True,
        },
    }
}

LOGIN_URL = "/accounts/login/"
AUTH_PROFILE_MODULE = "developer.Profile"

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

import os

STORAGE_PATH = os.path.abspath(
    os.path.join(
        MASTER_PATH,
        "../../../storage/",
    ),
)

MEDIA_ROOT = STORAGE_PATH

VERSION_CONTROL_STORAGE_PATH = os.path.join(
    STORAGE_PATH,
    "version_control",
)

EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_HOST_USER = ""
EMAIL_HOST_PASSWORD = ""
EMAIL_USE_TLS = True

EMAIL_IO = ""

try :
    from settings_local import *
except :
    pass

EMAIL_IO_SERVICE_PARTED = tuple(EMAIL_IO.split("@", 1), )

EMAIL_IO_SERVICE = "%s+service@%s" % EMAIL_IO_SERVICE_PARTED


