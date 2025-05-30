import os
from pathlib import Path
from decouple import config
from dotenv import load_dotenv
import pymysql
import ipaddress
import os
import logging
from django.utils.log import DEFAULT_LOGGING
pymysql.install_as_MySQLdb()
load_dotenv()


load_dotenv()
BC_API_BASE_URL = os.getenv("BC_API_BASE_URL")
BC_DOMAIN = os.getenv("BC_DOMAIN")
BC_USERNAME = os.getenv("BC_USERNAME")
BC_PASSWORD = os.getenv("BC_PASSWORD")
BC_COMPANY_NAME = os.getenv("BC_COMPANY_NAME")

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY')
DEBUG = False

ALLOWED_HOSTS = ['angel24.es']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'previsiones',
    'pedidos',
	'sustituciones',
	'clientes',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'middleware.ip_address_checker.IPAddressCheckerMiddleware',
]

#Introducir las IP's validas

ALLOWED_IPS = [
    ipaddress.ip_network('192.168.0.0/16')
]


ROOT_URLCONF = 'ImportMoca.urls'
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name} - {message}",
            "style": "{",
        },
    },
    "handlers": {
        "file": {
            "level": "INFO",  # <- solo info, warning, error, critical
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": os.path.join(BASE_DIR, "logs", "django.log"),
            "when": "midnight",
            "backupCount": 32,
            "formatter": "verbose",
            "encoding": "utf-8",
            "utc": False,
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["file", "console"],
            "level": "ERROR",
            "propagate": False,
        },
        "": {  # Logger raíz
            "handlers": ["file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'ImportMoca.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'"
        }
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'Europe/Madrid'
USE_I18N = True
USE_TZ = True

# HTTPS + rutas específicas
FORCE_SCRIPT_NAME = '/importmoca'
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

STATIC_URL = '/importmoca/staticfiles/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

MEDIA_URL = '/importmoca/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Seguridad HTTPS
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
