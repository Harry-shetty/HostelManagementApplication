"""
Django settings for nestora project.
"""

from pathlib import Path
import os
import sys

# Load environment variables from .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent.parent / '.env')
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = BASE_DIR / 'backend'
FRONTEND_DIR = BASE_DIR / 'frontend'

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

SECRET_KEY = 'django-insecure-2ke-u3s7%f9#zlf88u&*uj3fp^$z-zqzfk3@f@hk==(rlgo(ze'

DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'housing',
    'student',
    'admin.apps.CustomAdminConfig',
]

MIDDLEWARE = [
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'

AUTHENTICATION_BACKENDS = [
    'housing.auth_backend.CachedModelBackend',
]

ROOT_URLCONF = 'nestora.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [FRONTEND_DIR / 'templates'],
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

WSGI_APPLICATION = 'nestora.wsgi.application'

# Database Configuration (Track P: PostgreSQL with automatic fallback)
DB_ENGINE = os.getenv('DB_ENGINE', '').lower()
DB_URL = os.getenv('DATABASE_URL', '')
USE_POSTGRES = DB_ENGINE in ('postgresql', 'postgres') or bool(DB_URL) or bool(os.getenv('POSTGRES_DB') or os.getenv('DB_NAME'))

if USE_POSTGRES:
    if DB_URL:
        import urllib.parse as urlparse
        _url = urlparse.urlparse(DB_URL)
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': _url.path.lstrip('/') or 'nestora',
                'USER': _url.username or 'postgres',
                'PASSWORD': _url.password or '',
                'HOST': _url.hostname or 'localhost',
                'PORT': str(_url.port or '5432'),
                'CONN_MAX_AGE': 600,
                'CONN_HEALTH_CHECKS': True,
                'OPTIONS': {
                    'connect_timeout': 10,
                    'keepalives': 1,
                    'keepalives_idle': 30,
                    'keepalives_interval': 10,
                    'keepalives_count': 5,
                }
            }
        }
    else:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': os.getenv('POSTGRES_DB', os.getenv('DB_NAME', 'nestora')),
                'USER': os.getenv('POSTGRES_USER', os.getenv('DB_USER', 'postgres')),
                'PASSWORD': os.getenv('POSTGRES_PASSWORD', os.getenv('DB_PASSWORD', '')),
                'HOST': os.getenv('POSTGRES_HOST', os.getenv('DB_HOST', 'localhost')),
                'PORT': os.getenv('POSTGRES_PORT', os.getenv('DB_PORT', '5432')),
                'CONN_MAX_AGE': 600,
                'CONN_HEALTH_CHECKS': True,
                'OPTIONS': {
                    'connect_timeout': 10,
                    'keepalives': 1,
                    'keepalives_idle': 30,
                    'keepalives_interval': 10,
                    'keepalives_count': 5,
                }
            }
        }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
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

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'nestora-memory-cache',
        'TIMEOUT': 120,
    }
}

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [FRONTEND_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = 'login'

TEST_RUNNER = 'nestora.test_runner.BackendDiscoverRunner'
