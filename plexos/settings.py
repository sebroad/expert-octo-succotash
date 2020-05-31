"""
Django settings for plexos project.

Generated by 'django-admin startproject' using Django 1.11.5.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import os, venv

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Grab environment variables from /etc/environment
if os.path.exists('/etc/environment'):
    with open('/etc/environment') as fenv:
        for line in fenv:
            os.environ.setdefault(line.split('=')[0], '='.join(line.split('=')[1:]))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'pd4whrszb4mh!b@720l$2^)6oz%uo9=(75c0r40bbqw#&mhkpm')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = bool(os.environ.get('DJANGO_DEBUG','False'))

ALLOWED_HOSTS = ['172.20.0.65','localhost','127.0.0.1']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'quote',
    'timecards',
    'leaverequest',
    'implan',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'implan.models.AuditingMiddleWare',
]

ROOT_URLCONF = 'plexos.urls'
LOGIN_URL = '/admin/login'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['quote','timecards','leaverequest','implan'],#'productselection'],
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

WSGI_APPLICATION = 'plexos.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = { 'default': {} }
DATABASES['default']['ENGINE'] = os.environ.get('DJANGO_DB_ENGINE','django.db.backends.sqlite3')
DATABASES['default']['NAME'] = os.environ.get('DJANGO_DATABASE','plexos_web.db')
DATABASES['default']['USER'] = os.environ.get('DJANGO_DB_USER','')
DATABASES['default']['PASSWORD'] = os.environ.get('DJANGO_DB_PWD','')
DATABASES['default']['HOST'] = os.environ.get('DJANGO_DB_HOST','') # localhost for MySQL
DATABASES['default']['PORT'] = os.environ.get('DJANGO_DB_PORT','') # 3306 for MySQL
if print(DATABASES)

# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'
DATE_FORMAT = 'j N Y'
TIME_ZONE = 'America/Los_Angeles'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = './static/'
