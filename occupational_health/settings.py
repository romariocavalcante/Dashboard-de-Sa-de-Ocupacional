import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
IS_VERCEL = bool(os.getenv("VERCEL"))


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-local-dashboard-saude-ocupacional")

DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() in {"1", "true", "yes", "on"}

ALLOWED_HOSTS = os.getenv(
    "ALLOWED_HOSTS",
    "127.0.0.1,localhost,.vercel.app"
).split(",")


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'health',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'occupational_health.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'occupational_health.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

SQLITE_DB_PATH = Path(os.getenv("SQLITE_DB_PATH", "/tmp/db.sqlite3")) if IS_VERCEL else BASE_DIR / "db.sqlite3"

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': SQLITE_DB_PATH,
        'OPTIONS': {
            'timeout': 20,
        },
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'pt-br'

TIME_ZONE = 'America/Sao_Paulo'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
CSRF_TRUSTED_ORIGINS = os.getenv(
    "CSRF_TRUSTED_ORIGINS",
    "https://*.vercel.app"
).split(",")

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/painel/'
LOGOUT_REDIRECT_URL = '/login/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
